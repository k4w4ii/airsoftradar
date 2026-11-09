"""
Termékpárosítás: bolti ajánlat (offer) -> kanonikus termék (product).

Kulcs: gyártó + normalizált modellkód. Kaszkád:
  1. EAN egyezés                         -> auto (1.00)
  2. gyártó + erős kód egyezés           -> auto (0.97)
  3. gyártó + erős kód, nincs ilyen termék -> ÚJ termék (0.90)
  4. gyártó + gyenge kód egyedi egyezése -> auto (0.85)
  5. gyártón belüli fuzzy cím            -> auto (>=0.92) / review (>=0.75)
  6. egyébként                           -> pending (kézi döntés)
Függőség: csak stdlib.
"""
from __future__ import annotations

import html
import re
import unicodedata
from dataclasses import dataclass, field
from difflib import SequenceMatcher

from filters import is_part, is_variant, spec_conflict, specs

AUTO_FUZZY = 0.92
REVIEW_FUZZY = 0.75

# --- Gyártóspecifikus "erős" kódminták (bővítés = több automatikus párosítás) ---
# (regex, prefix) -> normalizált kód = prefix + regex csoport, szeparátorok nélkül
STRONG_PATTERNS: dict[str, list[tuple[re.Pattern, str]]] = {
    "cyma":        [(re.compile(r"\bCM\s?[.\-]?\s?(\d{3}[A-Z]{0,2})\b", re.I), "CM")],
    "specna-arms": [(re.compile(r"\bSA\s?-?\s?([A-Z]{1,2}\d{2,3}[A-Z]?)\b", re.I), "SA")],
    "ares":        [(re.compile(r"\bAR\s?-?\s?(\d{3}[A-Z]?)\b", re.I), "AR")],
    "double-bell": [(re.compile(r"\bRK\s?-?\s?(\d{2,3}(?:-?[A-Z]{1,2})?)\b", re.I), "RK")],   # RK-01-W != RK-01
    "arsenal":     [(re.compile(r"\bSLR\s?-?\s?(\d{3}[A-Z]*)\b", re.I), "SLR")],
    "gg-armament": [(re.compile(r"\b((?:EGC|EGR|EGM|TGR|TGT|TGM|GGB)(?:-[A-Z0-9]{2,4}){2,5})\b", re.I), "")],
    "jg":          [(re.compile(r"\bJG\s?-?\s?(\d{3,4}[A-Z]?)\b", re.I), "JG")],
    "amoeba":      [(re.compile(r"\bAM\s?-?\s?(\d{3})\b", re.I), "AM")],
    "tokyo-marui": [(re.compile(r"(?<!\d)(4952839\d{6})(?!\d)"), "")],                          # TM JAN kód
}

# Gyenge kód: betű+szám token. Csak meglévő kódokra illeszt, új terméket NEM hoz létre.
_WEAK_TOKEN = re.compile(r"\b(?=[A-Z0-9.\-]*\d)(?=[A-Z0-9.\-]*[A-Z])[A-Z0-9][A-Z0-9.\-]{2,19}\b", re.I)
_UNIT_NOISE = re.compile(r"^\d+([.,]\d+)?(MM|M|CM|FPS|J|W|MAH|V|BB|RDS|G|KG|GR|LBS)$", re.I)
_FAMILY_NOISE = {"M4", "M16", "AK47", "AK74", "MP5", "G36", "M4A1", "AR15", "HK416", "MK4", "GEN2", "GEN3", "M14"}

_TITLE_STOP = {
    "airsoft", "aeg", "replica", "replika", "rifle", "carbine", "puska", "fegyver", "karabely",
    "elektromos", "gun", "the", "and", "with", "es", "black", "fekete", "tan", "olive", "od",
    "version", "verzio", "new", "uj", "sport", "line", "series",
}

_SHORT_ALIAS_MAX = 2  # 'tm', 'we', 'el', 'db', 'gg': címben csak NAGYBETŰS tokenként fogadjuk el
# „&”-es márkák, amelyek & nélkül platformnevet / gyakori rövidítést adnának: a címben csak „A&K”, „S&T” alakban
_AMP_ONLY = {"ak", "st"}


def unescape_all(s: str) -> str:
    """HTML-entitások feloldása akár többszörösen kódolva is (néhány bolt: „G&amp;amp;G”)."""
    for _ in range(3):
        u = html.unescape(s)
        if u == s:
            break
        s = u
    return s


def norm_alias(s: str) -> str:
    s = unicodedata.normalize("NFKD", unescape_all(s)).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", s.lower())


def norm_code(s: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", s.upper())


def ean_valid(d: str) -> bool:
    if not d.isdigit() or len(d) not in (8, 12, 13, 14):
        return False
    body, check = d[:-1], int(d[-1])
    s = sum(int(c) * (3 if i % 2 == 0 else 1) for i, c in enumerate(reversed(body)))
    return (10 - s % 10) % 10 == check


def norm_ean(s: str | None) -> str | None:
    if not s:
        return None
    d = re.sub(r"\D", "", s)
    if not ean_valid(d):
        return None
    return d[-13:].zfill(13) if len(d) != 14 or d[0] == "0" else d


def find_ean(text: str | None) -> str | None:
    """EAN/JAN egy SKU-mezőben elrejtve, pl. Powair6: 'TM-4952839180025'."""
    for m in re.findall(r"(?<!\d)(\d{13}|\d{12}|\d{8})(?!\d)", text or ""):
        if ean_valid(m):
            return m.zfill(13)
    return None


def detect_manufacturer(brand_raw: str | None, title: str, aliases: dict[str, int]) -> int | None:
    """aliases: alias_norm -> manufacturer_id. Előbb a brand mező, aztán a cím 3/2/1 szavas n-gramjai."""
    if brand_raw and (mid := aliases.get(norm_alias(brand_raw))):
        return mid
    tokens = re.findall(r"[\w&]+", unescape_all(title or ""))
    for n in (3, 2, 1):
        for i in range(len(tokens) - n + 1):
            chunk = tokens[i:i + n]
            key = norm_alias("".join(chunk))
            mid = aliases.get(key)
            if not mid:
                continue
            if len(key) <= _SHORT_ALIAS_MAX and not (n == 1 and chunk[0].isupper() or "&" in chunk[0]):
                continue
            if key in _AMP_ONLY and not (n == 1 and "&" in chunk[0]):
                continue
            return mid
    return None


def extract_codes(text: str, manufacturer_slug: str | None) -> tuple[list[str], list[str]]:
    """Visszaad: (erős kódok, gyenge kódok), normalizálva, sorrendtartóan, duplikátum nélkül."""
    strong: list[str] = []
    for rx, prefix in STRONG_PATTERNS.get(manufacturer_slug or "", []):
        for m in rx.finditer(text):
            strong.append(norm_code(prefix + m.group(1)))
    weak = []
    for tok in _WEAK_TOKEN.findall(text):
        c = norm_code(tok)
        if len(c) >= 3 and c not in strong and c not in _FAMILY_NOISE and not _UNIT_NOISE.match(tok):
            weak.append(c)
    return list(dict.fromkeys(strong)), list(dict.fromkeys(weak))


def title_key(title: str, manufacturer_name: str | None) -> str:
    t = norm_alias_spaces(title)
    drop = set(norm_alias_spaces(manufacturer_name or "").split()) | _TITLE_STOP
    return " ".join(sorted(w for w in t.split() if w not in drop))


def norm_alias_spaces(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


# ----------------------------------------------------------------------------
@dataclass
class Product:
    id: int
    manufacturer_id: int
    name: str
    model_code_norm: str | None


@dataclass
class Catalog:
    """A DB-ből egyszer betöltött, memóriában tartott index (pár tízezer terméknél bőven elég)."""
    aliases: dict[str, int]                         # alias_norm -> manufacturer_id
    manufacturers: dict[int, tuple[str, str]]       # id -> (slug, name)
    products: dict[int, Product] = field(default_factory=dict)
    ean_index: dict[str, int] = field(default_factory=dict)              # ean -> product_id
    code_index: dict[tuple[int, str], int] = field(default_factory=dict)  # (mfr, code) -> product_id
    _title_keys: dict[int, list[tuple[int, str]]] = field(default_factory=dict)
    _key_of: dict[int, str] = field(default_factory=dict)                         # product_id -> title key
    _tok_index: dict[tuple[int, str], set[int]] = field(default_factory=dict)     # (mfr, token) -> product_ids
    part_ids: set[int] = field(default_factory=set)                               # alkatrész/kiegészítő termékek
    variant_ids: set[int] = field(default_factory=set)                            # egyedi/átépített (custom, HPA) termékek
    specs: dict[int, dict] = field(default_factory=dict)                          # termékjellemzők (BB-súly, ml, V, M120...)

    def learn(self, pid: int, sp: dict) -> None:
        """A termékhez került ajánlat jellemzőit megjegyezzük (ha a névből hiányoztak), így a következő eltérő nem kerül mellé."""
        known = self.specs.setdefault(pid, {})
        for k, v in sp.items():
            known.setdefault(k, v)

    def fuzzy_candidates(self, mid: int, key: str, top: int = 40) -> list[tuple[int, str]]:
        """Előszűrés: csak a közös szót tartalmazó termékek (a legtöbb közös szóval elöl). Kis gyártónál mind."""
        allp = self._title_keys.get(mid, [])
        if len(allp) <= top:
            return allp
        shared: dict[int, int] = {}
        for tok in set(key.split()):
            ids = self._tok_index.get((mid, tok), ())
            if len(ids) > 400:              # túl gyakori szó (pl. 'm4') nem különböztet meg
                continue
            for pid in ids:
                shared[pid] = shared.get(pid, 0) + 1
        best = sorted(shared, key=lambda p: -shared[p])[:top]
        return [(pid, self._key_of[pid]) for pid in best]

    def add_product(self, p: Product, extra_codes: list[str] = (), eans: list[str] = ()) -> None:
        self.products[p.id] = p
        for c in filter(None, [p.model_code_norm, *extra_codes]):
            self.code_index[(p.manufacturer_id, c)] = p.id
        for e in eans:
            self.ean_index[e] = p.id
        mname = self.manufacturers[p.manufacturer_id][1]
        k = title_key(p.name, mname)
        self._title_keys.setdefault(p.manufacturer_id, []).append((p.id, k))
        self._key_of[p.id] = k
        if is_part(p.name):
            self.part_ids.add(p.id)
        if is_variant(p.name):
            self.variant_ids.add(p.id)
        self.specs[p.id] = specs(p.name)
        for tok in set(k.split()):
            self._tok_index.setdefault((p.manufacturer_id, tok), set()).add(p.id)


@dataclass
class OfferIn:
    title: str
    brand_raw: str | None = None
    sku_raw: str | None = None
    ean_raw: str | None = None
    price_huf: float | None = None    # az alkatrész/fegyver döntéshez (olcsó + alkatrészszó = alkatrész)


@dataclass
class MatchResult:
    status: str                       # 'auto' | 'review' | 'pending'
    method: str | None                # 'ean' | 'code' | 'new' | 'weak_code' | 'fuzzy'
    confidence: float
    product_id: int | None = None
    new_product: dict | None = None   # ha létre kell hozni: {manufacturer_id, model_code_norm, name}
    candidates: list[tuple[int, float]] = field(default_factory=list)
    manufacturer_id: int | None = None


def match_offer(o: OfferIn, cat: Catalog) -> MatchResult:
    # 1. EAN
    ean = norm_ean(o.ean_raw) or find_ean(o.sku_raw)
    if ean and (pid := cat.ean_index.get(ean)):
        return MatchResult("auto", "ean", 1.0, pid)

    mid = detect_manufacturer(o.brand_raw, o.title, cat.aliases)
    if mid is None:
        return MatchResult("pending", None, 0.0)
    slug, mname = cat.manufacturers[mid]

    # Alkatrész/kiegészítő (tár, rugó, akku...): a címben lévő modellkód a FEGYVERÉ, amihez készült,
    # ezért kódra nem párosítjuk (különben a „Magazine for CM.041K” a CM.041K fegyverhez kerülne).
    part = is_part(o.title, o.price_huf)
    text = f"{o.title} {o.sku_raw or ''}"
    strong, weak = ([], []) if part else extract_codes(text, slug)

    # Egyedi/átépített változat (custom, HPA...) csak ugyanilyen termékhez kerülhet.
    variant = is_variant(o.title)
    osp = specs(o.title)              # 0.20g ≠ 0.28g, 500 ml ≠ 1000 ml, M100 ≠ M120: eltérő jellemző = más termék
    same_kind = lambda pid: ((pid in cat.part_ids) == part and (pid in cat.variant_ids) == variant
                             and not spec_conflict(osp, cat.specs.get(pid, {})))

    # 2. erős kód -> meglévő termék
    for c in strong:
        if (pid := cat.code_index.get((mid, c))) and same_kind(pid):
            return MatchResult("auto", "code", 0.97, pid, manufacturer_id=mid)
    # a kód foglalt, de más fajta termék (pl. az alap fegyver) -> nem kódra, hanem cím alapján megy tovább
    if any((mid, c) in cat.code_index for c in strong):
        strong, weak = [], []

    # 3. erős kód, de még nincs termék -> létrehozzuk
    if strong:
        return MatchResult("auto", "new", 0.90, new_product={
            "manufacturer_id": mid, "model_code_norm": strong[0], "name": o.title.strip(),
            "alt_codes": strong[1:], "ean": ean},
            manufacturer_id=mid)

    # 4. gyenge kód csak akkor, ha pontosan EGY termékre illik
    hits = {cat.code_index[(mid, c)] for c in weak if (mid, c) in cat.code_index and same_kind(cat.code_index[(mid, c)])}
    if len(hits) == 1:
        return MatchResult("auto", "weak_code", 0.85, hits.pop(), manufacturer_id=mid)

    # 5. fuzzy a gyártó termékein belül
    key = title_key(o.title, mname)
    scored = sorted(
        ((pid, SequenceMatcher(None, key, pk).ratio()) for pid, pk in cat.fuzzy_candidates(mid, key)
         if same_kind(pid)),          # alkatrész csak alkatrészhez, custom csak customhoz
        key=lambda x: x[1], reverse=True)[:5]
    if scored:
        best_pid, best = scored[0]
        runner_up = scored[1][1] if len(scored) > 1 else 0.0
        if best >= AUTO_FUZZY and best - runner_up >= 0.05:
            return MatchResult("auto", "fuzzy", round(best, 3), best_pid, candidates=scored, manufacturer_id=mid)
        if best >= REVIEW_FUZZY:
            return MatchResult("review", "fuzzy", round(best, 3), None, candidates=scored, manufacturer_id=mid)

    # 6. ismert gyártó, nincs kód és nincs hasonló termék -> új termék cím alapján
    #    (EMG, Krytac, VFC... gyakran nem ad modellkódot; különben láthatatlan maradna)
    if len(key.split()) >= 2:
        return MatchResult("auto", "new_title", 0.6, new_product={
            "manufacturer_id": mid, "model_code_norm": None, "name": o.title.strip(),
            "alt_codes": [], "ean": ean}, candidates=scored, manufacturer_id=mid)
    return MatchResult("pending", None, 0.0, candidates=scored, manufacturer_id=mid)
