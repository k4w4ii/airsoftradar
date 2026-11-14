"""D1 út tesztje: a D1-et helyi SQLite helyettesíti (a D1 is SQLite), a scraper valódi kódja fut rajta."""
import json
import sqlite3
import unittest
from pathlib import Path

import summary
from d1db import D1DB
from run_shop import OFFER_COLS, create_product, load_catalog, match_offers

SCHEMA = (Path(__file__).parent.parent / "d1" / "schema.sql").read_text()


class LocalD1(D1DB):
    """Mint a web/app/api/db végpont: egy kérés = egy tranzakció (D1 batch)."""
    def __init__(self):
        self.con = sqlite3.connect(":memory:")
        self.con.row_factory = sqlite3.Row
        self.con.executescript(SCHEMA)
        self.calls = 0

    def _post(self, body):
        self.calls += 1
        out = []
        try:
            for st in body["statements"]:
                assert len(st["params"]) <= 100, "D1: legfeljebb 100 paraméter"
                cur = self.con.execute(st["sql"], st["params"])
                out.append({"results": [dict(r) for r in cur.fetchall()]})
            self.con.commit()
        except sqlite3.Error as e:
            self.con.rollback()
            raise RuntimeError(f"D1 400: {e}") from None
        return json.loads(json.dumps(out))


def seed(db):
    db.execute([
        ("INSERT INTO shops (id,slug,name,base_url,country,currency,lang) VALUES (1,'a','ShopA','x','PL','EUR','en'),(2,'b','ShopB','x','HU','HUF','hu'),(3,'c','ShopC','x','FR','EUR','en')", []),
        ("INSERT INTO manufacturers (id,slug,name) VALUES (1,'cyma','CYMA'),(2,'specna-arms','Specna Arms')", []),
        ("INSERT INTO manufacturer_aliases VALUES ('cyma',1),('specnaarms',2)", []),
        ("INSERT INTO exchange_rates (currency,rate_date,huf_per_unit) VALUES ('EUR','2026-11-08',380),('EUR','2026-11-09',385)", []),
    ])


class TestD1Pipeline(unittest.TestCase):
    def setUp(self):
        self.db = LocalD1()
        seed(self.db)

    def test_filters_and_paging(self):
        self.db.upsert("offers", [{"shop_id": 1, "external_id": f"e{i}", "url": f"u{i}", "title_raw": "x", "price": 1,
                                   "currency": "EUR"} for i in range(2300)], on_conflict="shop_id,external_id", returning=False)
        self.assertEqual(len(self.db.select("offers", select="id", is_active="eq.true")), 2300)     # 3 lap
        ids = [r["id"] for r in self.db.select("offers", select="id")][:500]
        self.db.update("offers", {"match_status": "review"}, id=f"in.({','.join(map(str, ids))})")  # nagy IN-lista szétvágva
        self.assertEqual(len(self.db.select("offers", select="id", match_status="eq.review")), 500)
        self.assertEqual(self.db.select("latest_rates", select="currency,huf_per_unit"), [{"currency": "EUR", "huf_per_unit": 385.0}])

    def test_full_flow(self):
        db = self.db
        rows = [
            {"shop_id": 1, "external_id": "1", "url": "https://a/cm048", "title_raw": "CYMA CM.048 AKM AEG", "price": 220, "currency": "EUR", "stock": "in_stock"},
            {"shop_id": 2, "external_id": "2", "url": "https://b/cm048", "title_raw": "CYMA CM048 AK47 elektromos", "price": 87000, "currency": "HUF", "stock": "in_stock"},
            {"shop_id": 3, "external_id": "3", "url": "https://c/cm048", "title_raw": "CYMA CM048 AKM Wood", "price": 260, "currency": "EUR", "stock": "out_of_stock"},
            {"shop_id": 3, "external_id": "4", "url": "https://c/hpa", "title_raw": "Evike Custom CYMA CM048 AKM with Wolverine Inferno HPA", "price": 893, "currency": "EUR", "stock": "out_of_stock"},
            {"shop_id": 1, "external_id": "5", "url": "https://a/bb20", "title_raw": "Specna Arms FLEX precision BBs 0.20g 1kg", "price": 15, "currency": "EUR", "stock": "in_stock"},
            {"shop_id": 3, "external_id": "6", "url": "https://c/bb28", "title_raw": "Specna Arms FLEX precision BBs 0.28g - 1kg", "price": 17, "currency": "EUR", "stock": "in_stock"},
        ]
        saved = db.upsert("offers", rows, on_conflict="shop_id,external_id")
        self.assertEqual(len(saved), 6)
        self.assertEqual(saved[0]["match_status"], "pending")
        cat, _ = load_catalog(db)
        rates = {"EUR": 385, "HUF": 1}
        from decimal import Decimal
        stats = match_offers(db, cat, db.select("offers", select=OFFER_COLS, match_status="eq.pending"),
                             {k: Decimal(v) for k, v in rates.items()}, lambda o: "en", {})
        self.assertNotIn("hiba", stats)
        prods = db.query("SELECT p.id, p.name, count(o.id) n FROM products p JOIN offers o ON o.product_id=p.id GROUP BY p.id ORDER BY p.id")
        names = {p["name"]: p["n"] for p in prods}
        self.assertEqual(names.get("CYMA CM.048 AKM AEG"), 3, names)          # a 3 alap ajánlat egy termék
        self.assertEqual(len(prods), 4, names)                                  # + HPA külön, + 0.20g, + 0.28g külön
        # második futás: upsert nem rontja el a párosítást
        db.upsert("offers", [{**rows[0], "price": 210}], on_conflict="shop_id,external_id")
        self.assertEqual(db.query("SELECT match_status FROM offers WHERE external_id='1'")[0]["match_status"], "auto")
        # ártörténet + inaktiválás
        db.upsert("price_history", [{"offer_id": 1, "observed_on": "2026-11-09", "price": 210, "currency": "EUR",
                                     "price_huf": 80850, "price_eur": 210, "stock": "in_stock"}], on_conflict="offer_id,observed_on", returning=False)
        db.update("offers", {"is_active": False}, shop_id="eq.9", last_seen_at="lt.2000-01-01")
        # összesítés
        st = summary.rebuild(db)
        self.assertEqual(st["termekek"], 4)
        ps = {r["name"]: r for r in db.query("SELECT * FROM product_summary")}
        cm = ps["CYMA CM.048 AKM AEG"]
        self.assertEqual((cm["category"], cm["offer_count"], cm["stock"]), ("rifle", 3, "in_stock"))
        self.assertEqual(cm["best_price_huf"], 80850)                            # 210 EUR * 385
        self.assertIn(",ak,", cm["platforms"])
        self.assertEqual(ps["Specna Arms FLEX precision BBs 0.20g 1kg"]["category"], "acc_ammo")
        again = summary.rebuild(db)
        self.assertEqual(again["valtozott"], 0)                                  # változatlan adat: nincs írás

    def test_create_product_slug_conflict(self):
        cat, _ = load_catalog(self.db)
        np = {"manufacturer_id": 1, "model_code_norm": "CM048", "name": "CYMA CM048", "alt_codes": [], "ean": None}
        p1 = create_product(self.db, cat, dict(np), "en", None)
        self.db.execute([("UPDATE products SET model_code_norm=NULL", [])])     # kód elengedve, webcím marad
        cat2, _ = load_catalog(self.db)
        p2 = create_product(self.db, cat2, dict(np), "en", None)
        self.assertNotEqual(p1, p2)



class TestHealthCheck(unittest.TestCase):
    def test_db_and_site(self):
        import health_check as hc
        from datetime import date, datetime, timezone
        db = LocalD1()
        seed(db)
        now = datetime.now(timezone.utc).isoformat()
        db.execute([("INSERT INTO products (id,manufacturer_id,name,slug) VALUES (1,1,'CYMA CM048','cyma-cm048')", []),
                    ("INSERT INTO offers (id,shop_id,external_id,url,title_raw,price,currency,product_id,match_status,last_seen_at) "
                     "VALUES (5,1,'x','https://a/x','CYMA CM048',200,'EUR',1,'matched',?)", [now])])
        summary.rebuild(db)
        rep = hc.Report()
        sample = hc.check_db(db, rep, date(2026, 11, 10))
        self.assertEqual(sample, {"slug": "cyma-cm048", "name": "CYMA CM048", "offer_id": 5})
        levels = {n: l for l, n, _ in rep.rows}
        self.assertEqual(levels["Weboldal-összesítő"], "HIBA")      # 1 termék < 100
        self.assertEqual(levels["MNB árfolyam"], "OK")
        self.assertEqual(levels["Napi letöltés"], "OK")

        pages = {"/hu": '<a class="cat-tile">', "/hu?cat=weapons": "<a href=/hu/p/x>", "/en?cat=weapons": "<a href=/en/p/x>",
                 "/api/suggest?l=hu&q=cyma": '{"products":[]}', "/go/5": "location.replace(", "/sitemap.xml": "<loc>",
                 "/robots.txt": "Disallow: /api/", "/hu/adatvedelem": "Cloudflare, Inc."}
        def get(url, method="GET", body=None, headers=None):
            path = url.split("workers.dev", 1)[-1] if "workers.dev" in url else None
            if path is None:
                return 403, {"cf-mitigated": "challenge"}, ""
            if path == "/api/db":
                return (404 if method == "GET" else 401), {}, ""
            if path == "/hu/p/cyma-cm048":
                return 200, {}, "<p>Az adatok most nem érhetők el. / Data</p>"     # hibaoldal 200-as kóddal
            return 200, {}, pages.get(path, pages.get(path.split("?")[0], "ok"))
        rep = hc.Report()
        hc.check_site("https://a.workers.dev", "https://www.example.com", sample, rep, get)
        levels = {n: l for l, n, _ in rep.rows}
        self.assertEqual(levels["Termékoldal"], "HIBA")
        self.assertEqual(levels["Saját domain"], "FIGYELEM")
        self.assertEqual(levels["Titkos végpont token nélkül"], "OK")
        self.assertTrue(all(l == "OK" for n, l in levels.items() if n not in ("Termékoldal", "Saját domain")))
        self.assertIn("❌", rep.markdown())



class TestAuditKinds(unittest.TestCase):
    def test_parts_and_custom_detached(self):
        import rematch
        from decimal import Decimal
        from run_shop import load_catalog
        db = LocalD1()
        seed(db)
        db.execute([
            ("INSERT INTO products (id,manufacturer_id,name,slug) VALUES (1,1,'CYMA CM.048 AKM','cyma-cm048')", []),
            ("INSERT INTO product_summary (id,slug,name,manufacturer,category,offer_count,in_stock_count,stock) VALUES (1,'cyma-cm048','CYMA CM.048 AKM','CYMA','rifle',1,1,'in_stock')", []),
            ("INSERT INTO offers (id,shop_id,external_id,url,title_raw,price,currency,product_id,match_status) VALUES "
             "(1,1,'a','u1','CYMA CM.048 AKM AEG',160,'EUR',1,'auto'),"
             "(2,2,'b','u2','CYMA Šroub pažbičky AK 2ks',673,'HUF',1,'auto'),"
             "(3,3,'c','u3','CYMA CM.048 AKM HPA custom build',600,'EUR',1,'auto'),"
             "(4,2,'d','u4','CYMA CM048 tárrugó',900,'HUF',1,'manual')", []),
        ])
        cat, _ = load_catalog(db)
        self.assertIs(cat.gun_kind(1), True)
        n = rematch.audit_kinds(db, cat, {"EUR": Decimal(385), "HUF": Decimal(1)})
        self.assertEqual(n, 2)
        rows = {r["id"]: r for r in db.query("SELECT id, product_id, match_status FROM offers")}
        self.assertEqual(rows[1]["product_id"], 1)                       # a fegyver marad
        self.assertEqual((rows[2]["product_id"], rows[2]["match_status"]), (None, "pending"))   # csavar le
        self.assertIsNone(rows[3]["product_id"])                         # custom le
        self.assertEqual(rows[4]["product_id"], 1)                       # kézi párosítás érintetlen

    def test_custom_category_in_summary(self):
        import summary
        rows, _ = summary.compute([{"id": 1, "country": "PL"}], {1: "CYMA"},
                                  {7: {"id": 7, "manufacturer_id": 1, "name": "CYMA CM.048 AKM HPA Custom", "slug": "x"}},
                                  [{"id": 1, "product_id": 7, "shop_id": 1, "url": "u", "title_raw": "CYMA CM.048 AKM HPA Custom AEG",
                                    "price": 600, "currency": "EUR", "stock": "in_stock", "last_seen_at": "2026-11-10"}],
                                  {"EUR": 385, "HUF": 1})
        self.assertEqual(rows[7]["category"], "custom_rifle")

    def test_stale_offers_hidden(self):
        """Hetek óta nem látott ajánlat (tartósan blokkolt bolt) nem számít a legjobb árba; a viszonyítás a legfrissebb adat."""
        import summary
        off = lambda i, shop, price, seen: {"id": i, "product_id": 7, "shop_id": shop, "url": f"u{i}", "title_raw": "CYMA CM.048 AKM AEG",
                                            "price": price, "currency": "EUR", "stock": "in_stock", "last_seen_at": seen}
        prods = {7: {"id": 7, "manufacturer_id": 1, "name": "CYMA CM.048 AKM", "slug": "x"}}
        shops = [{"id": 1, "country": "PL"}, {"id": 2, "country": "CZ"}]
        diag = {}
        rows, _ = summary.compute(shops, {1: "CYMA"}, prods,
                                  [off(1, 1, 150, "2026-10-01T03:00:00Z"), off(2, 2, 170, "2026-11-10T03:00:00Z")],
                                  {"EUR": 385, "HUF": 1}, diag=diag)
        self.assertEqual((rows[7]["offer_count"], rows[7]["best_price_huf"], diag["elavult"]), (1, 170 * 385, 1))
        # ha minden adat régi (a teljes letöltés áll), semmi nem tűnik el
        rows, _ = summary.compute(shops, {1: "CYMA"}, prods,
                                  [off(1, 1, 150, "2026-10-01T03:00:00Z"), off(2, 2, 170, "2026-10-03T03:00:00Z")], {"EUR": 385, "HUF": 1})
        self.assertEqual(rows[7]["offer_count"], 2)



if __name__ == "__main__":
    unittest.main()
