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
import hashlib
import json
import os
from datetime import datetime, timezone
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


# --- biztosíték (circuit breaker) -------------------------------------------------------------------------------------------
# Ha VÁLTOZATLAN besoroló kód mellett egy éjjel tömegesen változna a kategória (pl. egy bolt átírta a címeit, vagy hibás
# adat jött), a változás NEM kerül ki: a termékek a régi kategóriájukban maradnak, a health pirosat jelez (e-mail).
# Új kódnál (új besorolási szabályok) a tömeges változás szándékos – azt a „tests” lépés már ellenőrizte.
CODE_FILES = ["classify.py", "filters.py", "facets.py", "quality.py", "summary.py", "dictionary.py", "javitasok.txt"]
MAX_CAT_CHANGES = (300, 0.03)      # legfeljebb 300 termék vagy 3% – amelyik nagyobb
MAX_DELETES = (500, 0.05)


def code_version() -> str:
    h = hashlib.sha1()
    base = Path(__file__).parent
    for name in CODE_FILES + sorted(str(p.relative_to(base)) for p in (base / "dict").glob("*")):
        p = base / name
        if p.exists():
            h.update(name.encode() + p.read_bytes())
    return h.hexdigest()[:16]


def _meta(db, key: str):
    db.execute([("CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT)", [])])
    rows = db.select("meta", select="value", key=f"eq.{key}")
    return rows[0]["value"] if rows else None


def _set_meta(db, key: str, value: str) -> None:
    db.execute([("INSERT INTO meta (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value", [key, value])])


def circuit_breaker(db, rows: dict[int, dict], prev: dict[int, dict]) -> dict:
    """Tömeges kategória-változás / törlés ellen. A rows sorait helyben visszaállítja, ha kell. Visszaad: állapot."""
    ver, force = code_version(), os.environ.get("FORCE_RECLASSIFY") == "1"
    same_code = _meta(db, "classifier_version") == ver
    moved = [pid for pid, r in rows.items() if pid in prev and prev[pid]["category"] != r["category"]]
    gone = [pid for pid in prev if pid not in rows]
    lim_c = max(MAX_CAT_CHANGES[0], int(MAX_CAT_CHANGES[1] * len(prev)))
    lim_d = max(MAX_DELETES[0], int(MAX_DELETES[1] * len(prev)))
    out = {"moved": len(moved), "deleted": len(gone), "blocked_moves": 0, "keep_deleted": False, "code": ver,
           "same_code": same_code}
    if prev and same_code and not force and len(moved) > lim_c:
        for pid in moved:                                  # régi kategória marad (a többi mező frissülhet)
            r = rows[pid]
            r["category"] = prev[pid]["category"]
            r.pop("sig", None)
            r["sig"] = hashlib.sha1(json.dumps(r, sort_keys=True, default=str).encode()).hexdigest()[:16]
        out["blocked_moves"] = len(moved)
        print(f"[minoseg] BIZTOSÍTÉK: {len(moved)} termék kategóriája változott volna kódváltozás nélkül (> {lim_c}) – "
              "a régi kategóriák maradnak. Ha szándékos: Actions → rematch → force", flush=True)
    if prev and not force and len(gone) > lim_d:
        out["keep_deleted"] = True
        print(f"[minoseg] BIZTOSÍTÉK: {len(gone)} termék tűnne el (> {lim_d}) – a törlés elmarad", flush=True)
    if not out["blocked_moves"]:
        _set_meta(db, "classifier_version", ver)
    return out


def save_status(db, issues: list[dict], fixed: list[dict], guard: dict) -> None:
    """A health ellenőrzéshez: mennyi az ellenőrizendő, mennyit javított, megakadt-e a biztosíték."""
    status = {"ts": datetime.now(timezone.utc).isoformat(timespec="seconds"), "review": len(issues), "fixed": len(fixed),
              **{k: guard[k] for k in ("moved", "deleted", "blocked_moves", "keep_deleted")}}
    try:
        _set_meta(db, "quality", json.dumps(status))
    except Exception as e:                                 # pragma: no cover – az állapot mentése ne állítsa meg a frissítést
        print(f"[minoseg] állapot mentése sikertelen: {e}", flush=True)
