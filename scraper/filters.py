"""
Mit NEM gyűjtünk: ruházat és lábbeli (az oldal fegyverekre és kiegészítőkre fókuszál).
A védő- és taktikai felszerelés (szemüveg, maszk, kesztyű, mellény, tasak, tok, sisak) marad.
URL-re (letöltés előtt, időt spórol) és címre (letöltés után) is alkalmazzuk. Csak stdlib.
"""
from __future__ import annotations

import re

_CLOTHING = [
    # en
    r"clothing", r"apparel", r"uniforms?", r"trousers", r"pants", r"t-?shirts?", r"shirts?", r"hoodies?", r"sweatshirts?",
    r"jackets?", r"softshell", r"fleece", r"boots", r"shoes", r"footwear", r"sneakers", r"socks", r"beanies?",
    r"baseball[- ]cap", r"boonie", r"underwear", r"combat[- ]shirt", r"bdu", r"acu",
    # hu
    r"ruha\w*", r"ruházat\w*", r"nadrág\w*", r"póló\w*", r"kabát\w*", r"dzseki\w*", r"bakancs\w*", r"cipő\w*",
    r"zokni\w*", r"egyenruha\w*", r"pulóver\w*", r"ing(?:ek)?",
    # pl
    r"odzie[żz]\w*", r"mundur\w*", r"spodnie", r"koszul\w*", r"kurtk\w*", r"buty", r"obuwie", r"bluz\w*", r"czapk\w*",
    # de
    r"bekleidung", r"kleidung", r"hemd\w*", r"jacke\w*", r"stiefel", r"schuhe", r"socken", r"mütze\w*",
    # fr
    r"v[eê]tements?", r"pantalons?", r"chemises?", r"chaussures?", r"rangers", r"casquettes?", r"blousons?",
    # cs / sk
    r"oble[cč]en[ií]", r"kalhoty", r"ko[sš]ile", r"bundy?", r"boty", r"pono[zž]ky", r"[cč]epice", r"uniformy",
    # es / it / nl
    r"ropa", r"camisetas?", r"chaquetas?", r"botas", r"zapatos", r"abbigliamento", r"pantaloni", r"giacca", r"scarpe",
    r"stivali", r"kleding", r"broeken?", r"schoenen", r"laarzen", r"jassen",
]
CLOTHING_RX = re.compile(r"(?<![a-z0-9])(?:" + "|".join(_CLOTHING) + r")(?![a-z0-9])", re.I)


def is_clothing(*texts: str | None) -> bool:
    """URL-ben a kötőjeles/perjeles szavakat is nézi (pl. /uniforms-and-clothing-396.html)."""
    return any(t and CLOTHING_RX.search(t.replace("-", " ").replace("_", " ").replace("/", " ")) for t in texts)


# ---------------------------------------------------------------------------------------------
# Alkatrész / kiegészítő felismerése a címből. A párosító ezzel akadályozza meg, hogy egy tár vagy
# alkatrész („Magazine for CM.041K”) a fegyver modellkódja alapján a fegyverhez kerüljön.
# Szigorú lista: csak egyértelmű szavak (a stock/grip/rail/slide/barrel fegyverneveben is előfordul).
# A kategória-besorolás ugyanezt a logikát követi: classify.py.
_PART = [
    # tárak, töltények
    r"magazines?", r"mags?", r"hi-?caps?", r"mid-?caps?", r"low-?caps?", r"drum ?mags?", r"t[aá]r(?:ak|at|ral)?",
    r"z[aá]sobn[ií]k\w*", r"magazyn\w*", r"chargeurs?", r"magazin(?:e|es)?", r"cargador\w*", r"caricator\w*", r"shells?",
    # akku, töltő
    r"batter(?:y|ies)", r"akku\w*", r"akkumul[aá]tor\w*", r"bateri[ea]\w*", r"akumul[aá]tor\w*", r"batterie\w*",
    r"li-?po", r"li-?ion", r"li-?fe", r"nimh", r"chargers?", r"t[oö]lt[oő]\w*", r"nab[ií]je[cč]k\w*", r"[lł]adowar\w*",
    # optika
    r"scopes?", r"c[eé]lt[aá]vcs[oő]\w*", r"red ?dots?", r"holo(?:graphic)? ?sights?", r"kolim[aá]tor\w*", r"celownik\w*",
    r"zam[eě][rř]ova[cč]\w*", r"magnifiers?", r"optics?",
    # gearbox, belső alkatrészek
    r"gearbox\w*", r"mechabox\w*", r"gear ?sets?", r"gears", r"fogasker[eé]k\w*", r"pistons?", r"piston ?heads?",
    r"dugatty[uú]\w*", r"cylinders?", r"cylinder ?heads?", r"nozzles?", r"tappet\w*", r"spring ?guides?",
    r"rug[oó]vezet[oő]\w*", r"bushings?", r"bearings?", r"anti-?reversal", r"selector ?plates?", r"air ?seal\w*",
    r"o-?rings?", r"(?:main|aeg|upgrade|gearbox|power|valve|nozzle|hammer|recoil|tappet|trigger) ?springs?",
    r"springs? (?:m|sp)\d{2,3}", r"(?:m|sp)\d{2,3} ?springs?", r"rug[oó]", r"pru[zž]in\w*", r"spr[eę][zż]yn\w*",
    # hop-up, belső cső
    r"hop-?up\w*", r"bucking\w*", r"inner ?barrels?", r"bels[oő] ?cs[oő]\w*", r"precision ?barrels?", r"tight ?bore",
    r"r-?hop", r"hop ?chambers?",
    # motor, elektronika
    r"motors?", r"mosfet\w*", r"wiring",
    # cseh / lengyel / német / francia / olasz / spanyol / magyar alkatrésznevek
    r"v[aá]lec\w*", r"v[aá]lce", r"p[ií]st(?:u|y|em)?", r"t[lł]ok\w*", r"kolben", r"zylinder", r"cylindre", r"cilindro",
    r"pistone", r"feder", r"ressort", r"molla", r"muelle", r"t[eě]sn[eě]n[ií]", r"t[oö]m[ií]t[eé]s\w*", r"p[rř]evod\w*",
    r"ozuben\w*", r"spou[sš][tť]\w*", r"ravasz\w*", r"(?:upgrade|tuning) ?(?:set|kit)s?", r"ersatzteil\w*",
    r"n[aá]hradn[ií]", r"alkatr[eé]sz\w*", r"cz[eę][sś]ci", r"hlave[nň]\w*", r"lufa", r"lauf", r"canna",
    r"gumi[cč]k\w*", r"pa[zž]b\w*", r"kolba", r"p[rř]edpa[zž]b\w*", r"el[oő]agy\w*", r"rukoje[tť]\w*", r"chwyt\w*",
    r"t[lł]umik\w*", r"conversion ?kits?", r"konverz\w*", r"pu[sš]kohled\w*", r"luneta", r"nab[ií]je[cč]\w*",
    # védő- és taktikai felszerelés, egyéb
    r"masks?", r"maszk\w*", r"goggles?", r"szem[uü]veg\w*", r"helmets?", r"sisak\w*", r"holsters?", r"pisztolytok\w*",
    r"pouch\w*", r"tasak\w*", r"slings?", r"heveder\w*", r"vests?", r"mell[eé]ny\w*", r"plate ?carriers?",
    r"chest ?rigs?", r"backpacks?", r"h[aá]tizs[aá]k\w*", r"(?:gun|rifle|pistol|hard|soft|transport) ?(?:cases?|bags?)",
    r"fegyvert[aá]sk\w*", r"kufr\w*", r"pouzdr\w*", r"futera[lł]\w*", r"pokrowi\w*",
    r"bbs?", r"\d[.,]\d{2} ?g", r"goly[oó]\w*", r"kuli[cč]k\w*", r"kulki", r"kulek", r"billes", r"kugeln", r"pallini",
    r"green ?gas", r"top ?gas", r"propane", r"co2 ?(?:cartridges?|capsules?|patron\w*|bombi[cč]k\w*|kapsu[lł]\w*)",
    r"g[aá]z ?palack\w*", r"speed ?loaders?", r"bb ?loaders?", r"targets?", r"c[eé]lt[aá]bl\w*", r"chrono\w*",
    r"tracers?", r"suppressors?", r"silencers?", r"hangtomp[ií]t[oó]\w*", r"tlumi[cč]\w*", r"flash ?hiders?",
    r"flashlights?", r"l[aá]mp[aá]\w*", r"bipods?", r"villal[aá]b\w*", r"mounts?", r"cleaning", r"silicone? ?oil",
    r"szilikon\w*", r"grease",
]
PART_RX = re.compile(r"(?<![\w])(?:" + "|".join(_PART) + r")(?![\w])", re.I)
# „vele járó” részek levágása: „M4 AEG with battery and charger”, „Glock 17 + 2 magazines”
BUNDLE_RX = re.compile(r"(?:\s\+|(?<![\w])(?:with|w/|incl\.?|including|included|mit|avec|con|v[cč]etn[eě]|v[cč]\.|plus|[eé]s|w zestawie|z zestawem|set with)(?![\w])).*$", re.I)
# fegyverre utaló szavak (főnév vagy rendszer)
WEAPON_RX = re.compile(r"(?<![\w])(?:aeg|aep|gbbr?|nbb|hpa|ebb|rifles?|carbines?|karab[eé]ly\w*|karabin\w*|puska\w*|pu[sš]k\w*|"
                       r"pistols?|pistole\w*|pistolet\w*|pistola\w*|pisztoly(?!tok)\w*|replica\w*|replik\w*|r[eé]plique\w*|"
                       r"gewehr\w*|fusil\w*|zbra[nň]\w*|shotguns?|s[oö]r[eé]tes|brokovnic\w*|samopal\w*|submachine|smg|lmg|"
                       r"sniper|revolver\w*)(?![\w])", re.I)
# „X-hez”, „for X”: biztosan alkatrész/kiegészítő
FOR_RX = re.compile(r"(?<![\w])(?:for|do|pro|f[uü]r|pour|per|para|compatible|kompatib\w*|\w+(?:hoz|hez|h[oö]z))(?![\w])", re.I)
WEAPON_MIN_HUF = 30000
# „X-hez / for X / pro X” + modellkód vagy platform: a termék valami MÁSHOZ készült -> alkatrész/tartozék,
# akkor is, ha a szót nem ismerjük („Upgrade set pro CYMA M24 CM.702”, „RIS conversion for CM.030”).
_TARGET = r"(?:\S+\s+){0,2}\S*(?:\d|m4|ak|glock|hi-?capa|vsr|mp5|g36|l96|aeg|gbb|pistol\w*|rifle\w*|pu[sš]k\w*|replik\w*|replic\w*|karabin\w*)"
FOR_TARGET_RX = re.compile(r"(?<![\w])(?:for|f[uü]r|pour|para|compatible(?: with)?|kompatib\w*)\s+" + _TARGET, re.I)
LOWER_FOR_RX = re.compile(r"(?<![\w])(?:pro|do|per)\s+" + _TARGET.replace("m4|ak|glock", "[Mm]4|AK|[Gg]lock"))   # kisbetűs cseh/lengyel/olasz „pro/do/per” (a „VSR-10 Pro” terméknév nem az)
HOZ_RX = re.compile(r"\S*(?:\d|m4|ak|glock|vsr|mp5|g36)\S*-(?:hoz|hez|h[oö]z)(?![\w])", re.I)


PIECE_RX = re.compile(r"(?<![\w])(?:stocks?|buttstock|handguard|receiver|body|slides?|frame|outer\s+barrel|rails?|grips?|"
                      r"pažb\w*|kolba|válltámasz|előagy|tok|ház)(?![\w])", re.I)


def made_for_other(title: str) -> bool:
    core = BUNDLE_RX.sub("", title)
    if FOR_TARGET_RX.search(core) or LOWER_FOR_RX.search(core) or HOZ_RX.search(core):
        return True
    # a csomagnak hitt „w/ …” részben is számít a „for CM.708 … Rifles” (Evike: „Stock w/ Cheek Rest for CM.708 …”)
    return bool(FOR_TARGET_RX.search(title) and (PART_RX.search(core) or PIECE_RX.search(core)))


def is_part(title: str | None, price_huf: float | None = None) -> bool:
    """Igaz, ha a cím alkatrészt/kiegészítőt jelöl (nem fegyvert). A csomag-részeket („with battery”) figyelmen kívül hagyja.
    Ha fegyverszó is van és az ár fegyverár (>= 30 000 Ft), fegyvernek tekinti – kivéve „for X / X-hez” alakban."""
    if not title:
        return False
    core = BUNDLE_RX.sub("", title.replace("_", " "))
    if made_for_other(title.replace("_", " ")):
        return True
    m = PART_RX.search(core)
    if not m:
        return False
    if FOR_RX.search(core):
        return True
    if WEAPON_RX.search(core) and price_huf is not None and price_huf >= WEAPON_MIN_HUF:
        return False
    return True


# ---------------------------------------------------------------------------------------------
# Egyedi / átépített változat („Evike Custom CYMA CM048 ... with Wolverine Inferno HPA System”):
# ugyanaz a modellkód, de más termék és más árkategória. Ilyen ajánlat csak ilyen termékhez párosulhat.
VARIANT_RX = re.compile(
    r"(?<![\w])(?:custom|hpa|wolverine|polarstar|inferno|fusion ?engine|jack ?engine|tuned|tuning|upgraded|"
    r"high ?speed ?build|dmr ?build|full ?upgrade|egyedi|tuningolt|felújított|refurbished|used|használt)(?![\w])", re.I)


# nem egyedi változat, csak említés: „HPA ready”, „HPA adapter”, „used by …”, „custom series/fit/logo”, gyári „upgraded version”
VARIANT_NOT_RX = re.compile(
    r"(?<![\w])(?:hpa[\s-]*(?:ready|compatible|kompatibilis|adapt\w*|tank|line|hose|regulator|tömlő|palack)|"
    r"(?:ready|compatible|adapter)\s+(?:for\s+)?hpa|used\s+(?:by|in|with|for)|"
    r"custom\s+(?:series|fit|logo|marking\w*|engraving|colou?r|edition\s+box)|upgraded\s+version|"
    r"tuning\s+(?:kit|parts?|set))(?![\w])", re.I)


def is_variant(title: str | None) -> bool:
    if not title:
        return False
    t = VARIANT_NOT_RX.sub(" ", BUNDLE_RX.sub("", title))
    return bool(VARIANT_RX.search(t))


# ---------------------------------------------------------------------------------------------
# Termékjellemzők a címből (BB-súly, kiszerelés, gázfajta és -térfogat, akku feszültség/kapacitás/csatlakozó,
# rugóerősség, csőhossz/-átmérő, gumikeménység, tárkapacitás, generáció, verzió, fps, csőhossz hüvelykben).
# Ha két cím ugyanabban a jellemzőben eltér (0.20g vs 0.28g), az két külön termék – soha nem párosítjuk össze.
_NUM = r"(\d+(?:[.,]\d+)?)"
_SPEC_RULES = [
    ("bb_g",  re.compile(r"(?<![\d.,])(0[.,]\d{1,2})\s*g(?:r|ram)?(?![a-z])", re.I)),
    ("mass",  re.compile(_NUM + r"\s*(kg|g)(?![a-z])", re.I)),
    ("ml",    re.compile(_NUM + r"\s*ml(?![a-z])", re.I)),
    ("volt",  re.compile(r"(\d{1,2}[.,]\d)\s*v(?![a-z])", re.I)),
    ("mah",   re.compile(r"(\d{3,5})\s*mah", re.I)),
    ("deg",   re.compile(r"(\d{2,3})\s*(?:°|deg|fok)", re.I)),
    ("inner_d", re.compile(r"(?<![\d.,])(6[.,]0\d|6[.,]1\d)(?![\d])(?!\s*(?:v|g|kg|ml|mm))", re.I)),
    ("mm",    re.compile(r"(\d{2,3})\s*mm(?![a-z])", re.I)),
    ("inch",  re.compile(r"(\d{1,2}(?:[.,]\d)?)\s*(?:\"|″|''|inch|in(?![a-z]))", re.I)),
    ("fps",   re.compile(r"(\d{3})\s*fps", re.I)),
    ("gen",   re.compile(r"(?<![a-z])gen(?:eration)?\.?\s*(\d)(?!\d)", re.I)),
    ("mk",    re.compile(r"(?<![a-z])mk\.?\s*-?\s*(iv|i{1,3}|\d{1,2})(?![a-z\d])", re.I)),   # MK-I ≠ MK-II
    ("ver",   re.compile(r"(?<![\w.])v\s?(\d)(?![\d.,]|\s*(?:v|mm))", re.I)),
    ("rounds", re.compile(r"(\d{2,4})\s*(?:rounds?|rds|ran|lövetű|lövés\w*|kulek|kulí\w*|billes|colpi|schuss|bb(?!s?\s*(?:0|bag))s?(?=\s|$|[,)]))", re.I)),
    ("count", re.compile(r"(\d{3,6})\s*(?:pcs|db|ks|szt|bbs|darab|stück|kusů|pieces|kul\w*)(?![a-z])", re.I)),
    ("pack",  re.compile(r"(?:(?<![\w.])(\d{1,2})\s*(?:pcs|db|ks|szt|pack|pk|darab|stück|kusy)(?![a-z])|(?<![\w])x\s?(\d{1,2})(?![\d]))", re.I)),
]
_SPRING_RX = re.compile(r"(?<![a-z0-9])(?:m|sp)\s?(9\d|1\d\d|2\d\d)(?!\d)", re.I)
_SPRING_CTX = re.compile(r"spring|rug[oó]|pru[zž]in|spr[eę][zż]yn|feder|ressort|molla|muelle", re.I)
_GAS_CTX = re.compile(r"(?<![a-z])(gas|gáz|gaz|plyn|propan\w*)(?![a-z])", re.I)
_GAS_TYPE = re.compile(r"(?<![a-z])(green|top|red|black|blue|ultra|white|grey|gray|purple|zöld|zelen\w*|zielon\w*)(?![a-z])", re.I)
_GAS_NORM = {"zöld": "green", "gray": "grey"}
_CONN = re.compile(r"(?<![a-z])(deans|t-?plug|tamiya|mini ?tamiya|xt-?30|xt-?60)(?![a-z])", re.I)
_CAP = re.compile(r"(?<![a-z])(hi|mid|low|real)-?\s?cap(?![a-z])", re.I)
_RATIO = re.compile(r"(?<![\d.])(\d{2}(?:[.,]\d{1,2})?)\s*:\s*1(?!\d)")
_MOTOR_CTX = re.compile(r"(?<![a-z])motor\w*", re.I)
_AXLE = re.compile(r"(?<![a-z])(long|short|medium|mid)\s*(?:type|axle|shaft|tengely\w*)?(?![a-z])", re.I)
_MOTOR_TYPE = re.compile(r"(?<![a-z])(ultra high torque|super high torque|high torque|ultra high speed|super high speed|high speed|balanced?)(?![a-z])", re.I)
_BATT_CTX = re.compile(r"(?<![a-z])(li-?po|li-?ion|li-?fe|nimh|akku\w*|batter\w*|bateri\w*|akumul\w*)(?![a-z])", re.I)
_BATT_FORM = re.compile(r"(?<![a-z])(stick|butterfly|nunchu(?:c)?k|split|buffer ?tube|crane ?stock|mini|large)(?![a-z])", re.I)
_AMMO_CTX = re.compile(r"(?<![a-z])(bbs?|golyó\w*|kuli\w*|kulki|billes|pallini|ammo)(?![a-z])", re.I)


def _num(s: str) -> str:
    v = float(s.replace(",", "."))
    return f"{v:g}"


_SPECNA_CODE = re.compile(r"\bsa-[a-z]{1,2}\d", re.I)
_SPECNA_LINE = re.compile(r"\b(core|flex|edge|prime|vapor|one)\b", re.I)


def specs(title: str | None) -> dict[str, str]:
    """Normalizált jellemzők: {'bb_g': '0.2', 'kg': '1', 'ml': '500', 'gas': 'green', 'spring': 'M120', ...}"""
    if not title:
        return {}
    t = BUNDLE_RX.sub("", title)
    out: dict[str, str] = {}
    import classify                                   # késleltetett import (classify -> dictionary -> names -> filters)
    if pw := classify.powers(t, gun=False):           # AEG ≠ GBB ≠ HPA ≠ rugós: soha nem ugyanaz a termék
        out["power"] = ",".join(pw)
    if _SPECNA_CODE.search(t) and (m := _SPECNA_LINE.search(t)):
        out["line"] = m.group(1).lower()              # Specna: CORE ≠ FLEX ≠ EDGE ≠ PRIME ≠ VAPOR (azonos SA-kód mellett is)
    for key, rx in _SPEC_RULES:
        if key == "mass":          # a „0.25g 1kg” első találata a BB-súly: az első >= 1 g értéket keressük
            for m in rx.finditer(t):
                grams = float(m.group(1).replace(",", ".")) * (1000 if m.group(2).lower() == "kg" else 1)
                if grams >= 1:
                    out.setdefault("mass_g", f"{grams:g}")
                    break
            continue
        m = rx.search(t)
        if m:
            g = next(g for g in m.groups() if g)
            if key == "mk":                                # római szám -> szám (MK-II = MK2)
                g = str({"i": 1, "ii": 2, "iii": 3, "iv": 4}.get(g.lower(), g))
            out.setdefault(key, _num(g))
    if _SPRING_CTX.search(t) and (m := _SPRING_RX.search(t)):
        out["spring"] = m.group(1)
    if _GAS_CTX.search(t) and (m := _GAS_TYPE.search(t)):
        g = m.group(1).lower()
        out["gas"] = _GAS_NORM.get(g, "green" if g.startswith(("zelen", "zielon")) else g)
    if m := _RATIO.search(t):
        out["ratio"] = _num(m.group(1))
    if _MOTOR_CTX.search(t):
        if m := _AXLE.search(t):
            out["axle"] = {"mid": "medium"}.get(m.group(1).lower(), m.group(1).lower())
        if m := _MOTOR_TYPE.search(t):
            out["motor"] = m.group(1).lower().replace("balanced", "balance")
    if _BATT_CTX.search(t) and (m := _BATT_FORM.search(t)):
        out["form"] = re.sub(r"\s", "", m.group(1).lower()).replace("nunchuck", "nunchuk")
    if m := _CONN.search(t):
        out["conn"] = re.sub(r"[\s-]", "", m.group(1).lower())
    if m := _CAP.search(t):
        out["cap"] = m.group(1).lower()
    if "bb_g" in out and _AMMO_CTX.search(t):     # BB-zacskó: bio / nyomjelző / sima – külön termékek
        out["bio"] = "bio" if re.search(r"(?<![a-z])bio", t, re.I) else "no"
        out["tracer"] = "tracer" if re.search(r"tracer|nyomjelz|svíti|fluo", t, re.I) else "no"
    return out


def spec_conflict(a: dict[str, str], b: dict[str, str]) -> bool:
    """Igaz, ha van olyan jellemző, ami mindkettőben szerepel, de eltér.
    „power” (AEG/GBB/HPA…): csak akkor ütközik, ha nincs közös elem („for VSR & GBB” ≈ „for GBB”)."""
    for k, v in a.items():
        if k not in b:
            continue
        if k == "power":
            if not set(v.split(",")) & set(b[k].split(",")):
                return True
        elif b[k] != v:
            return True
    return False
