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


class TestPowers(unittest.TestCase):
    def test_powers(self):
        import classify
        self.assertEqual(classify.powers("Specna Arms SA-J22 FLEX AEG"), ["aeg"])
        self.assertEqual(classify.powers("Tokyo Marui VSR-10 G-Spec sniper rifle"), ["spring"])
        self.assertEqual(classify.powers("Tokyo Marui VSR-10 GBB"), ["gbb"])
        self.assertEqual(classify.powers("WE Glock 17 non-blowback gas pistol"), ["gas"])
        self.assertEqual(classify.powers("Prometheus MS120 non-linear spring", gun=False), [])
        self.assertEqual(classify.powers("Maple Leaf Hop Up Rubber for VSR-10 & GBB", gun=False), ["gbb", "spring"])

    def test_aeg_never_merges_with_gbbr(self):
        from filters import spec_conflict, specs
        flex, vapor = specs("Specna Arms AK-12 SA-J22 FLEX AEG - Black"), specs("Specna Arms AK-12 SA-J22 VAPOR GBBR - Black")
        self.assertTrue(spec_conflict(flex, vapor))
        self.assertFalse(spec_conflict(specs("Hop Up Rubber for VSR-10 & GBB"), specs("Hop Up Rubber for GBB")))
        self.assertTrue(spec_conflict(specs("SA-E07 EDGE carbine"), specs("SA-E07 CORE carbine")))

    def test_summary_powers_and_non_products(self):
        prods = {1: {"id": 1, "manufacturer_id": 1, "name": "CYMA CM.048 AKM AEG", "slug": "a"},
                 2: {"id": 2, "manufacturer_id": 1, "name": "Gift card 50 EUR", "slug": "g"}}
        rows, _ = run(prods, [offer(1, 1, "CYMA CM.048 AKM AEG", 160, "EUR"), offer(2, 2, "Atom Airsoft Gift card", 50, "EUR")])
        self.assertEqual(rows[1]["powers"], ",aeg,")
        self.assertNotIn(2, rows)


class TestKits(unittest.TestCase):
    def test_bundles_and_hv_are_separate(self):
        from filters import spec_conflict, specs
        base = specs("SA-S02 CORE™ Sniper Rifle Replica - MC")
        self.assertTrue(spec_conflict(base, specs("SA-S02 CORE™ sniper rifle replica with scope and bipod - tan")))
        self.assertTrue(spec_conflict(base, specs("SA-S02 CORE™ High Velocity Sniper Rifle Replica - MC")))
        self.assertFalse(spec_conflict(base, specs("Specna Arms SA-S02 CORE™ Sniper Rifle - Black")))   # csak a szín más
        self.assertFalse(spec_conflict(specs("SNIPER RIFLE SA-S02 CORE + OPTIC E BIPOD - TAN"),
                                       specs("Specna Arms SA-S02 CORE™ Sniper Rifle with scope and bipod - Black")))
        self.assertNotIn("kit", specs("Bipod for sniper rifle"))


class TestGrenades(unittest.TestCase):
    def test_types(self):
        import classify
        self.assertEqual(classify.grenade_types("Smoke grenade Enola Gaye EG18", 3500), ["smoke"])
        self.assertEqual(classify.grenade_types("TAG-67 BB impact grenade", 12000), ["bb"])
        self.assertEqual(classify.grenade_types("APS M203 grenade launcher", 30000), ["launcher"])
        self.assertEqual(classify.grenade_types("Moscart 40mm shell 72 BBs", 12000), ["shell"])
        self.assertEqual(classify.grenade_types("Zestaw 12 skorup Pineapple do granatu Thunder B", 3000), ["part"])
        self.assertIn("sound", classify.grenade_types("Thunder B Sonic Grenade Complete Set", 9000))

    def test_summary_subtypes(self):
        prods = {1: {"id": 1, "manufacturer_id": 1, "name": "CYMA Smoke grenade", "slug": "s"}}
        rows, _ = run(prods, [offer(1, 1, "CYMA Smoke grenade white", 3000)])
        self.assertEqual((rows[1]["category"], rows[1]["subtypes"]), ("grenade", ",gt=smoke,"))
