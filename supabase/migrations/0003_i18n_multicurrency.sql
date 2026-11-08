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
