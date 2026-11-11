"""
Kategória- és platform-besorolás (eredetileg Postgres SQL-függvény volt, ennek pontos Python-megfelelője).
A D1 (SQLite) nem tud regexet, ezért a besorolás itt fut (scraper/summary.py hívja). A mintákat a SQL-ből
generáltuk (\\y -> \\b); ha a szabály változik, mindkét helyen módosítsd (teszt: test_classify.py).
"""
from __future__ import annotations

import re
from urllib.parse import urlsplit

_C = {
    'BUNDLE': re.compile('(\\s\\+|\\sw/|\\b(with|incl|including|included|mit|avec|con|včetně|vcetne|vč|plus|és|w zestawie|z zestawem|set with)\\b).*$', re.I),
    'W': re.compile('\\b(aeg|aep|gbbr?|gbber|co2|guns?|nbb|hpa|ebbr?|sbr|mws|ptw|gas blowback|rifles?|carbines?|karabély\\w*|karabin\\w*|puska\\w*|pušk\\w*|pusk\\w*|pistols?|pistole\\w*|pistolet\\w*|pistola\\w*|pisztoly(?!tok)\\w*|replica\\w*|replik\\w*|réplique\\w*|gewehr\\w*|fusil\\w*|zbraň\\w*|zbran\\w*|shotguns?|sörétes|brokovnic\\w*|samopal\\w*|submachine|smg|lmg|sniper|revolver\\w*)\\b', 0),
    'F': re.compile('\\b(for|do|pro|für|pour|per|compatible|kompatib\\w*|\\w+(hoz|hez|höz))\\b', 0),
    'M1': re.compile('\\b(for|für|pour|compatible|kompatib\\w*)\\s+(\\S+\\s+){0,2}\\S*(\\d|m4|ak|glock|hi-?capa|vsr|mp5|g36|l96|aeg|gbb|pistol\\w*|rifle\\w*|pu[sš]k\\w*|replik\\w*|replic\\w*|karabin\\w*)', 0),
    'M2': re.compile('(^|\\s)(pro|do|per)\\s+(\\S+\\s+){0,2}\\S*(\\d|[Mm]4|AK|[Gg]lock|[Hh]i-?[Cc]apa|VSR|vsr|MP5|mp5|G36|g36|pistol|rifle|pu[sš]k|replik|karabin)', 0),
    'M3': re.compile('\\S*(\\d|m4|ak|glock|vsr|mp5|g36)\\S*-(hoz|hez|höz)\\b', 0),
    'GEAR': re.compile('(\\bpatch(es)?\\b|nášivk|nasivk|naszywk|felvarró|morale|pouch|\\btasak|holster|pisztolytok|\\bslings?\\b|heveder|\\bvests?\\b|mellény|plate ?carrier|chest ?rig|backpack|hátizsák|\\b(gun|rifle|pistol|hard|soft|transport) ?(cases?|bags?)\\b|fegyvertásk|\\bkufr|pouzdr|futerał|futeral|pokrowi|\\bbelt\\b|\\böv\\b|\\btok\\b|táska)', 0),
    'PROTECT': re.compile('(hearing|earmuffs?|ear ?defend\\w*|\\bmasks?\\b|maszk|goggles?|szemüveg|\\bglasses\\b|helmets?|sisak|face ?shield|\\bear ?pro|kesztyű|\\bgloves?\\b|knee ?pads?|térdvédő)', 0),
    'MAG': re.compile('(magazin|magazyn|\\bmags?\\b|\\bhi-?caps?\\b|\\bmid-?caps?\\b|\\blow-?caps?\\b|\\btár(ak|at|ral)?\\b|zásobník|zasobnik|chargeur|cargador|caricator|\\bshells?\\b|speed ?loader|bb ?loader|magazynek|caricatore)', 0),
    'AMMO': re.compile('(\\bbbs?\\b|\\b\\d[.,]\\d{2} ?g\\b|\\bgolyó\\b|golyók\\b|kuličky\\b|kulki\\b|green ?gas|top ?gas|\\bpropane|co2 ?(cartridge|capsule|patron|bombičk|bombick|kapsuł|kapsul)|gáz ?palack|\\bgas ?(can|bottle|refill)s?\\b)', 0),
    'POWER': re.compile('(\\b(hpa|air|co2) ?(tanks?|bottles?)\\b|\\btanks?\\b|lahev|palack|batter(y|ies)|\\bakku|akkumul|\\bbaterie|akumul|batterie|\\bli-?po\\b|\\bli-?ion\\b|\\bli-?fe\\b|\\bnimh\\b|chargers?\\b|\\btöltő|nabíječk|ładowar|ladowar|\\bdeans\\b|akumulátor|akkumulátor|nabíječ)', 0),
    'OPTICS': re.compile('(scopes?\\b|céltávcs|red ?dots?|holo(graphic)? ?sights?|reflex|dot ?sights?|rangefinder|range ?finder|dalmierz|távolságmérő|night ?vision|éjjellátó|thermal|binocular|kolimátor|kolimator|celownik|zaměřovač|magnifier|\\boptics?\\b|flashlights?|lámpa|\\blasers?\\b|tracer|puškohled|puskohled|\\bluneta)', 0),
    'HOPUP': re.compile('(hop-?up|\\b6[.,]0\\d ?mm\\b|\\bcső\\b|cijev|barrel precision|précision|hop ?up|bucking|inner ?barrel|belső ?cső|precision ?barrel|tight ?bore|\\br-?hop|hop ?chamber|\\bnub\\b|hlaveň|hlaven|\\blufa\\b|\\blauf\\b|\\bcanna\\b|gumičk|gumick)', 0),
    'MOTOR': re.compile('(\\bmotors?\\b|mosfet|wiring|trigger ?unit)', 0),
    'INTERNAL': re.compile('(gearbox|\\b(spare |original )?parts?\\b|hard ?gears?|\\b\\d{2}:1\\b|bolt ?carrier|regulators?\\b|\\breg\\b|feed ?plate|adagolólap|\\btriggers?\\b|trigger ?(box|unit|set)|hpa ?engine|fusion ?engine|mosfet|mechabox|gear ?sets?|\\bgears\\b|fogaskerék|piston|dugattyú|cylinder|\\bhenger|nozzle|tappet|spring ?guide|rugóvezet|bushings?|bearings?|anti-?reversal|selector ?plate|air ?seal|o-?rings?|(main|aeg|upgrade|gearbox|power|valve|nozzle|hammer|recoil|tappet|trigger) ?springs?|\\bsprings? (m|sp)\\d{2,3}\\b|\\b(m|sp)\\d{2,3} ?springs?|\\brugó(szett|készlet|k)?\\b|pružin|sprężyn|sprezyn|blowback ?unit|\\bvalves?\\b|\\bsear\\b|\\bválec|\\bvalec|\\bválce|\\bpíst|\\bpist(u|y|em)?\\b|tłok|\\btlok|kolben|zylinder|cylindre|cilindro|pistone|\\bfeder\\b|ressort|\\bmolla\\b|muelle|těsnění|tesneni|tömítés|převod|prevod|ozuben|spoušť|spoust|ravasz|(upgrade|tuning) ?(set|kit)|ersatzteil|náhradní|nahradni|alkatrész|części|czesci)', 0),
    'EXTERNAL': re.compile('(suppressor|silencer|hangtompító|tlumič|flash ?hider|compensator|bipod|villaláb|tłumik|tlumik|conversion ?kit|konverz)', 0),
    'STRONG_W': re.compile('\\b(aeg|aep|gbbr?|gbber|ebbr?|sniper|lmg|smg|machine ?gun|replica|replika|carbine|gas blowback)\\b', 0),
    'PISTOL_POWER': re.compile('\\b(gbb|gas blowback|co2|nbb|gnb)\\b', 0),
    'GRENADE': re.compile('(gránát|granát|grenade|granate|granada|granata|launcher|\\b40 ?mm\\b|\\bm203\\b|\\bm320\\b|\\bgl-?06\\b|claymore)', 0),
    'GRENADE_NOT': re.compile('(pouch|tasak|holder|tartó|zseb|pocket|sumka|\\bpatch|nášivk|nasivk|naszywk|felvarró|velcro|morale|sticker|matrica|keychain|kulcstartó|t-shirt|póló|\\btoy\\b)', 0),
    'M_EXTERNAL': re.compile('(handguard|forend|\\bris\\b|keymod|m-?lok|\\brails?\\b|\\bstocks?\\b|válltámasz|\\bgrips?\\b|markolat|outer ?barrel|külső ?cső|\\bbody\\b|receiver|\\bslides?\\b|sights?\\b|\\bmounts?\\b|pažb|pazb|\\bkolba\\b|předpažb|előagy|rukojeť|rukojet|chwyt|conversion)', 0),
    'AMBIG_EXTERNAL': re.compile('(handguard|forend|\\bris\\b|keymod|m-?lok|\\brails?\\b|\\bstocks?\\b|válltámasz|\\bgrips?\\b|markolat|outer ?barrel|külső ?cső|\\bbody\\b|receiver|\\bslides?\\b|iron ?sights?|\\bmounts?\\b|buffer ?tube|charging ?handle)', 0),
    'OTHER_MISC': re.compile('(cleaning|\\bracks?\\b|\\bstands?\\b|display|maintenance|\\boil\\b|olaj|silicon|szilikon|grease|\\btargets?\\b|céltábl|chrono|\\bpatch|\\bradio|headset|knife|\\bkés\\b|bayonet|\\btools?\\b|szerszám)', 0),
    'SNIPER': re.compile('(sniper|\\btrg\\b|\\bpgm\\b|\\.338|\\bhti\\b|\\bm40a\\d|kar ?98|enfield|\\ble4\\b|mesterlövész|odstřel|odstrel|\\bdmr\\b|\\bsvd\\b|dragunov|\\bvsr|\\bl96|\\bawm\\b|\\baw ?338|\\bm24\\b|\\bm40\\b|\\bm700\\b|\\bsrs\\b|\\bssg|\\bmb ?0?\\d{2}\\b|bolt[- ]action|\\bsr-?25|\\bm14\\b|\\bg28\\b|\\bsr-?10\\b|\\bmk ?1[12]\\b|\\btac-?41|\\bt-?10\\b|\\bscout\\b|marksman)', 0),
    'LMG': re.compile('(\\blmg\\b|géppuska|kulomet|(?<!sub)(?<!sub-)(?<!sub )machine[ -]?gun|\\bm249|\\bm60\\b|\\bpkm?\\b|\\brpk|\\bmg ?(3|4|42|5)\\b|\\bmk ?4[68]\\b|minimi|\\bnegev|\\bm240|\\brpd\\b|\\bsaw\\b)', 0),
    'SHOTGUN': re.compile('(shotgun|sörétes|brokovnic|fusil à pompe|\\bm870|\\bspas|\\bm1014|\\baa-?12|\\bmp-?153|\\bksg\\b|\\bm3 super|\\bpump\\b|flinta)', 0),
    'SMG': re.compile('(\\bsmg\\b|\\bpp-?2k\\b|\\bots-?126|géppisztoly|samopal|submachine|sub-machine|pistolet[- ]mitrailleur|\\bmp ?5|\\bmp ?7\\b|\\bp ?90\\b|\\bump|\\bvector\\b|kriss|scorpion|\\buzi\\b|\\bmp ?9\\b|\\bmac-?1[01]|\\bvmp|\\bpdw\\b|ppsh|thompson|\\bsten\\b|\\bmp ?40|\\bpp-?19|bizon|\\bpp-?2000)', 0),
    'PISTOL': re.compile('(pisztoly(?!tok)|\\bpistol|\\bpistole|\\bpistolet|\\bpistola|handgun|revolver|glock|\\bg ?1[789]\\b|hi-?capa|\\b1911|\\bm9\\b|\\bp226|\\bp320|\\busp\\b|beretta|desert eagle|\\bcz ?75|\\bcz ?p-?0\\d|\\bm&p|five-seven|walther|\\bppk|makarov|\\btt-?33|\\baep\\b)', 0),
    'RIFLE': re.compile('(\\baeg\\b|\\bgbbr\\b|\\bgbber\\b|\\bebbr?\\b|\\bsbr\\b|\\bmws\\b|\\bptw\\b|\\bmtw\\b|\\bmcx\\b|\\bpc1\\b|\\bl85|\\bel?ak-?\\d{2}|\\blk-?33|\\bheretic labs|\\bgarand\\b|replica|replika|réplique|rifle|carbine|karabély|karabin|puska|puška|zbraň|zbran|fusil|gewehr|\\bm4\\b|\\bm16|\\bar-?15|\\bhk ?416|\\bak-?\\d{2}|\\baks|\\bakm|\\bg36|\\bscar|\\baug\\b|famas|\\bsa-[a-z]\\d|\\bcm\\.?\\d{3}|assault)', 0),
    'URL_PARTS': re.compile('(parts|alkatr|części|czesci|díly|dily|ersatzteil|tuning|upgrade|ricambi|repuestos|pieces-detachees)', 0),
    'URL_ACC': re.compile('(accessor|kiegeszit|zubehor|prislusenstvi|akcesori|accessoires|accesorios)', 0),
    'URL_SNIPER': re.compile('(sniper|odstrel|mesterlovesz)', 0),
    'URL_PISTOL': re.compile('(pistol|pisztoly|pistole|pistolet)', 0),
    'URL_SMG': re.compile('(smg|submachine|samopal|geppisztoly)', 0),
    'URL_RIFLE': re.compile('(rifle|carbine|karabin|gewehr|assault|aeg|elektromos|airsoft-guns|airsoftove-zbrane)', 0),
}
_BUNDLE_O = re.compile(_C['BUNDLE'].pattern, re.I)

WEAPONS = {'rifle', 'pistol', 'smg', 'sniper', 'lmg', 'shotgun', 'grenade'}
# egyedi építésű / tuningolt / HPA / használt fegyverek külön csoportban (summary.py dönti el a termék szintjén)
CUSTOM = {'custom_rifle', 'custom_pistol', 'custom_sniper'}


ALL_CATEGORIES = WEAPONS | CUSTOM | {'part_internal', 'part_hopup', 'part_motor', 'part_external', 'acc_mag', 'acc_power',
                                     'acc_optics', 'acc_ammo', 'acc_protect', 'acc_gear', 'other'}


def custom_of(cat: str) -> str:
    return 'custom_pistol' if cat == 'pistol' else 'custom_sniper' if cat == 'sniper' else 'custom_rifle'


def is_gun(cat: str | None) -> bool:
    return cat in WEAPONS or cat in CUSTOM
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


_MODEL_CODE = re.compile(r"(?<![\w])[A-Z]{1,5}[-.]?\d{2,4}[A-Z]?(?![\w])")   # CM048, SA-C08, AM-007, LVOA-S nincs


_TAIL_NOISE = re.compile(r"(\W+(black|tan|od|olive|fde|de|grey|gray|green|coyote|multicam|silver|red|blue|sand|desert|"
                         r"dark earth|bronze|gold|white|airsoftpl[aá]za|airsoft|m-?lok|keymod|ris|mil|spec|mil-spec|style|type|model|version|\w{1,2}|\d+\w*))+\W*$")
_ENDS_PIECE = re.compile(r"\b(stocks?|handguards?|forends?|grips?|receivers?|body|slides?|mounts?|"
                         r"buffer tube|outer barrel|charging handle|dust cover|magwell|frame)\W*$")


_HEAD_PIECE = re.compile(r"\b(stocks?|handguards?|forends?|grips?|receivers?|body|slides?|mounts?|rails?|buffer tube|outer barrel|"
                         r"charging handle|dust cover|magwell|frame|(?<!starter )(?<!complete )(?<!full )(?<!go airsoft )kits?|"
                         r"conversions?|upper|lower|chassis|shell|housing)\W*$")
_COMPLETE = re.compile(r"\b(complete|completed|pre-?built|installed|fully assembled)\b")


def _translated(title: str) -> str:
    try:                                   # késleltetett import (a dictionary -> names -> matcher lánc ezt a modult is használja)
        from dictionary import translate
        return translate(title) or ''
    except Exception:                      # pragma: no cover
        return ''


def category(title: str | None, url: str | None = None, price: float | None = None) -> str:
    title = title or ''
    tt = _translated(title)                # idegen nyelvű cím: az angol fordítás is számít („SPEGNIFIAMMA” = flash hider)
    extra = tt if tt and tt.lower() != title.lower() else ''
    o = (_BUNDLE_O.sub('', title) + ' ' + _BUNDLE_O.sub('', extra)).strip()
    c = (_C['BUNDLE'].sub('', title.lower()) + ' ' + _C['BUNDLE'].sub('', extra.lower())).strip()
    u = urlsplit(url or '').path.lower()            # csak az útvonal: az „airsoft-guns.eu” domain nem fegyver
    p = float(price or 0)
    has = lambda k, s=c: _C[k].search(s) is not None
    w, f = has('W'), has('F')
    full = (title + ' ' + extra).lower()
    # „Stock w/ Adjustable Buttpad … for CM.708 Sniper Rifles”: a „w/” utáni rész nem csomag, a „for X” a fő tárgyra vonatkozik
    piece = has('AMBIG_EXTERNAL') or has('M_EXTERNAL') or any(has(k) for k, _ in _SUBS)
    m = has('M1') or has('M2', o) or has('M3') or (piece and has('M1', full))
    f = f or (piece and has('M1', full))
    sub = next((name for k, name in _SUBS if has(k)), None)
    if has('GRENADE') and not has('GRENADE_NOT'):
        return 'grenade'                                  # a gránát-alkatrész is itt marad (a „Gránát típusa” szűrőben: alkatrész)
    if m:
        return sub or ('part_external' if has('M_EXTERNAL') else 'other')
    # „Sniper M82 … Scope + bipod”, „FMG-9 tracer GBB”, „KAR98K Green Gas”: a tartozékszó a fegyver része, nem a termék
    gun_typed = any(has(k) for k, _ in _WEAPON_RULES if k != 'PISTOL')
    weapon_first = not f and sub in ('acc_optics', 'acc_ammo', 'acc_gear', 'acc_mag', 'acc_power') and (
        (has('STRONG_W') and p >= 30000 and sub != 'acc_mag')                     # 5-ös tárcsomag ≠ fegyver
        or (gun_typed and p >= 90000 and sub in ('acc_ammo', 'acc_mag')))         # „rifle scope”, „Rifle Plate Carrier” ≠ puska
    if weapon_first and sub == 'acc_gear' and _C['GEAR'].search(c).start() < _C['STRONG_W'].search(c).start():
        weapon_first = False          # „Gas Tank Cordura Pouch … M249 Machine Gun”: a tok a tárgy, a fegyver csak a „mihez”
    if sub and not weapon_first and (sub in ('acc_optics', 'acc_protect', 'acc_ammo', 'acc_gear', 'acc_mag') or f
                                     or not (has('STRONG_W') and p >= 30000)):   # „HPA regulator”, „Rifle Plate Carrier”
        return sub
    if (not w or f) and p < 40000 and has('AMBIG_EXTERNAL'):
        return 'part_external'
    # „A&K M1A Airsoft Rifle Polymer Stock”, „AAP01 SMG forend, M-LOK”: a cím utolsó szava a tárgy (színek, márka nélkül)
    if 0 < p < 60000 and _ENDS_PIECE.search(_TAIL_NOISE.sub('', c)):
        return 'part_external'
    # „King Arms CNC PDW M11 Kit for KWA … Sub-Machine Gun”, „VIK II M-LOK Handguard for Kriss Vector SMG”: a „for” előtti
    # rész (a termék maga) alkatrész/készlet -> árától függetlenül nem fegyver (kivéve a gyárilag összeszerelt „Complete” csomag)
    if f and (fm := _C['F'].search(c)) and _HEAD_PIECE.search(_TAIL_NOISE.sub('', c[:fm.start()])) and not _COMPLETE.search(c):
        return 'part_external'
    if has('OTHER_MISC') and (not w or 0 < p < 40000):
        return 'other'
    explicit = w and not f
    not_weapon = 'part_external' if (has('M_EXTERNAL') or platforms(o)) else 'other'
    for k, name in _WEAPON_RULES:
        if has(k):
            return name if _weapon_ok(name, p, explicit) else not_weapon
    # általános fegyverszó (GBB, gas blowback, HPA…) típus nélkül: drágán fegyver; GBB 120 000 Ft alatt pisztoly, felette puska
    if explicit and p >= 12000 and has('PISTOL_POWER') and p < 120000 and not platforms(o):
        return 'pistol'                                            # „Army Armament R28 GBB”, „Rogue 11 CO2”
    if explicit and p >= 25000:
        return 'rifle'
    if has('URL_PARTS', u) and p < 40000:
        return 'part_internal'
    if has('URL_ACC', u) and p < 40000:
        return 'other'
    for k, name in _URL_TYPES:
        if has(k, u):
            return name if _weapon_ok(name, p, explicit) else not_weapon
    # végső tartalék: drága, de semmi nem utal fegyverre -> csak akkor puska, ha modellkód vagy platform van a címben
    if p >= 40000 and ([x for x in platforms(o) if not x.startswith('gb_')] or _MODEL_CODE.search(o)):
        return 'rifle'
    if p >= 40000 and not f and _C['STRONG_W'].search(full) and not any(_C[k].search(full) for k, _ in _SUBS):
        return 'pistol' if _C['PISTOL'].search(full) else 'rifle'
    return 'other'


def group(cat: str | None) -> str:
    if cat in WEAPONS:
        return 'weapons'
    if cat in CUSTOM:
        return 'custom'
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


# Működés (hajtás): a szűrő „AEG / GBB / gáz / CO2 / rugós / HPA / AEP” értékei – fegyvereknél és alkatrészeknél is
# (alkatrésznél a „mihez jó”: „Hop-up rubber for GBB”, „gearbox V2” = AEG). Sorrend = a szűrő sorrendje.
POWERS = ['aeg', 'gbb', 'gas', 'co2', 'spring', 'hpa', 'aep']
_NBB = re.compile(r'\b(nbb|gnb|non[- ]?blow ?back)\b', re.I)
_POWER_RX = {
    'aeg': re.compile(r'\b(aeg|ebbr?|ptw|electric|elektromos|elektrick\w*|elektryczn\w*|gearbox\w*|mechabox\w*|mosfet|ngrs)\b', re.I),
    'gbb': re.compile(r'\b(gbbr?|gbber|gas ?blow ?back|blowback|mws|gbb\w*|gas ?mag\w*)\b', re.I),
    'gas': re.compile(r'\b(nbb|gnb|non[- ]?blow ?back)\b', re.I),
    'co2': re.compile(r'\bco2\b', re.I),
    'hpa': re.compile(r'\b(hpa|polar ?star|fusion engine|wolverine|inferno|mtw|reaper|heretic labs)\b', re.I),
    'aep': re.compile(r'\baep\b', re.I),
}
_SPRING_GUN = re.compile(r'\b(spring|springer|bolt[- ]action|manu[aá]l\w*|rug[oó]s|vsr-?\d*|l96|bar-?10|mb-?0\d+|ssg-?\d*)\b', re.I)
_SPRING_PART = re.compile(r'\b(vsr-?\d*|l96|bar-?10|mb-?0\d+|ssg-?\d*|bolt[- ]action|spring[- ]powered)\b', re.I)


def powers(title: str | None, gun: bool = True) -> list[str]:
    """A cím hajtás-típusai. gun=False (alkatrész/kiegészítő): a „spring” szó itt rugót jelent, nem rugós fegyvert."""
    t = title or ''
    out = {k for k, rx in _POWER_RX.items() if rx.search(t)}
    if _NBB.search(t):
        out.discard('gbb')                       # „non-blowback” ≠ GBB
    if (_SPRING_GUN if gun else _SPRING_PART).search(t) and (not gun or not out - {'co2'}):
        out.add('spring')                        # rugós fegyver: csak ha nincs más hajtás (pl. „VSR-10 GBB” gázos)
    if gun and 'aep' in out:
        out.discard('aeg')
    return [p for p in POWERS if p in out]


# Gránátok altípusa (szűrő a gránát-kategórián belül). Sorrend = a szűrő sorrendje.
GRENADE_TYPES = ['sound', 'bb', 'smoke', 'flash', 'pyro', 'launcher', 'shell', 'part']
_GT_RX = {
    'launcher': re.compile(r'(launcher|gránátvető|granatvet|lanciagranat\w*|granátomet|granatnik|\bm203\b|\bm320\b|\bm79\b|'
                           r'\bgl-?06\b|\bgp-?25\b|\bag-?36\b|milkor|\bm32\b|\brpg\b|\bat-?4\b|rocket)', re.I),
    'shell': re.compile(r'(\b40 ?mm\b.*\b(shells?|cartridges?|rounds?|grenades?|lövedék\w*|patron\w*|nábojnic\w*|granat\w*)|'
                        r'moscart|gas ?shell|cartouche|\bshells? 40)', re.I),
    'smoke': re.compile(r'(smoke|füst|fumogen\w*|\bdym\w*|kouř\w*|rauch)', re.I),
    'flash': re.compile(r'(flash ?bang|flashbang|villanó|záblesk\w*|błysk\w*|\bflash\b)', re.I),
    'sound': re.compile(r'(thunder ?b|sound|sonic|\bhang\w*|dźwięk\w*|zvukov\w*|acoustic|petard)', re.I),
    'bb': re.compile(r'(\bco2\b|\bbbs?\b|kulk\w*|kuličk\w*|impact|tornado|storm 360|\btag-?\d|spring grenade|kimera|bb-?s|szétnyíl\w*|spray)', re.I),
    'pyro': re.compile(r'(\bpyro|\bpiro|pirotechn\w*|pyrotechn\w*|p-?67|tűzijáték)', re.I),
    'part': re.compile(r'(\b(spare|part|parts|o-?rings?|seals?|pins?|adapter|valve|spring|repair|tömítés\w*|zawleczk\w*|skorup\w*|'
                       r'héj\w*|shells? for|plug|nozzle|bearings?)\b|\bfor\b|\bdo\b|\bpro\b|-hoz\b|-hez\b)', re.I),
}


def grenade_types(title: str | None, price: float | None = None) -> list[str]:
    """Gránát-altípusok egy címből (több is lehet: „Thunder B + 12 shells” = hang + alkatrész)."""
    t = title or ''
    out = {k for k, rx in _GT_RX.items() if rx.search(t)}
    if 'part' in out and price and price >= 15000 and out & {'launcher', 'sound', 'bb', 'smoke', 'flash', 'pyro'}:
        out.discard('part')                       # drága tétel: maga a gránát / gránátvető, nem alkatrész
    if 'part' in out and price and price < 8000:
        return ['part']                           # olcsó „… for/do Thunder B”, héj, gyűrű: alkatrész
    if 'launcher' in out and not re.search(r'\b(shells?|cartridges?|rounds?|lövedék\w*|patron\w*)\b', t, re.I):
        out.discard('shell')                      # „40mm Grenade Launcher” ≠ lövedék
    if out & {'launcher', 'shell'}:
        out -= {'bb', 'sound'}                    # a 40 mm-es „BB-s” lövedék nem kézigránát
    return [g for g in GRENADE_TYPES if g in out]
