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
