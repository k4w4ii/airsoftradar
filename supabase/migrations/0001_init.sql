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
