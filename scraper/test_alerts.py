"""Ár- és készletfigyelő: mikor szól, milyen levelet küld, mit töröl (helyi SQLite a D1 helyett)."""
import sqlite3
import unittest
from datetime import datetime, timezone
from pathlib import Path

import alerts


class FakeDB:
    def __init__(self):
        self.c = sqlite3.connect(":memory:")
        self.c.row_factory = sqlite3.Row
        self.c.executescript((Path(__file__).parent.parent / "d1" / "schema.sql").read_text(encoding="utf-8"))

    def execute(self, stmts):
        out = []
        for sql, params in stmts:
            out.append([dict(r) for r in self.c.execute(sql, params).fetchall()])
        self.c.commit()
        return out

    def query(self, sql, params=None):
        return self.execute([(sql, params or [])])[0]


NOW = datetime(2026, 11, 20, 6, 0, tzinfo=timezone.utc)


class TestAlerts(unittest.TestCase):
    def setUp(self):
        self.db = FakeDB()
        self.db.execute([(s, []) for s in alerts.SCHEMA])
        self.db.c.executescript("""
          INSERT INTO exchange_rates (currency, rate_date, huf_per_unit) VALUES ('EUR', '2026-11-19', 400);
          INSERT INTO product_summary (id, slug, name, manufacturer, search_code, category, best_price_huf, offer_count, in_stock_count, stock, price)
          VALUES (1, 'cyma-cm048', 'CYMA CM048 AKM', 'CYMA', 'x', 'rifle', 80000, 3, 2, 'in_stock', 80000),
                 (2, 'we-g17', 'WE G17', 'WE', 'x', 'pistol', NULL, 2, 0, 'out_of_stock', 30000);
          INSERT INTO alerts (email, product_id, kind, target_huf, currency, locale, token, created_at, confirmed_at) VALUES
            ('a@x.hu', 1, 'stock', NULL, 'HUF', 'hu', 't1', '2026-11-10T00:00:00Z', '2026-11-10T00:05:00Z'),
            ('b@x.hu', 1, 'price', 85000, 'EUR', 'en', 't2', '2026-11-10T00:00:00Z', '2026-11-10T00:05:00Z'),
            ('c@x.hu', 1, 'price', 70000, 'HUF', 'hu', 't3', '2026-11-10T00:00:00Z', '2026-11-10T00:05:00Z'),
            ('d@x.hu', 2, 'stock', NULL, 'HUF', 'hu', 't4', '2026-11-10T00:00:00Z', '2026-11-10T00:05:00Z'),
            ('e@x.hu', 1, 'stock', NULL, 'HUF', 'hu', 't5', '2026-11-01T00:00:00Z', NULL),
            ('f@x.hu', 1, 'stock', NULL, 'HUF', 'hu', 't6', '2026-11-19T00:00:00Z', NULL),
            ('g@x.hu', 1, 'stock', NULL, 'HUF', 'hu', 't7', '2026-10-01T00:00:00Z', '2026-10-01T00:05:00Z');
          UPDATE alerts SET sent_at = '2026-10-02T00:00:00Z' WHERE token = 't7';
        """)
        self.db.c.commit()

    def test_run(self):
        mails = []
        stats = alerts.run(self.db, sender=lambda m: mails.append(m) or True, now=NOW)
        self.assertEqual(sorted(m["to"] for m in mails), ["a@x.hu", "b@x.hu"])     # c: célár alatt nincs; d: nincs raktáron
        self.assertEqual(stats["elkuldve"], 2)
        left = {r["token"]: r for r in self.db.query("SELECT token, sent_at FROM alerts")}
        self.assertNotIn("t5", left)                    # 7 napnál régebbi, meg nem erősített: törölve
        self.assertIn("t6", left)                       # friss, meg nem erősített: marad
        self.assertNotIn("t7", left)                    # 30 napnál régebben teljesült: törölve
        self.assertIsNotNone(left["t1"]["sent_at"])
        self.assertIsNone(left["t3"]["sent_at"])
        # második futás: nem küld újra
        mails.clear()
        alerts.run(self.db, sender=lambda m: mails.append(m) or True, now=NOW)
        self.assertEqual(mails, [])

    def test_failed_send_retries_next_day(self):
        alerts.run(self.db, sender=lambda m: False, now=NOW)
        self.assertIsNone(self.db.query("SELECT sent_at FROM alerts WHERE token = 't1'")[0]["sent_at"])

    def test_mail_content(self):
        a = {"email": "b@x.hu", "kind": "price", "target_huf": 85000, "currency": "EUR", "locale": "en", "token": "tok",
             "slug": "cyma-cm048", "name": "CYMA <CM048>", "best_price_huf": 80000, "in_stock_count": 2}
        m = alerts.build_mail(a, {"EUR": 400})
        self.assertIn("200.00 €", m["subject"])
        self.assertIn("212.50 €", m["html"])
        self.assertIn("CYMA &lt;CM048&gt;", m["html"])      # HTML-escape
        self.assertIn("https://www.airsofthunter.com/en/p/cyma-cm048", m["html"])
        self.assertIn("a=stopall&amp;t=tok", m["html"])
        self.assertEqual(m["headers"]["List-Unsubscribe"], "<https://www.airsofthunter.com/api/alert?a=stop&t=tok>")
        hu = alerts.build_mail({**a, "kind": "stock", "locale": "hu", "currency": "HUF"}, {})
        self.assertIn("Újra raktáron", hu["subject"])
        self.assertIn("80 000 Ft", hu["html"])

    def test_due(self):
        self.assertFalse(alerts.due({"kind": "stock", "slug": None, "in_stock_count": 3}))
        self.assertTrue(alerts.due({"kind": "price", "slug": "x", "best_price_huf": 100, "target_huf": 100}))
        self.assertFalse(alerts.due({"kind": "price", "slug": "x", "best_price_huf": None, "target_huf": 100}))


if __name__ == "__main__":
    unittest.main()
