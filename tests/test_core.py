import unittest

from agent_ads import AdServer, relevance


class Tests(unittest.TestCase):
    def setUp(self):
        self.s = AdServer()
        self.a = self.s.add("A", "Hotel A", ["hotel"], ["lisbon", "hotel"], 2.0, 10, 0.8, price=150)
        self.b = self.s.add("B", "Hotel B", ["hotel"], ["lisbon", "hotel"], 1.0, 10, 0.8, price=120)
        self.lux = self.s.add("L", "Luxury", ["hotel"], ["lisbon", "hotel"], 9.0, 10, 0.9, price=500)
        self.off = self.s.add("F", "Flights", ["flight"], ["flights"], 50.0, 100, 1.0)

    def test_relevance_gate(self):
        self.assertEqual(relevance(self.off, "hotel in lisbon", "hotel"), 0.0)
        res = self.s.auction("hotel in lisbon", "hotel", {"max_price": 200})
        offers = [w["offer"] for w in res["sponsored"]]
        self.assertEqual(offers, ["Hotel A", "Hotel B"])  # luxury filtered by constraint, flights by intent
        self.assertTrue(all(w["sponsored"] and w["label"].startswith("Sponsored") for w in res["sponsored"]))

    def test_second_price(self):
        res = self.s.auction("hotel in lisbon", "hotel", {"max_price": 200})
        first, second = res["sponsored"]
        self.assertLessEqual(first["cpc"], 2.0)
        self.assertAlmostEqual(first["cpc"], 1.01)
        self.assertEqual(second["cpc"], 0.10)

    def test_budget_and_attribution(self):
        self.a.daily_budget = 1.05
        res = self.s.auction("hotel lisbon", "hotel", {"max_price": 200})
        imp = res["sponsored"][0]["impression_id"]
        self.s.click(imp)
        with self.assertRaises(ValueError):
            self.s.convert(res["sponsored"][1]["impression_id"], 10)
        self.s.convert(imp, 300)
        res2 = self.s.auction("hotel lisbon", "hotel", {"max_price": 200})
        self.assertNotIn("Hotel A", [w["offer"] for w in res2["sponsored"]])
        row = next(r for r in self.s.report() if r["advertiser"] == "A")
        self.assertEqual(row["conversions"], 1)

    def test_organic_dedupe(self):
        res = self.s.auction("hotel lisbon", "hotel", {"max_price": 200}, organic=["Hotel A", "Other"])
        self.assertEqual(res["organic"], ["Other"])


if __name__ == "__main__":
    unittest.main()
