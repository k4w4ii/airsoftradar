"""
Kézzel összeállított fordító szótár: a bolti címek idegen nyelvű (cseh, lengyel, magyar, olasz, finn, holland, német)
szavai angolul. Forrás: scraper/dict/*.txt („szó=angol”, üres = töltelékszó, törlendő). Ingyenes, nincs külső szolgáltatás.
A szótár a „words” workflow listájából készült (2026-11-10, 4668 szó; a márkanevek, kódok és angol szavak maradnak).
A weboldal ugyanezt használja (web/lib/dictionary.json, a gen_dictionary_json() készíti).
"""
from __future__ import annotations

import json
import re
from pathlib import Path

DIR = Path(__file__).parent / "dict"
WORD = re.compile(r"[^\W\d_]+(?:['’-][^\W\d_]+)*", re.U)
# ezek angolul / márkanévként is előfordulnak („VSR-10 Pro”, „Porta”): csak kisbetűs alakban vagy csupa nagybetűs címben cseréljük
AMBIGUOUS = {"pro", "na", "do", "per", "porta", "pas", "bal", "oko", "lap", "pont", "man", "tok", "más", "fix", "stal",
             "alto", "mira", "ram", "nov", "kol", "kus", "typ", "patron", "mama", "ran", "lampa", "apa", "kule", "sal",
             "z", "s", "ze", "mit"}


_HU_MAP = {"fekete", "homokszín", "homokszínű", "olívzöld", "zöld", "szürke", "barna", "fém", "gáz", "tár", "tárak", "henger",
           "dugattyú", "dugattyu", "rugó", "tömítés", "acél", "rozsdamentes", "könnyített", "hibrid", "szett", "készlet",
           "töltő", "akkumulátor", "golyó", "ravasz", "előagy", "markolat", "hangtompító", "céltávcső", "taktikai"}


def load() -> dict[str, str]:
    out: dict[str, str] = {}
    for f in sorted(DIR.glob("*.txt")):
        for line in f.read_text(encoding="utf-8").splitlines():
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                out[k.strip().lower()] = v.strip()
    return out


def load_hu() -> set[str]:
    f = DIR / "hu_words.lst"
    return {l.strip().lower() for l in f.read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")} if f.exists() else set()


WORDS = load()
HU = load_hu()


_ALL: dict[str, str] | None = None


def all_words() -> dict[str, str]:
    """A szótár + a névtisztító (names._WORD_MAP) szín/anyag szavai (fekete, zásobník, rugó ...)."""
    global _ALL
    if _ALL is None:
        from names import _WORD_MAP                  # késleltetett import: a names is ezt a modult importálja
        _ALL = {**{k: v.lower() for k, v in _WORD_MAP.items() if k != v.lower() and v.upper() != v}, **WORDS}
    return _ALL


def _case(src: str, dst: str, all_caps: bool) -> str:
    if not dst:
        return dst
    if all_caps or (src.isupper() and len(src) > 1):
        return dst.upper()
    if src[:1].isupper():
        return dst[:1].upper() + dst[1:]
    return dst


def _spaced(m: re.Match) -> bool:
    s, a, b = m.string, m.start(), m.end()
    return (a == 0 or s[a - 1].isspace()) and (b == len(s) or s[b].isspace())


def translate(text: str | None, words: dict[str, str] | None = None, keep: set[str] | None = None) -> str | None:
    """A cím idegen szavait angolra cseréli (a kis- és nagybetűs írásmódot megtartva). Ismeretlen szó marad.
    keep: ezeket a szavakat nem bántjuk (a magyar oldalon a magyar szavakat: keep=HU)."""
    if not text:
        return text
    words = all_words() if words is None else words
    keep = keep or set()
    letters = [c for c in text if c.isalpha()]
    all_caps = bool(letters) and sum(c.isupper() for c in letters) / len(letters) > 0.8

    def rep(m: re.Match) -> str:
        w = m.group(0)
        key = w.lower()
        if key not in words or key in keep:
            return w
        if key in AMBIGUOUS and not (w.islower() or all_caps):
            return w
        if key in AMBIGUOUS and len(key) <= 2 and not _spaced(m):            # „z”, „s”: csak önálló szóként (nem „Emperor`s”)
            return w
        return _case(w, words[key], all_caps)

    out = WORD.sub(rep, text)
    out = re.sub(r"\s{2,}", " ", out)
    out = re.sub(r"\s+([,.;:)])", r"\1", out)
    out = re.sub(r"(\(|^)\s+", r"\1", out)
    out = re.sub(r"(\s-\s*)+(?=\s*-)", " ", out)          # üresen maradt „ - - ” elválasztók
    return out.strip(" -–,")


def gen_dictionary_json(path: Path | None = None) -> Path:
    path = path or Path(__file__).parent.parent / "web" / "lib" / "dictionary.json"
    words = all_words()
    hu = HU | _HU_MAP
    path.write_text(json.dumps({"ambiguous": sorted(AMBIGUOUS), "hu": sorted(hu), "words": words}, ensure_ascii=False, sort_keys=True,
                               separators=(",", ":")), encoding="utf-8")
    return path


if __name__ == "__main__":
    print(gen_dictionary_json(), len(WORDS), "szó")
