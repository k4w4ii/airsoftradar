import json
import tempfile
import unittest
from pathlib import Path

import facets
from facets import attributes as a


class TestFacets(unittest.TestCase):
    def test_values(self):
        self.assertEqual(a("acc_ammo", "Specna Arms BB 0.25g 4000pcs bio"), {"bbw=0.25", "bbt=bio", "bbq=l"})
        self.assertEqual(a("acc_ammo", "Nuprol 2.0 Red gas 500ml"), {"gas=high", "gml=small"})
        self.assertEqual(a("acc_ammo", "12g CO2 cartridges box of 5"), {"gas=co2_12"})
        self.assertEqual(a("acc_power", "Specna Arms LiPo 7.4V 1200mAh 20C T-Connect"),
                         {"pk=battery", "chem=lipo", "volt=7.4", "conn=deans"})
        self.assertEqual(a("acc_power", "iMAX B6 universal charger"), {"pk=charger", "chg=universal"})
        self.assertEqual(a("acc_optics", "Vector Optics 3-9x40 scope"), {"ot=scope"})
        self.assertEqual(a("acc_optics", "Killflash for T1"), {"ot=mount"})
        self.assertEqual(a("part_internal", "Specna Arms V2 gearbox ETU"), {"pt=gearbox"})
        self.assertEqual(a("part_hopup", "Maple Leaf Hop Up Rubber 60°"), {"pt=bucking"})
        self.assertEqual(a("rifle", "Specna Arms SA-E07"), {"mdl=m4"})

    def test_models(self):
        self.assertEqual(a("lmg", "Cybergun FN Herstal M249 Para GBB Machine Gun"), {"mdl=m249"})
        self.assertEqual(a("lmg", "A&K MP5 something"), set())                   # MP5 nem géppuska-modell
        self.assertEqual(a("smg", "Maruyama MP-IX MP9 DX GBB"), {"mdl=mp9"})
        self.assertEqual(a("smg", "S&T PPSH-41 WWII Submachine Gun"), {"mdl=ppsh", "mdl=ww2"})
        self.assertEqual(a("shotgun", "CYMA M1014 / M4 Super 90 shotgun"), {"mdl=m1014"})   # nem M4 karabély
        self.assertEqual(a("pistol", "WE Glock 18C GBB"), {"mdl=glock"})
        self.assertEqual(a("rifle", "CYMA CM.040 AKM"), {"mdl=ak"})
        self.assertEqual(a("sniper", "Well MB4401 L96"), {"mdl=l96"})

    def test_values_are_declared(self):
        declared = {f"{k}={v[0]}" for k, d in facets.DIMS.items() for v in d["values"]}
        for cat, t in [("acc_ammo", "BLS 0,28g BIO 1kg tracer"), ("acc_power", "NiMH 9.6V mini Tamiya"), ("grenade", "Smoke grenade"), ("lmg", "M249 minimi"), ("custom_rifle", "HPA M4 Polarstar")]:
            self.assertTrue(a(cat, t) <= declared, a(cat, t) - declared)

    def test_web_json_up_to_date(self):
        with tempfile.TemporaryDirectory() as d:
            fresh = json.loads(facets.gen_facets_json(Path(d) / "f.json").read_text(encoding="utf-8"))
        current = json.loads((Path(__file__).parent.parent / "web" / "lib" / "facets.json").read_text(encoding="utf-8"))
        self.assertEqual(fresh, current, "futtasd: python scraper/facets.py")


if __name__ == "__main__":
    unittest.main()
