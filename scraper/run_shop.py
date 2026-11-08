"""
Egy bolt teljes futása: felderítés -> letöltés -> JSON-LD -> offers upsert -> párosítás -> ártörténet.

  python scraper/run_shop.py taiwangun --limit 20 --dry-run   # DB nélkül, csak kiírja
  python scraper/run_shop.py taiwangun                        # éles
  python scraper/run_shop.py --refresh                        # product_summary frissítés
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import time
import sys
import unicodedata
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

from crawl import from_listing, from_sitemap
from fetcher import Fetcher
from jsonld import ScrapedOffer, extract
from matcher import Catalog, OfferIn, Product, match_offer

CONFIG = json.loads((Path(__file__).parent / "shops.json").read_text())
STALE_DAYS = 3


def scrape(slug: str, limit: int | None) -> tuple[list[ScrapedOffer], list[dict], bool]:
    """Visszaad: (ajánlatok, hibák, teljes-e). Nem teljes, ha időkorlát vagy max_products vágta le
    -> ilyenkor nem inaktiválunk (különben a le nem töltött termékek tévesen eltűnnének)."""
    cfg = CONFIG[slug]
    deadline = time.monotonic() + float(os.environ.get("SCRAPE_BUDGET_MIN", 90)) * 60
    f, errors, out = Fetcher(extra_headers=cfg.get("headers")), [], []
    if cfg["source"] == "sitemap":
        maps = f.sitemaps(cfg["base_url"]) if cfg["sitemap"] == "auto" else [cfg["sitemap"]]
        urls = list(dict.fromkeys(u for m in maps for u in from_sitemap(f, m, cfg["product_pattern"])))
    else:
        urls, out = from_listing(f, cfg["start_urls"], cfg["product_pattern"], cfg.get("page_tpl"),
                                 cfg.get("max_pages", 50), extract_fn=extract)
    cap = min(limit or 10**9, cfg.get("max_products", 2000))
    complete = limit is None and len(urls) <= cap
    urls, out = urls[:cap], out[:cap]
    print(f"[{slug}] {len(out)} ajánlat kategóriaoldalról, {len(urls)} termék URL", file=sys.stderr)
    for i, u in enumerate(urls):
        if time.monotonic() > deadline:
            errors.append({"error": f"időkorlát: {i}/{len(urls)} URL után leállt"})
            complete = False
            break
        try:
            page = f.get(u)
            found = extract(page, u) if page else []
            if not found:
                errors.append({"url": u, "error": "no product data"})
            out += found
        except Exception as e:  # egy hibás oldal ne állítsa le a futást
            errors.append({"url": u, "error": repr(e)[:200]})
    return out, errors, complete


def slugify(text: str, key: str) -> str:
    s = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")[:80]
    return f"{s}-{hashlib.sha1(key.encode()).hexdigest()[:6]}"


def load_catalog(db) -> tuple[Catalog, dict[int, str]]:
    mfrs = {m["id"]: (m["slug"], m["name"]) for m in db.select("manufacturers", select="id,slug,name")}
    aliases = {a["alias_norm"]: a["manufacturer_id"] for a in db.select("manufacturer_aliases", select="*")}
    codes = defaultdict(lambda: ([], []))
    for c in db.select("product_codes", select="product_id,code_type,code_norm"):
        codes[c["product_id"]][1 if c["code_type"] == "ean" else 0].append(c["code_norm"])
    cat, name_lang = Catalog(aliases, mfrs), {}
    for p in db.select("products", select="id,manufacturer_id,name,model_code_norm,name_lang"):
        alt, eans = codes[p["id"]]
        cat.add_product(Product(p["id"], p["manufacturer_id"], p["name"], p["model_code_norm"]), alt, eans)
        name_lang[p["id"]] = p["name_lang"]
    return cat, name_lang


def create_product(db, cat: Catalog, np: dict, lang: str, image: str | None) -> int:
    mid, code = np["manufacturer_id"], np["model_code_norm"]
    try:
        pid = db.insert("products", [{
            "manufacturer_id": mid, "model_code": code, "model_code_norm": code, "name": np["name"],
            "slug": slugify(np["name"], f"{mid}:{code}"), "name_lang": lang, "image_url": image}])[0]["id"]
    except RuntimeError as e:          # párhuzamos futás már létrehozta
        if "23505" not in str(e):
            raise
        pid = db.select("products", select="id", manufacturer_id=f"eq.{mid}", model_code_norm=f"eq.{code}")[0]["id"]
    codes = [{"product_id": pid, "code_type": "model", "code_norm": c, "manufacturer_id": mid}
             for c in [code, *np.get("alt_codes", [])]]
    if np.get("ean"):
        codes.append({"product_id": pid, "code_type": "ean", "code_norm": np["ean"], "manufacturer_id": None})
    for row in codes:
        try:
            db.insert("product_codes", [row])
        except RuntimeError:
            pass                       # már létező kód: nem gond
    cat.add_product(Product(pid, mid, np["name"], code), np.get("alt_codes", []), [np["ean"]] if np.get("ean") else [])
    return pid


def run(slug: str, limit: int | None, dry: bool) -> None:
    if not CONFIG[slug].get("enabled", True):
        print(f"[{slug}] kihagyva (enabled=false): {CONFIG[slug].get('note', '')}")
        return
    scraped, errors, complete = scrape(slug, limit)
    if dry:
        for s in scraped:
            print(json.dumps(s.__dict__, default=str, ensure_ascii=False))
        print(f"[{slug}] {len(scraped)} ajánlat, {len(errors)} hiba", file=sys.stderr)
        return

    from db import DB
    db = DB()
    shop = db.select("shops", select="*", slug=f"eq.{slug}")[0]
    run_id = db.insert("scrape_runs", [{"shop_id": shop["id"]}])[0]["id"]
    rates = {r["currency"]: Decimal(str(r["huf_per_unit"])) for r in db.select("latest_rates", select="*")}
    rates["HUF"] = Decimal(1)
    now = datetime.now(timezone.utc).isoformat()

    rows = [{
        "shop_id": shop["id"], "external_id": s.external_id, "url": s.url, "title_raw": s.title,
        "brand_raw": s.brand, "sku_raw": " ".join(dict.fromkeys(filter(None, [s.mpn, s.sku]))) or None, "ean_raw": s.ean,
        "image_url": s.image, "price": str(s.price), "currency": s.currency or shop["currency"],
        "stock": s.stock, "is_active": True, "last_seen_at": now} for s in scraped]
    rows = list({r["external_id"]: r for r in rows}.values())   # egy batch-ben nem lehet duplikált kulcs
    saved = db.upsert("offers", rows, on_conflict="shop_id,external_id")

    # --- párosítás (csak 'pending'; manual/review/auto érintetlen) ---
    cat, name_lang = load_catalog(db)
    stats = defaultdict(int)
    for o in (o for o in saved if o["match_status"] == "pending"):
        r = match_offer(OfferIn(o["title_raw"], o["brand_raw"], o["sku_raw"], o["ean_raw"]), cat)
        stats[r.method or r.status] += 1
        if r.status == "auto":
            pid = r.product_id or create_product(db, cat, r.new_product, shop["lang"], o["image_url"])
            db.update("offers", {"product_id": pid, "match_status": "auto", "match_method": r.method,
                                 "match_confidence": r.confidence}, id=f"eq.{o['id']}")
            if shop["lang"] == "en" and name_lang.get(pid, "en") != "en":   # angol név előnyben
                db.update("products", {"name": o["title_raw"], "name_lang": "en"}, id=f"eq.{pid}")
                name_lang[pid] = "en"
        elif r.status == "review":
            db.update("offers", {"match_status": "review", "match_method": r.method,
                                 "match_confidence": r.confidence}, id=f"eq.{o['id']}")
            db.upsert("match_candidates", [{"offer_id": o["id"], "product_id": pid, "score": sc,
                                            "reasons": {"method": "fuzzy"}} for pid, sc in r.candidates[:3]],
                      on_conflict="offer_id,product_id", returning=False)

    # --- ártörténet (napi 1 pont, HUF + EUR rögzítve) ---
    hist = []
    for o in saved:
        rate = rates.get(o["currency"])
        if rate is None:
            errors.append({"offer": o["id"], "error": f"nincs árfolyam: {o['currency']}"})
            continue
        huf = Decimal(str(o["price"])) * rate
        hist.append({"offer_id": o["id"], "observed_on": date.today().isoformat(), "price": o["price"],
                     "currency": o["currency"], "price_huf": str(huf.quantize(Decimal(1))),
                     "price_eur": str((huf / rates["EUR"]).quantize(Decimal("0.01"))), "stock": o["stock"]})
    db.upsert("price_history", hist, on_conflict="offer_id,observed_on", returning=False)

    # --- eltűnt termékek inaktiválása ---
    if complete:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=STALE_DAYS)).isoformat()
        db.update("offers", {"is_active": False}, shop_id=f"eq.{shop['id']}", last_seen_at=f"lt.{cutoff}")

    status = "ok" if complete and not errors else ("partial" if scraped else "failed")
    db.update("scrape_runs", {"finished_at": datetime.now(timezone.utc).isoformat(), "status": status,
                              "offers_seen": len(saved), "offers_new": stats.get("new", 0),
                              "errors": errors[:50]}, id=f"eq.{run_id}")
    db.update("shops", {"last_scraped_at": now}, id=f"eq.{shop['id']}")
    print(f"[{slug}] {status}: {len(saved)} ajánlat, párosítás: {dict(stats)}, hibák: {len(errors)}")
    if status == "failed":
        sys.exit(1)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("shop", nargs="?", choices=[k for k in CONFIG if not k.startswith("_")])
    ap.add_argument("--limit", type=int)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--refresh", action="store_true", help="product_summary frissítése")
    a = ap.parse_args()
    if a.refresh:
        from db import DB
        DB().rpc("refresh_product_summary")
        print("product_summary frissítve")
    elif a.shop:
        run(a.shop, a.limit, a.dry_run)
    else:
        ap.error("adj meg boltot vagy --refresh-et")
