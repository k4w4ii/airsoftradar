"""
Egységes terméknév: „<Márka> <modell> [típus] [szín]”.
  'Airsoftová zbraň AK47 Arsenal SLR105' (ASG)        -> 'ASG AK47 Arsenal SLR105'
  'WE GLOCK 18 GEN.3 GREEN GÁZ GBB - FEKETE' (WE)     -> 'WE Glock 18 Gen.3 Green Gas GBB Black'
  'CM.513 Sport Line, GEN-2 - TAN [CYMA]' (CYMA)      -> 'CYMA CM.513 Sport Line GEN-2 Tan'
Idempotens: clean_name(clean_name(x)) == clean_name(x). Csak stdlib.
"""
from __future__ import annotations

import re

from matcher import norm_alias

# Többnyelvű általános szavak (a kategóriát külön mutatjuk, a „replika/airsoft” üres töltelék)
_GENERIC = [
    r"airsoft(?:ov[áéý]|ow[aey]|-?gun|-?rifle)?", r"softair", r"zbra[nň]", r"pu[sš]ka", r"samopal", r"pistole",
    r"repli[ck]a", r"repliky", r"réplique", r"replik", r"elektromos", r"elektrick[áéý]", r"electric",
    r"gázos", r"rugós", r"fegyver(?:ek)?", r"assault\s+rifle", r"rohampuska", r"gépkarabély", r"karabély",
    r"géppisztoly", r"pisztoly", r"sniper\s+rifle", r"mesterlövész(?:\s+puska)?", r"odstřelovací", r"útočná",
    r"karabin\w*", r"pistolet\w*", r"replik\w*", r"pistolet(?:\s+mitrailleur)?", r"fusil(?:\s+d['’]assaut)?", r"sturmgewehr",
    r"gewehr", r"rifle", r"carbine", r"airsoft\s+gun", r"új", r"new",
]
_GENERIC_RX = re.compile(r"(?<![\w-])(?:" + "|".join(_GENERIC) + r")(?![\w-])", re.I)

_WORD_MAP = {  # szín és anyag egységesen angolul
    "fekete": "Black", "black": "Black", "černá": "Black", "cerna": "Black", "noir": "Black", "schwarz": "Black",
    "czarny": "Black", "nero": "Black", "negro": "Black", "bk": "Black",
    "tan": "Tan", "homokszín": "Tan", "homokszínű": "Tan", "písková": "Tan",
    "olive": "OD", "od": "OD", "oliv": "OD", "olívzöld": "OD", "zöld": "Green", "green": "Green",
    "szürke": "Grey", "grey": "Grey", "gray": "Grey", "šedá": "Grey", "šedý": "Grey", "szary": "Grey", "grau": "Grey",
    "gris": "Grey", "barna": "Brown", "brown": "Brown", "hnědá": "Brown", "hnědý": "Brown",
    "černý": "Black", "černé": "Black", "czarna": "Black", "czarne": "Black", "noire": "Black", "nera": "Black", "negra": "Black",
    "pískový": "Tan", "pískové": "Tan", "piaskowy": "Tan", "piaskowa": "Tan", "sand": "Tan", "sabbia": "Tan", "arena": "Tan",
    "coyote": "Coyote", "olivový": "OD", "olivová": "OD", "oliwkowy": "OD", "oliwkowa": "OD", "oliva": "OD",
    "zelený": "Green", "zelená": "Green", "zielony": "Green", "zielona": "Green", "grün": "Green", "verde": "Green",
    "vert": "Green", "celokov": "Full Metal",
    "fém": "Metal", "metal": "Metal", "gáz": "Gas", "gas": "Gas",
    # alkatrész- és tartozéknevek egységesen angolul (cseh, magyar, lengyel, német, francia, olasz, spanyol)
    "zásobník": "Magazine", "zásobníky": "Magazines", "zásobníku": "Magazine", "zasobnik": "Magazine",
    "tár": "Magazine", "tárak": "Magazines", "magazynek": "Magazine", "magazynki": "Magazines",
    "chargeur": "Magazine", "caricatore": "Magazine", "cargador": "Magazine",
    "válec": "Cylinder", "valec": "Cylinder", "válce": "Cylinder", "henger": "Cylinder", "zylinder": "Cylinder",
    "cylindre": "Cylinder", "cilindro": "Cylinder",
    "píst": "Piston", "dugattyú": "Piston", "dugattyu": "Piston", "tłok": "Piston", "kolben": "Piston", "pistone": "Piston",
    "pružina": "Spring", "pružinu": "Spring", "rugó": "Spring", "sprężyna": "Spring", "feder": "Spring",
    "ressort": "Spring", "molla": "Spring", "muelle": "Spring",
    "hlaveň": "Barrel", "lufa": "Barrel", "lauf": "Barrel", "canna": "Barrel",
    "těsnění": "Seal", "tömítés": "Seal", "gumička": "Bucking",
    "ocelový": "Steel", "ocelová": "Steel", "ocelové": "Steel", "acél": "Steel", "stalowy": "Steel", "stalowa": "Steel",
    "nerezový": "Stainless", "nerezová": "Stainless", "nerezové": "Stainless", "rozsdamentes": "Stainless",
    "odlehčený": "Lightweight", "odlehčená": "Lightweight", "könnyített": "Lightweight",
    "hybridní": "Hybrid", "hibrid": "Hybrid", "sada": "Set", "szett": "Set", "készlet": "Set", "zestaw": "Set",
    "nabíječka": "Charger", "töltő": "Charger", "ładowarka": "Charger", "akumulátor": "Battery", "akkumulátor": "Battery",
    "akumulator": "Battery", "baterie": "Battery", "kuličky": "BBs", "golyó": "BBs", "kulki": "BBs",
    "spoušť": "Trigger", "ravasz": "Trigger", "pažba": "Stock", "kolba": "Stock", "předpažbí": "Handguard",
    "előagy": "Handguard", "rukojeť": "Grip", "markolat": "Grip", "chwyt": "Grip", "tlumič": "Suppressor",
    "hangtompító": "Suppressor", "tłumik": "Suppressor", "puškohled": "Scope", "céltávcső": "Scope", "luneta": "Scope",
    "kolimátor": "Red Dot", "pouzdro": "Holster", "taktická": "Tactical", "taktikai": "Tactical",
}
# kisbetűs kötőszavak (kis-nagybetű érzékeny: a „VSR-10 Pro” terméknév marad)
_LOWER_PHRASES = [
    (re.compile(r"(?<![\w])(?:pro|do)\s+(?:pušk\w*|pistol\w*|zbra\w*|repliky|replik\w*|karabin\w*)(?![\w])"), "for"),
    (re.compile(r"(?<![\w])(?:pro|do|per)(?=\s+\S*(?:\d|[A-Z]{2}))"), "for"),
]
# Többnyelvű jelzők -> egységes angol (vagy törlés). Sorrend számít; mind idempotens.
_PHRASES = [
    (r"licencovan[éá]\s+značen[íi]|with\s+licensed\s+markings|licensed\s+markings|s\s+licenc[íi]|oficiáln[íi]\s+licence"
     r"|(?:licencelt|licenszelt|eredeti)\s+jelöl\w*|jelöl[ée]s(?:ek)?kel|jelöléssel"
     r"|licencovan[éáý]|licen[sc]ed|licencja\w*|licencjonowan\w*|licencelt|licenszelt|licenc(?:es|szel)?", ""),
    (r"celokov\w*|teljesen\s+fém\w*|full[- ]metal|all[- ]metal|pełny\s+metal|tout\s+métal|vollmetall", "Full Metal"),
    (r"\bfa\s+(?:markolat|előagy|elem|tus|agy|borítás)\w*|dřev[ěo]\w*|drewn\w*|real\s+wood|wooden|holz\w*|bois", "Wood"),
    (r"\bfém\s+(?:tok|ház|test)\w*|kovov[áéý]\w*|metalow\w*", "Metal"),
    (r"\bna\s+(\d+)\s+ran\b|\b(\d+)\s+(?:ran|kulek|lövetű|lövésre|golyós|billes|colpi)\b", lambda m: f"{m.group(1) or m.group(2)} rounds"),
    (r"(?<![\w])([\w.]*\w)-(?:hoz|hez|höz)(?![\w])", r"for \1"),     # „M24-HEZ” -> „for M24”
    (r"\((?P<x>[^()]{1,24})\)", r" \g<x> "),           # rövid zárójel: tartalom marad, zárójel nem
]
_PHRASES = [(re.compile(rx, re.I), rep) for rx, rep in _PHRASES]

_ACRONYMS = {"AEG", "AEP", "GBB", "GBBR", "NBB", "EBB", "HPA", "SMG", "LMG", "DMR", "CQB", "CQC", "RIS", "RAS",
             "MOSFET", "ETU", "ECU", "FPS", "ASG", "KJW", "VFC", "LCT", "ICS", "APS", "EMG", "KWA", "CYMA", "SRC",
             "WE", "JG", "TM", "PDW", "UMP", "AKM", "AKS", "SVD", "VSS", "OD", "DE", "USP", "MP5", "MP7", "SCAR",
             "HK", "URG-I", "MWS", "ERG", "SA", "CM", "RK", "II", "III", "IV", "MK", "SD", "SBR"}
_SEP_RX = re.compile(r"\s*(?:\s[-–—|/]\s|[,;]\s*|\s[-–—]$)\s*")


def _brand_patterns(brand: str, aliases: set[str]) -> re.Pattern:
    variants = {brand}
    if "&" in brand:
        variants.add(brand.split()[0])                      # 'G&G Armament' -> 'G&G'
    parts = [re.escape(v).replace(r"\ ", r"[\s.\-]*") for v in sorted(variants, key=len, reverse=True) if v]
    return re.compile(r"(?<![\w])(?:" + "|".join(parts) + r")(?![\w])", re.I)


def _strip_bracket_brands(t: str, brand_norm: str, aliases: set[str]) -> str:
    def repl(m):
        inner = norm_alias(m.group(1))
        return " " if (inner and (inner in aliases or inner.startswith(brand_norm) or brand_norm.startswith(inner))) else m.group(0)
    return re.sub(r"[\[(]([^\])]{1,30})[\])]", repl, t)


def _fix_case(words: list[str]) -> list[str]:
    letters = [c for w in words for c in w if c.isalpha()]
    mostly_upper = letters and sum(c.isupper() for c in letters) / len(letters) > 0.7
    out = []
    for w in words:
        key = w.lower().strip(".,")
        if key in _WORD_MAP:
            out.append(_WORD_MAP[key])
        elif mostly_upper and w.isalpha() and len(w) > 4 and w.upper() not in _ACRONYMS:
            out.append(w.capitalize())
        elif mostly_upper and re.fullmatch(r"[A-ZÁÉÍÓÖŐÚÜŰ]{3,}\.\d+", w):   # GEN.3 -> Gen.3
            out.append(w[0] + w[1:].split(".")[0].lower() + "." + w.split(".", 1)[1])
        else:
            out.append(w)
    return out


def clean_name(title: str, brand: str, aliases: set[str] | None = None) -> str:
    """aliases: az összes gyártó-alias (norm_alias formában) – a zárójeles/farok-márkák felismeréséhez."""
    aliases = aliases or set()
    original = re.sub(r"\s+", " ", title or "").strip()
    if not original:
        return brand
    brand_norm = norm_alias(brand)
    t = _strip_bracket_brands(original, brand_norm, aliases | {brand_norm})
    t = _brand_patterns(brand, aliases).sub(" ", t)
    # „ - EMG / APS” típusú farok: csak gyártónevekből álló szakasz eldobása
    segs = [s for s in re.split(r"\s[-–—|]\s", t)]
    def junk(seg: str) -> bool:      # csak gyártónevek, vagy a márka csonkja (Evike: '- EM')
        ws = [norm_alias(w) for w in re.split(r"[\s/&,]+", seg) if w.strip()]
        return bool(ws) and all(w in aliases or (len(w) >= 2 and brand_norm.startswith(w)) for w in ws)
    segs = [s for s in segs if not junk(s)]
    t = " ".join(segs)
    for rx, rep in _LOWER_PHRASES:
        t = rx.sub(rep, t)
    for rx, rep in _PHRASES:
        t = rx.sub(rep, t)
    t = _GENERIC_RX.sub(" ", t)
    t = _SEP_RX.sub(" ", " " + t + " ")
    t = re.sub(r"[\s\-–—|/,:;]+$", "", re.sub(r"^[\s\-–—|/,:;]+", "", t))
    words = [w for w in t.split() if w not in {"-", "–", "—", "|", "/"}]
    words = _fix_case(words)
    words = [w for i, w in enumerate(words) if i == 0 or w.lower() != words[i - 1].lower()]
    while words and words[0].lower() in {"of", "the", "for", "a", "an", "with"}:
        words = words[1:]
    rest = " ".join(words).strip()
    if len(rest) < 2:
        return f"{brand} {original}"[:100]
    if len(brand) <= 4 and re.match(rf"{re.escape(brand)}\d", rest, re.I):   # 'JG1011B' már tartalmazza a márkát
        return rest[:100]
    return f"{brand} {rest}"[:100]
