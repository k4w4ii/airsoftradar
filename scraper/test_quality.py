import tempfile
import unittest
from pathlib import Path

import quality
import summary

RATES = {"EUR": 385, "HUF": 1}
SHOPS = [{"id": 1, "country": "PL"}, {"id": 2, "country": "CZ"}]


def offer(i, pid, title, price, cur="HUF", shop=1, stock="in_stock", url=None):
    return {"id": i, "product_id": pid, "shop_id": shop, "url": url or f"u{i}", "title_raw": title, "price": price,
            "currency": cur, "stock": stock, "last_seen_at": "2026-11-11"}


def run(products, offers, fixes=None):
    diag = {}
    rows, _ = summary.compute(SHOPS, {1: "CYMA"}, products, offers, RATES, fixes, diag)
    return rows, diag


class TestFixesFile(unittest.TestCase):
    def test_parse(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "j.txt"
            p.write_text("# megjegyzés\nkategoria acm-patch = acc_gear\nelrejt https://shop.example/p#x\n"
                         "kategoria rossz = nincs_ilyen\nvalami zagyvaság\n", encoding="utf-8")
            f = quality.load_fixes(p)
        self.assertEqual(f["kategoria"], {"acm-patch": "acc_gear"})
        self.assertEqual(f["elrejt"], {"https://shop.example/p#x"})


class TestAutoFix(unittest.TestCase):
    def test_cheap_weapon_becomes_accessory(self):
        # 1 fegyver-szavazat + a név fél szavazata > 1 kiegészítő, de a medián ár (5250 Ft) mesterlövész puskának kevés
        prods = {1: {"id": 1, "manufacturer_id": 1, "name": "CYMA Sniper Rifle", "slug": "s"}}
        rows, diag = run(prods, [offer(1, 1, "CYMA Sniper Rifle", 6500), offer(2, 1, "CYMA Sniper Rifle sling", 4000, shop=2)])
        self.assertNotIn(rows[1]["category"], {"sniper", "rifle"})
        self.assertTrue(diag["fixed"])

    def test_part_name_not_weapon(self):
        prods = {1: {"id": 1, "manufacturer_id": 1, "slug": "st",
                     "name": "CYMA Fixed Sniper Stock w/ Cheek Rest for CM.708 Series Sniper Rifles"}}
        rows, _ = run(prods, [offer(1, 1, "CYMA Fixed Sniper Stock w/ Adjustable Buttpad and Cheek Rest for CM.708 Series Sniper Rifles", 26500)])
        self.assertTrue(rows[1]["category"].startswith("part_"))

    def test_real_weapon_untouched(self):
        prods = {1: {"id": 1, "manufacturer_id": 1, "name": "CYMA CM.048 AKM", "slug": "a"}}
        rows, diag = run(prods, [offer(1, 1, "CYMA CM.048 AKM AEG", 160, "EUR")])
        self.assertEqual(rows[1]["category"], "rifle")
        self.assertEqual(diag["fixed"], [])

    def test_manual_category_and_hide(self):
        prods = {1: {"id": 1, "manufacturer_id": 1, "name": "CYMA CM.048 AKM", "slug": "a"}}
        fixes = {"kategoria": {"a": "custom_rifle"}, "elrejt": {"u2"}}
        rows, diag = run(prods, [offer(1, 1, "CYMA CM.048 AKM AEG", 160, "EUR"), offer(2, 1, "CYMA CM048 stock", 20, "EUR", shop=2)], fixes)
        self.assertEqual(rows[1]["category"], "custom_rifle")
        self.assertEqual(rows[1]["offer_count"], 1)                   # az elrejtett ajánlat nem számít


class TestReview(unittest.TestCase):
    def test_flags(self):
        prods = {1: {"id": 1, "manufacturer_id": 1, "name": "CYMA Šroub pažbičky AK", "slug": "z"},
                 2: {"id": 2, "manufacturer_id": 1, "name": "CYMA CM.048 AKM", "slug": "a"}}
        rows, diag = run(prods, [offer(1, 1, "CYMA AK magazine", 3000), offer(2, 2, "CYMA CM.048 AKM AEG", 100, "EUR"),
                                 offer(3, 2, "CYMA CM.048 AKM AEG", 230, "EUR", shop=2)])
        kinds = {(i["tipus"], i["termek"]) for i in quality.review(rows, diag["by_product"], diag["cats"])}
        self.assertIn(("idegen nyelvű név", "CYMA Šroub pažbičky AK"), kinds)
        self.assertNotIn(("nagy árkülönbség", "CYMA CM.048 AKM"), kinds)    # 2,3x: még belefér

    def test_report_writes_csv(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "m.csv"
            quality.report([{"tipus": "x", "termek": "t", "kategoria": "rifle", "reszlet": "", "link": "l"}], [], str(p))
            self.assertIn("ellenőrizendő;x;t", p.read_text(encoding="utf-8-sig"))


if __name__ == "__main__":
    unittest.main()
