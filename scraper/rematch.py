"""
Gyors újrapárosítás letöltés nélkül (percek): minden 'pending' ajánlat újrapárosítása az aktuális szabályokkal,
majd a terméknevek egységesítése (fordítás, tisztítás) és a weboldal frissítése.
Mikor kell: egy takarító SQL (pl. 0012) után, hogy ne kelljen a következő éjszakai futásra várni.
Futtatás: GitHub → Actions → rematch → Run workflow   (vagy helyben: python scraper/rematch.py)
"""
from __future__ import annotations

import sys
from decimal import Decimal

from names import clean_name
from run_shop import OFFER_COLS, load_catalog, match_offers


def main() -> None:
    from db import DB
    db = DB()
    rates = {r["currency"]: Decimal(str(r["huf_per_unit"])) for r in db.select("latest_rates", select="*")}
    rates["HUF"] = Decimal(1)
    lang = {s["id"]: s["lang"] for s in db.select("shops", select="id,lang")}

    cat, _ = load_catalog(db)
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

    db.rpc("refresh_product_summary")
    print("[rematch] kész, a weboldal frissítve")


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as e:
        print(f"[rematch] hiba: {e}", file=sys.stderr)
        sys.exit(1)
