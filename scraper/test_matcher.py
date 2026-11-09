"""Futtatás: python -m unittest test_matcher -v"""
import unittest

from matcher import Catalog, OfferIn, Product, ean_valid, extract_codes, find_ean, match_offer, norm_alias

MFR = {1: ("cyma", "CYMA"), 2: ("ares", "ARES"), 3: ("double-bell", "Double Bell"),
       4: ("tokyo-marui", "Tokyo Marui"), 5: ("we", "WE"), 6: ("jg", "JG"), 7: ("amoeba", "Amoeba")}
ALIASES = {"cyma": 1, "ares": 2, "doublebell": 3, "db": 3, "tokyomarui": 4, "tm": 4, "marui": 4, "we": 5,
           "jg": 6, "amoeba": 7}


def catalog() -> Catalog:
    c = Catalog(aliases=ALIASES, manufacturers=MFR)
    c.add_product(Product(10, 1, "CYMA CM.522 Sport Line Gen 2", "CM522"), eans=["4710000000011"])
    c.add_product(Product(11, 1, "CYMA CM.523 Sport Line", "CM523"))
    c.add_product(Product(20, 2, "ARES G36 ECU", "AR078E"))
    c.add_product(Product(40, 4, "Tokyo Marui EVOLT RS FPR MK4 Recoil", None))
    c.add_product(Product(41, 4, "Tokyo Marui Hi-Capa 5.1 GBB", None))
    return c


class TestMatcher(unittest.TestCase):
    def setUp(self):
        self.c = catalog()

    def test_code_variants_same_product(self):
        for title in ["CM.522 Sport Line Gen 2 (CYMA)", "Cyma CM522 AK", "CYMA cm-522 replica"]:
            r = match_offer(OfferIn(title), self.c)
            self.assertEqual((r.product_id, r.method), (10, "code"), title)

    def test_neighbour_code_never_merged(self):
        r = match_offer(OfferIn("CYMA CM.524 Sport Line"), self.c)
        self.assertEqual(r.method, "new")
        self.assertEqual(r.new_product["model_code_norm"], "CM524")

    def test_brand_field_and_code_in_sku(self):
        r = match_offer(OfferIn("G36 ECU fekete", brand_raw="Ares", sku_raw="AR-078E"), self.c)
        self.assertEqual(r.product_id, 20)

    def test_ean_wins(self):
        r = match_offer(OfferIn("valami teljesen más cím", ean_raw="4710000000011"), self.c)
        self.assertEqual((r.product_id, r.method), (10, "ean"))

    def test_new_product_from_strong_code(self):
        r = match_offer(OfferIn("Double Bell RK-10 AKMS"), self.c)
        self.assertEqual((r.method, r.new_product["model_code_norm"]), ("new", "RK10"))

    def test_fuzzy_codeless(self):
        r = match_offer(OfferIn("Tokyo Marui EVOLT RS FPR MK4 AEG Recoil Version"), self.c)
        self.assertEqual((r.status, r.product_id), ("auto", 40))

    def test_unknown_brand_pending(self):
        r = match_offer(OfferIn("Ismeretlen AK47 replika"), self.c)
        self.assertEqual(r.status, "pending")

    def test_short_alias_needs_uppercase(self):
        self.assertIsNone(match_offer(OfferIn("we love this rifle"), self.c).manufacturer_id)
        self.assertEqual(match_offer(OfferIn("WE Glock 17 GBB"), self.c).manufacturer_id, 5)

    def test_family_names_not_codes(self):
        strong, weak = extract_codes("CYMA AK47 CM.522 11.1V 350FPS", "cyma")
        self.assertEqual(strong, ["CM522"])
        self.assertNotIn("AK47", weak)
        self.assertNotIn("350FPS", weak)

    def test_probe_titles(self):
        """Valós címek a probe kimenetéből."""
        cases = [
            (OfferIn("Replica of the RK-01-W carbine", "Double Bell"), "RK01W"),
            (OfferIn("Double Bell RK-10 AKMS AK47 Fém"), "RK10"),
            (OfferIn("JG Works JG2338 V2 AEG Assault Rifle - Black", "JG"), "JG2338"),
            (OfferIn("AM-009 Airsoft Carbine Replica - Black", "AMOEBA"), "AM009"),
            (OfferIn("CM.522 Sport Line, GEN-2 [CYMA]"), None),          # meglévő termék
            (OfferIn("Tokyo Marui EVOLT RS FPR MK4 AEG - Recoil version", "Tokyo Marui", "TM-4952839180025"), "4952839180025"),
        ]
        for o, code in cases:
            r = match_offer(o, self.c)
            if code is None:
                self.assertEqual((r.product_id, r.method), (10, "code"), o.title)
            else:
                self.assertEqual((r.method, r.new_product["model_code_norm"]), ("new", code), o.title)
        tm = match_offer(cases[-1][0], self.c)
        self.assertEqual(tm.new_product["ean"], "4952839180025")

    def test_jan_in_sku_matches_existing_ean(self):
        self.c.add_product(Product(42, 4, "Tokyo Marui EVOLT", "4952839180025"), eans=["4952839180025"])
        r = match_offer(OfferIn("EVOLT RS FPR", "Tokyo Marui", "TM-4952839180025"), self.c)
        self.assertEqual((r.product_id, r.method), (42, "ean"))

    def test_ean_checksum(self):
        self.assertTrue(ean_valid("4952839180025"))
        self.assertFalse(ean_valid("4952839180026"))
        self.assertIsNone(find_ean("sku 11406 11406"))

    def test_new_product_from_title_when_no_code(self):
        self.c.manufacturers[8] = ("emg", "EMG")
        self.c.aliases["emg"] = 8
        r = match_offer(OfferIn('Noveske N4 Gen.4 "Shorty" AEG - 350 fps version', "EMG"), self.c)
        self.assertEqual((r.status, r.method, r.new_product["model_code_norm"]), ("auto", "new_title", None))
        from matcher import Product as P
        self.c.add_product(P(80, 8, r.new_product["name"], None))
        r2 = match_offer(OfferIn('Noveske N4 Gen.4 "Shorty" AEG - 350 fps version - Black', "EMG"), self.c)
        self.assertEqual((r2.product_id, r2.method), (80, "fuzzy"))     # második bolt ugyanarra párosul

    def test_fuzzy_scales_to_large_catalog(self):
        import time
        c = Catalog(aliases={"specna": 9}, manufacturers={9: ("specna-arms", "Specna Arms")})
        for i in range(6000):     # 6000 kód nélküli termék egy gyártónál
            c.add_product(Product(1000 + i, 9, f"Specna Arms part {i} widget model{i} kit", None))
        c.add_product(Product(1, 9, "Specna Arms Flex FX01 HAL ETU carbine", None))
        t0 = time.perf_counter()
        for _ in range(200):
            r = match_offer(OfferIn("Specna Arms FLEX FX01 HAL ETU Carbine Black", "Specna"), c)
        self.assertEqual((r.product_id, r.method), (1, "fuzzy"))
        self.assertLess(time.perf_counter() - t0, 3.0)     # 200 ajánlat < 3 mp (régen ~percek)

    def test_norm_alias(self):
        self.assertEqual(norm_alias("G&G Armament"), "ggarmament")


if __name__ == "__main__":
    unittest.main()


class TestPartGate(unittest.TestCase):
    """Tár/alkatrész nem kerülhet a fegyverhez a fegyver modellkódja alapján."""
    def setUp(self):
        self.cat = Catalog({"cyma": 1}, {1: ("cyma", "CYMA")})
        self.cat.add_product(Product(10, 1, "CYMA CM.041K MP5K", "CM041K"))

    def test_magazine_not_matched_to_gun(self):
        r = match_offer(OfferIn("Magazine for CYMA CM.041K MP5K 200 rds", price_huf=2800), self.cat)
        self.assertNotEqual(r.product_id, 10)
        self.assertNotEqual(r.method, "code")

    def test_gun_still_matches_by_code(self):
        r = match_offer(OfferIn("CYMA CM.041K MP5K AEG", price_huf=45000), self.cat)
        self.assertEqual((r.product_id, r.method), (10, "code"))

    def test_bundle_is_gun(self):
        r = match_offer(OfferIn("CYMA CM.041K MP5K AEG with battery and charger", price_huf=52000), self.cat)
        self.assertEqual(r.product_id, 10)


class TestVariantGate(unittest.TestCase):
    """Az átépített (custom/HPA) változat nem kerülhet az alap fegyverhez, és fordítva."""
    def setUp(self):
        self.cat = Catalog({"cyma": 1}, {1: ("cyma", "CYMA")})
        self.cat.add_product(Product(20, 1, "CYMA CM048", "CM048"))

    def test_custom_hpa_not_matched_to_base(self):
        r = match_offer(OfferIn("Evike Custom CYMA CM048 AKM Rifle with Wolverine Inferno HPA System (Model: Fixed Stock)",
                                price_huf=325000), self.cat)
        self.assertNotEqual(r.product_id, 20)
        self.assertIsNone((r.new_product or {}).get("model_code_norm"))   # a kód az alap termékké marad

    def test_base_still_matches(self):
        r = match_offer(OfferIn("CYMA CM.048 AKM AEG - Wood", price_huf=85000), self.cat)
        self.assertEqual(r.product_id, 20)

    def test_hungarian_spring_part(self):
        self.cat.add_product(Product(21, 1, "CYMA VSR10 sniper spring CM.701B", "CM701B"))
        r = match_offer(OfferIn("CYMA VSR-10 SNIPER RUGÓ (CM.701B) - Airsoftpláza", price_huf=3700), self.cat)
        self.assertNotEqual(r.product_id, 21)


class TestRematchAfterCleanup(unittest.TestCase):
    """A 0012 takarítás után: a puska saját terméket kap a kódjával, az alkatrészek külön termékek lesznek."""
    def test_flow(self):
        cat = Catalog({"cyma": 1}, {1: ("cyma", "CYMA")})
        cat.add_product(Product(301, 1, "CYMA Zásobník pro M24 CM.702 na 20 ran C.112", None))   # kód elengedve
        gun = match_offer(OfferIn("CYMA M24 CM.702 sniper rifle", price_huf=45000), cat)
        self.assertEqual((gun.method, gun.new_product["model_code_norm"]), ("new", "CM702"))
        cat.add_product(Product(400, 1, "CYMA M24 CM.702 Sniper Rifle", "CM702"))
        self.assertEqual(match_offer(OfferIn("CYMA CM.702 M24 Black", price_huf=47000), cat).product_id, 400)
        for t, p in [("Odlehčený hybridní píst pro pušku CYMA M24 CM.702", 2800),
                     ("AIRSOFTPRO ACÉL HENGER CYMA CM.702 M24-HEZ (12773)", 25500),
                     ("Upgrade set pro CYMA M24 CM.702", 19000)]:
            r = match_offer(OfferIn(t, price_huf=p), cat)
            self.assertNotEqual(r.product_id, 400, t)
            self.assertNotEqual(r.method, "code", t)


class TestSpecGuard(unittest.TestCase):
    """Eltérő jellemző (BB-súly, gáz, rugó...) = külön termék."""
    def setUp(self):
        self.cat = Catalog({norm_alias("Specna Arms"): 2, norm_alias("Nimrod"): 3},
                           {2: ("specna-arms", "Specna Arms"), 3: ("nimrod", "Nimrod")})
        self.cat.add_product(Product(60, 2, "Specna Arms FLEX precision BBs 0.20g 1kg", None))
        self.cat.add_product(Product(61, 3, "Nimrod Green Gas 500ml", None))

    def test_bb_weights_stay_apart(self):
        r = match_offer(OfferIn("Specna Arms FLEX™ precision BBs 0.28g - 1kg", price_huf=2300), self.cat)
        self.assertNotEqual(r.product_id, 60)

    def test_same_bb_matches(self):
        r = match_offer(OfferIn("Specna Arms FLEX precision BBs 0.20g - 1kg", price_huf=2200), self.cat)
        self.assertEqual(r.product_id, 60)

    def test_gas_volume_and_type(self):
        self.assertNotEqual(match_offer(OfferIn("Nimrod Green Gas 1000ml", price_huf=4000), self.cat).product_id, 61)
        self.assertNotEqual(match_offer(OfferIn("Nimrod Top Gas 500ml", price_huf=3000), self.cat).product_id, 61)

    def test_learned_spec_blocks_next(self):
        self.cat.add_product(Product(62, 2, "Specna Arms FLEX precision BBs", None))     # névben nincs súly
        self.cat.learn(62, {"bb_g": "0.2"})
        r = match_offer(OfferIn("Specna Arms FLEX precision BBs 0.32g", price_huf=2500), self.cat)
        self.assertNotEqual(r.product_id, 62)
