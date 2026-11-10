"""
Gyors újrapárosítás letöltés nélkül (percek): minden 'pending' ajánlat újrapárosítása az aktuális szabályokkal,
majd a terméknevek egységesítése (fordítás, tisztítás) és a weboldal frissítése.
Előtte: jellemző-audit (egy terméken belül 0.20g és 0.28g BB, 500 és 1000 ml gáz stb. szétválasztása).
A napi futás végén automatikusan lefut; kézzel egy takarító SQL után érdemes.
Futtatás: GitHub → Actions → rematch → Run workflow   (vagy helyben: python scraper/rematch.py)
"""
from __future__ import annotations

import sys
from decimal import Decimal

from collections import Counter, defaultdict

import classify
from filters import is_part, is_variant, specs
from matcher import gun_kind_of
from names import clean_name
from run_shop import OFFER_COLS, load_catalog, match_offers


def audit_specs(db, cat) -> int:
    """Egy terméken belül eltérő jellemzőjű ajánlatok (0.20g és 0.28g BB, 500 és 1000 ml gáz...) szétválasztása.
    A termék neve szerinti értéket (ha nincs, a leggyakoribbat) tartjuk meg; a többi ajánlat leválik és újrapárosul."""
    rows = db.select("offers", select="id,product_id,title_raw", match_status="eq.auto", is_active="eq.true",
                     product_id="not.is.null")
    by_product = defaultdict(list)
    for r in rows:
        by_product[r["product_id"]].append((r["id"], specs(r["title_raw"])))
    detach = []
    for pid, offers in by_product.items():
        keep = dict(cat.specs.get(pid, {}))
        for key in {k for _, sp in offers for k in sp}:
            if key not in keep:
                vals = Counter(sp[key] for _, sp in offers if key in sp)
                keep[key] = sorted(vals.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
        bad = [oid for oid, sp in offers if any(k in keep and keep[k] != v for k, v in sp.items())]
        if bad:
            detach += bad
            cat.specs[pid] = keep          # az újrapárosításnál már ne kerüljenek vissza
    for i in range(0, len(detach), 200):
        db.update("offers", {"product_id": None, "match_status": "pending", "match_method": None,
                             "match_confidence": None}, id=f"in.({','.join(map(str, detach[i:i + 200]))})")
    return len(detach)


def audit_kinds(db, cat, rates) -> int:
    """Rossz helyre került ajánlatok leválasztása:
    - alkatrész / tartozék egy fegyver alatt (pl. „Šroub pažbičky M4” a CYMA M4 mellett) vagy fegyver egy alkatrész alatt;
    - egyedi / tuningolt / HPA / használt változat a gyári termék alatt, vagy fordítva.
    Csak határozott jel alapján (a besoroló 'other' eredménye nem dönt). A leválasztott ajánlat utána újrapárosul,
    a matcher pedig már nem engedi vissza ugyanoda (same_kind)."""
    rows = db.select("offers", select="id,product_id,title_raw,price,currency,match_status", is_active="eq.1",
                     product_id="not.is.null")
    detach = []
    for r in rows:
        pid = r["product_id"]
        if r["match_status"] == "manual" or pid not in cat.products:
            continue
        rate = rates.get(r["currency"] or "HUF")
        huf = float(Decimal(str(r["price"])) * rate) if rate and r["price"] is not None else None
        okind = gun_kind_of(classify.category(r["title_raw"], None, huf))
        pkind = cat.gun_kind(pid)
        wrong_kind = okind is not None and pkind is not None and okind != pkind
        wrong_variant = is_variant(r["title_raw"]) != (pid in cat.variant_ids)
        wrong_part = pkind is True and is_part(r["title_raw"], huf)
        if wrong_kind or wrong_variant or wrong_part:
            detach.append(r["id"])
    for i in range(0, len(detach), 200):
        db.update("offers", {"product_id": None, "match_status": "pending", "match_method": None,
                             "match_confidence": None}, id=f"in.({','.join(map(str, detach[i:i + 200]))})")
    return len(detach)


def main() -> None:
    from db import get_db
    db = get_db()
    rates = {r["currency"]: Decimal(str(r["huf_per_unit"])) for r in db.select("latest_rates", select="*")}
    rates["HUF"] = Decimal(1)
    lang = {s["id"]: s["lang"] for s in db.select("shops", select="id,lang")}

    cat, _ = load_catalog(db)
    n = audit_specs(db, cat)
    print(f"[rematch] eltérő jellemző miatt leválasztva: {n}", flush=True)
    n = audit_kinds(db, cat, rates)
    print(f"[rematch] rossz helyen lévő ajánlat (alkatrész a fegyver alatt, custom a gyári alatt stb.) leválasztva: {n}", flush=True)
    pending = db.select("offers", select=OFFER_COLS, match_status="eq.pending", is_active="eq.true")
    print(f"[rematch] {len(pending)} párosításra váró ajánlat", flush=True)
    stats = match_offers(db, cat, pending, rates, lambda o: lang.get(o["shop_id"], "en"), {})
    print(f"[rematch] párosítás: {dict(stats)}", flush=True)

    # terméknevek egységesítése (idempotens: csak a ténylegesen változókat írja)
    aliases, renamed = set(cat.aliases), 0
    print(f"[rematch] terméknevek egységesítése ({len(cat.products)} termék)...", flush=True)
    for pid, prod in cat.products.items():
        new = clean_name(prod.name, cat.manufacturers[prod.manufacturer_id][1], aliases)
        if new != prod.name:
            db.update("products", {"name": new}, id=f"eq.{pid}")
            renamed += 1
            if renamed % 500 == 0:
                print(f"[rematch] átnevezve eddig: {renamed}", flush=True)
    print(f"[rematch] átnevezve: {renamed}", flush=True)

    import summary                      # az összesítő tábla (product_summary) újraépítése
    summary.rebuild(db)
    print("[rematch] kész, a weboldal frissítve", flush=True)


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as e:
        print(f"[rematch] hiba: {e}", file=sys.stderr)
        sys.exit(1)
