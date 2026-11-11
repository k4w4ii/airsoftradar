"""
Minőség-őr: a besorolási hibák automatikus javítása és a maradék gyanús esetek listája.

Minden éjjel (és minden kézi rematch-nél) fut, a summary.rebuild része:
1. Kézi javítások (scraper/javitasok.txt) – ezek mindig nyernek, és megmaradnak (mindörökre).
2. Automatikus javítások – amit a gép biztosan el tud dönteni:
   - fegyver-kategória, de a termék ára a típusra jellemző minimum alatt (pl. 4000 Ft-os „puska” = alkatrész/kiegészítő);
   - fegyver-kategória, de a termék neve alkatrész („Stock for CM.708…”) és az ajánlatok többsége sem fegyver.
3. Ellenőrzésre váró esetek (minoseg.csv + a GitHub-futás összesítője), pl. vegyes ajánlatok egy termék alatt,
   2,5x-es árkülönbség a raktáron lévők között, drága „alkatrész”, idegen nyelvű név.
"""
from __future__ import annotations

import csv
import os
import re
import statistics
from pathlib import Path

import classify
from filters import is_part

FIXES_FILE = Path(__file__).parent / "javitasok.txt"
SITE = "https://www.airsofthunter.com/hu/p/"
_FOREIGN = re.compile(r"[ěščřžůňťďąęłńśźżćàèìòùâêîôûçãõñßøåœ]", re.I)   # æ nem: „Æther” márkanév   # nem magyar ékezetek
EXPENSIVE_PART_HUF = 150_000
# nem termék (ajándékkártya, szerviz, tesztsor): sosem jelenik meg az oldalon
NON_PRODUCT = re.compile(r"gift ?card|ajándékkártya|ajandekkartya|voucher|gutschein|carte cadeau|bon cadeau|buono regalo|"
                         r"karta podarunkowa|dárkový poukaz|teszt termék|riparazione prodotto|repair service", re.I)


def load_fixes(path: Path | None = None) -> dict:
    """javitasok.txt: soronként egy javítás, # = megjegyzés.
         kategoria <termék-slug> = <kategória>     pl.  kategoria acm-patch-0399-dont-run = acc_gear
         elrejt <bolti URL>                        az ajánlat soha többé nem jelenik meg (és nem párosul)"""
    out = {"kategoria": {}, "elrejt": set()}
    path = path or FIXES_FILE
    if not path.exists():
        return out
    for n, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        cmd, _, rest = line.partition(" ")
        if cmd == "kategoria" and "=" in rest:
            slug, cat = (x.strip() for x in rest.split("=", 1))
            if cat not in classify.ALL_CATEGORIES:
                print(f"[minoseg] javitasok.txt {n}. sor: ismeretlen kategória: {cat}", flush=True)
                continue
            out["kategoria"][slug] = cat
        elif cmd == "elrejt" and rest.strip().startswith("http"):
            out["elrejt"].add(rest.strip())
        else:
            print(f"[minoseg] javitasok.txt {n}. sor nem értelmezhető: {raw!r}", flush=True)
    return out


def fix_category(cat: str, product: dict, clean: list[dict], cats: dict[int, str], fixes: dict) -> tuple[str, str | None]:
    """A szavazással kapott kategória végső ellenőrzése. Visszaad: (kategória, javítás oka vagy None)."""
    forced = fixes.get("kategoria", {}).get(product.get("slug"))
    if forced:
        return forced, "kézi javítás"
    if cat not in classify.WEAPONS:
        return cat, None
    mid = statistics.median(o["price_huf"] for o in clean)
    other = [c for c in (cats[o["id"]] for o in clean) if c not in classify.WEAPONS]
    fallback = max(set(other), key=other.count) if other else "other"
    if cat != "grenade" and mid < classify._FLOOR.get(cat, 6000):
        return fallback, f"fegyvernek túl olcsó ({round(mid)} Ft)"
    if is_part(product["name"], mid) and 2 * len(other) >= len(clean):
        return fallback, "a név alkatrész / tartozék"
    return cat, None


def review(rows: dict[int, dict], by_product: dict[int, list[dict]], cats: dict[int, str]) -> list[dict]:
    """Amit a gép nem dönthet el biztosan: lista kézi ellenőrzésre."""
    issues = []
    for pid, r in rows.items():
        offs = by_product.get(pid, [])
        add = lambda kind, detail: issues.append({"tipus": kind, "termek": r["name"], "kategoria": r["category"],
                                                   "reszlet": detail, "link": SITE + r["slug"]})
        grp = classify.group(r["category"])
        gun = classify.is_gun(r["category"])          # csak a fegyver ↔ nem fegyver keveredés számít (az alkatrész/kiegészítő határ nem)
        mixed = [o for o in offs if classify.is_gun(cats.get(o["id"], r["category"])) != gun and not o.get("outlier")]
        if mixed and len(mixed) < len(offs):
            add("vegyes ajánlatok", f"{len(mixed)}/{len(offs)} ajánlat {'nem fegyver' if gun else 'fegyver'}: {mixed[0]['title_raw'][:80]}")
        instock = [o["price_huf"] for o in offs if o["stock"] == "in_stock" and not o.get("outlier")]
        if len(instock) >= 2 and max(instock) > 2.5 * min(instock) and max(instock) >= 20000:   # olcsó tételnél a felár zaj
            add("nagy árkülönbség", f"{min(instock)}–{max(instock)} Ft a raktáron lévők között")
        name = r["name"].lower()
        if (grp in ("parts", "acc") and r["price"] and r["price"] > EXPENSIVE_PART_HUF
                and classify._C["STRONG_W"].search(name) and not classify._C["F"].search(name)):
            add("drága alkatrész/kiegészítő", f"{r['price']} Ft – lehet, hogy fegyver?")
        if _FOREIGN.search(r["name"]):
            add("idegen nyelvű név", r["name"])
    return issues


def report(issues: list[dict], fixed: list[dict], path: str = "minoseg.csv") -> None:
    """minoseg.csv (letölthető a futás oldaláról) + rövid összesítő a GitHub-futás Summary oldalára."""
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["allapot", "tipus", "termek", "kategoria", "reszlet", "link"], delimiter=";")
        w.writeheader()
        for x in fixed:
            w.writerow({"allapot": "javítva", **x})
        for x in issues:
            w.writerow({"allapot": "ellenőrizendő", **x})
    counts: dict[str, int] = {}
    for x in issues:
        counts[x["tipus"]] = counts.get(x["tipus"], 0) + 1
    print(f"[minoseg] automatikusan javítva: {len(fixed)}, ellenőrizendő: {counts or 0}", flush=True)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        lines = ["## Minőség-őr", "", f"Automatikusan javítva: **{len(fixed)}**", "",
                 "| Ellenőrizendő | db |", "|---|---|", *[f"| {k} | {v} |" for k, v in sorted(counts.items())], "",
                 "A teljes lista: a futás oldalán lent, **Artifacts → minoseg** (CSV).", ""]
        for kind in sorted(counts):                      # típusonként 15 példa közvetlenül az összesítőben
            lines += [f"<details><summary>{kind} – példák</summary>", "", "| Termék | Kategória | Részlet |", "|---|---|---|"]
            for x in [i for i in issues if i["tipus"] == kind][:15]:
                cell = lambda v: str(v).replace("|", "/").replace("\n", " ")[:90]
                lines.append(f"| [{cell(x['termek'])}]({x['link']}) | {x['kategoria']} | {cell(x['reszlet'])} |")
            lines += ["", "</details>", ""]
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
