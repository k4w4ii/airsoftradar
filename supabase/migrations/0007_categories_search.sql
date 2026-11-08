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
