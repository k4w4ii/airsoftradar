"""
Ismeretlen márkák listája: a 'pending' (gyártó nélkül maradt) aktív ajánlatok márkánként csoportosítva.
Actions → brands → Run workflow. Eredmény: a futás Summary oldalán táblázat + letölthető ismeretlen_markak.csv.
A márka: a bolt brand mezője, ha van, különben a cím első szava (a legtöbb bolt így írja a címet).
"""
from __future__ import annotations

import csv
import os
import re
import sys
from collections import Counter, defaultdict

from matcher import norm_alias

TOP = 250
# a cím elején gyakori, nem márka szavak
NOISE = {"airsoft", "replika", "replica", "aeg", "gbb", "set", "sada", "zestaw", "kit", "the", "new", "nowy", "nova",
         "uj", "used", "custom", "upgrade", "pack", "bundle", "mag", "magazine", "tar", "zasobnik", "magazynek", "bb",
         "bbs", "kulicky", "gas", "green", "black", "tan", "od", "olive", "for", "pro", "x", "1", "2"}


def brand_key(brand_raw: str | None, title: str) -> tuple[str, str]:
    if brand_raw and norm_alias(brand_raw) and norm_alias(brand_raw) not in NOISE:
        return norm_alias(brand_raw), brand_raw.strip()
    for tok in re.findall(r"[\w&.\-]+", title or ""):
        k = norm_alias(tok)
        if k and k not in NOISE and not k.isdigit():
            return k, tok.strip(".-")
    return "", ""


def collect(offers: list[dict], shop_names: dict[int, str]) -> list[dict]:
    groups: dict[str, dict] = defaultdict(lambda: {"n": 0, "shops": set(), "names": Counter(), "minta": [], "brand_mezo": 0})
    for o in offers:
        key, disp = brand_key(o.get("brand_raw"), o.get("title_raw") or "")
        if not key:
            continue
        g = groups[key]
        g["n"] += 1
        g["shops"].add(shop_names.get(o["shop_id"], str(o["shop_id"])))
        g["names"][disp] += 1
        g["brand_mezo"] += 1 if o.get("brand_raw") else 0
        if len(g["minta"]) < 3 and o.get("title_raw") not in g["minta"]:
            g["minta"].append(o["title_raw"])
    rows = [{"kulcs": k, "marka": g["names"].most_common(1)[0][0], "ajanlat": g["n"], "boltok": len(g["shops"]),
             "boltnevek": ", ".join(sorted(g["shops"])), "brand_mezobol": g["brand_mezo"], "minta": " | ".join(g["minta"])}
            for k, g in groups.items()]
    rows.sort(key=lambda r: (-r["ajanlat"], r["kulcs"]))
    return rows


def main() -> int:
    from db import get_db
    db = get_db()
    shops = {s["id"]: s["slug"] for s in db.select("shops", select="id,slug")}
    known = {a["alias_norm"] for a in db.select("manufacturer_aliases", select="alias_norm")}
    offers = db.select("offers", select="id,shop_id,brand_raw,title_raw", match_status="eq.pending", is_active="eq.1")
    rows = [r for r in collect(offers, shops) if r["kulcs"] not in known]
    print(f"{len(offers)} párosítatlan ajánlat, {len(rows)} ismeretlen márka-jelölt", flush=True)

    with open("ismeretlen_markak.csv", "w", newline="", encoding="utf-8-sig") as f:   # utf-8-sig: Excelben is jó
        w = csv.DictWriter(f, fieldnames=list(rows[0]) if rows else ["kulcs"], delimiter=";")
        w.writeheader()
        w.writerows(rows)

    md = [f"## Ismeretlen márkák ({len(offers)} párosítatlan ajánlat)", "",
          "| # | Márka | Ajánlat | Boltok | Minta cím |", "|---|---|---|---|---|"]
    for i, r in enumerate(rows[:TOP], 1):
        md.append(f"| {i} | {r['marka']} | {r['ajanlat']} | {r['boltok']} | {r['minta'].split(' | ')[0][:90].replace('|', '/')} |")
    out = os.environ.get("GITHUB_STEP_SUMMARY")
    if out:
        with open(out, "a", encoding="utf-8") as f:
            f.write("\n".join(md) + "\n")
    for r in rows[:40]:
        print(f"{r['ajanlat']:6}  {r['boltok']:2} bolt  {r['marka']:<25} {r['minta'][:80]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
