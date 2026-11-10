"""
Idegen nyelvű szavak listája a teljes adatbázisból (terméknevek + aktív bolti címek), gyakoriság szerint.
Actions → words → Run workflow → letölthető idegen_szavak.csv. Ebből készül a fordító szótár (names.py), ingyen.
Idegennek számít: ékezetes/speciális betűs szó, vagy ami nem angol nyelvű boltok címeiben gyakori,
az angol nyelvű boltokéban viszont alig fordul elő. Kihagyja: márkaneveket, kódokat, a már lefordított szavakat.
"""
from __future__ import annotations

import csv
import os
import re
import sys
import unicodedata
from collections import Counter, defaultdict

from matcher import norm_alias

WORD = re.compile(r"[^\W\d_]+(?:['’-][^\W\d_]+)*", re.U)
SPECIAL = set("łŁøØæÆßœŒđĐ")


def has_accent(w: str) -> bool:
    return any(ch in SPECIAL or (ch.isalpha() and unicodedata.decomposition(ch)) for ch in w)


def collect(titles: list[tuple[str, str]], aliases: set[str], known: set[str]) -> list[dict]:
    """titles: (cím, a bolt nyelve) párok. Visszaad: szavak gyakoriság szerint."""
    total, en, other, langs, sample = Counter(), Counter(), Counter(), defaultdict(Counter), {}
    for title, lang in titles:
        for w in {m.group(0).lower() for m in WORD.finditer(title or "")}:
            if len(w) < 2:
                continue
            total[w] += 1
            (en if lang == "en" else other)[w] += 1
            langs[w][lang] += 1
            sample.setdefault(w, title)
    rows = []
    for w, n in total.items():
        if norm_alias(w) in aliases or w in known:
            continue
        accent = has_accent(w)
        foreign_stat = other[w] >= 2 and en[w] * 10 < other[w]
        if not (accent or foreign_stat):
            continue
        rows.append({"szo": w, "db": n, "nyelv": langs[w].most_common(1)[0][0], "angol_boltban": en[w],
                     "ekezetes": "igen" if accent else "", "pelda": sample[w][:120]})
    rows.sort(key=lambda r: (-r["db"], r["szo"]))
    return rows


def main() -> int:
    from db import get_db
    from names import _WORD_MAP
    db = get_db()
    lang = {s["id"]: (s.get("lang") or "en") for s in db.select("shops", select="id,lang")}
    aliases = {a["alias_norm"] for a in db.select("manufacturer_aliases", select="alias_norm")}
    from dictionary import DIR, all_words
    skip = DIR / "nem_forditando.lst"
    known = {k.lower() for k in _WORD_MAP} | set(all_words())
    known |= {l.strip().lower() for l in skip.read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")}
    titles = [(o["title_raw"], lang.get(o["shop_id"], "en"))
              for o in db.select("offers", select="shop_id,title_raw", is_active="eq.1")]
    titles += [(p["name"], p.get("name_lang") or "en") for p in db.select("products", select="name,name_lang")]
    rows = collect(titles, aliases, known)
    print(f"{len(titles)} cím, {len(rows)} idegen szó-jelölt (ebből {sum(r['db'] >= 2 for r in rows)} legalább kétszer)", flush=True)
    with open("idegen_szavak.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["szo", "db", "nyelv", "angol_boltban", "ekezetes", "pelda"], delimiter=";")
        w.writeheader()
        w.writerows(rows)
    out = os.environ.get("GITHUB_STEP_SUMMARY")
    if out:
        with open(out, "a", encoding="utf-8") as f:
            f.write(f"## Idegen szavak: {len(rows)} (letölthető: idegen-szavak csatolmány)\n\n| Szó | Db | Nyelv | Példa |\n|---|---|---|---|\n")
            for r in rows[:100]:
                f.write(f"| {r['szo']} | {r['db']} | {r['nyelv']} | {r['pelda'][:80].replace('|', '/')} |\n")
    for r in rows[:30]:
        print(f"{r['db']:6}  {r['nyelv']:3} {r['szo']:<22} {r['pelda'][:70]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
