"""
product_summary újraépítése D1-ben (a Postgres materializált nézet + v_offer_flags + v_offers_clean Python-megfelelője).
A napi futás végén egyszer fut (rematch.py). Csak a ténylegesen változott sorokat írja (D1: a sorírás a költség).

Lépések: árfolyamok -> aktív, párosított ajánlatok -> bolt+URL ismétlődés szűrése -> HUF/EUR ár ->
kiugró árak (>=3 bolt: a medián 40%-a alatt / 250%-a felett; 2 bolt: 2,5x olcsóbb – szinte mindig alkatrész vagy más termék) -> offers.is_outlier ->
kategória a boltok többségi szavazatával (+ a terméknév fél szavazat) -> platformok -> összesítő sor.
"""
from __future__ import annotations

import hashlib
import json
import re
import statistics
from collections import Counter, defaultdict

import classify
from filters import is_variant

STOCK_RANK = {"in_stock": 0, "preorder": 1, "out_of_stock": 2}


def _rates(db) -> dict[str, float]:
    r = {x["currency"].strip(): float(x["huf_per_unit"]) for x in db.select("latest_rates", select="currency,huf_per_unit")}
    r["HUF"] = 1.0
    return r


def compute(shops, mfrs, products, offers, rates) -> tuple[dict[int, dict], set[int]]:
    """Tiszta függvény (teszthez): visszaadja az összesítő sorokat (termék-id -> sor) és a kiugró ajánlatok id-jét."""
    eur = rates.get("EUR")
    country = {s["id"]: s["country"] for s in shops}
    for o in offers:
        rate = rates.get((o["currency"] or "").strip())
        o["price_huf"] = round(float(o["price"]) * rate) if rate else None
        o["price_eur"] = round(o["price_huf"] / eur, 2) if (eur and o["price_huf"] is not None) else None
    # bolt + URL ismétlődés: a legutóbb látott, raktáron lévő, olcsóbb marad
    best = {}
    for o in offers:
        if o["price_huf"] is None:
            continue
        key = (o["shop_id"], o["url"])
        rank = ((o["last_seen_at"] or "")[:10], o["stock"] == "in_stock", -o["price_huf"])
        if key not in best or rank > best[key][0]:
            best[key] = (rank, o)
    by_product = defaultdict(list)
    for _, o in best.values():
        by_product[o["product_id"]].append(o)

    outliers, rows = set(), {}
    for pid, offs in by_product.items():
        p = products.get(pid)
        if not p:
            continue
        prices = [o["price_huf"] for o in offs]
        n, mx, mid = len(prices), max(prices), statistics.median(prices)
        for o in offs:
            if (n >= 3 and (o["price_huf"] < 0.4 * mid or o["price_huf"] > 2.5 * mid)) or (n == 2 and o["price_huf"] * 2.5 < mx):
                outliers.add(o["id"])
        clean = [o for o in offs if o["id"] not in outliers]
        if not clean:
            continue
        mname = mfrs.get(p["manufacturer_id"], "")
        # kategória: boltok többségi szavazata + a terméknév fél szavazat (döntetlennél ábécé szerint, mint az SQL-ben)
        votes = Counter()
        cats = {}
        for o in clean:
            cats[o["id"]] = classify.category(f"{mname} {o['title_raw']}", o["url"], o["price_huf"])
            votes[cats[o["id"]]] += 1
        votes[classify.category(p["name"], None, None)] += 0.5
        cat = sorted(votes.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
        # egyedi / tuningolt / HPA / használt fegyver: külön kategória (a név, vagy az ajánlatok többsége szerint)
        if cat in classify.WEAPONS and cat != "grenade" and (
                is_variant(p["name"]) or 2 * sum(is_variant(o["title_raw"]) for o in clean) > len(clean)):
            cat = classify.custom_of(cat)
        grp = classify.group(cat)
        plats = set(classify.platforms(p["name"]))
        for o in clean:
            if classify.group(cats[o["id"]]) == grp:
                plats.update(classify.platforms(o["title_raw"]))
        instock = [o for o in clean if o["stock"] == "in_stock"]
        best_huf = min((o["price_huf"] for o in instock), default=None)
        min_any = min(o["price_huf"] for o in clean)
        stock = min((o["stock"] for o in clean), key=lambda s: STOCK_RANK.get(s, 3))
        rows[pid] = {
            "id": pid, "slug": p["slug"], "name": p["name"], "model_code": p.get("model_code"), "image_url": p.get("image_url"),
            "manufacturer": mname,
            "search_code": re.sub(r"[^a-z0-9]", "", f"{mname} {p['name']} {p.get('model_code') or ''}".lower()),
            "category": cat, "platforms": ("," + ",".join(sorted(plats)) + ",") if plats else "",
            "best_price_huf": best_huf,
            "best_price_eur": min((o["price_eur"] for o in instock if o["price_eur"] is not None), default=None),
            "max_price_huf": max(o["price_huf"] for o in clean),
            "min_price_any_huf": min_any,
            "min_price_any_eur": min((o["price_eur"] for o in clean if o["price_eur"] is not None), default=None),
            "offer_count": len({o["shop_id"] for o in clean}),
            "in_stock_count": len({o["shop_id"] for o in instock}),
            "shop_countries": "," + ",".join(sorted({(country.get(o["shop_id"]) or "").strip() for o in clean})) + ",",
            "stock": stock if stock in STOCK_RANK else "unknown",
            "updated_at": max(o["last_seen_at"] or "" for o in clean) or None,
            "price": best_huf if best_huf is not None else min_any,
        }
    for r in rows.values():
        r["sig"] = hashlib.sha1(json.dumps(r, sort_keys=True, default=str).encode()).hexdigest()[:16]
    return rows, outliers


def rebuild(db) -> dict:
    """D1: product_summary + offers.is_outlier frissítése (csak a különbségek)."""
    rates = _rates(db)
    shops = db.select("shops", select="id,country")
    mfrs = {m["id"]: m["name"] for m in db.select("manufacturers", select="id,name")}
    products = {p["id"]: p for p in db.select("products", select="id,manufacturer_id,name,slug,model_code,image_url")}
    offers = db.select("offers", select="id,product_id,shop_id,url,title_raw,price,currency,stock,last_seen_at,is_outlier",
                       is_active="eq.1", product_id="not.is.null")
    rows, outliers = compute(shops, mfrs, products, offers, rates)

    # kiugró jelzők: csak a változókat
    now_out = {o["id"] for o in offers if o.get("is_outlier")}
    set_on, set_off = sorted(outliers - now_out), sorted(now_out - outliers)
    for vals, ids in ((1, set_on), (0, set_off)):
        if ids:
            db.update("offers", {"is_outlier": vals}, id=f"in.({','.join(map(str, ids))})")

    # összesítő: törlés + csak a megváltozott sorok írása
    old = {r["id"]: r["sig"] for r in db.select("product_summary", select="id,sig")}
    gone = sorted(set(old) - set(rows))
    changed = [r for pid, r in rows.items() if old.get(pid) != r["sig"]]
    if gone:
        for i in range(0, len(gone), 80):
            db.execute([(f"DELETE FROM product_summary WHERE id IN ({','.join('?' * len(gone[i:i + 80]))})", gone[i:i + 80])])
    if changed:
        db.upsert("product_summary", changed, on_conflict="id", returning=False)
    stats = {"termekek": len(rows), "valtozott": len(changed), "torolve": len(gone), "elteroar": len(outliers)}
    print(f"[summary] {stats}", flush=True)
    return stats
