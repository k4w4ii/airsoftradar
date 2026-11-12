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
import os
import re
import statistics
from collections import Counter, defaultdict

import classify
import facets
import quality
from filters import is_variant

STOCK_RANK = {"in_stock": 0, "preorder": 1, "out_of_stock": 2}


def _rates(db) -> dict[str, float]:
    r = {x["currency"].strip(): float(x["huf_per_unit"]) for x in db.select("latest_rates", select="currency,huf_per_unit")}
    r["HUF"] = 1.0
    return r


def compute(shops, mfrs, products, offers, rates, fixes=None, diag=None) -> tuple[dict[int, dict], set[int]]:
    """Tiszta függvény (teszthez): visszaadja az összesítő sorokat (termék-id -> sor) és a kiugró ajánlatok id-jét.
    fixes: quality.load_fixes() (kézi javítások); diag: ide kerülnek a minőség-őr adatai (javítások, ajánlat-kategóriák)."""
    fixes = fixes or {"kategoria": {}, "elrejt": set()}
    diag = diag if diag is not None else {}
    diag.update(fixed=[], cats={}, by_product={})
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
        if o["url"] not in fixes["elrejt"] and not quality.NON_PRODUCT.search(o["title_raw"] or ""):
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
        cat, why = quality.fix_category(cat, p, clean, cats, fixes)      # minőség-őr: kézi + biztos automatikus javítás
        if why == quality.AI_WHY:
            diag.setdefault("ai", set()).add(pid)
        elif why and why != "kézi javítás":
            diag["fixed"].append({"tipus": why, "termek": p["name"], "kategoria": cat, "reszlet": "",
                                  "link": quality.SITE + p["slug"]})
        diag["cats"].update(cats)
        for o in offs:
            o["outlier"] = o["id"] in outliers
        diag["by_product"][pid] = offs
        # egyedi / tuningolt / HPA / használt fegyver: külön kategória (a név, vagy az ajánlatok többsége szerint)
        if why != "kézi javítás" and cat in classify.WEAPONS and cat != "grenade" and (
                is_variant(p["name"]) or 2 * sum(is_variant(o["title_raw"]) for o in clean) > len(clean)):
            cat = classify.custom_of(cat)
        grp = classify.group(cat)
        gun = classify.is_gun(cat)
        pows = set(classify.powers(p["name"], gun))
        plats = set(classify.platforms(p["name"]))
        for o in clean:
            if classify.group(cats[o["id"]]) == grp:
                plats.update(classify.platforms(o["title_raw"]))
                pows.update(classify.powers(o["title_raw"], gun))
        instock = [o for o in clean if o["stock"] == "in_stock"]
        best_huf = min((o["price_huf"] for o in instock), default=None)
        min_any = min(o["price_huf"] for o in clean)
        stock = min((o["stock"] for o in clean), key=lambda s: STOCK_RANK.get(s, 3))
        rows[pid] = {
            "id": pid, "slug": p["slug"], "name": p["name"], "model_code": p.get("model_code"), "image_url": pick_image(p.get("image_url"), clean),
            "manufacturer": mname,
            "search_code": re.sub(r"[^a-z0-9]", "", f"{mname} {p['name']} {p.get('model_code') or ''}".lower()),
            "category": cat, "platforms": ("," + ",".join(sorted(plats)) + ",") if plats else "",
            "powers": ("," + ",".join(sorted(pows)) + ",") if pows else "",
            "subtypes": _subtypes(cat, p["name"], clean),
            "best_price_huf": best_huf,
            "best_price_eur": min((o["price_eur"] for o in instock if o["price_eur"] is not None), default=None),
            "max_price_huf": max((o["price_huf"] for o in instock), default=None),   # csak raktáron lévők egymás közt
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


_IMG_EXT = re.compile(r"\.(jpe?g|png|webp|gif|avif)(?:$|[?#])", re.I)


def _img_score(u: str | None) -> int:
    """2 = biztosan képcím (kiterjesztés), 1 = lehet (http, nincs szóköz az utolsó részben), 0 = rossz."""
    if not u or not re.match(r"https?://[^/\s]+/", u.strip(), re.I):
        return 0
    if _IMG_EXT.search(u):
        return 2
    last = u.strip().split("?")[0].rstrip("/").rsplit("/", 1)[-1]
    return 0 if (" " in last or "%20" in last) else 1


def pick_image(product_img: str | None, offers: list[dict]) -> str | None:
    """A termék képe; ha rossz (pl. a régi hibás „…/Termék neve” cím), a boltok friss képei közül az első jó.
    Sorrend: termékkép, majd a raktáron lévő ajánlatok, majd a többi."""
    cands = [product_img] + [o.get("image_url") for o in sorted(offers, key=lambda o: o.get("stock") != "in_stock")]
    for want in (2, 1):
        if img := next((c.strip() for c in cands if _img_score(c) >= want), None):
            return img
    return None


def _subtypes(cat: str, name: str, offers: list[dict]) -> str:
    """Kategórián belüli szűrő-értékek (facets.py): „,gt=smoke,”, „,bbw=0.25,bbt=bio,” stb."""
    mid = statistics.median(o["price_huf"] for o in offers)
    vals = set(facets.attributes(cat, name, mid))
    for o in offers:
        vals |= facets.attributes(cat, o["title_raw"], o["price_huf"])
    if cat == "grenade" and "gt=part" in vals and len(vals) > 1 and mid >= 8000:
        vals.discard("gt=part")
    return ("," + ",".join(sorted(vals)) + ",") if vals else ""


def _ensure_powers_column(db) -> None:
    """2026-11-11: új oszlopok (működés- és gránát-szűrő). Magától létrehozza, ha még nincsenek (nem kell kézi SQL)."""
    for col in ("powers", "subtypes"):
        try:
            db.execute([(f"SELECT {col} FROM product_summary LIMIT 1", [])])
        except Exception:
            db.execute([(f"ALTER TABLE product_summary ADD COLUMN {col} TEXT NOT NULL DEFAULT ''", [])])
            print(f"[summary] új oszlop: product_summary.{col}", flush=True)


def rebuild(db) -> dict:
    """D1: product_summary + offers.is_outlier frissítése (csak a különbségek)."""
    rates = _rates(db)
    shops = db.select("shops", select="id,country")
    mfrs = {m["id"]: m["name"] for m in db.select("manufacturers", select="id,name")}
    products = {p["id"]: p for p in db.select("products", select="id,manufacturer_id,name,slug,model_code,image_url")}
    offers = db.select("offers", select="id,product_id,shop_id,url,title_raw,price,currency,stock,last_seen_at,is_outlier,image_url",
                       is_active="eq.1", product_id="not.is.null")
    fixes, diag = quality.load_fixes(), {}
    if os.environ.get("AI_APPLY") == "1":   # alapból KI: az AI csak javasol (ai_javaslatok.csv), az oldalt a szabályok rendezik
        import ai_review
        fixes["ai"] = ai_review.load(db)
    if fixes["elrejt"]:                 # kézzel elrejtett ajánlat: soha ne párosuljon újra (manual = az automatika nem nyúl hozzá)
        hide = [o["id"] for o in offers if o["url"] in fixes["elrejt"]]
        for i in range(0, len(hide), 80):
            db.update("offers", {"product_id": None, "match_status": "manual"}, id=f"in.({','.join(map(str, hide[i:i + 80]))})")
    rows, outliers = compute(shops, mfrs, products, offers, rates, fixes, diag)
    issues = quality.review(rows, diag["by_product"], diag["cats"])
    quality.report(issues, diag["fixed"])

    # kiugró jelzők: csak a változókat
    now_out = {o["id"] for o in offers if o.get("is_outlier")}
    set_on, set_off = sorted(outliers - now_out), sorted(now_out - outliers)
    for vals, ids in ((1, set_on), (0, set_off)):
        if ids:
            db.update("offers", {"is_outlier": vals}, id=f"in.({','.join(map(str, ids))})")

    _ensure_powers_column(db)
    # összesítő: törlés + csak a megváltozott sorok írása
    prev = {r["id"]: r for r in db.select("product_summary", select="id,sig,category")}
    guard = quality.circuit_breaker(db, rows, prev, diag.get("ai"))        # biztosíték: tömeges, gyanús változás nem kerül ki az oldalra
    old = {pid: r["sig"] for pid, r in prev.items()}
    gone = sorted(set(old) - set(rows)) if not guard["keep_deleted"] else []
    changed = [r for pid, r in rows.items() if old.get(pid) != r["sig"]]
    quality.save_status(db, issues, diag["fixed"], guard)
    if gone:
        for i in range(0, len(gone), 80):
            db.execute([(f"DELETE FROM product_summary WHERE id IN ({','.join('?' * len(gone[i:i + 80]))})", gone[i:i + 80])])
    if changed:
        db.upsert("product_summary", changed, on_conflict="id", returning=False)
    stats = {"termekek": len(rows), "valtozott": len(changed), "torolve": len(gone), "elteroar": len(outliers)}
    print(f"[summary] {stats}", flush=True)
    return stats


if __name__ == "__main__":             # csak az összesítő újraépítése (pl. az AI-ellenőrzés után): python scraper/summary.py
    from db import get_db
    rebuild(get_db())
