-- =====================================================================
-- TELJES TELEPÍTÉS EGY LÉPÉSBEN (Supabase SQL Editor)
-- Törli az árkereső táblákat (ha vannak), majd lefuttatja a 0001–0009 migrációkat sorrendben.
-- Bármikor újrafuttatható. FIGYELEM: a meglévő árkereső-adatok elvesznek!
-- =====================================================================
drop materialized view if exists product_summary cascade;
drop view if exists v_offers cascade;
drop view if exists v_offers_dedup cascade;
drop view if exists latest_rates cascade;
drop table if exists price_alerts, scrape_runs, match_candidates, price_history, offers, product_codes,
                     products, categories, manufacturer_aliases, manufacturers, shops, exchange_rates cascade;
drop function if exists refresh_product_summary();
drop function if exists catalog_search(text, text, text[], numeric, numeric, boolean, text, int, int, numeric[]);
drop function if exists airsoft_category(text, numeric);
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

-- >>>>>>>>>> migrations/0005_web_views.sql
-- =====================================================================
-- 0005: nézetek a weboldalnak + olvasási jog a publishable (anon) kulcsnak.
-- Adatot NEM töröl, a meglévő ajánlatok megmaradnak. Újrafuttatható.
-- =====================================================================

-- product_summary bővítése: legdrágább ár (árfolyosóhoz)
drop materialized view if exists product_summary cascade;
create materialized view product_summary as
select p.id, p.slug, p.name, p.model_code, p.image_url, p.category_id,
       m.name                                                     as manufacturer,
       min(v.price_huf) filter (where v.stock = 'in_stock')        as best_price_huf,
       min(v.price_eur) filter (where v.stock = 'in_stock')        as best_price_eur,
       max(v.price_huf)                                            as max_price_huf,
       min(v.price_huf)                                            as min_price_any_huf,
       min(v.price_eur)                                            as min_price_any_eur,
       count(*)                                                    as offer_count,
       count(*) filter (where v.stock = 'in_stock')                as in_stock_count,
       array_agg(distinct s.country)                               as shop_countries,
       case
         when bool_or(v.stock = 'in_stock') then 'in_stock'
         when bool_or(v.stock = 'preorder') then 'preorder'
         when bool_or(v.stock = 'out_of_stock') then 'out_of_stock'
         else 'unknown'
       end::stock_status                                           as stock,
       max(v.last_seen_at)                                         as updated_at
from products p
join manufacturers m on m.id = p.manufacturer_id
join v_offers v on v.product_id = p.id and v.is_active
join shops s on s.id = v.shop_id
group by p.id, m.name;
create unique index product_summary_id on product_summary (id);
create index product_summary_slug on product_summary (slug);
create index product_summary_price on product_summary (best_price_huf);

-- Termékoldal: aktív ajánlatok bolt adataival
create or replace view v_product_offers as
select o.id, o.product_id, o.url, o.title_raw, o.price, o.currency, o.price_huf, o.price_eur,
       o.stock, o.last_seen_at, s.name as shop_name, s.slug as shop_slug, s.country as shop_country
from v_offers o
join shops s on s.id = o.shop_id
where o.is_active and o.product_id is not null;

-- Árdiagram: termékenként napi legalacsonyabb raktáron lévő ár
create or replace view v_price_daily as
select o.product_id, h.observed_on, min(h.price_huf) as min_huf, min(h.price_eur) as min_eur
from price_history h
join offers o on o.id = h.offer_id
where o.product_id is not null and h.stock = 'in_stock'
group by o.product_id, h.observed_on;

-- Gyártószűrő
create or replace view v_manufacturers as
select manufacturer, count(*) as products
from product_summary
group by manufacturer;

-- Statisztika a főoldalra
create or replace view v_site_stats as
select (select count(*) from product_summary)                         as products,
       (select count(*) from offers where is_active and product_id is not null) as offers,
       (select count(distinct shop_id) from offers where is_active)   as shops,
       (select max(last_seen_at) from offers)                         as updated_at;

-- Olvasási jog (a táblákon az RLS továbbra is szűr; a belső táblák policy nélkül láthatatlanok)
grant usage on schema public to anon, authenticated;
grant select on all tables in schema public to anon, authenticated;
grant select on product_summary to anon, authenticated;

select refresh_product_summary();
select 'kész' as eredmeny, (select count(*) from product_summary) as termekek;


-- >>>>>>>>>> migrations/0006_dedupe_search.sql
-- =====================================================================
-- 0006: ismétlődő ajánlatok kiszűrése (boltonként + URL-enként a legfrissebb),
--       "N bolt" = valódi boltszám, kódos keresés (CM522 = CM.522). Adatot NEM töröl.
-- =====================================================================

-- Ugyanaz a bolti oldal csak egyszer: a legutóbbi futásból, azon belül a raktáron lévő legolcsóbb változat
create or replace view v_offers_dedup as
select distinct on (shop_id, url) *
from v_offers
where is_active and product_id is not null
order by shop_id, url, (last_seen_at at time zone 'UTC')::date desc, (stock = 'in_stock') desc, price_huf asc;

drop materialized view if exists product_summary cascade;
create materialized view product_summary as
select p.id, p.slug, p.name, p.model_code, p.image_url, p.category_id,
       m.name                                                     as manufacturer,
       regexp_replace(lower(m.name || ' ' || p.name || ' ' || coalesce(p.model_code, '')), '[^a-z0-9]', '', 'g') as search_code,
       min(v.price_huf) filter (where v.stock = 'in_stock')        as best_price_huf,
       min(v.price_eur) filter (where v.stock = 'in_stock')        as best_price_eur,
       max(v.price_huf)                                            as max_price_huf,
       min(v.price_huf)                                            as min_price_any_huf,
       min(v.price_eur)                                            as min_price_any_eur,
       count(distinct v.shop_id)                                   as offer_count,
       count(distinct v.shop_id) filter (where v.stock = 'in_stock') as in_stock_count,
       array_agg(distinct s.country)                               as shop_countries,
       case
         when bool_or(v.stock = 'in_stock') then 'in_stock'
         when bool_or(v.stock = 'preorder') then 'preorder'
         when bool_or(v.stock = 'out_of_stock') then 'out_of_stock'
         else 'unknown'
       end::stock_status                                           as stock,
       max(v.last_seen_at)                                         as updated_at
from products p
join manufacturers m on m.id = p.manufacturer_id
join v_offers_dedup v on v.product_id = p.id
join shops s on s.id = v.shop_id
group by p.id, m.name;
create unique index product_summary_id on product_summary (id);
create index product_summary_slug on product_summary (slug);
create index product_summary_price on product_summary (best_price_huf);

create or replace view v_product_offers as
select o.id, o.product_id, o.url, o.title_raw, o.price, o.currency, o.price_huf, o.price_eur,
       o.stock, o.last_seen_at, s.name as shop_name, s.slug as shop_slug, s.country as shop_country
from v_offers_dedup o
join shops s on s.id = o.shop_id;

create or replace view v_manufacturers as
select manufacturer, count(*) as products
from product_summary
group by manufacturer;

grant select on all tables in schema public to anon, authenticated;
grant select on product_summary to anon, authenticated;

select refresh_product_summary();
select 'kész' as eredmeny, (select count(*) from product_summary) as termekek;


-- >>>>>>>>>> migrations/0007_categories_search.sql
-- =====================================================================
-- 0007: fegyvertípus-besorolás + egy hívásos kereső/szűrő (lista + darabszámok).
-- Adatot NEM töröl. Újrafuttatható.
-- Kategóriák: rifle (AR/AK gépkarabély), pistol, smg, sniper (mesterlövész/DMR), lmg (géppuska),
--             shotgun, grenade (gránát/gránátvető), other (kiegészítő/egyéb). 'weapons' = minden fegyver.
-- =====================================================================

-- t: kisbetűs szöveg (gyártó + név + bolti címek + bolti URL-ek), price: HUF
create or replace function airsoft_category(t text, price numeric) returns text
language sql immutable as $$
  select case
    -- gránátok, gránátvetők (de a gránáttartó tasak kiegészítő)
    when t ~* '(gránát|granát|grenade|granate|granada|granata|launcher|\y40 ?mm\y|\ym203\y|\ym320\y|\ygl-?06\y|\yakna\y|claymore)'
         and t !~* '(pouch|tasak|holder|tartó|zseb|pocket|sumka)' then 'grenade'
    -- kiegészítő: alkatrész/felszerelés szó, kivéve ha egyértelműen fegyver ÉS fegyverár (>= 25 000 Ft)
    when (t ~* '(magazin|magazine|\ymag\y|\ytár\y|tárak|zásobník|chargeur|magazyn|cargador|caricatore|akku|akkumul|battery|batterie|bateri|\ylipo\y|li-po|nimh|charger|töltő|nabíj|scope|céltávcső|optic|optika|red ?dot|holster|pisztolytok|pouch|tasak|sling|\yszíj|\ybbs?\y|golyó|kuličky|billes|kugeln|hop-?up|barrel|\ycső\y|hlaveň|gearbox|mechabox|\ymotor|mosfet|piston|dugattyú|cylinder|nozzle|bucking|suppressor|silencer|hangtompító|tlumič|flash ?hider|\ygrip\y|markolat|\yrail\y|\ystock\y|válltámasz|flashlight|lámpa|svítiln|\ylaser\y|\yvest\y|mellény|plate carrier|helmet|sisak|\ymask|maszk|goggle|szemüveg|glasses|glove|kesztyű|\ybag\y|táska|backpack|hátizsák|\ycase\y|kufr|uniform|nadrág|pants|shirt|jacket|kabát|boots|bakancs|patch|\yradio\y|headset|target|céltábla|chrono|speed ?loader|loader|tracer|bipod|villaláb|\ymount\y|adapter|cleaning|\yoil\y|olaj|silicon|szilikon|grease|\ycap\y|sapka|bayonet|knife|kés)'
          or (t ~* '\y(gas|gáz|plyn|propane|co2)\y' and t !~* '\y(gbbr?|nbb|gas blow ?back|pistol|pisztoly|pistole|pistolet|revolver)\y'))
         and not (t ~* '(\yaeg\y|\yaep\y|\ygbbr?\y|\ynbb\y|\yhpa\y|\yebb\y|replica|replika|réplique|rifle|carbine|karabély|karabin|puska|puška|samopal|pisztoly|pistol|pistole|pistolet|pistola|\ysmg\y|\ylmg\y|sniper|shotgun|revolver|zbraň|zbran|fusil|gewehr)'
                  and coalesce(price, 0) >= 25000) then 'other'
    when t ~* '(sniper|mesterlövész|odstřel|odstrel|\ydmr\y|\ysvd\y|dragunov|\yvsr|\yl96|\yawm\y|\yaw ?338|\ym24\y|\ym40\y|\ym700\y|\ysrs\y|\yssg|\ymb ?0?\d{2}\y|bolt[- ]action|\ysr-?25|\ym14\y|\yg28\y|\ysr-?10\y|\ymk ?1[12]\y|\ytac-?41|\yt-?10\y|\yscout\y|marksman)' then 'sniper'
    when t ~* '(\ylmg\y|géppuska|kulomet|machine ?gun|machine-gun|\ym249|\ym60\y|\ypkm?\y|\yrpk|\ymg ?(3|4|42|5)\y|\ymk ?4[68]\y|minimi|\ynegev|\ym240|\yrpd\y|\ysaw\y|támogató)' then 'lmg'
    when t ~* '(shotgun|sörétes|brokovnic|fusil à pompe|\ym870|\yspas|\ym1014|\yaa-?12|\ymp-?153|\yksg\y|\ym3 super|\ypump\y|flinta)' then 'shotgun'
    when t ~* '(\ysmg\y|géppisztoly|samopal|submachine|sub-machine|pistolet[- ]mitrailleur|\ymp ?5|\ymp ?7\y|\yp ?90\y|\yump|\yvector\y|kriss|scorpion|\yuzi\y|\ymp ?9\y|\ymac-?1[01]|\yvmp|\ypdw\y|ppsh|thompson|\ysten\y|\ymp ?40|\ypp-?19|bizon|\ypp-?2000)' then 'smg'
    when t ~* '(pisztoly|\ypistol|\ypistole|\ypistolet|\ypistola|handgun|revolver|glock|\yg ?1[789]\y|hi-?capa|\y1911|\ym9\y|\yp226|\yp320|\yusp\y|beretta|desert eagle|\ycz ?75|\ycz ?p-?0\d|\ym&p|five-seven|walther|\yppk|makarov|\ytt-?33|\yaep\y)' then 'pistol'
    when t ~* '(\yaeg\y|\ygbbr\y|\yhpa\y|\yebb\y|replica|replika|réplique|rifle|carbine|karabély|karabin|puska|puška|zbraň|zbran|fusil|gewehr|\ym4\y|\ym16|\yar-?15|\yhk ?416|\yak-?\d{2}|\yaks|\yakm|\yg36|\yscar|\yaug\y|famas|\ysa-[a-z]\d|\ycm\.?\d{3}|assault|airsoft-guns|airsoftove-zbrane|elektromos-airsoft)' then 'rifle'
    when coalesce(price, 0) >= 40000 then 'rifle'   -- drága, de ismeretlen típusú: nagy eséllyel fegyver
    else 'other'
  end
$$;

-- product_summary + kategória
drop materialized view if exists product_summary cascade;
create materialized view product_summary as
select p.id, p.slug, p.name, p.model_code, p.image_url,
       m.name                                                     as manufacturer,
       regexp_replace(lower(m.name || ' ' || p.name || ' ' || coalesce(p.model_code, '')), '[^a-z0-9]', '', 'g') as search_code,
       airsoft_category(lower(m.name || ' ' || p.name || ' ' || string_agg(v.title_raw || ' ' || v.url, ' ')),
                        coalesce(min(v.price_huf) filter (where v.stock = 'in_stock'), min(v.price_huf))) as category,
       min(v.price_huf) filter (where v.stock = 'in_stock')        as best_price_huf,
       min(v.price_eur) filter (where v.stock = 'in_stock')        as best_price_eur,
       max(v.price_huf)                                            as max_price_huf,
       min(v.price_huf)                                            as min_price_any_huf,
       min(v.price_eur)                                            as min_price_any_eur,
       count(distinct v.shop_id)                                   as offer_count,
       count(distinct v.shop_id) filter (where v.stock = 'in_stock') as in_stock_count,
       array_agg(distinct s.country)                               as shop_countries,
       case
         when bool_or(v.stock = 'in_stock') then 'in_stock'
         when bool_or(v.stock = 'preorder') then 'preorder'
         when bool_or(v.stock = 'out_of_stock') then 'out_of_stock'
         else 'unknown'
       end::stock_status                                           as stock,
       max(v.last_seen_at)                                         as updated_at
from products p
join manufacturers m on m.id = p.manufacturer_id
join v_offers_dedup v on v.product_id = p.id
join shops s on s.id = v.shop_id
group by p.id, m.name;
create unique index product_summary_id on product_summary (id);
create index product_summary_slug on product_summary (slug);
create index product_summary_cat on product_summary (category);
create index product_summary_price on product_summary (best_price_huf);

create or replace view v_manufacturers as
select manufacturer, count(*) as products from product_summary group by manufacturer;

-- Egy hívás: találatok + szűrő-darabszámok. Minden szűrő darabszáma a TÖBBI szűrővel számol
-- (mint az árösszehasonlítóknál: a márkák mellett az a szám áll, ami az adott márka bejelölésével jönne).
-- edges: ársáv-határok HUF-ban (növekvő), a frontend adja a választott pénznem kerek értékeiből.
create or replace function catalog_search(
  q text default null, cat text default null, brands text[] default null,
  pmin numeric default null, pmax numeric default null, in_stock boolean default false,
  sort text default 'popular', lim int default 24, off int default 0, edges numeric[] default null)
returns jsonb language sql stable as $$
with base as (
  select ps.id, ps.slug, ps.name, ps.manufacturer, ps.image_url, ps.category, ps.best_price_huf,
         ps.max_price_huf, ps.min_price_any_huf, ps.offer_count, ps.in_stock_count, ps.stock,
         coalesce(ps.best_price_huf, ps.min_price_any_huf) as price
  from product_summary ps
  where coalesce(trim(q), '') = '' or not exists (
    select 1 from unnest(string_to_array(trim(q), ' ')) w
    where w <> '' and not (
      ps.name ilike '%' || w || '%' or ps.manufacturer ilike '%' || w || '%'
      or (regexp_replace(lower(w), '[^a-z0-9]', '', 'g') <> ''
          and ps.search_code like '%' || regexp_replace(lower(w), '[^a-z0-9]', '', 'g') || '%')))
),
f as (
  select b.*,
    (coalesce(cat, '') = '' or (cat = 'weapons' and b.category <> 'other') or b.category = cat) as c_ok,
    (brands is null or cardinality(brands) = 0 or b.manufacturer = any(brands))                  as b_ok,
    ((pmin is null or b.price >= pmin) and (pmax is null or b.price <= pmax))                    as p_ok,
    (not coalesce(in_stock, false) or b.stock = 'in_stock')                                     as s_ok
  from base b
),
hits as (
  select f.*, row_number() over (order by
      case when sort = 'price' then price end asc nulls last,
      case when sort = 'price_desc' then price end desc nulls last,
      case when sort = 'name' then name end asc,
      offer_count desc, price asc nulls last, id) as rn
  from f where c_ok and b_ok and p_ok and s_ok
)
select jsonb_build_object(
  'total', (select count(*) from hits),
  'items', coalesce((select jsonb_agg(jsonb_build_object(
              'id', id, 'slug', slug, 'name', name, 'manufacturer', manufacturer, 'image_url', image_url,
              'category', category, 'best_price_huf', best_price_huf, 'max_price_huf', max_price_huf,
              'min_price_any_huf', min_price_any_huf, 'offer_count', offer_count, 'stock', stock) order by rn)
            from hits where rn > greatest(0, off) and rn <= greatest(0, off) + least(greatest(lim, 1), 100)), '[]'::jsonb),
  'facets', jsonb_build_object(
    'categories', (select coalesce(jsonb_object_agg(category, n), '{}'::jsonb)
                   from (select category, count(*) n from f where b_ok and p_ok and s_ok group by category) c),
    'brands', (select coalesce(jsonb_agg(jsonb_build_object('name', manufacturer, 'n', n) order by n desc, manufacturer), '[]'::jsonb)
               from (select manufacturer, count(*) n from f where c_ok and p_ok and s_ok group by manufacturer) m),
    'price', (select jsonb_build_object('min', min(price), 'max', max(price)) from f where c_ok and b_ok and s_ok),
    'buckets', case when edges is null then null else
               (select coalesce(jsonb_object_agg(bk, n), '{}'::jsonb)
                from (select width_bucket(price, edges) bk, count(*) n
                      from f where c_ok and b_ok and s_ok and price is not null group by bk) w) end,
    'in_stock', (select count(*) from f where c_ok and b_ok and p_ok and stock = 'in_stock'))
)
$$;

grant select on all tables in schema public to anon, authenticated;
grant select on product_summary to anon, authenticated;
grant execute on function catalog_search(text, text, text[], numeric, numeric, boolean, text, int, int, numeric[]) to anon, authenticated;

select refresh_product_summary();
select category, count(*) as termekek from product_summary group by category order by 2 desc;


-- >>>>>>>>>> migrations/0008_eu_shops.sql
-- =====================================================================
-- 0008: 12 új EU-s bolt (UK nélkül) + Evike Europe valójában francia + néhány új gyártó.
-- Adatot NEM töröl. Újrafuttatható.
-- =====================================================================
update shops set country = 'FR', lang = 'en' where slug = 'evike-europe';

insert into shops (slug, name, base_url, country, currency, scraper_key, lang) values
  ('begadi',          'Begadi',          'https://www.begadi.com',        'DE', 'EUR', 'jsonld', 'de'),
  ('airsoftsports',   'Airsoft Sports',  'https://airsoftsports.de',      'DE', 'EUR', 'jsonld', 'de'),
  ('airsoft-guns-eu', 'AirsoftGuns.eu',  'https://www.airsoft-guns.eu',   'CZ', 'EUR', 'jsonld', 'en'),
  ('airsoftmania',    'Airsoftmania',    'https://airsoftmania.eu',       'IT', 'EUR', 'jsonld', 'en'),
  ('gunshot',         'Gunshot',         'https://www.gunshot.it',        'IT', 'EUR', 'jsonld', 'it'),
  ('vsgun',           'VSGUN',           'https://www.vsgun.com',         'ES', 'EUR', 'jsonld', 'es'),
  ('airsoft-legends', 'Airsoft Legends', 'https://www.airsoft-legends.nl','NL', 'EUR', 'jsonld', 'nl'),
  ('bunker501',       'Bunker501',       'https://www.bunker501.nl',      'NL', 'EUR', 'jsonld', 'nl'),
  ('phenixairsoft',   'Phenix Airsoft',  'https://www.phenixairsoft.com', 'FR', 'EUR', 'jsonld', 'fr'),
  ('militaria',       'Militaria.pl',    'https://militaria.pl',          'PL', 'PLN', 'jsonld', 'pl'),
  ('redberet',        'Red Beret',       'https://www.redberet.pl',       'PL', 'PLN', 'jsonld', 'pl'),
  ('atom-airsoft',    'Atom Airsoft',    'https://atom-airsoft.fi',       'FI', 'EUR', 'jsonld', 'fi')
on conflict (slug) do nothing;

insert into manufacturers (slug, name) values
  ('begadi','Begadi'), ('swiss-arms','Swiss Arms'), ('agm','AGM'), ('wolverine','Wolverine Airsoft'),
  ('tippmann','Tippmann'), ('phylax','Phylax'), ('archwick','Archwick'), ('saigo','Saigo Defense')
on conflict (slug) do nothing;

insert into manufacturer_aliases (alias_norm, manufacturer_id)
select a, m.id from manufacturers m
join (values ('begadi','begadi'), ('swissarms','swiss-arms'), ('agm','agm'), ('wolverine','wolverine'),
             ('wolverineairsoft','wolverine'), ('tippmann','tippmann'), ('phylax','phylax'), ('archwick','archwick'),
             ('saigo','saigo'), ('saigodefense','saigo'), ('eliteforce','umarex')) v(a, slug) on v.slug = m.slug
on conflict (alias_norm) do nothing;

select count(*) as boltok from shops;


-- >>>>>>>>>> migrations/0009_accessory_brands.sql
-- =====================================================================
-- 0009: kiegészítő- és alkatrészgyártók (hogy a tárak, akkuk, BB-k, alkatrészek is megjelenjenek),
--       a már letöltött ruházati ajánlatok elrejtése. Adatot NEM töröl. Újrafuttatható.
-- =====================================================================
insert into manufacturers (slug, name) values
  ('nimrod','Nimrod'), ('bls','BLS'), ('rockets','Rockets'), ('lonex','Lonex'), ('maple-leaf','Maple Leaf'),
  ('shs','SHS'), ('prometheus','Prometheus'), ('gate','GATE'), ('perun','Perun'), ('jefftron','Jefftron'),
  ('guarder','Guarder'), ('element','Element'), ('big-dragon','Big Dragon'), ('battleaxe','BattleAxe'),
  ('vector-optics','Vector Optics'), ('theta-optics','Theta Optics'), ('abbey','Abbey'), ('puff-dino','Puff Dino'),
  ('mancraft','Mancraft'), ('polarstar','PolarStar'), ('xcortech','Xcortech'), ('bolt-airsoft','BOLT Airsoft'),
  ('g-and-p','G&P'), ('cowcow','CowCow'), ('pts','PTS Syndicate'), ('magpul','Magpul'), ('ipower','iPower'),
  ('electro-river','Electro River'), ('titan-power','Titan Power'), ('ase-utra','ASE Utra'), ('swiss-arms-acc','Strike Systems')
on conflict (slug) do nothing;

insert into manufacturer_aliases (alias_norm, manufacturer_id)
select a, m.id from manufacturers m
join (values
  ('nimrod','nimrod'), ('bls','bls'), ('blsbbs','bls'), ('rockets','rockets'), ('rocketsprofessional','rockets'),
  ('lonex','lonex'), ('mapleleaf','maple-leaf'), ('shs','shs'), ('prometheus','prometheus'), ('gate','gate'),
  ('gateenterprise','gate'), ('perun','perun'), ('jefftron','jefftron'), ('guarder','guarder'), ('element','element'),
  ('bigdragon','big-dragon'), ('battleaxe','battleaxe'), ('vectoroptics','vector-optics'), ('thetaoptics','theta-optics'),
  ('abbey','abbey'), ('puffdino','puff-dino'), ('mancraft','mancraft'), ('polarstar','polarstar'), ('xcortech','xcortech'),
  ('boltairsoft','bolt-airsoft'), ('gp','g-and-p'), ('gandp','g-and-p'), ('cowcow','cowcow'), ('cowcowtechnology','cowcow'),
  ('pts','pts'), ('ptssyndicate','pts'), ('magpul','magpul'), ('ipower','ipower'), ('electroriver','electro-river'),
  ('titanpower','titan-power'), ('aseutra','ase-utra'), ('strikesystems','swiss-arms-acc')
) v(a, slug) on v.slug = m.slug
on conflict (alias_norm) do nothing;

-- már letöltött ruházat elrejtése (a scraper mostantól le sem tölti)
update offers set is_active = false
where is_active and (title_raw || ' ' || url) ~* '(\y(clothing|apparel|uniforms?|trousers|pants|t-?shirts?|shirts?|hoodies?|jackets?|softshell|fleece|boots|shoes|socks|nadrág|póló|kabát|bakancs|egyenruha|pulóver|mundur|spodnie|koszul\w*|kurtk\w*|buty|bluz\w*|kalhoty|bunda|boty)\y)';

select refresh_product_summary();
select (select count(*) from manufacturers) as gyartok, (select count(*) from offers where not is_active) as rejtett_ajanlatok;


-- Ellenőrzés: 20 bolt, 81 gyártó, 6 kategória
select (select count(*) from shops) as boltok, (select count(*) from manufacturers) as gyartok, (select count(*) from categories) as kategoriak;
