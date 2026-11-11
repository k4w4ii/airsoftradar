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
import math
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
from urllib.parse import urlsplit
from fetcher import Fetcher
import classify
from filters import is_clothing, specs
from jsonld import ScrapedOffer, extract
from matcher import Catalog, OfferIn, Product, gun_kind_of, match_offer
from names import clean_name

CONFIG = json.loads((Path(__file__).parent / "shops.json").read_text())
STALE_DAYS = 3


def scrape(slug: str, limit: int | None) -> tuple[list[ScrapedOffer], list[dict], int | None]:
    """Visszaad: (ajánlatok, hibák, stale_days). stale_days: hány nap után inaktiválható egy nem látott
    ajánlat; None = ne inaktiváljunk (teszt-limit vagy időkorlát miatt csonka futás).
    Ha több termék van, mint max_products, naponta forgó ablakot tölt le -> N nap alatt mindet."""
    cfg = CONFIG[slug]
    deadline = time.monotonic() + float(os.environ.get("SCRAPE_BUDGET_MIN", 300)) * 60
    errors, out, urls, diag = [], [], [], {}
    for attempt in (1, 2):
        # 2. próba: ha az első csak időtúllépést / hálózati / 5xx hibát kapott (a bolt szervere épp lassú), 2 perc múlva
        # még egyszer, dupla időkorláttal – így egy átmeneti akadás miatt nem lesz piros az egész napi futás
        f = Fetcher(extra_headers=cfg.get("headers"), timeout=cfg.get("timeout", 30) * attempt)
        errors, out, urls, diag = [], [], [], {}
        try:
            if cfg["source"] == "sitemap":
                sm = cfg["sitemap"]
                maps = f.sitemaps(cfg["base_url"]) if sm == "auto" else (list(sm) if isinstance(sm, list) else [sm])
                diag["sitemapek"] = maps[:5]
                urls = list(dict.fromkeys(u for m in maps for u in from_sitemap(f, m, cfg["product_pattern"], limit=60000, diag=diag)))
            else:
                urls, out = from_listing(f, cfg["start_urls"], cfg["product_pattern"], cfg.get("page_tpl"),
                                         cfg.get("max_pages", 50), extract_fn=extract, diag=diag,
                                         page_size=cfg.get("page_size", 24))
            if rw := cfg.get("url_rewrite"):                        # pl. ["/fr/", "/en/"]: angol oldal a francia sitemapből
                urls = list(dict.fromkeys(u.replace(rw[0], rw[1], 1) for u in urls))
        except Exception as e:
            errors.append({"error": f"felderítés hiba: {e!r}"[:300]})
        transient = f.stats and all(k in ("timeout", "neterr") or str(k).startswith("5") for k in f.stats)
        if urls or out or attempt == 2 or not transient:
            break
        print(f"[{slug}] felderítés: csak átmeneti hiba ({dict(f.stats)}), 2 perc múlva újra", file=sys.stderr)
        time.sleep(120)
    # ruházat kiszűrése még letöltés előtt (URL-ben gyakran ott a kategória), + boltonkénti kizáró minta
    excl = re.compile(cfg["exclude_pattern"], re.I) if cfg.get("exclude_pattern") else None
    skip = lambda u: is_clothing(urlsplit(u).path) or (excl is not None and bool(excl.search(u)))
    n_before = len(urls) + len(out)
    urls = [u for u in urls if not skip(u)]
    out = [o for o in out if not skip(o.url) and not is_clothing(o.title)]
    diag["kiszurve"] = n_before - len(urls) - len(out)
    if not urls and not out:   # semmit nem talált: diagnosztika az allapot.sql-hez
        errors.insert(0, {"error": "0 termék – blokkolás vagy rossz URL-minta?", "http": dict(f.stats), **diag})
    cap = min(limit or 10**9, cfg.get("max_products", 6000))
    stale_days = None if limit else STALE_DAYS
    if limit is None and len(urls) > cap:
        total = len(urls)
        start = (date.today().toordinal() * cap) % total
        urls = (urls + urls)[start:start + cap]
        stale_days = STALE_DAYS + math.ceil(total / cap)
    out = out[:cap]
    urls = urls[:cap]
    print(f"[{slug}] {len(out)} ajánlat kategóriaoldalról, {len(urls)} termék URL, http: {dict(f.stats)}", file=sys.stderr)
    for i, u in enumerate(urls):
        if time.monotonic() > deadline:
            errors.append({"error": f"időkorlát: {i}/{len(urls)} URL után leállt"})
            stale_days = None
            break
        try:
            page = f.get(u)
            found = extract(page, u) if page else []
            if not found:
                errors.append({"url": u, "error": "no product data" if page else f"letöltés sikertelen ({dict(f.stats)})"})
            out += [o for o in found if not is_clothing(o.title)]
        except Exception as e:  # egy hibás oldal ne állítsa le a futást
            errors.append({"url": u, "error": repr(e)[:200]})
    return out, errors, stale_days


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
    try:                                   # a weboldal kategóriája: fegyver vagy nem (új adatbázisban még üres)
        for r in db.select("product_summary", select="id,category"):
            cat.gun_of[r["id"]] = gun_kind_of(r["category"])
    except (KeyError, RuntimeError):
        pass
    return cat, name_lang


def create_product(db, cat: Catalog, np: dict, lang: str, image: str | None) -> int:
    mid, code = np["manufacturer_id"], np["model_code_norm"]          # code None: cím alapú termék
    raw_name = np["name"]
    np = {**np, "name": clean_name(raw_name, cat.manufacturers[mid][1], set(cat.aliases))}
    slug, pid = slugify(np["name"], f"{mid}:{code or raw_name.lower()}"), None
    fast = hasattr(db, "execute")                  # D1: a termék és a kódjai egy kérésben (egy tranzakció)
    for attempt in range(4):
        try:
            row = {"manufacturer_id": mid, "model_code": code, "model_code_norm": code, "name": np["name"],
                   "slug": slug, "name_lang": lang, "image_url": image}
            if fast:
                pid = _insert_product_d1(db, row, np)
                cat.add_product(Product(pid, mid, np["name"], code), np.get("alt_codes", []),
                                [np["ean"]] if np.get("ean") else [])
                return pid
            pid = db.insert("products", [row])[0]["id"]
            break
        except RuntimeError as e:
            if "23505" not in str(e):
                raise
            # 1) párhuzamos futás már létrehozta ugyanezt a kódot -> azt használjuk
            if code is not None:
                found = db.select("products", select="id", manufacturer_id=f"eq.{mid}", model_code_norm=f"eq.{code}")
                if found:
                    pid = found[0]["id"]
                    break
            elif "slug" in str(e):
                found = db.select("products", select="id,model_code_norm", slug=f"eq.{slug}")
                if found and found[0]["model_code_norm"] is None and \
                        cat.products.get(found[0]["id"]) and cat.products[found[0]["id"]].name == np["name"]:
                    pid = found[0]["id"]          # ugyanaz a cím alapú termék
                    break
            # 2) a webcím foglalt (pl. egy régi, kódját elengedett termék) -> egyedi webcím
            slug = slugify(np["name"], f"{mid}:{code or raw_name.lower()}:{attempt + 1}")
    if pid is None:
        raise RuntimeError(f"nem sikerült terméket létrehozni: {np['name']}")
    codes = [{"product_id": pid, "code_type": "model", "code_norm": c, "manufacturer_id": mid}
             for c in [code, *np.get("alt_codes", [])] if c]
    if np.get("ean"):
        codes.append({"product_id": pid, "code_type": "ean", "code_norm": np["ean"], "manufacturer_id": None})
    for row in codes:
        try:
            db.insert("product_codes", [row])
        except RuntimeError:
            pass                       # már létező kód: nem gond
    cat.add_product(Product(pid, mid, np["name"], code), np.get("alt_codes", []), [np["ean"]] if np.get("ean") else [])
    return pid


def _insert_product_d1(db, row: dict, np: dict) -> int:
    """D1: products + product_codes egy kötegben. Ütköző kód: kihagyva (INSERT OR IGNORE); foglalt webcím: hiba (23505)."""
    cols = list(row)
    stmts = [(f"INSERT INTO products ({','.join(cols)}) VALUES ({','.join('?' * len(cols))}) RETURNING id",
              [row[c] for c in cols])]
    mid = row["manufacturer_id"]
    for c in [row["model_code_norm"], *np.get("alt_codes", [])]:
        if c:
            stmts.append(("INSERT OR IGNORE INTO product_codes (product_id, code_type, code_norm, manufacturer_id) "
                          "SELECT max(id), 'model', ?, ? FROM products WHERE slug = ?", [c, mid, row["slug"]]))
    if np.get("ean"):
        stmts.append(("INSERT OR IGNORE INTO product_codes (product_id, code_type, code_norm, manufacturer_id) "
                      "SELECT max(id), 'ean', ?, NULL FROM products WHERE slug = ?", [np["ean"], row["slug"]]))
    try:
        return db.execute(stmts)[0][0]["id"]
    except RuntimeError as e:
        if "UNIQUE constraint failed" in str(e):
            raise RuntimeError(f"23505 duplicate key ({e}) slug") from None
        raise


OFFER_COLS = "id,shop_id,title_raw,brand_raw,sku_raw,ean_raw,price,currency,image_url,product_id,match_status"


def match_offers(db, cat: Catalog, offers: list[dict], rates: dict, lang_of, offer_pid: dict) -> dict:
    """Pending ajánlatok párosítása (a run_shop és a rematch is ezt használja). offer_pid-be írja az eredményt."""
    stats, batch = defaultdict(int), defaultdict(list)     # azonos frissítések csoportosítva (1 kérés / 200 ajánlat)

    d1 = hasattr(db, "execute")

    def flush(force: bool = False) -> None:
        if d1:                                                # D1: kötegelt UPDATE-ek (100 utasítás / kérés)
            if not force and sum(map(len, batch.values())) < 100:
                return
            stmts = []
            for key, ids in batch.items():
                cols, vals = [k for k, _ in key], [v for _, v in key]
                for i in range(0, len(ids), 80):
                    chunk = ids[i:i + 80]
                    stmts.append((f"UPDATE offers SET {','.join(c + '=?' for c in cols)} WHERE id IN ({','.join('?' * len(chunk))})",
                                  vals + chunk))
            try:
                db.execute(stmts)
            except Exception as e:
                stats["hiba"] += sum(map(len, batch.values()))
                print(f"[match] frissítési hiba: {e}", file=sys.stderr)
            batch.clear()
            return
        for key in list(batch):
            ids = batch[key]
            while ids and (force or len(ids) >= 200):
                chunk, ids[:] = ids[:200], ids[200:]
                try:
                    db.update("offers", dict(key), id=f"in.({','.join(map(str, chunk))})")
                except Exception as e:
                    stats["hiba"] += len(chunk)
                    print(f"[match] frissítési hiba: {e}", file=sys.stderr)
            if not ids:
                del batch[key]

    for i, o in enumerate(offers, 1):
        try:
            _match_one(db, cat, o, rates, lang_of, offer_pid, stats, batch)
        except Exception as e:             # egy hibás ajánlat ne állítsa le az egészet
            stats["hiba"] += 1
            if stats["hiba"] <= 10:
                print(f"[match] ajánlat {o.get('id')}: {e}", file=sys.stderr)
        flush()
        if i % 2000 == 0:
            print(f"[match] {i}/{len(offers)}", flush=True)
    flush(force=True)
    return stats


def _match_one(db, cat: Catalog, o: dict, rates: dict, lang_of, offer_pid: dict, stats, batch) -> None:
    rate = rates.get(o["currency"])
    huf = float(Decimal(str(o["price"])) * rate) if rate and o.get("price") is not None else None
    r = match_offer(OfferIn(o["title_raw"], o["brand_raw"], o["sku_raw"], o["ean_raw"], huf), cat)
    stats[r.method or r.status] += 1
    if r.status == "auto":
        pid = r.product_id or create_product(db, cat, r.new_product, lang_of(o), o["image_url"])
        offer_pid[o["id"]] = pid
        cat.learn(pid, specs(o["title_raw"]))
        batch[(("product_id", pid), ("match_status", "auto"), ("match_method", r.method),
               ("match_confidence", round(r.confidence, 2)))].append(o["id"])
    elif r.status == "review":
        batch[(("match_status", "review"), ("match_method", r.method),
               ("match_confidence", round(r.confidence, 2)))].append(o["id"])
        db.upsert("match_candidates", [{"offer_id": o["id"], "product_id": pid, "score": sc,
                                        "reasons": {"method": "fuzzy"}} for pid, sc in r.candidates[:3]],
                  on_conflict="offer_id,product_id", returning=False)


def run(slug: str, limit: int | None, dry: bool) -> None:
    if not CONFIG[slug].get("enabled", True):
        print(f"[{slug}] kihagyva (enabled=false): {CONFIG[slug].get('note', '')}")
        return
    scraped, errors, stale_days = scrape(slug, limit)
    if dry:
        for s in scraped:
            print(json.dumps(s.__dict__, default=str, ensure_ascii=False))
        print(f"[{slug}] {len(scraped)} ajánlat, {len(errors)} hiba", file=sys.stderr)
        return

    from db import get_db
    db = get_db()
    shop = db.select("shops", select="*", slug=f"eq.{slug}")[0]
    run_id = db.insert("scrape_runs", [{"shop_id": shop["id"]}])[0]["id"]
    rates = {r["currency"]: Decimal(str(r["huf_per_unit"])) for r in db.select("latest_rates", select="*")}
    rates["HUF"] = Decimal(1)
    now = datetime.now(timezone.utc).isoformat()

    shop_tail = re.compile(rf"\s*[-–|:]\s*{re.escape(shop.get('name') or slug)}(\.\w+)?\s*$", re.I)
    rows = [{
        "shop_id": shop["id"], "external_id": s.external_id, "url": s.url, "title_raw": shop_tail.sub("", s.title) or s.title,
        "brand_raw": s.brand, "sku_raw": " ".join(dict.fromkeys(filter(None, [s.mpn, s.sku]))) or None, "ean_raw": s.ean,
        "image_url": s.image, "price": str(s.price), "currency": s.currency or shop["currency"],
        "stock": s.stock, "is_active": True, "last_seen_at": now} for s in scraped]
    rows = list({r["external_id"]: r for r in rows}.values())   # egy batch-ben nem lehet duplikált kulcs
    saved = db.upsert("offers", rows, on_conflict="shop_id,external_id")

    # --- párosítás (csak 'pending'; manual/review/auto érintetlen) ---
    # A korábban leválasztott (pending) ajánlatokat is újrapárosítjuk, nem csak a mostani futásét.
    cat, name_lang = load_catalog(db)
    seen = {o["id"] for o in saved}
    older = [o for o in db.select("offers", select=OFFER_COLS, shop_id=f"eq.{shop['id']}",
                                  match_status="eq.pending", is_active="eq.true") if o["id"] not in seen]
    offer_pid = {o["id"]: o["product_id"] for o in saved if o.get("product_id")}
    stats = match_offers(db, cat, [o for o in saved if o["match_status"] == "pending"] + older,
                         rates, lambda o: shop["lang"], offer_pid)

    # --- egységes terméknevek: angol bolt címe előnyben, egyébként a meglévő név tisztítása (idempotens) ---
    titles = {o["id"]: o["title_raw"] for o in saved + older}
    alias_set, renamed = set(cat.aliases), 0
    for oid, pid in offer_pid.items():
        prod = cat.products.get(pid)
        if prod is None or getattr(prod, "_renamed", False):
            continue
        brand = cat.manufacturers[prod.manufacturer_id][1]
        from_en = shop["lang"] == "en" and name_lang.get(pid, "en") != "en"
        new = clean_name(titles[oid] if from_en else prod.name, brand, alias_set)
        if new != prod.name or from_en:
            db.update("products", {"name": new, **({"name_lang": "en"} if from_en else {})}, id=f"eq.{pid}")
            prod.name, renamed = new, renamed + 1
            if from_en:
                name_lang[pid] = "en"
        prod._renamed = True
    stats["átnevezve"] = renamed

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
    if stale_days:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=stale_days)).isoformat()
        db.update("offers", {"is_active": False}, shop_id=f"eq.{shop['id']}", last_seen_at=f"lt.{cutoff}")

    status = "ok" if stale_days and not errors else ("partial" if scraped else "failed")
    db.update("scrape_runs", {"finished_at": datetime.now(timezone.utc).isoformat(), "status": status,
                              "offers_seen": len(saved), "offers_new": stats.get("new", 0),
                              "errors": errors[:50]}, id=f"eq.{run_id}")
    db.update("shops", {"last_scraped_at": now}, id=f"eq.{shop['id']}")
    # a weboldal (product_summary) a napi futás végén frissül: rematch.py -> summary.rebuild
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
        from db import get_db
        db = get_db()
        import summary
        summary.rebuild(db)
        print("product_summary frissítve")
    elif a.shop:
        run(a.shop, a.limit, a.dry_run)
    else:
        ap.error("adj meg boltot vagy --refresh-et")
