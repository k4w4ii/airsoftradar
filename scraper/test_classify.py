"""A Python-besoroló (classify.py) ugyanazt adja, mint a Postgres airsoft_category (59 valós cím)."""
import json
import unittest
from pathlib import Path

import classify


class TestClassify(unittest.TestCase):
    def test_cases(self):
        cases = json.loads((Path(__file__).parent / "classify_cases.json").read_text())
        bad = [(t, e, classify.category(t, u, p)) for t, u, p, e in cases if classify.category(t, u, p) != e]
        self.assertEqual(bad, [])

    def test_platforms(self):
        self.assertEqual(classify.platforms("Magazine for M4/M16 AEG midcap"), ["m4"])
        self.assertEqual(classify.platforms("Gearbox V2 complete for M4"), ["m4", "gb_v2"])
        self.assertEqual(classify.group("acc_mag"), "acc")
        self.assertEqual(classify.group("sniper"), "weapons")


if __name__ == "__main__":
    unittest.main()
