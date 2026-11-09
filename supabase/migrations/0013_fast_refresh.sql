-- =====================================================================
-- 0013: gyors weboldal-frissítés. A besorolás (kategória, platform, egyedi változat) ajánlatonként EGYSZER fut le
-- és eltárolódik (offers.cat / plats / variant); a product_summary frissítése már csak összesít.
-- Ok: a 0010–0012 óta a frissítés minden ajánlatra regexeket futtatott, és túllépte a Supabase időkorlátját
-- („canceling statement due to statement timeout”). A besorolók külön utasításban futnak, mert a PostgreSQL
-- legfeljebb 32 lefordított regexet tart gyorsítótárban; egy utasításban együtt 50x lassabbak.
-- Adatot NEM töröl. Újrafuttatható. A 0012 UTÁN futtasd.
-- =====================================================================

set check_function_bodies = off;

alter table offers   add column if not exists cat text, add column if not exists plats text[], add column if not exists variant boolean;
alter table products add column if not exists name_cat text, add column if not exists name_plats text[];
drop trigger if exists offers_classify on offers;
drop trigger if exists products_classify on products;
drop function if exists offers_classify();
drop function if exists products_classify();

-- mentéskor csak megjelöljük az új / megváltozott sort (olcsó); a besorolás a frissítés elején fut
create or replace function offers_mark_dirty() returns trigger language plpgsql as $$
begin
  if tg_op = 'INSERT' or new.title_raw is distinct from old.title_raw or new.url is distinct from old.url
     or new.price is distinct from old.price or new.currency is distinct from old.currency
     or new.brand_raw is distinct from old.brand_raw then
    new.cat := null; new.plats := null; new.variant := null;
  end if;
  return new;
end $$;
drop trigger if exists offers_mark_dirty on offers;
create trigger offers_mark_dirty before insert or update of title_raw, url, price, currency, brand_raw on offers
  for each row execute function offers_mark_dirty();

create or replace function products_mark_dirty() returns trigger language plpgsql as $$
begin
  if tg_op = 'INSERT' or new.name is distinct from old.name then
    new.name_cat := null; new.name_plats := null;
  end if;
  return new;
end $$;
drop trigger if exists products_mark_dirty on products;
create trigger products_mark_dirty before insert or update of name on products
  for each row execute function products_mark_dirty();

-- a megjelölt sorok besorolása: minden besoroló KÜLÖN utasításban (regex-gyorsítótár)
create or replace function airsoft_classify_pending() returns void language plpgsql as $$
begin
  with r as materialized (select currency, huf_per_unit from latest_rates)
  update offers o set cat = airsoft_category(coalesce(o.brand_raw, '') || ' ' || coalesce(o.title_raw, ''), o.url,
           o.price * coalesce(case when o.currency = 'HUF' then 1 end,
                              (select r.huf_per_unit from r where r.currency = o.currency), 0))
  where o.cat is null;
  update offers set plats = airsoft_platforms(coalesce(title_raw, '')) where plats is null;
  update offers set variant = airsoft_is_variant(coalesce(title_raw, '')) where variant is null;
  update products set name_cat = airsoft_category(coalesce(name, ''), null, null) where name_cat is null;
  update products set name_plats = airsoft_platforms(coalesce(name, '')) where name_plats is null;
end $$;

-- a weboldal frissítése: előbb az új ajánlatok besorolása, aztán az összesítés (regex nélkül)
create or replace function refresh_product_summary() returns void
language plpgsql security definer set search_path = public as $$
begin
  perform airsoft_classify_pending();
  refresh materialized view concurrently product_summary;
end $$;
revoke execute on function refresh_product_summary() from public, anon, authenticated;
revoke execute on function airsoft_classify_pending() from public, anon, authenticated;

-- egyszeri besorolás a meglévő sorokra (az összes sor újra, a 0012 szabályaival)
update offers set cat = null, plats = null, variant = null;
update products set name_cat = null, name_plats = null;
select airsoft_classify_pending();

-- eltérő árak: egy menetben (a 0011-es változat háromszor számolta a dedup nézetet)
create or replace view v_offer_flags as
with d as materialized (select id, product_id, price_huf from v_offers_dedup),
st as (select product_id, count(*) as n, max(price_huf) as mx,
              percentile_cont(0.5) within group (order by price_huf) as mid
       from d group by product_id)
select d.id, d.product_id,
       case when st.n >= 3 then d.price_huf < 0.4 * st.mid or d.price_huf > 2.5 * st.mid
            when st.n = 2  then d.price_huf * 4 < st.mx
            else false end as is_outlier
from d join st on st.product_id = d.product_id;

create or replace view v_offers_clean as
with d as materialized (select * from v_offers_dedup),
st as (select product_id, count(*) as n, max(price_huf) as mx,
              percentile_cont(0.5) within group (order by price_huf) as mid
       from d group by product_id)
select d.* from d join st on st.product_id = d.product_id
where not (case when st.n >= 3 then d.price_huf < 0.4 * st.mid or d.price_huf > 2.5 * st.mid
                when st.n = 2  then d.price_huf * 4 < st.mx
                else false end);

drop materialized view if exists product_summary cascade;
create materialized view product_summary as
with oc as (            -- a besorolás már az ajánlaton van (offers.cat / plats), itt nincs regex
  select v.*, oo.cat, oo.plats
  from v_offers_clean v
  join offers oo on oo.id = v.id
),
votes as (
  select product_id, cat, count(*)::numeric as n from oc group by product_id, cat
  union all
  select p.id, p.name_cat, 0.5 from products p
  where p.name_cat is not null and p.id in (select distinct product_id from oc)
),
pick as (
  select distinct on (product_id) product_id, cat
  from (select product_id, cat, sum(n) as n from votes group by product_id, cat) t
  order by product_id, n desc, cat
),
plat as (
  select oc.product_id, array_agg(distinct pl) filter (where pl is not null) as platforms
  from oc join pick on pick.product_id = oc.product_id
  left join lateral unnest(oc.plats) pl on true
  where airsoft_group(oc.cat) = airsoft_group(pick.cat)
  group by oc.product_id
)
select p.id, p.slug, p.name, p.model_code, p.image_url,
       m.name                                                     as manufacturer,
       regexp_replace(lower(m.name || ' ' || p.name || ' ' || coalesce(p.model_code, '')), '[^a-z0-9]', '', 'g') as search_code,
       pick.cat                                                   as category,
       (select array(select distinct e from unnest(coalesce(plat.platforms, '{}') || coalesce(p.name_plats, '{}')) e order by e)) as platforms,
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
join oc v on v.product_id = p.id
join shops s on s.id = v.shop_id
join pick on pick.product_id = p.id
left join plat on plat.product_id = p.id
group by p.id, m.name, pick.cat, plat.platforms, p.name_plats;
create unique index product_summary_id on product_summary (id);
create index product_summary_slug on product_summary (slug);
create index product_summary_cat on product_summary (category);
create index product_summary_price on product_summary (best_price_huf);
create index product_summary_plat on product_summary using gin (platforms);

create or replace view v_manufacturers as
select manufacturer, count(*) as products from product_summary group by manufacturer;
grant select on all tables in schema public to anon, authenticated;

-- biztonsági tartalék: a szerveroldali (service_role) hívásoknak több idő (ha a Supabase engedi)
do $$ begin
  execute 'alter role service_role set statement_timeout = ''5min''';
exception when others then raise notice 'service_role statement_timeout nem állítható: %', sqlerrm;
end $$;
notify pgrst, 'reload config';

select refresh_product_summary();
select (select count(*) from product_summary) as termekek,
       (select count(*) from offers where cat is null) as besorolatlan_ajanlat;
