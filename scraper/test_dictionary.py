import json
import tempfile
import unittest
from pathlib import Path

import dictionary
from dictionary import translate
from names import clean_name


class TestDictionary(unittest.TestCase):
    def test_translate_keeps_case_and_unknown_words(self):
        self.assertEqual(translate("Retro Arms Šroub pažbičky M4 2ks"), "Retro Arms Screw stock M4 2pcs")
        self.assertEqual(translate("CYMA M14 rugószett"), "CYMA M14 spring set")
        self.assertEqual(translate("SHS M4 V2 TŰZKAPCSOLÓ HÁTRA"), "SHS M4 V2 FIRE SELECTOR REAR")

    def test_filler_words_removed(self):
        self.assertNotIn("Airsoftpláza", translate("NIMROD RED GÁZ SZILIKONNAL 500ML - Airsoftpláza"))

    def test_ambiguous_words_only_lowercase(self):
        self.assertEqual(translate("VSR-10 Pro Sniper"), "VSR-10 Pro Sniper")
        self.assertEqual(translate("Zásobník pro AK74"), "Magazine for AK74")

    def test_keep_hungarian(self):
        self.assertEqual(translate("CYMA M14 rugószett", keep=dictionary.HU), "CYMA M14 rugószett")

    def test_clean_name_translates_and_is_idempotent(self):
        n = clean_name("Tvrzená vnitřní hlaveň GUREN 1 6,03 AEG - 363 mm", "Guren")
        self.assertEqual(n, "Guren Hardened inner Barrel 1 6,03 AEG 363 mm")
        self.assertEqual(clean_name(n, "Guren"), n)

    def test_dictionary_files_are_clean(self):
        for f in dictionary.DIR.glob("*.txt"):
            for i, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
                if line and not line.startswith("#"):
                    self.assertIn("=", line, f"{f.name}:{i}")
                    self.assertEqual(line.split("=", 1)[0], line.split("=", 1)[0].strip().lower(), f"{f.name}:{i}")

    def test_web_json_up_to_date(self):
        with tempfile.TemporaryDirectory() as d:
            fresh = dictionary.gen_dictionary_json(Path(d) / "x.json").read_text(encoding="utf-8")
        current = (Path(__file__).parent.parent / "web" / "lib" / "dictionary.json").read_text(encoding="utf-8")
        self.assertEqual(json.loads(fresh), json.loads(current), "futtasd: python scraper/dictionary.py")


if __name__ == "__main__":
    unittest.main()
