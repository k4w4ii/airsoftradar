-- =====================================================================
-- TELJES TELEPÍTÉS EGY LÉPÉSBEN (Supabase SQL Editor)
-- Törli az árkereső táblákat (ha vannak), majd lefuttatja a 0001–0004 migrációkat sorrendben.
-- Bármikor újrafuttatható. FIGYELEM: a meglévő árkereső-adatok elvesznek!
-- =====================================================================
drop materialized view if exists product_summary cascade;
drop view if exists v_offers cascade;
drop view if exists latest_rates cascade;
drop table if exists price_alerts, scrape_runs, match_candidates, price_history, offers, product_codes,
                     products, categories, manufacturer_aliases, manufacturers, shops, exchange_rates cascade;
drop function if exists refresh_product_summary();
drop type if exists stock_status, match_status, code_type, power_source cascade;


-- >>>>>>>>>> migrations/0001_init.sql
-- =====================================================================
-- Airsoft árkereső – MVP séma (PostgreSQL 15+ / Supabase)
-- =====================================================================
create extension if not exists pg_trgm;

-- ---------- Enumok ----------
create type stock_status   as enum ('in_stock', 'out_of_stock', 'preorder', 'unknown');
create type match_status   as enum ('pending', 'auto', 'review', 'manual', 'rejected');
create type code_type      as enum ('model', 'ean', 'alt');
create type power_source   as enum ('aeg', 'gbb', 'gas_nbb', 'hpa', 'spring', 'other');

-- ---------- Törzsadatok ----------
create table shops (
    id                 smallint generated always as identity primary key,
    slug               text unique not null,             -- 'gunfire'
    name               text not null,
    base_url           text not null,
    country            char(2) not null,                 -- 'PL', 'HU', 'CZ'
    currency           char(3) not null,                 -- 'PLN', 'EUR', 'HUF', 'CZK'
    affiliate_template text,                             -- 'https://x.com/aff?u={url}&id=123'
    scraper_key        text not null,                    -- adapter neve a Python oldalon
    is_active          boolean not null default true,
    last_scraped_at    timestamptz
);

create table manufacturers (
    id    integer generated always as identity primary key,
    slug  text unique not null,                          -- 'tokyo-marui'
    name  text not null                                  -- 'Tokyo Marui'
);

-- 'TM', 'tokyomarui', 'marui' -> Tokyo Marui. Normalizált (lowercase, csak a-z0-9).
create table manufacturer_aliases (
    alias_norm       text primary key,
    manufacturer_id  integer not null references manufacturers on delete cascade
);

create table categories (
    id         smallint generated always as identity primary key,
    slug       text unique not null,
    name_hu    text not null,
    parent_id  smallint references categories
);

-- ---------- Kanonikus termék (ez jelenik meg a frontend-en) ----------
create table products (
    id               bigint generated always as identity primary key,
    manufacturer_id  integer not null references manufacturers,
    model_code       text,                               -- megjelenítési forma: 'CM.522'
    model_code_norm  text,                               -- párosítási kulcs: 'CM522'
    name             text not null,
    slug             text unique not null,
    category_id      smallint references categories,
    power_source     power_source,
    image_url        text,
    search_text      text generated always as (lower(name || ' ' || coalesce(model_code, ''))) stored,
    created_at       timestamptz not null default now(),
    unique (manufacturer_id, model_code_norm)
);
create index products_search_trgm on products using gin (search_text gin_trgm_ops);
create index products_category on products (category_id);

-- Több kód ugyanarra a termékre (EAN, régi/alternatív gyári kód).
-- A párosító ELŐSZÖR ebben keres.
create table product_codes (
    product_id  bigint not null references products on delete cascade,
    code_type   code_type not null,
    code_norm   text not null,
    manufacturer_id integer references manufacturers,    -- EAN-nél null (globálisan egyedi)
    primary key (code_type, code_norm, product_id)
);
create unique index product_codes_ean_uq   on product_codes (code_norm) where code_type = 'ean';
create unique index product_codes_model_uq on product_codes (manufacturer_id, code_norm) where code_type <> 'ean';

-- ---------- Bolti ajánlatok (1 sor = 1 termékoldal egy boltban) ----------
create table offers (
    id                bigint generated always as identity primary key,
    shop_id           smallint not null references shops,
    external_id       text not null,                     -- bolt saját ID / URL hash
    url               text not null,
    title_raw         text not null,
    brand_raw         text,
    sku_raw           text,                              -- bolt által adott kód (lehet belső!)
    ean_raw           text,
    image_url         text,
    price             numeric(12,2) not null check (price >= 0),
    currency          char(3) not null,
    stock             stock_status not null default 'unknown',
    product_id        bigint references products on delete set null,
    match_status      match_status not null default 'pending',
    match_method      text,                              -- 'ean' | 'code' | 'fuzzy' | 'new' | 'manual'
    match_confidence  real,
    is_active         boolean not null default true,     -- false, ha N napig nem láttuk
    first_seen_at     timestamptz not null default now(),
    last_seen_at      timestamptz not null default now(),
    unique (shop_id, external_id)
);
create index offers_product on offers (product_id) where is_active;
create index offers_match_queue on offers (match_status) where match_status in ('pending', 'review');

-- Napi 1 pont / ajánlat (upsert). HUF a napi árfolyamon rögzítve -> történeti diagram.
create table price_history (
    offer_id     bigint not null references offers on delete cascade,
    observed_on  date not null default current_date,
    price        numeric(12,2) not null,
    currency     char(3) not null,
    price_huf    numeric(12,0) not null,
    stock        stock_status not null,
    primary key (offer_id, observed_on)
);

-- ---------- Árfolyam (MNB) ----------
create table exchange_rates (
    currency   char(3) not null,
    rate_date  date not null,
    huf_per_unit numeric(12,4) not null check (huf_per_unit > 0),  -- MNB 'unit'-tal már elosztva
    source     text not null default 'MNB',
    primary key (currency, rate_date)
);

-- Legfrissebb árfolyam devizánként (hétvégén/ünnepnap is működik). HUF = 1.
create view latest_rates as
select distinct on (currency) currency, huf_per_unit, rate_date
from exchange_rates
order by currency, rate_date desc;

create view v_offers as
select o.*,
       round(o.price * case when o.currency = 'HUF' then 1 else r.huf_per_unit end)::numeric(12,0) as price_huf
from offers o
left join latest_rates r on r.currency = o.currency;

-- ---------- Párosítási review sor ----------
create table match_candidates (
    offer_id    bigint not null references offers on delete cascade,
    product_id  bigint not null references products on delete cascade,
    score       real not null,
    reasons     jsonb not null default '{}',
    created_at  timestamptz not null default now(),
    primary key (offer_id, product_id)
);

-- ---------- Üzemeltetés ----------
create table scrape_runs (
    id            bigint generated always as identity primary key,
    shop_id       smallint references shops,
    started_at    timestamptz not null default now(),
    finished_at   timestamptz,
    status        text not null default 'running',       -- running | ok | partial | failed
    offers_seen   integer default 0,
    offers_new    integer default 0,
    errors        jsonb default '[]'
);

-- ---------- Árriasztás (2. fázis, a séma már kész) ----------
create table price_alerts (
    id                bigint generated always as identity primary key,
    user_id           uuid not null references auth.users on delete cascade,
    product_id        bigint not null references products on delete cascade,
    target_price_huf  numeric(12,0) not null,
    is_active         boolean not null default true,
    last_notified_at  timestamptz,
    created_at        timestamptz not null default now(),
    unique (user_id, product_id)
);

-- ---------- Listázó nézet (frontend fő forrása) ----------
create materialized view product_summary as
select p.id, p.slug, p.name, p.model_code, p.image_url, p.category_id,
       m.name                                                     as manufacturer,
       min(v.price_huf) filter (where v.stock = 'in_stock')        as best_price_huf,
       min(v.price_huf)                                            as min_price_any_huf,
       count(*)                                                    as offer_count,
       count(*) filter (where v.stock = 'in_stock')                as in_stock_count,
       case
         when bool_or(v.stock = 'in_stock') then 'in_stock'
         when bool_or(v.stock = 'preorder') then 'preorder'
         when bool_or(v.stock = 'out_of_stock') then 'out_of_stock'
         else 'unknown'
       end::stock_status                                           as stock
from products p
join manufacturers m on m.id = p.manufacturer_id
join v_offers v on v.product_id = p.id and v.is_active
group by p.id, m.name;
create unique index product_summary_id on product_summary (id);
create index product_summary_price on product_summary (best_price_huf);

-- Scrape után hívandó (service role, RPC-ként: supabase.rpc('refresh_product_summary'))
create function refresh_product_summary() returns void
language sql security definer as $$
    refresh materialized view concurrently product_summary;
$$;

-- ---------- RLS: publikus olvasás, írás csak service role-lal ----------
alter table shops            enable row level security;
alter table manufacturers    enable row level security;
alter table categories       enable row level security;
alter table products         enable row level security;
alter table offers           enable row level security;
alter table price_history    enable row level security;
alter table exchange_rates   enable row level security;
alter table price_alerts     enable row level security;
alter table match_candidates enable row level security;
alter table product_codes    enable row level security;
alter table manufacturer_aliases enable row level security;
alter table scrape_runs      enable row level security;

create policy read_all on shops          for select using (true);
create policy read_all on manufacturers  for select using (true);
create policy read_all on categories     for select using (true);
create policy read_all on products       for select using (true);
create policy read_all on offers         for select using (true);
create policy read_all on price_history  for select using (true);
create policy read_all on exchange_rates for select using (true);
create policy own_alerts on price_alerts for all
    using (auth.uid() = user_id) with check (auth.uid() = user_id);

grant select on product_summary, v_offers, latest_rates to anon, authenticated;
revoke execute on function refresh_product_summary() from public, anon, authenticated;

-- >>>>>>>>>> migrations/0002_seed.sql
-- 0002: törzsadatok (boltok, gyártók, kategóriák) – migrációként, hogy a későbbi migrációk ráépülhessenek
-- Boltok (weboldal_pelda.txt alapján)
insert into shops (slug, name, base_url, country, currency, scraper_key) values
  ('gunfire',         'Gunfire',          'https://gunfire.com',          'PL', 'PLN', 'jsonld'),
  ('taiwangun',       'Taiwangun',        'https://www.taiwangun.com',    'PL', 'EUR', 'jsonld'),
  ('evike-europe',    'Evike Europe',     'https://evike-europe.com',     'HU', 'EUR', 'jsonld'),
  ('powair6',         'Powair6',          'https://www.powair6.com',      'FR', 'EUR', 'jsonld'),
  ('airsoftpro',      'AirsoftPro',       'https://airsoftpro.cz',        'CZ', 'CZK', 'jsonld'),
  ('combat-zone',     'Combat-Zone',      'https://www.combat-zone.hu',   'HU', 'HUF', 'jsonld'),
  ('airsoftplaza',    'AirsoftPlaza',     'https://airsoftplaza.hu',      'HU', 'HUF', 'jsonld'),
  ('airsoftcentrum',  'AirsoftCentrum',   'https://www.airsoftcentrum.hu','HU', 'HUF', 'jsonld');

-- Gyártók + aliasok (alias_norm: lowercase, csak a-z0-9)
insert into manufacturers (slug, name) values
  ('cyma','CYMA'), ('specna-arms','Specna Arms'), ('tokyo-marui','Tokyo Marui'),
  ('gg-armament','G&G Armament'), ('ares','ARES'), ('double-bell','Double Bell'),
  ('arcturus','Arcturus'), ('lct','LCT'), ('e-and-l','E&L'), ('krytac','Krytac'),
  ('vfc','VFC'), ('we','WE'), ('jg','JG'), ('arsenal','Arsenal (ASG)');

insert into manufacturer_aliases (alias_norm, manufacturer_id)
select a, m.id from manufacturers m
join (values
  ('cyma','cyma'), ('specnaarms','specna-arms'), ('specna','specna-arms'),
  ('tokyomarui','tokyo-marui'), ('marui','tokyo-marui'), ('tm','tokyo-marui'),
  ('ggarmament','gg-armament'), ('gg','gg-armament'), ('ares','ares'),
  ('doublebell','double-bell'), ('db','double-bell'), ('arcturus','arcturus'),
  ('lct','lct'), ('el','e-and-l'), ('eandl','e-and-l'), ('krytac','krytac'),
  ('vfc','vfc'), ('vegaforcecompany','vfc'), ('we','we'), ('jg','jg'),
  ('arsenal','arsenal'), ('asg','arsenal')
) v(a, slug) on v.slug = m.slug;

insert into categories (slug, name_hu) values
  ('aeg-rifle','Elektromos puskák (AEG)'), ('gbb-rifle','Gázos puskák (GBBR)'),
  ('pistol','Pisztolyok'), ('sniper','Mesterlövész puskák'), ('dmr','DMR'), ('smg','Géppisztolyok');

-- >>>>>>>>>> migrations/0003_i18n_multicurrency.sql
-- =====================================================================
-- 0003: európai kiterjesztés – HU + EN nyelv, EUR kijelzés, szállítási országok
-- Belső bázisdeviza marad a HUF (MNB); EUR = HUF / EUR-árfolyam.
-- Egyéb kijelzési devizák (PLN, CZK, GBP...) a frontend-en számolva a latest_rates-ből.
-- =====================================================================

-- Kategória-nevek angolul
alter table categories add column name_en text;
update categories set name_en = v.en from (values
  ('aeg-rifle','Electric rifles (AEG)'), ('gbb-rifle','Gas rifles (GBBR)'), ('pistol','Pistols'),
  ('sniper','Sniper rifles'), ('dmr','DMR'), ('smg','SMGs')) v(slug, en)
where categories.slug = v.slug;
alter table categories alter column name_en set not null;

-- Bolt: oldal nyelve (terméknév-forráshoz) + hova szállít
alter table shops add column lang char(2) not null default 'en';
alter table shops add column ships_to char(2)[] not null default '{}';   -- üres = ismeretlen
create index shops_ships_to on shops using gin (ships_to);
update shops set lang = 'hu' where country = 'HU' and slug <> 'evike-europe';
update shops set lang = 'cs' where slug = 'airsoftpro';

-- Kanonikus terméknév nyelve: angol bolt címe felülírhatja a magyart/csehet
alter table products add column name_lang char(2) not null default 'en';

-- Ártörténet EUR-ban is (napi árfolyamon rögzítve)
alter table price_history add column price_eur numeric(12,2);

-- Nézetek újraépítése EUR oszloppal
drop materialized view product_summary;
drop view v_offers;

create view v_offers as
with eur as (select huf_per_unit from latest_rates where currency = 'EUR')
select o.*,
       round(o.price * case when o.currency = 'HUF' then 1 else r.huf_per_unit end)::numeric(12,0) as price_huf,
       round(o.price * case when o.currency = 'HUF' then 1 else r.huf_per_unit end
             / (select huf_per_unit from eur), 2)::numeric(12,2)                                       as price_eur
from offers o
left join latest_rates r on r.currency = o.currency;

create materialized view product_summary as
select p.id, p.slug, p.name, p.model_code, p.image_url, p.category_id,
       m.name                                                     as manufacturer,
       min(v.price_huf) filter (where v.stock = 'in_stock')        as best_price_huf,
       min(v.price_eur) filter (where v.stock = 'in_stock')        as best_price_eur,
       min(v.price_eur)                                            as min_price_any_eur,
       count(*)                                                    as offer_count,
       count(*) filter (where v.stock = 'in_stock')                as in_stock_count,
       array_agg(distinct s.country)                               as shop_countries,
       case
         when bool_or(v.stock = 'in_stock') then 'in_stock'
         when bool_or(v.stock = 'preorder') then 'preorder'
         when bool_or(v.stock = 'out_of_stock') then 'out_of_stock'
         else 'unknown'
       end::stock_status                                           as stock
from products p
join manufacturers m on m.id = p.manufacturer_id
join v_offers v on v.product_id = p.id and v.is_active
join shops s on s.id = v.shop_id
group by p.id, m.name;
create unique index product_summary_id on product_summary (id);
create index product_summary_price on product_summary (best_price_eur);

grant select on product_summary, v_offers to anon, authenticated;

-- >>>>>>>>>> migrations/0004_more_manufacturers.sql
-- Kétértelmű angol szavak (well, bolt, ultimate, evolution) szándékosan NEM címalias.
-- 0004: probe alapján hiányzó gyártók + gyakori európai márkák; Gunfire /en EUR-ban ad árat
update shops set currency = 'EUR' where slug = 'gunfire';

insert into manufacturers (slug, name) values
  ('emg','EMG'), ('amoeba','Amoeba'), ('novritsch','Novritsch'), ('classic-army','Classic Army'),
  ('ics','ICS'), ('kwa','KWA'), ('bolt','BOLT'), ('aps','APS'), ('golden-eagle','Golden Eagle'),
  ('cybergun','Cybergun'), ('umarex','Umarex'), ('kj-works','KJ Works'), ('action-army','Action Army'),
  ('silverback','Silverback'), ('well','Well'), ('lancer-tactical','Lancer Tactical'),
  ('evolution','Evolution Airsoft'), ('nuprol','Nuprol'), ('delta-armory','Delta Armory'),
  ('modify','Modify'), ('snow-wolf','Snow Wolf'), ('king-arms','King Arms'), ('vorsk','Vorsk'),
  ('asg','ASG'), ('ultimate','Ultimate'), ('src','SRC'), ('apex','APEX'), ('real-sword','Real Sword')
on conflict (slug) do nothing;

-- 'arsenal' korábban 'asg' aliast is kapott; ASG (Action Sport Games) külön gyártó
delete from manufacturer_aliases where alias_norm = 'asg';

insert into manufacturer_aliases (alias_norm, manufacturer_id)
select a, m.id from manufacturers m
join (values
  ('emg','emg'), ('amoeba','amoeba'), ('novritsch','novritsch'), ('classicarmy','classic-army'),
  ('ics','ics'), ('kwa','kwa'), ('boltairsoft','bolt'), ('aps','aps'),
  ('goldeneagle','golden-eagle'), ('cybergun','cybergun'), ('umarex','umarex'), ('kjworks','kj-works'),
  ('kj','kj-works'), ('actionarmy','action-army'), ('silverback','silverback'),
  ('wellfire','well'), ('lancertactical','lancer-tactical'), ('lancer','lancer-tactical'),
  ('evolutionairsoft','evolution'), ('nuprol','nuprol'),
  ('deltaarmory','delta-armory'), ('modify','modify'), ('snowwolf','snow-wolf'), ('kingarms','king-arms'),
  ('vorsk','vorsk'), ('asg','asg'), ('actionsportgames','asg'), ('src','src'),
  ('apex','apex'), ('realsword','real-sword'), ('jgworks','jg'), ('jingong','jg')
) v(a, slug) on v.slug = m.slug
on conflict (alias_norm) do nothing;

-- Ellenőrzés: 8 bolt, 42 gyártó, 6 kategória
select (select count(*) from shops) as boltok, (select count(*) from manufacturers) as gyartok, (select count(*) from categories) as kategoriak;
