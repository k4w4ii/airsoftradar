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


if __name__ == "__main__":
    unittest.main()


class FakePG:
    """Supabase PostgREST helyettesítő a migrációs teszthez (select / order / limit / offset / and=(k.gte.a,k.lt.b))."""
    def __init__(self, tables):
        self.t = tables

    def _req(self, method, table, params):
        rows = list(self.t.get(table, []))
        if "and" in params:
            conds = params["and"][1:-1].split(",")
            for c in conds:
                col, op, val = c.split(".")
                rows = [r for r in rows if (r[col] >= int(val) if op == "gte" else r[col] < int(val))]
        o = params.get("order", "")
        if o:
            col, *desc = o.split(",")[0].split(".")
            rows.sort(key=lambda r: r[col], reverse=bool(desc and desc[0] == "desc"))
        off, lim = params.get("offset", 0), params.get("limit", 10**9)
        rows = rows[off:off + lim]
        sel = params.get("select", "*")
        return rows if sel == "*" else [{k: r[k] for k in sel.split(",")} for r in rows]


class TestMigration(unittest.TestCase):
    def test_copy(self):
        import migrate_to_d1 as m
        m.PG_PAGE = 7
        offers = [{"id": i, "shop_id": 1, "external_id": f"e{i}", "url": f"https://a/{i}", "title_raw": f"O'Brien \"{i}\" ; DROP TABLE x; --",
                   "brand_raw": None, "sku_raw": None, "ean_raw": None, "image_url": None, "price": 10.5 + i, "currency": "EUR",
                   "stock": "in_stock", "product_id": 1 if i < 5 else None, "match_status": "matched" if i < 5 else "pending",
                   "match_method": None, "match_confidence": None, "is_active": True, "cat": "aeg", "plats": ["m4"], "variant": False,
                   "first_seen_at": "2026-10-01T10:00:00+00:00", "last_seen_at": "2026-11-09T02:17:00.12+00:00"} for i in range(1, 30)]
        pg = FakePG({
            "shops": [{"id": 1, "slug": "a", "name": "A", "base_url": "x", "country": "PL", "currency": "EUR", "lang": "en",
                       "ships_to": ["HU", "PL"], "is_active": True, "affiliate_template": None, "scraper_key": "a", "last_scraped_at": None}],
            "manufacturers": [{"id": 1, "slug": "cyma", "name": "CYMA"}],
            "manufacturer_aliases": [{"alias_norm": "cyma", "manufacturer_id": 1}],
            "exchange_rates": [{"currency": "EUR", "rate_date": "2026-11-09", "huf_per_unit": 385.12, "source": "MNB"}],
            "products": [{"id": 1, "manufacturer_id": 1, "model_code": "CM048", "model_code_norm": "cm048", "name": "CYMA CM048",
                          "slug": "cyma-cm048", "image_url": None, "name_lang": "en", "category_id": 3, "name_cat": "aeg",
                          "created_at": "2026-10-01T10:00:00Z"}],
            "product_codes": [], "match_candidates": [],
            "offers": offers,
            "price_history": [{"offer_id": o, "observed_on": f"2026-11-0{d}", "price": 10, "currency": "EUR", "price_huf": 3850,
                               "price_eur": 10, "stock": "in_stock"} for o in range(1, 30) for d in range(1, 4)],
        })
        d1 = LocalD1()
        m.TABLES = [(t, k, o, 4 if s and s < 10**9 else s) for t, k, o, s in m.TABLES]     # sok kis blokk
        m.SQL_MAX = 600                                                                    # sok kis utasítás
        m.apply_schema(d1)                                                                 # újrafuttatható
        for args in m.TABLES:
            m.copy_table(pg, d1, *args)
        for args in m.TABLES:                                                              # második futás: ugyanaz marad
            m.copy_table(pg, d1, *args)
        q = d1.query
        self.assertEqual(q("SELECT count(*) n FROM offers")[0]["n"], 29)
        self.assertEqual(q("SELECT count(*) n FROM price_history")[0]["n"], 87)
        o = q("SELECT * FROM offers WHERE id=3")[0]
        self.assertEqual(o["title_raw"], "O'Brien \"3\" ; DROP TABLE x; --")
        self.assertEqual((o["is_active"], o["price"]), (1, 13.5))
        self.assertEqual(o["last_seen_at"], "2026-11-09T02:17:00.120000+00:00")
        self.assertEqual(q("SELECT ships_to FROM shops")[0]["ships_to"], ",HU,PL,")
        self.assertNotIn("cat", o)
        stats = summary.rebuild(d1)
        self.assertEqual(stats["termekek"], 1)
        self.assertEqual(q("SELECT best_price_huf FROM product_summary")[0]["best_price_huf"], round(11.5 * 385.12))
