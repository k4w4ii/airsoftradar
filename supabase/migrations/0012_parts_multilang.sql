-- =====================================================================
-- 0012: alkatrész-felismerés több nyelven + a régi, modellkód alapján összevont termékek szétbontása.
-- Adatot NEM töröl (ajánlatot sem). Újrafuttatható. A 0010 és 0011 UTÁN futtasd, utána: Actions -> rematch.
--  - új szabály: „X-hez / for X / pro X / do X” + modellkód vagy platform = alkatrész/tartozék
--    („Upgrade set pro CYMA M24 CM.702”, „AIRSOFTPRO ACÉL HENGER CYMA CM.702 M24-HEZ”, „RIS conversion for CM.030”)
--  - cseh / lengyel / német / francia / olasz / magyar alkatrésznevek (válec, píst, tłok, Zylinder, henger...)
--  - takarítás: (A) az alkatrész nevű termékek elengedik a fegyver modellkódját, a fegyver-ajánlataik leválnak;
--    (B) az alkatrész/tartozék ajánlatok leválnak a fegyver-termékekről, és ha modellkóddal párosultak, mindenhonnan
--    (a kód a fegyveré, nem az alkatrészé). A leválasztottakat a „rematch” művelet percek alatt újrapárosítja.
-- Ugyanez Pythonban: scraper/filters.py (is_part, made_for_other).
-- =====================================================================

set check_function_bodies = off;

create or replace function airsoft_category(title text, url text, price numeric) returns text
language sql immutable as $$
  with x as (
    select regexp_replace(coalesce(title, ''), '(\s\+|\sw/|\y(with|incl|including|included|mit|avec|con|com|včetně|vcetne|vč|plus|és|w zestawie|z zestawem|set with)\y).*$', '', 'i') as o,
           regexp_replace(lower(coalesce(title, '')), '(\s\+|\sw/|\y(with|incl|including|included|mit|avec|con|com|včetně|vcetne|vč|plus|és|w zestawie|z zestawem|set with)\y).*$', '') as c, lower(coalesce(url, '')) as u, coalesce(price, 0) as p,
      -- fegyverre utaló szó (főnév vagy rendszer)
      '\y(aeg|aep|gbbr?|nbb|hpa|ebb|rifles?|carbines?|karabély\w*|karabin\w*|puska\w*|pušk\w*|pusk\w*|pistols?|pistole\w*|pistolet\w*|pistola\w*|pisztoly(?!tok)\w*|replica\w*|replik\w*|réplique\w*|gewehr\w*|fusil\w*|zbraň\w*|zbran\w*|shotguns?|sörétes|brokovnic\w*|samopal\w*|submachine|smg|lmg|sniper|revolver\w*)\y' as w,
      -- „X-hez / for X”: biztosan alkatrész vagy kiegészítő
      '\y(for|do|pro|für|pour|per|para|compatible|kompatib\w*|\w+(hoz|hez|höz))\y' as f
  ),
  s as (
    select x.*,
      -- „X-hez / for X / pro X” + modellkód vagy platform: valami MÁSHOZ készült -> alkatrész/tartozék
      (c ~ '\y(for|für|pour|para|compatible|kompatib\w*)\s+(\S+\s+){0,2}\S*(\d|m4|ak|glock|hi-?capa|vsr|mp5|g36|l96|aeg|gbb|pistol\w*|rifle\w*|pu[sš]k\w*|replik\w*|replic\w*|karabin\w*)'
       or o ~ '(^|\s)(pro|do|per)\s+(\S+\s+){0,2}\S*(\d|[Mm]4|AK|[Gg]lock|[Hh]i-?[Cc]apa|VSR|vsr|MP5|mp5|G36|g36|pistol|rifle|pu[sš]k|replik|karabin)'
       or c ~ '\S*(\d|m4|ak|glock|vsr|mp5|g36)\S*-(hoz|hez|höz)\y') as m,
      case
        when c ~ '(pouch|\ytasak|holster|pisztolytok|\yslings?\y|heveder|\yvests?\y|mellény|plate ?carrier|chest ?rig|backpack|hátizsák|\y(gun|rifle|pistol|hard|soft|transport) ?(cases?|bags?)\y|fegyvertásk|\ykufr|pouzdr|futerał|futeral|pokrowi|\ybelt\y|\yöv\y|\ytok\y|táska)' then 'acc_gear'
        when c ~ '(\ymasks?\y|maszk|goggles?|szemüveg|\yglasses\y|helmets?|sisak|face ?shield|\year ?pro|kesztyű|\ygloves?\y|knee ?pads?|térdvédő)' then 'acc_protect'
        when c ~ '(magazin|magazyn|\ymags?\y|\yhi-?caps?\y|\ymid-?caps?\y|\ylow-?caps?\y|\ytár(ak|at|ral)?\y|zásobník|zasobnik|chargeur|cargador|caricator|\yshells?\y|speed ?loader|bb ?loader|magazynek|caricatore)' then 'acc_mag'
        when c ~ '(\ybbs?\y|\y\d[.,]\d{2} ?g\y|\ygolyó\y|golyók\y|kuličky\y|kulki\y|green ?gas|top ?gas|\ypropane|co2 ?(cartridge|capsule|patron|bombičk|bombick|kapsuł|kapsul)|gáz ?palack|\ygas ?(can|bottle|refill)s?\y)' then 'acc_ammo'
        when c ~ '(batter(y|ies)|\yakku|akkumul|\ybaterie|akumul|batterie|\yli-?po\y|\yli-?ion\y|\yli-?fe\y|\ynimh\y|chargers?\y|\ytöltő|nabíječk|ładowar|ladowar|\ydeans\y|akumulátor|akkumulátor|nabíječ)' then 'acc_power'
        when c ~ '(scopes?\y|céltávcs|red ?dots?|holo(graphic)? ?sights?|kolimátor|kolimator|celownik|zaměřovač|magnifier|\yoptics?\y|flashlights?|lámpa|\ylasers?\y|tracer|puškohled|puskohled|\yluneta)' then 'acc_optics'
        when c ~ '(hop-?up|bucking|inner ?barrel|belső ?cső|precision ?barrel|tight ?bore|\yr-?hop|hop ?chamber|\ynub\y|hlaveň|hlaven|\ylufa\y|\ylauf\y|\ycanna\y|gumičk|gumick)' then 'part_hopup'
        when c ~ '(\ymotors?\y|mosfet|wiring|trigger ?unit)' then 'part_motor'
        when c ~ '(gearbox|mechabox|gear ?sets?|\ygears\y|fogaskerék|piston|dugattyú|cylinder|\yhenger|nozzle|tappet|spring ?guide|rugóvezet|bushings?|bearings?|anti-?reversal|selector ?plate|air ?seal|o-?rings?|(main|aeg|upgrade|gearbox|power|valve|nozzle|hammer|recoil|tappet|trigger) ?springs?|\ysprings? (m|sp)\d{2,3}\y|\y(m|sp)\d{2,3} ?springs?|\yrugó\y|pružin|sprężyn|sprezyn|blowback ?unit|\yvalves?\y|\ysear\y|\yválec|\yvalec|\yválce|\ypíst|\ypist(u|y|em)?\y|tłok|\ytlok|kolben|zylinder|cylindre|cilindro|pistone|\yfeder\y|ressort|\ymolla\y|muelle|těsnění|tesneni|tömítés|převod|prevod|ozuben|spoušť|spoust|ravasz|(upgrade|tuning) ?(set|kit)|ersatzteil|náhradní|nahradni|alkatrész|części|czesci)' then 'part_internal'
        when c ~ '(suppressor|silencer|hangtompító|tlumič|flash ?hider|compensator|bipod|villaláb|tłumik|tlumik|conversion ?kit|konverz)' then 'part_external'
      end as sub
    from x
  )
  select case
    -- gránát, gránátvető (a gránáttartó tasak felszerelés)
    when c ~ '(gránát|granát|grenade|granate|granada|granata|launcher|\y40 ?mm\y|\ym203\y|\ym320\y|\ygl-?06\y|claymore)'
         and c !~ '(pouch|tasak|holder|tartó|zseb|pocket|sumka)' then 'grenade'
    when m then coalesce(sub, case when c ~ '(handguard|\yris\y|keymod|m-?lok|\yrails?\y|\ystocks?\y|válltámasz|\ygrips?\y|markolat|outer ?barrel|külső ?cső|\ybody\y|receiver|\yslides?\y|sights?\y|\ymounts?\y|pažb|pazb|\ykolba\y|předpažb|előagy|rukojeť|rukojet|chwyt|conversion)' then 'part_external' else 'other' end)
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


-- termékek csoportja a név alapján (a termék ajánlatainak medián árával)
create or replace view v_product_name_group as
select p.id, airsoft_group(airsoft_category(m.name || ' ' || p.name, null, med.mid::numeric)) as grp
from products p
join manufacturers m on m.id = p.manufacturer_id
left join (select product_id, percentile_cont(0.5) within group (order by price_huf) as mid
           from v_offers where product_id is not null group by product_id) med on med.product_id = p.id;

-- (A) alkatrész nevű termékek: a fegyver modellkódja felszabadul (a fegyver saját terméket kaphat) ...
update products p set model_code = null, model_code_norm = null
from v_product_name_group g where p.id = g.id and g.grp <> 'weapons' and p.model_code_norm is not null;

delete from product_codes pc
using v_product_name_group g
where pc.product_id = g.id and g.grp <> 'weapons' and pc.code_type <> 'ean';

-- ... és a rajtuk lévő fegyver-ajánlatok leválnak
with bad as (
  select o.id
  from v_offers o
  join products p on p.id = o.product_id
  join manufacturers m on m.id = p.manufacturer_id
  join v_product_name_group g on g.id = p.id
  where o.match_status <> 'manual' and g.grp <> 'weapons'
    and airsoft_group(airsoft_category(m.name || ' ' || o.title_raw, o.url, o.price_huf)) = 'weapons'
)
update offers o set product_id = null, match_status = 'pending', match_method = null, match_confidence = null
from bad where o.id = bad.id;

-- (B) alkatrész/tartozék ajánlatok: le a fegyver-termékekről, és le mindenhonnan, ha modellkóddal párosultak
with bad as (
  select o.id
  from v_offers o
  join products p on p.id = o.product_id
  join manufacturers m on m.id = p.manufacturer_id
  left join product_summary ps on ps.id = p.id
  where o.match_status <> 'manual'
    and airsoft_group(airsoft_category(m.name || ' ' || o.title_raw, o.url, o.price_huf)) <> 'weapons'
    and (airsoft_group(coalesce(ps.category, 'other')) = 'weapons' or o.match_method in ('code', 'new', 'weak_code'))
)
update offers o set product_id = null, match_status = 'pending', match_method = null, match_confidence = null
from bad where o.id = bad.id;

grant select on all tables in schema public to anon, authenticated;
select refresh_product_summary();
select (select count(*) from offers where match_status = 'pending' and is_active) as ujraparositasra_var,
       (select count(*) from product_summary) as latszo_termekek;
