-- =====================================================================
-- 0010: alkatrészek és kiegészítők külön kategóriában, „mihez jó” (platform) szűrő,
--       több kategória egyszerre (pl. AR + mesterlövész), a fegyverhez tévesen párosított
--       olcsó tárak/alkatrészek leválasztása. Adatot NEM töröl. Újrafuttatható.
--
-- Kategóriák
--   fegyverek:     rifle, pistol, smg, sniper, lmg, shotgun, grenade          (csoport: weapons)
--   alkatrészek:   part_internal, part_hopup, part_motor, part_external       (csoport: parts)
--   kiegészítők:   acc_mag, acc_power, acc_optics, acc_ammo, acc_protect, acc_gear, other   (csoport: acc)
-- Platformok: m4, ak, g36, mp5, aug, scar, m14, p90, vsr, l96, glock, hicapa, m9, gb_v2, gb_v3
--
-- A besorolás ajánlatonként (bolti cím + ár) történik, a termék kategóriája a boltok többségi
-- szavazata. Így egy-egy rossz bolti cím nem rontja el a terméket. A bolt URL-je csak végső
-- tartalék (az „/aeg-parts/” útvonal korábban fegyvernek mutatta az alkatrészt).
-- Ugyanez a logika Pythonban: scraper/filters.py (is_part) – a párosító ezzel dolgozik.
-- =====================================================================

-- A függvények egymásra hivatkoznak: a létrehozáskori ellenőrzés kikapcsolva (mint a pg_dump-nál), így a sorrend nem számít.
set check_function_bodies = off;

-- „vele járó” részek levágása: „M4 AEG with battery and charger”, „Glock 17 + 2 magazines”
create or replace function airsoft_core(t text) returns text
language sql immutable as $$
  select regexp_replace(lower(coalesce(t, '')),
    '(\s\+|\sw/|\y(with|incl|including|included|mit|avec|con|com|včetně|vcetne|vč|plus|és|w zestawie|z zestawem|set with)\y).*$', '')
$$;

create or replace function airsoft_category(title text, url text, price numeric) returns text
language sql immutable as $$
  with x as (
    select regexp_replace(lower(coalesce(title, '')), '(\s\+|\sw/|\y(with|incl|including|included|mit|avec|con|com|včetně|vcetne|vč|plus|és|w zestawie|z zestawem|set with)\y).*$', '') as c, lower(coalesce(url, '')) as u, coalesce(price, 0) as p,
      -- fegyverre utaló szó (főnév vagy rendszer)
      '\y(aeg|aep|gbbr?|nbb|hpa|ebb|rifles?|carbines?|karabély\w*|karabin\w*|puska\w*|pušk\w*|pusk\w*|pistols?|pistole\w*|pistolet\w*|pistola\w*|pisztoly(?!tok)\w*|replica\w*|replik\w*|réplique\w*|gewehr\w*|fusil\w*|zbraň\w*|zbran\w*|shotguns?|sörétes|brokovnic\w*|samopal\w*|submachine|smg|lmg|sniper|revolver\w*)\y' as w,
      -- „X-hez / for X”: biztosan alkatrész vagy kiegészítő
      '\y(for|do|pro|für|pour|per|para|compatible|kompatib\w*|\w+(hoz|hez|höz))\y' as f
  ),
  s as (
    select x.*,
      case
        when c ~ '(pouch|\ytasak|holster|pisztolytok|\yslings?\y|heveder|\yvests?\y|mellény|plate ?carrier|chest ?rig|backpack|hátizsák|\y(gun|rifle|pistol|hard|soft|transport) ?(cases?|bags?)\y|fegyvertásk|\ykufr|pouzdr|futerał|futeral|pokrowi|\ybelt\y|\yöv\y|\ytok\y|táska)' then 'acc_gear'
        when c ~ '(\ymasks?\y|maszk|goggles?|szemüveg|\yglasses\y|helmets?|sisak|face ?shield|\year ?pro|kesztyű|\ygloves?\y|knee ?pads?|térdvédő)' then 'acc_protect'
        when c ~ '(magazin|magazyn|\ymags?\y|\yhi-?caps?\y|\ymid-?caps?\y|\ylow-?caps?\y|\ytár(ak|at|ral)?\y|zásobník|zasobnik|chargeur|cargador|caricator|\yshells?\y|speed ?loader|bb ?loader)' then 'acc_mag'
        when c ~ '(\ybbs?\y|\y\d[.,]\d{2} ?g\y|\ygolyó\y|golyók\y|kuličky\y|kulki\y|green ?gas|top ?gas|\ypropane|co2 ?(cartridge|capsule|patron|bombičk|bombick|kapsuł|kapsul)|gáz ?palack|\ygas ?(can|bottle|refill)s?\y)' then 'acc_ammo'
        when c ~ '(batter(y|ies)|\yakku|akkumul|\ybaterie|akumul|batterie|\yli-?po\y|\yli-?ion\y|\yli-?fe\y|\ynimh\y|chargers?\y|\ytöltő|nabíječk|ładowar|ladowar|\ydeans\y)' then 'acc_power'
        when c ~ '(scopes?\y|céltávcs|red ?dots?|holo(graphic)? ?sights?|kolimátor|kolimator|celownik|zaměřovač|magnifier|\yoptics?\y|flashlights?|lámpa|\ylasers?\y|tracer)' then 'acc_optics'
        when c ~ '(hop-?up|bucking|inner ?barrel|belső ?cső|precision ?barrel|tight ?bore|\yr-?hop|hop ?chamber|\ynub\y)' then 'part_hopup'
        when c ~ '(\ymotors?\y|mosfet|wiring|trigger ?unit)' then 'part_motor'
        when c ~ '(gearbox|mechabox|gear ?sets?|\ygears\y|fogaskerék|piston|dugattyú|cylinder|\yhenger|nozzle|tappet|spring ?guide|rugóvezet|bushings?|bearings?|anti-?reversal|selector ?plate|air ?seal|o-?rings?|(main|aeg|upgrade|gearbox|power|valve|nozzle|hammer|recoil|tappet|trigger) ?springs?|\ysprings? (m|sp)\d{2,3}\y|\y(m|sp)\d{2,3} ?springs?|\yrugó\y|pružin|sprężyn|sprezyn|blowback ?unit|\yvalves?\y|\ysear\y)' then 'part_internal'
        when c ~ '(suppressor|silencer|hangtompító|tlumič|flash ?hider|compensator|bipod|villaláb)' then 'part_external'
      end as sub
    from x
  )
  select case
    -- gránát, gránátvető (a gránáttartó tasak felszerelés)
    when c ~ '(gránát|granát|grenade|granate|granada|granata|launcher|\y40 ?mm\y|\ym203\y|\ym320\y|\ygl-?06\y|claymore)'
         and c !~ '(pouch|tasak|holder|tartó|zseb|pocket|sumka)' then 'grenade'
    -- alkatrész / kiegészítő, hacsak nem fegyver fegyveráron (csomag: „AK AEG + akku”)
    -- (optika, védőfelszerelés, BB/gáz sosem fegyver: „rifle scope”)
    when sub is not null and (sub in ('acc_optics','acc_protect','acc_ammo') or c ~ f or not (c ~ w and p >= 30000)) then sub
    -- kétértelmű külső alkatrész-szavak (tus, markolat, sín, szán...) csak olcsón, és fegyverszó nélkül vagy „for X” alakban
    when (c !~ w or c ~ f) and p < 40000 and c ~ '(handguard|\yris\y|keymod|m-?lok|\yrails?\y|\ystocks?\y|válltámasz|\ygrips?\y|markolat|outer ?barrel|külső ?cső|\ybody\y|receiver|\yslides?\y|iron ?sights?|\ysights?\y|\ymounts?\y|buffer ?tube|charging ?handle)' then 'part_external'
    when c !~ w and c ~ '(cleaning|\yoil\y|olaj|silicon|szilikon|grease|\ytargets?\y|céltábl|chrono|\ypatch|\yradio|headset|knife|\ykés\y|bayonet|\ytools?\y|szerszám)' then 'other'
    -- fegyvertípusok a címből
    when c ~ '(sniper|mesterlövész|odstřel|odstrel|\ydmr\y|\ysvd\y|dragunov|\yvsr|\yl96|\yawm\y|\yaw ?338|\ym24\y|\ym40\y|\ym700\y|\ysrs\y|\yssg|\ymb ?0?\d{2}\y|bolt[- ]action|\ysr-?25|\ym14\y|\yg28\y|\ysr-?10\y|\ymk ?1[12]\y|\ytac-?41|\yt-?10\y|\yscout\y|marksman)' then 'sniper'
    when c ~ '(\ylmg\y|géppuska|kulomet|machine ?gun|machine-gun|\ym249|\ym60\y|\ypkm?\y|\yrpk|\ymg ?(3|4|42|5)\y|\ymk ?4[68]\y|minimi|\ynegev|\ym240|\yrpd\y|\ysaw\y)' then 'lmg'
    when c ~ '(shotgun|sörétes|brokovnic|fusil à pompe|\ym870|\yspas|\ym1014|\yaa-?12|\ymp-?153|\yksg\y|\ym3 super|\ypump\y|flinta)' then 'shotgun'
    when c ~ '(\ysmg\y|géppisztoly|samopal|submachine|sub-machine|pistolet[- ]mitrailleur|\ymp ?5|\ymp ?7\y|\yp ?90\y|\yump|\yvector\y|kriss|scorpion|\yuzi\y|\ymp ?9\y|\ymac-?1[01]|\yvmp|\ypdw\y|ppsh|thompson|\ysten\y|\ymp ?40|\ypp-?19|bizon|\ypp-?2000)' then 'smg'
    when c ~ '(pisztoly(?!tok)|\ypistol|\ypistole|\ypistolet|\ypistola|handgun|revolver|glock|\yg ?1[789]\y|hi-?capa|\y1911|\ym9\y|\yp226|\yp320|\yusp\y|beretta|desert eagle|\ycz ?75|\ycz ?p-?0\d|\ym&p|five-seven|walther|\yppk|makarov|\ytt-?33|\yaep\y)' then 'pistol'
    when c ~ '(\yaeg\y|\ygbbr\y|\yhpa\y|\yebb\y|replica|replika|réplique|rifle|carbine|karabély|karabin|puska|puška|zbraň|zbran|fusil|gewehr|\ym4\y|\ym16|\yar-?15|\yhk ?416|\yak-?\d{2}|\yaks|\yakm|\yg36|\yscar|\yaug\y|famas|\ysa-[a-z]\d|\ycm\.?\d{3}|assault)' then 'rifle'
    -- végső tartalék: a bolt URL-je (alkatrész-útvonal -> alkatrész, fegyver-útvonal -> fegyvertípus)
    when u ~ '(parts|alkatr|części|czesci|díly|dily|ersatzteil|tuning|upgrade|ricambi|repuestos|pieces-detachees)' and p < 40000 then 'part_internal'
    when u ~ '(accessor|kiegeszit|zubehor|prislusenstvi|akcesori|accessoires|accesorios)' and p < 40000 then 'other'
    when u ~ '(sniper|odstrel|mesterlovesz)' then 'sniper'
    when u ~ '(pistol|pisztoly|pistole|pistolet)' then 'pistol'
    when u ~ '(smg|submachine|samopal|geppisztoly)' then 'smg'
    when u ~ '(rifle|carbine|karabin|gewehr|assault|aeg|elektromos|airsoft-guns|airsoftove-zbrane)' then 'rifle'
    when p >= 40000 then 'rifle'      -- drága, de ismeretlen típusú: nagy eséllyel fegyver
    else 'other'
  end
  from s
$$;

-- régi, 2 paraméteres változat (0007) a régi hívások miatt: URL nélkül
create or replace function airsoft_category(t text, price numeric) returns text
language sql immutable as $$ select airsoft_category(t, null, price) $$;

create or replace function airsoft_group(cat text) returns text
language sql immutable as $$
  select case when cat in ('rifle','pistol','smg','sniper','lmg','shotgun','grenade') then 'weapons'
              when cat like 'part\_%' then 'parts' else 'acc' end
$$;

-- „Mihez jó”: platformok a címből (fegyvernél is: M4 vagy AK)
create or replace function airsoft_platforms(t text) returns text[]
language sql immutable as $$
  select array_remove(array[
    case when t ~* '(\ym4a?1?\y|\ym16|\yar-?15|\yhk ?416|\ymk ?18\y|\ycqb-?r|\yurg-?i|\ysr-?16|\ysa-[ce]\d)' then 'm4' end,
    case when t ~* '(\yak-?\d{2,3}[a-z]{0,3}\y|\yakm[sn]?\y|\yaks-?\d{2}|\yak ?47|\yrpk|\ysaiga|\ykrinkov|\yvepr)' then 'ak' end,
    case when t ~* '\yg36' then 'g36' end,
    case when t ~* '\ymp ?5' then 'mp5' end,
    case when t ~* '\yaug\y' then 'aug' end,
    case when t ~* '\yscar' then 'scar' end,
    case when t ~* '(\ym14\y|\yebr\y)' then 'm14' end,
    case when t ~* '\yp ?90\y' then 'p90' end,
    case when t ~* '(\yvsr|\ymb ?0?(1|2|3|4)\y|\ybar ?10\y)' then 'vsr' end,
    case when t ~* '(\yl96|\yawp\y|\ymb ?(44|4401|01)\y)' then 'l96' end,
    case when t ~* '(glock|\yg ?1[789]x?\y)' then 'glock' end,
    case when t ~* '(hi-?capa|\y1911|\ym1911)' then 'hicapa' end,
    case when t ~* '(\ym9\y|\ym92|\ym9a1|beretta ?92)' then 'm9' end,
    case when t ~* '((gearbox|mechabox)[^,]{0,20}\yv ?2\y|\yv ?2\y[^,]{0,20}(gearbox|mechabox))' then 'gb_v2' end,
    case when t ~* '((gearbox|mechabox)[^,]{0,20}\yv ?3\y|\yv ?3\y[^,]{0,20}(gearbox|mechabox))' then 'gb_v3' end
  ], null)
$$;

-- ---------------------------------------------------------------------------------------------
-- product_summary: kategória = a boltok többségi szavazata (+ a terméknév fél szavazat döntetlenhez),
-- platformok = a név és az azonos csoportba sorolt bolti címek uniója.
drop materialized view if exists product_summary cascade;
create materialized view product_summary as
with oc as (
  select v.*, airsoft_category(m.name || ' ' || v.title_raw, v.url, v.price_huf) as cat
  from v_offers_dedup v
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
join v_offers_dedup v on v.product_id = p.id
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

-- ---------------------------------------------------------------------------------------------
-- Kereső: több kategória (levél vagy csoport: weapons / parts / acc) és több platform egyszerre.
drop function if exists catalog_search(text, text, text[], numeric, numeric, boolean, text, int, int, numeric[]);
create or replace function catalog_search(
  q text default null, cats text[] default null, plats text[] default null, brands text[] default null,
  pmin numeric default null, pmax numeric default null, in_stock boolean default false,
  sort text default 'popular', lim int default 24, off int default 0, edges numeric[] default null)
returns jsonb language sql stable as $$
with base as (
  select ps.id, ps.slug, ps.name, ps.manufacturer, ps.image_url, ps.category, ps.platforms, ps.best_price_huf,
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
    (cats is null or cardinality(cats) = 0 or b.category = any(cats)
       or airsoft_group(b.category) = any(cats))                                                as c_ok,
    (plats is null or cardinality(plats) = 0 or b.platforms && plats)                            as l_ok,
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
  from f where c_ok and l_ok and b_ok and p_ok and s_ok
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
                   from (select category, count(*) n from f where l_ok and b_ok and p_ok and s_ok group by category) c),
    'platforms', (select coalesce(jsonb_object_agg(pl, n), '{}'::jsonb)
                  from (select pl, count(*) n from f, unnest(f.platforms) pl where c_ok and b_ok and p_ok and s_ok group by pl) x),
    'brands', (select coalesce(jsonb_agg(jsonb_build_object('name', manufacturer, 'n', n) order by n desc, manufacturer), '[]'::jsonb)
               from (select manufacturer, count(*) n from f where c_ok and l_ok and p_ok and s_ok group by manufacturer) m),
    'price', (select jsonb_build_object('min', min(price), 'max', max(price)) from f where c_ok and l_ok and b_ok and s_ok),
    'buckets', case when edges is null then null else
               (select coalesce(jsonb_object_agg(bk, n), '{}'::jsonb)
                from (select width_bucket(price, edges) bk, count(*) n
                      from f where c_ok and l_ok and b_ok and s_ok and price is not null group by bk) w) end,
    'in_stock', (select count(*) from f where c_ok and l_ok and b_ok and p_ok and stock = 'in_stock'))
)
$$;

grant select on all tables in schema public to anon, authenticated;
grant select on product_summary to anon, authenticated;
grant execute on function catalog_search(text, text[], text[], text[], numeric, numeric, boolean, text, int, int, numeric[]) to anon, authenticated;

-- ---------------------------------------------------------------------------------------------
-- Takarítás: a fegyverhez tévesen párosított olcsó tár/alkatrész/kiegészítő ajánlatok leválasztása.
-- Feltétel: az ajánlat saját címe alkatrész/kiegészítő, a termék többségi kategóriája fegyver, ÉS az ajánlat
-- ára a termék legdrágább ajánlatának 35%-a alatt van. A következő éjszakai futás újrapárosítja őket
-- (már az új szabállyal: alkatrész nem kerülhet fegyverhez). Kézi párosítást nem érint.
with bad as (
  select o.id
  from v_offers o
  join products p on p.id = o.product_id
  join manufacturers m on m.id = p.manufacturer_id
  join product_summary ps on ps.id = o.product_id
  where o.match_status <> 'manual'
    and airsoft_group(ps.category) = 'weapons'
    and airsoft_group(airsoft_category(m.name || ' ' || o.title_raw, o.url, o.price_huf)) <> 'weapons'
    and o.price_huf < 0.35 * ps.max_price_huf
)
update offers o set product_id = null, match_status = 'pending', match_method = null, match_confidence = null
from bad where o.id = bad.id;

select refresh_product_summary();
select category, count(*) as termekek from product_summary group by category order by 2 desc;
