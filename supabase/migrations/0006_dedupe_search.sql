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
