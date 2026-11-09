"""
Kategória- és platform-besorolás (eredetileg Postgres SQL-függvény volt, ennek pontos Python-megfelelője).
A D1 (SQLite) nem tud regexet, ezért a besorolás itt fut (scraper/summary.py hívja). A mintákat a SQL-ből
generáltuk (\\y -> \\b); ha a szabály változik, mindkét helyen módosítsd (teszt: test_classify.py).
"""
from __future__ import annotations

import re

_C = {
    'BUNDLE': re.compile('(\\s\\+|\\sw/|\\b(with|incl|including|included|mit|avec|con|com|včetně|vcetne|vč|plus|és|w zestawie|z zestawem|set with)\\b).*$', re.I),
    'W': re.compile('\\b(aeg|aep|gbbr?|nbb|hpa|ebb|rifles?|carbines?|karabély\\w*|karabin\\w*|puska\\w*|pušk\\w*|pusk\\w*|pistols?|pistole\\w*|pistolet\\w*|pistola\\w*|pisztoly(?!tok)\\w*|replica\\w*|replik\\w*|réplique\\w*|gewehr\\w*|fusil\\w*|zbraň\\w*|zbran\\w*|shotguns?|sörétes|brokovnic\\w*|samopal\\w*|submachine|smg|lmg|sniper|revolver\\w*)\\b', 0),
    'F': re.compile('\\b(for|do|pro|für|pour|per|para|compatible|kompatib\\w*|\\w+(hoz|hez|höz))\\b', 0),
    'M1': re.compile('\\b(for|für|pour|para|compatible|kompatib\\w*)\\s+(\\S+\\s+){0,2}\\S*(\\d|m4|ak|glock|hi-?capa|vsr|mp5|g36|l96|aeg|gbb|pistol\\w*|rifle\\w*|pu[sš]k\\w*|replik\\w*|replic\\w*|karabin\\w*)', 0),
    'M2': re.compile('(^|\\s)(pro|do|per)\\s+(\\S+\\s+){0,2}\\S*(\\d|[Mm]4|AK|[Gg]lock|[Hh]i-?[Cc]apa|VSR|vsr|MP5|mp5|G36|g36|pistol|rifle|pu[sš]k|replik|karabin)', 0),
    'M3': re.compile('\\S*(\\d|m4|ak|glock|vsr|mp5|g36)\\S*-(hoz|hez|höz)\\b', 0),
    'GEAR': re.compile('(pouch|\\btasak|holster|pisztolytok|\\bslings?\\b|heveder|\\bvests?\\b|mellény|plate ?carrier|chest ?rig|backpack|hátizsák|\\b(gun|rifle|pistol|hard|soft|transport) ?(cases?|bags?)\\b|fegyvertásk|\\bkufr|pouzdr|futerał|futeral|pokrowi|\\bbelt\\b|\\böv\\b|\\btok\\b|táska)', 0),
    'PROTECT': re.compile('(\\bmasks?\\b|maszk|goggles?|szemüveg|\\bglasses\\b|helmets?|sisak|face ?shield|\\bear ?pro|kesztyű|\\bgloves?\\b|knee ?pads?|térdvédő)', 0),
    'MAG': re.compile('(magazin|magazyn|\\bmags?\\b|\\bhi-?caps?\\b|\\bmid-?caps?\\b|\\blow-?caps?\\b|\\btár(ak|at|ral)?\\b|zásobník|zasobnik|chargeur|cargador|caricator|\\bshells?\\b|speed ?loader|bb ?loader|magazynek|caricatore)', 0),
    'AMMO': re.compile('(\\bbbs?\\b|\\b\\d[.,]\\d{2} ?g\\b|\\bgolyó\\b|golyók\\b|kuličky\\b|kulki\\b|green ?gas|top ?gas|\\bpropane|co2 ?(cartridge|capsule|patron|bombičk|bombick|kapsuł|kapsul)|gáz ?palack|\\bgas ?(can|bottle|refill)s?\\b)', 0),
    'POWER': re.compile('(batter(y|ies)|\\bakku|akkumul|\\bbaterie|akumul|batterie|\\bli-?po\\b|\\bli-?ion\\b|\\bli-?fe\\b|\\bnimh\\b|chargers?\\b|\\btöltő|nabíječk|ładowar|ladowar|\\bdeans\\b|akumulátor|akkumulátor|nabíječ)', 0),
    'OPTICS': re.compile('(scopes?\\b|céltávcs|red ?dots?|holo(graphic)? ?sights?|kolimátor|kolimator|celownik|zaměřovač|magnifier|\\boptics?\\b|flashlights?|lámpa|\\blasers?\\b|tracer|puškohled|puskohled|\\bluneta)', 0),
    'HOPUP': re.compile('(hop-?up|bucking|inner ?barrel|belső ?cső|precision ?barrel|tight ?bore|\\br-?hop|hop ?chamber|\\bnub\\b|hlaveň|hlaven|\\blufa\\b|\\blauf\\b|\\bcanna\\b|gumičk|gumick)', 0),
    'MOTOR': re.compile('(\\bmotors?\\b|mosfet|wiring|trigger ?unit)', 0),
    'INTERNAL': re.compile('(gearbox|mechabox|gear ?sets?|\\bgears\\b|fogaskerék|piston|dugattyú|cylinder|\\bhenger|nozzle|tappet|spring ?guide|rugóvezet|bushings?|bearings?|anti-?reversal|selector ?plate|air ?seal|o-?rings?|(main|aeg|upgrade|gearbox|power|valve|nozzle|hammer|recoil|tappet|trigger) ?springs?|\\bsprings? (m|sp)\\d{2,3}\\b|\\b(m|sp)\\d{2,3} ?springs?|\\brugó(szett|készlet|k)?\\b|pružin|sprężyn|sprezyn|blowback ?unit|\\bvalves?\\b|\\bsear\\b|\\bválec|\\bvalec|\\bválce|\\bpíst|\\bpist(u|y|em)?\\b|tłok|\\btlok|kolben|zylinder|cylindre|cilindro|pistone|\\bfeder\\b|ressort|\\bmolla\\b|muelle|těsnění|tesneni|tömítés|převod|prevod|ozuben|spoušť|spoust|ravasz|(upgrade|tuning) ?(set|kit)|ersatzteil|náhradní|nahradni|alkatrész|części|czesci)', 0),
    'EXTERNAL': re.compile('(suppressor|silencer|hangtompító|tlumič|flash ?hider|compensator|bipod|villaláb|tłumik|tlumik|conversion ?kit|konverz)', 0),
    'GRENADE': re.compile('(gránát|granát|grenade|granate|granada|granata|launcher|\\b40 ?mm\\b|\\bm203\\b|\\bm320\\b|\\bgl-?06\\b|claymore)', 0),
    'GRENADE_NOT': re.compile('(pouch|tasak|holder|tartó|zseb|pocket|sumka)', 0),
    'M_EXTERNAL': re.compile('(handguard|\\bris\\b|keymod|m-?lok|\\brails?\\b|\\bstocks?\\b|válltámasz|\\bgrips?\\b|markolat|outer ?barrel|külső ?cső|\\bbody\\b|receiver|\\bslides?\\b|sights?\\b|\\bmounts?\\b|pažb|pazb|\\bkolba\\b|předpažb|előagy|rukojeť|rukojet|chwyt|conversion)', 0),
    'AMBIG_EXTERNAL': re.compile('(handguard|\\bris\\b|keymod|m-?lok|\\brails?\\b|\\bstocks?\\b|válltámasz|\\bgrips?\\b|markolat|outer ?barrel|külső ?cső|\\bbody\\b|receiver|\\bslides?\\b|iron ?sights?|\\bsights?\\b|\\bmounts?\\b|buffer ?tube|charging ?handle)', 0),
    'OTHER_MISC': re.compile('(cleaning|\\boil\\b|olaj|silicon|szilikon|grease|\\btargets?\\b|céltábl|chrono|\\bpatch|\\bradio|headset|knife|\\bkés\\b|bayonet|\\btools?\\b|szerszám)', 0),
    'SNIPER': re.compile('(sniper|mesterlövész|odstřel|odstrel|\\bdmr\\b|\\bsvd\\b|dragunov|\\bvsr|\\bl96|\\bawm\\b|\\baw ?338|\\bm24\\b|\\bm40\\b|\\bm700\\b|\\bsrs\\b|\\bssg|\\bmb ?0?\\d{2}\\b|bolt[- ]action|\\bsr-?25|\\bm14\\b|\\bg28\\b|\\bsr-?10\\b|\\bmk ?1[12]\\b|\\btac-?41|\\bt-?10\\b|\\bscout\\b|marksman)', 0),
    'LMG': re.compile('(\\blmg\\b|géppuska|kulomet|machine ?gun|machine-gun|\\bm249|\\bm60\\b|\\bpkm?\\b|\\brpk|\\bmg ?(3|4|42|5)\\b|\\bmk ?4[68]\\b|minimi|\\bnegev|\\bm240|\\brpd\\b|\\bsaw\\b)', 0),
    'SHOTGUN': re.compile('(shotgun|sörétes|brokovnic|fusil à pompe|\\bm870|\\bspas|\\bm1014|\\baa-?12|\\bmp-?153|\\bksg\\b|\\bm3 super|\\bpump\\b|flinta)', 0),
    'SMG': re.compile('(\\bsmg\\b|géppisztoly|samopal|submachine|sub-machine|pistolet[- ]mitrailleur|\\bmp ?5|\\bmp ?7\\b|\\bp ?90\\b|\\bump|\\bvector\\b|kriss|scorpion|\\buzi\\b|\\bmp ?9\\b|\\bmac-?1[01]|\\bvmp|\\bpdw\\b|ppsh|thompson|\\bsten\\b|\\bmp ?40|\\bpp-?19|bizon|\\bpp-?2000)', 0),
    'PISTOL': re.compile('(pisztoly(?!tok)|\\bpistol|\\bpistole|\\bpistolet|\\bpistola|handgun|revolver|glock|\\bg ?1[789]\\b|hi-?capa|\\b1911|\\bm9\\b|\\bp226|\\bp320|\\busp\\b|beretta|desert eagle|\\bcz ?75|\\bcz ?p-?0\\d|\\bm&p|five-seven|walther|\\bppk|makarov|\\btt-?33|\\baep\\b)', 0),
    'RIFLE': re.compile('(\\baeg\\b|\\bgbbr\\b|\\bhpa\\b|\\bebb\\b|replica|replika|réplique|rifle|carbine|karabély|karabin|puska|puška|zbraň|zbran|fusil|gewehr|\\bm4\\b|\\bm16|\\bar-?15|\\bhk ?416|\\bak-?\\d{2}|\\baks|\\bakm|\\bg36|\\bscar|\\baug\\b|famas|\\bsa-[a-z]\\d|\\bcm\\.?\\d{3}|assault)', 0),
    'URL_PARTS': re.compile('(parts|alkatr|części|czesci|díly|dily|ersatzteil|tuning|upgrade|ricambi|repuestos|pieces-detachees)', 0),
    'URL_ACC': re.compile('(accessor|kiegeszit|zubehor|prislusenstvi|akcesori|accessoires|accesorios)', 0),
    'URL_SNIPER': re.compile('(sniper|odstrel|mesterlovesz)', 0),
    'URL_PISTOL': re.compile('(pistol|pisztoly|pistole|pistolet)', 0),
    'URL_SMG': re.compile('(smg|submachine|samopal|geppisztoly)', 0),
    'URL_RIFLE': re.compile('(rifle|carbine|karabin|gewehr|assault|aeg|elektromos|airsoft-guns|airsoftove-zbrane)', 0),
}
_BUNDLE_O = re.compile(_C['BUNDLE'].pattern, re.I)

WEAPONS = {'rifle', 'pistol', 'smg', 'sniper', 'lmg', 'shotgun', 'grenade'}
_SUBS = [('GEAR', 'acc_gear'), ('PROTECT', 'acc_protect'), ('MAG', 'acc_mag'), ('AMMO', 'acc_ammo'), ('POWER', 'acc_power'),
         ('OPTICS', 'acc_optics'), ('HOPUP', 'part_hopup'), ('MOTOR', 'part_motor'), ('INTERNAL', 'part_internal'),
         ('EXTERNAL', 'part_external')]
_WEAPON_RULES = [('SNIPER', 'sniper'), ('LMG', 'lmg'), ('SHOTGUN', 'shotgun'), ('SMG', 'smg'), ('PISTOL', 'pistol'), ('RIFLE', 'rifle')]
_URL_TYPES = [('URL_SNIPER', 'sniper'), ('URL_PISTOL', 'pistol'), ('URL_SMG', 'smg'), ('URL_RIFLE', 'rifle')]


# Árküszöb (Ft): ennél olcsóbb tétel nem lehet ilyen fegyver. Csak modellnév (M4, AK, SCAR, 1911, SVD…) és nincs
# fegyverszó (AEG, GBB, puska, pistol, replika…) -> magasabb küszöb. Így a „Šroub pažbičky M4” (csavar, 673 Ft)
# vagy a „Klapka pro SVD GBB” nem kerül a fegyverek közé. Ár nélkül (terméknév-szavazat) nincs küszöb.
_FLOOR = {'pistol': 2500, 'shotgun': 4000, 'smg': 6000, 'rifle': 6000, 'sniper': 6000, 'lmg': 20000}
_FLOOR_MODEL_ONLY = {'pistol': 8000, 'shotgun': 10000}
_FLOOR_MODEL_ONLY_DEFAULT = 15000


def _weapon_ok(cat: str, p: float, explicit: bool) -> bool:
    if p <= 0:
        return True
    if p < _FLOOR.get(cat, 6000):
        return False
    return explicit or p >= _FLOOR_MODEL_ONLY.get(cat, _FLOOR_MODEL_ONLY_DEFAULT)


def category(title: str | None, url: str | None = None, price: float | None = None) -> str:
    o = _BUNDLE_O.sub('', title or '')
    c = _C['BUNDLE'].sub('', (title or '').lower())
    u = (url or '').lower()
    p = float(price or 0)
    has = lambda k, s=c: _C[k].search(s) is not None
    w, f = has('W'), has('F')
    m = has('M1') or has('M2', o) or has('M3')
    sub = next((name for k, name in _SUBS if has(k)), None)
    if has('GRENADE') and not has('GRENADE_NOT'):
        if 0 < p < 8000 and (m or f or sub):              # „Bearings for 40mm grenades”, „seal kit pro granáty”
            return sub or 'part_internal'
        return 'grenade'
    if m:
        return sub or ('part_external' if has('M_EXTERNAL') else 'other')
    if sub and (sub in ('acc_optics', 'acc_protect', 'acc_ammo') or f or not (w and p >= 30000)):
        return sub
    if (not w or f) and p < 40000 and has('AMBIG_EXTERNAL'):
        return 'part_external'
    if not w and has('OTHER_MISC'):
        return 'other'
    explicit = w and not f
    not_weapon = 'part_external' if (has('M_EXTERNAL') or platforms(o)) else 'other'
    for k, name in _WEAPON_RULES:
        if has(k):
            return name if _weapon_ok(name, p, explicit) else not_weapon
    if has('URL_PARTS', u) and p < 40000:
        return 'part_internal'
    if has('URL_ACC', u) and p < 40000:
        return 'other'
    for k, name in _URL_TYPES:
        if has(k, u):
            return name if _weapon_ok(name, p, explicit) else not_weapon
    return 'rifle' if p >= 40000 else 'other'


def group(cat: str | None) -> str:
    if cat in WEAPONS:
        return 'weapons'
    return 'parts' if (cat or '').startswith('part_') else 'acc'


_PLATFORMS = [
    ('m4', re.compile('(\\bm4a?1?\\b|\\bm16|\\bar-?15|\\bhk ?416|\\bmk ?18\\b|\\bcqb-?r|\\burg-?i|\\bsr-?16|\\bsa-[ce]\\d)', re.I)),
    ('ak', re.compile('(\\bak-?\\d{2,3}[a-z]{0,3}\\b|\\bakm[sn]?\\b|\\baks-?\\d{2}|\\bak ?47|\\brpk|\\bsaiga|\\bkrinkov|\\bvepr)', re.I)),
    ('g36', re.compile('\\bg36', re.I)),
    ('mp5', re.compile('\\bmp ?5', re.I)),
    ('aug', re.compile('\\baug\\b', re.I)),
    ('scar', re.compile('\\bscar', re.I)),
    ('m14', re.compile('(\\bm14\\b|\\bebr\\b)', re.I)),
    ('p90', re.compile('\\bp ?90\\b', re.I)),
    ('vsr', re.compile('(\\bvsr|\\bmb ?0?(1|2|3|4)\\b|\\bbar ?10\\b)', re.I)),
    ('l96', re.compile('(\\bl96|\\bawp\\b|\\bmb ?(44|4401|01)\\b)', re.I)),
    ('glock', re.compile('(glock|\\bg ?1[789]x?\\b)', re.I)),
    ('hicapa', re.compile('(hi-?capa|\\b1911|\\bm1911)', re.I)),
    ('m9', re.compile('(\\bm9\\b|\\bm92|\\bm9a1|beretta ?92)', re.I)),
    ('gb_v2', re.compile('((gearbox|mechabox)[^,]{0,20}\\bv ?2\\b|\\bv ?2\\b[^,]{0,20}(gearbox|mechabox))', re.I)),
    ('gb_v3', re.compile('((gearbox|mechabox)[^,]{0,20}\\bv ?3\\b|\\bv ?3\\b[^,]{0,20}(gearbox|mechabox))', re.I)),
]


def platforms(title: str | None) -> list[str]:
    t = title or ''
    return [name for name, rx in _PLATFORMS if rx.search(t)]
