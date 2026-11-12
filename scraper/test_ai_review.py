"""AI-ellenőrzés: kérés összeállítása, válasz feldolgozása, becslés, és hogy a summary/minőség-őr helyesen használja."""
import io
import json
import unittest
import urllib.error

import ai_review
import quality


def _p(i, name, cat="rifle", price=20000):
    return {"id": i, "slug": f"s{i}", "name": name, "manufacturer": "Cyma", "category": cat, "price": price}


class FakeResp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class TestAiReview(unittest.TestCase):
    def test_candidates_order_and_cache(self):
        prods = [_p(1, "Bag", "acc_gear", 5000), _p(2, "Gun", "rifle", 90000), _p(3, "Pad", "rifle", 7000), _p(4, "X", "other")]
        todo = ai_review.candidates(prods, {"s2": "Gun"})            # s2 már kész, ugyanazzal a névvel
        self.assertEqual([p["id"] for p in todo], [3, 4, 1])
        todo = ai_review.candidates(prods, {"s2": "Gun old name"})   # átnevezték: újra kell
        self.assertIn(2, [p["id"] for p in todo])

    def test_request_body(self):
        body = ai_review.request_body([_p(1, "Invader Gear Padded Rifle Carrier")])
        self.assertIn("SOHA NEM FEGYVER", body["systemInstruction"]["parts"][0]["text"])
        self.assertIn('"i": 0', body["contents"][0]["parts"][0]["text"])
        enum = body["generationConfig"]["responseSchema"]["items"]["properties"]["c"]["enum"]
        self.assertIn("acc_gear", enum)
        self.assertNotIn("custom_rifle", enum)
        self.assertNotIn("thinkingConfig", ai_review.request_body([_p(1, "x")], thinking=False)["generationConfig"])

    def test_parse(self):
        batch = [_p(0, "a"), _p(1, "b")]
        self.assertEqual(ai_review.parse('[{"i":0,"c":"acc_gear"},{"i":1,"c":"nonsense"},{"i":7,"c":"rifle"}]', batch),
                         {0: "acc_gear"})
        self.assertEqual(ai_review.parse("nem json", batch), {})

    def test_call(self):
        batch = [_p(0, "Invader Gear Padded Rifle Carrier")]
        resp = {"candidates": [{"content": {"parts": [{"text": '[{"i":0,"c":"acc_gear"}]'}]}}],
                "usageMetadata": {"promptTokenCount": 1000, "candidatesTokenCount": 10}}
        sent = []

        def opener(req, timeout=0):
            sent.append(json.loads(req.data))
            return FakeResp(json.dumps(resp).encode())
        res, usage = ai_review.call("KEY", batch, opener)
        self.assertEqual(res, {0: "acc_gear"})
        self.assertEqual(usage["promptTokenCount"], 1000)

    def test_call_quota(self):
        def opener(req, timeout=0):
            raise urllib.error.HTTPError(req.full_url, 429, "x", {}, io.BytesIO(b"GenerateRequestsPerDay quota"))
        with self.assertRaises(ai_review.QuotaExceeded):
            ai_review.call("KEY", [_p(0, "a")], opener)

    def test_estimate(self):
        est = ai_review.estimate([_p(i, "Specna Arms SA-E20 EDGE HAL ETU AEG") for i in range(250)], 100)
        self.assertEqual(est["keres"], 3)
        self.assertGreater(est["usd"], 0)
        self.assertLess(est["usd"], 0.1)

    def test_fix_category_uses_ai(self):
        clean = [{"id": 1, "price_huf": 16000}]
        fixes = {"kategoria": {}, "ai": {"bag": "acc_gear", "cheap": "rifle"}}
        self.assertEqual(quality.fix_category("rifle", {"slug": "bag", "name": "Padded Rifle Carrier"}, clean, {1: "rifle"}, fixes),
                         ("acc_gear", quality.AI_WHY))
        # az AI sem tehet fegyverbe egy 2000 Ft-os tételt
        cat, why = quality.fix_category("other", {"slug": "cheap", "name": "x"}, [{"id": 1, "price_huf": 2000}], {1: "other"}, fixes)
        self.assertEqual(cat, "other")
        # kézi javítás erősebb
        fixes["kategoria"]["bag"] = "other"
        self.assertEqual(quality.fix_category("rifle", {"slug": "bag", "name": "x"}, clean, {1: "rifle"}, fixes)[1], "kézi javítás")


if __name__ == "__main__":
    unittest.main()
