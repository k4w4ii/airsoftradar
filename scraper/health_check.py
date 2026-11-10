"""
Állapot-ellenőrzés: adatbázis (Cloudflare D1) + weboldal. Csak stdlib.
GitHub Actions: health (kézzel) és a napi futás utolsó lépése. Hiba esetén piros lesz (a GitHub e-mailt küld).
Env: D1_API_URL, D1_API_TOKEN; SITE_URL (opcionális, alap: https://www.airsofthunter.com).

A weboldalt a workers.dev címen nézi (ugyanaz a Worker, de nincs előtte a domain botvédelme),
a www-címet csak tájékoztatásul (a Bot Fight Mode a GitHub gépeit kihívással fogadhatja).
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta, timezone

UA = "AirsoftHunterBot/1.0 health-check (+https://www.airsofthunter.com/bot)"
ERROR_TEXT = "Az adatok most nem érhetők el"


def http(url: str, method: str = "GET", body: bytes | None = None, headers: dict | None = None):
    """(státusz, fejlécek, szöveg) – hibakódnál sem dob kivételt."""
    req = urllib.request.Request(url, data=body, method=method, headers={"User-Agent": UA, **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            return r.status, dict(r.headers), r.read(2_000_000).decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read(200_000).decode("utf-8", "replace")
    except (urllib.error.URLError, TimeoutError) as e:
        return 0, {}, str(e)


class Report:
    def __init__(self):
        self.rows: list[tuple[str, str, str]] = []

    def add(self, level: str, name: str, detail: str = ""):
        self.rows.append((level, name, detail))
        print(f"{level:9} {name}{' – ' + detail if detail else ''}", flush=True)

    ok = lambda self, n, d="": self.add("OK", n, d)
    warn = lambda self, n, d="": self.add("FIGYELEM", n, d)
    fail = lambda self, n, d="": self.add("HIBA", n, d)

    @property
    def failed(self) -> bool:
        return any(r[0] == "HIBA" for r in self.rows)

    def markdown(self) -> str:
        icon = {"OK": "✅", "FIGYELEM": "⚠️", "HIBA": "❌"}
        lines = ["| | Ellenőrzés | Részlet |", "|---|---|---|"]
        lines += [f"| {icon[l]} | {n} | {d.replace('|', '/')} |" for l, n, d in self.rows]
        return "\n".join(lines)


def check_db(db, rep: Report, today: date) -> dict:
    """Adatbázis-ellenőrzések. Visszaad: minta termék és ajánlat a weboldal-teszthez."""
    q = db.query
    n = {t: q(f"SELECT count(*) AS n FROM {t}")[0]["n"] for t in ("shops", "products", "offers", "product_summary", "price_history")}
    active = q("SELECT count(*) AS n FROM offers WHERE is_active = 1")[0]["n"]
    rep.ok("D1 elérhető", f"{n['shops']} bolt, {n['products']} termék, {active} aktív ajánlat, {n['price_history']} ártörténet-sor")

    if n["product_summary"] >= 100:
        rep.ok("Weboldal-összesítő", f"{n['product_summary']} termék látszik az oldalon")
    else:
        rep.fail("Weboldal-összesítő", f"csak {n['product_summary']} sor – fusson le a rematch (Actions → rematch)")

    r = q("SELECT max(rate_date) AS d FROM exchange_rates WHERE currency = 'EUR'")[0]["d"]
    if r and date.fromisoformat(str(r)[:10]) >= today - timedelta(days=5):
        rep.ok("MNB árfolyam", f"EUR, {r}")
    else:
        rep.fail("MNB árfolyam", f"régi vagy hiányzik (utolsó: {r}) – az mnb_rates lépés hibás")

    last = q("SELECT max(last_seen_at) AS t FROM offers")[0]["t"]
    try:
        age = datetime.now(timezone.utc) - datetime.fromisoformat(str(last).replace("Z", "+00:00"))
        hours = age.total_seconds() / 3600
    except (TypeError, ValueError):
        hours = None
    if hours is not None and hours <= 50:
        rep.ok("Napi letöltés", f"utolsó friss ajánlat {hours:.0f} órája")
    else:
        rep.fail("Napi letöltés", f"régen nem jött új adat (utolsó: {last}) – nézd meg a daily-scrape futást")

    runs = q("""SELECT s.slug, r.status, r.offers_seen, r.started_at,
                       CASE WHEN json_valid(r.errors) THEN coalesce(json_extract(r.errors, '$[0].error'), '') END AS err
                FROM shops s
                JOIN scrape_runs r ON r.id = (SELECT max(id) FROM scrape_runs x WHERE x.shop_id = s.id)
                ORDER BY s.slug""")
    try:                                  # letiltott bolt (shops.json: enabled=false) régi hibája nem számít
        off = {k for k, v in json.load(open(os.path.join(os.path.dirname(__file__), "shops.json"), encoding="utf-8")).items()
               if isinstance(v, dict) and v.get("enabled") is False}
    except (OSError, ValueError):
        off = set()
    runs = [r for r in runs if r["slug"] not in off]
    bad = [f"{r['slug']} ({r['status']}{': ' + str(r['err'])[:120] if r.get('err') else ''})"
           for r in runs if r["status"] not in ("ok", "partial", "running")]
    if bad:
        rep.warn("Boltok utolsó futása", "sikertelen: " + ", ".join(bad) + " – részletek: d1/allapot.sql")
    elif runs:
        rep.ok("Boltok utolsó futása", f"{len(runs)} bolt rendben")

    missing = q("""SELECT count(DISTINCT product_id) AS n FROM offers
                   WHERE is_active = 1 AND product_id IS NOT NULL AND product_id NOT IN (SELECT id FROM product_summary)""")[0]["n"]
    if missing > max(50, n["product_summary"] * 0.05):
        rep.warn("Összesítő teljessége", f"{missing} termék hiányzik az oldalról – fusson le a rematch")

    outl = q("SELECT count(*) AS n FROM offers WHERE is_outlier = 1 AND is_active = 1")[0]["n"]
    pend = q("SELECT count(*) AS n FROM offers WHERE match_status = 'pending' AND is_active = 1")[0]["n"]
    rep.ok("Párosítás", f"{pend} párosítatlan ajánlat (ismeretlen márka), {outl} eltérő árú")

    sample = q("""SELECT p.slug, p.name, (SELECT o.id FROM offers o WHERE o.product_id = p.id AND o.is_active = 1 LIMIT 1) AS offer_id
                  FROM product_summary p ORDER BY p.offer_count DESC LIMIT 1""")
    return sample[0] if sample else {}


def check_site(base: str, site: str, sample: dict, rep: Report, get=http) -> None:
    def page(name: str, path: str, must: str = "", status: int = 200):
        code, _, body = get(base + path)
        if code != status:
            rep.fail(name, f"{path} → HTTP {code}")
        elif ERROR_TEXT in body:
            rep.fail(name, f"{path} → hibaoldal („{ERROR_TEXT}”) – Cloudflare → Worker → Observability napló")
        elif must and must not in body:
            rep.fail(name, f"{path} → hiányzik: {must}")
        else:
            rep.ok(name, path)
        return body

    page("Üdvözlő oldal (HU)", "/hu", "cat-tile")
    page("Katalógus (HU)", "/hu?cat=weapons", "/hu/p/")
    page("Katalógus (EN)", "/en?cat=weapons", "/en/p/")
    page("Keresési javaslatok", "/api/suggest?l=hu&q=cyma", '"products"')
    page("Szűrés + keresés", "/hu?cat=all&q=ak&sort=price")
    if sample.get("slug"):
        page("Termékoldal", f"/hu/p/{sample['slug']}")
    if sample.get("offer_id"):
        page("Bolti link (/go)", f"/go/{sample['offer_id']}", "location.replace")
    page("Sitemap", "/sitemap.xml", "<loc>")
    page("robots.txt", "/robots.txt", "/api/")
    page("Jogi oldal", "/hu/adatvedelem", "Cloudflare")

    code, _, _ = get(base + "/api/db")
    (rep.ok if code == 404 else rep.fail)("Titkos végpont (GET)", f"/api/db → {code} (404 a jó)")
    code, _, _ = get(base + "/api/db", "POST", b'{"statements":[{"sql":"SELECT 1"}]}', {"Content-Type": "application/json"})
    (rep.ok if code == 401 else rep.fail)("Titkos végpont token nélkül", f"/api/db → {code} (401 a jó)")

    code, hdr, body = get(site.rstrip("/") + "/hu")
    if code == 200 and ERROR_TEXT not in body:
        rep.ok("Saját domain", site)
    elif code in (403, 503) or "cf-mitigated" in {k.lower() for k in hdr}:
        rep.warn("Saját domain", f"{site} → {code}: a Cloudflare botvédelme kihívást adott a GitHub gépének (ez normális) – böngészőben nézd meg")
    else:
        rep.fail("Saját domain", f"{site} → HTTP {code}")


def main() -> int:
    from d1db import D1DB
    db = D1DB()
    base = db.url[: -len("/api/db")]
    site = os.environ.get("SITE_URL") or "https://www.airsofthunter.com"
    rep = Report()
    sample = {}
    try:
        sample = check_db(db, rep, date.today())
    except Exception as e:                                   # noqa: BLE001 – minden hibát jelenteni kell
        rep.fail("D1 elérhető", f"{e} – nézd meg a D1_API_URL változót és a D1_API_TOKEN / INGEST_TOKEN kulcsot")
    check_site(base, site, sample, rep)
    out = os.environ.get("GITHUB_STEP_SUMMARY")
    if out:
        with open(out, "a", encoding="utf-8") as f:
            f.write("## AirsoftHunter állapot\n\n" + rep.markdown() + "\n")
    print("\nEREDMÉNY:", "HIBA – lásd a fenti ❌ sorokat" if rep.failed else "minden rendben", flush=True)
    return 1 if rep.failed else 0


if __name__ == "__main__":
    sys.exit(main())
