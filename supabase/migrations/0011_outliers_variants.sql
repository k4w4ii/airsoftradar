-- =====================================================================
-- 0011: gyanús árak és egyedi változatok kezelése. Adatot NEM töröl. Újrafuttatható. (A 0010 UTÁN futtasd.)
--  1. Árkiugrás: ha egy terméknek legalább 3 boltja van, a medián ár 40%-a alatti vagy 250%-a feletti ajánlat
--     „eltérő” (tipikusan alkatrész vagy átépített/custom változat). 2 boltnál a 4x-nél olcsóbb az eltérő.
--     Az eltérő ajánlat nem számít bele a legjobb árba, az árfolyosóba és a boltszámba; a termékoldalon külön látszik.
--  2. Egyedi változat (custom, HPA, tuned, upgraded, használt...): ha az ajánlat ilyen, de a termék nem (vagy fordítva),
--     leválasztjuk; a következő éjszakai futás külön termékként párosítja (scraper/filters.py: is_variant).
-- =====================================================================

-- A függvények egymásra hivatkoznak: a létrehozáskori ellenőrzés kikapcsolva (mint a pg_dump-nál), így a sorrend nem számít.
set check_function_bodies = off;

create or replace function airsoft_is_variant(t text) returns boolean
language sql immutable as $$
  select regexp_replace(lower(coalesce(t, '')), '(\s\+|\sw/|\y(with|incl|including|included|mit|avec|con|com|včetně|vcetne|vč|plus|és|w zestawie|z zestawem|set with)\y).*$', '') ~ '\y(custom|hpa|wolverine|polarstar|inferno|fusion ?engine|jack ?engine|tuned|tuning|upgraded|high ?speed ?build|dmr ?build|full ?upgrade|egyedi|tuningolt|felújított|refurbished|used|használt)\y'
$$;

-- ajánlatonkénti jelzők (a weboldal és a product_summary is ebből dolgozik)
create or replace view v_offer_flags as
with o as (
  select v.id, v.product_id, v.price_huf,
         count(*) over (partition by v.product_id)        as n,
         max(v.price_huf) over (partition by v.product_id) as mx
  from v_offers_dedup v
),
med as (
  select product_id, percentile_cont(0.5) within group (order by price_huf) as mid
  from v_offers_dedup group by product_id
)
select o.id, o.product_id,
       case when o.n >= 3 then o.price_huf < 0.4 * med.mid or o.price_huf > 2.5 * med.mid
            when o.n = 2  then o.price_huf * 4 < o.mx
            else false end as is_outlier
from o join med on med.product_id = o.product_id;

create or replace view v_offers_clean as
select v.* from v_offers_dedup v
join v_offer_flags f on f.id = v.id
where not f.is_outlier;

drop materialized view if exists product_summary cascade;
create materialized view product_summary as
with oc as (
  select v.*, airsoft_category(m.name || ' ' || v.title_raw, v.url, v.price_huf) as cat
  from v_offers_clean v
  join products p on p.id = v.product_id
  join manufacturers m on m.id = p.manufacturer_id
),
med as (
  select product_id, percentile_cont(0.5) within group (order by price_huf) as mid_price
  from oc group by product_id
),
votes as (
  select product_id, cat, count(*)::numeric as n from oc group by product_id, cat
  union all
  select p.id, airsoft_category(m.name || ' ' || p.name, null, med.mid_price::numeric), 0.5
  from products p join manufacturers m on m.id = p.manufacturer_id join med on med.product_id = p.id
),
pick as (
  select distinct on (product_id) product_id, cat
  from (select product_id, cat, sum(n) as n from votes group by product_id, cat) t
  order by product_id, n desc, cat
),
plat as (
  select oc.product_id, array_agg(distinct pl) filter (where pl is not null) as platforms
  from oc join pick on pick.product_id = oc.product_id
  left join lateral unnest(airsoft_platforms(oc.title_raw)) pl on true
  where airsoft_group(oc.cat) = airsoft_group(pick.cat)
  group by oc.product_id
)
select p.id, p.slug, p.name, p.model_code, p.image_url,
       m.name                                                     as manufacturer,
       regexp_replace(lower(m.name || ' ' || p.name || ' ' || coalesce(p.model_code, '')), '[^a-z0-9]', '', 'g') as search_code,
       pick.cat                                                   as category,
       (select array(select distinct e from unnest(coalesce(plat.platforms, '{}') || airsoft_platforms(p.name)) e order by e)) as platforms,
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
join v_offers_clean v on v.product_id = p.id
join shops s on s.id = v.shop_id
join pick on pick.product_id = p.id
left join plat on plat.product_id = p.id
group by p.id, m.name, pick.cat, plat.platforms;
create unique index product_summary_id on product_summary (id);
create index product_summary_slug on product_summary (slug);
create index product_summary_cat on product_summary (category);
create index product_summary_price on product_summary (best_price_huf);
create index product_summary_plat on product_summary using gin (platforms);

create or replace view v_manufacturers as
select manufacturer, count(*) as products from product_summary group by manufacturer;

-- termékoldal: minden ajánlat, jelzővel (az eltérőket a weboldal külön mutatja)
create or replace view v_product_offers as
select o.id, o.product_id, o.url, o.title_raw, o.price, o.currency, o.price_huf, o.price_eur,
       o.stock, o.last_seen_at, s.name as shop_name, s.slug as shop_slug, s.country as shop_country,
       coalesce(f.is_outlier, false) as is_outlier
from v_offers_dedup o
join shops s on s.id = o.shop_id
left join v_offer_flags f on f.id = o.id;

-- ártörténet: az eltérő (alkatrész/custom) ajánlatok nélkül
create or replace view v_price_daily as
select o.product_id, h.observed_on, min(h.price_huf) as min_huf, min(h.price_eur) as min_eur
from price_history h
join offers o on o.id = h.offer_id
left join v_offer_flags f on f.id = o.id
where o.product_id is not null and h.stock = 'in_stock' and not coalesce(f.is_outlier, false)
group by o.product_id, h.observed_on;

grant select on all tables in schema public to anon, authenticated;
grant select on product_summary to anon, authenticated;

-- takarítás: egyedi változat <-> alap termék keveredés feloldása (kézi párosítást nem érint)
with bad as (
  select o.id
  from offers o
  join products p on p.id = o.product_id
  join manufacturers m on m.id = p.manufacturer_id
  where o.match_status <> 'manual'
    and airsoft_is_variant(o.title_raw) <> airsoft_is_variant(m.name || ' ' || p.name)
)
update offers o set product_id = null, match_status = 'pending', match_method = null, match_confidence = null
from bad where o.id = bad.id;

select refresh_product_summary();
select (select count(*) from v_offer_flags where is_outlier) as eltero_ajanlatok,
       (select count(*) from offers where match_status = 'pending') as ujraparositasra_var;
