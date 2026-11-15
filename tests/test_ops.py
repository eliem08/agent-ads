import contextlib
import io
import json
import os
import tempfile
import unittest
from datetime import date, timedelta

from agent_ads.__main__ import main
from agent_ads.ops import load, pairs, save


def run(*argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
        code = main(list(argv))
    return code, out.getvalue()


class AdsOpsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, "ads.json")
        self.s = ["--store", self.path]
        base = ["--intents", "buy", "--keywords", "running", "shoes", "--daily-budget", "20"]
        self.ok("campaign-add", "Acme", "Acme Trail Shoe", *base, "--bid", "1.2", "--attr", "price=120")
        self.ok("campaign-add", "Zoom", "Zoom Road Shoe", *base, "--bid", "0.9", "--attr", "price=200")

    def tearDown(self):
        self.tmp.cleanup()

    def ok(self, *argv):
        code, out = run(*argv, *self.s)
        self.assertEqual(code, 0, out)
        return out

    def serve(self, *extra):
        return json.loads(self.ok("serve", "--query", "running shoes", "--intent", "buy", *extra))

    def test_serve_click_convert_bills_once_and_survives_restarts(self):
        res = self.serve("--organic", "Indie Shoe")
        self.assertEqual([w["offer"] for w in res["sponsored"]], ["Acme Trail Shoe", "Zoom Road Shoe"])
        self.assertTrue(res["disclosure"])
        self.assertEqual(res["organic"], ["Indie Shoe"])
        imp = res["sponsored"][0]["impression_id"]
        first = self.ok("click", imp)
        self.assertEqual(self.ok("click", imp), "billed $0.00\n")  # a repeat click is never billed
        self.ok("convert", imp, "--value", "120")
        self.assertEqual(run("convert", imp, "--value", "120", *self.s)[0], 1)
        srv = load(self.path)
        self.assertEqual(f"billed ${srv.billed['C1']:.2f}\n", first)
        self.assertEqual(srv.campaigns["C1"].conversions, 1)

    def test_user_constraints_and_pause_remove_campaigns(self):
        offers = [w["offer"] for w in self.serve("--constraint", "max_price=150")["sponsored"]]
        self.assertEqual(offers, ["Acme Trail Shoe"])
        self.ok("campaign-pause", "C1")
        self.assertEqual([w["offer"] for w in self.serve()["sponsored"]], ["Zoom Road Shoe"])
        self.assertIn("(paused)", self.ok("report"))

    def test_new_day_refills_budgets_but_keeps_the_lifetime_bill(self):
        imp = self.serve()["sponsored"][0]["impression_id"]
        self.ok("click", imp)
        srv = load(self.path)
        billed = srv.billed["C1"]
        self.assertGreater(srv.campaigns["C1"].spent, 0)
        tomorrow = load(self.path, today=date.today() + timedelta(days=1))
        self.assertEqual((tomorrow.campaigns["C1"].spent, tomorrow.billed["C1"]), (0.0, billed))
        old = load(self.path, today=date.today() + timedelta(days=30))
        self.assertEqual(old.impressions, {})  # expired impressions are dropped
        save(old, self.path)

    def test_bad_input_is_refused(self):
        self.assertEqual(pairs(["price=120", "brand=acme"], "x"), {"price": 120.0, "brand": "acme"})
        for argv in (
            ["click", "I99"],
            ["campaign-pause", "C9"],
            ["serve", "--query", "q", "--intent", "buy", "--constraint", "nonsense"],
            ["campaign-add", "A", "o", "--intents", "buy", "--keywords", "k", "--bid", "-1", "--daily-budget", "5"],
        ):
            with self.subTest(argv=argv):
                self.assertEqual(run(*argv, *self.s)[0], 1)


if __name__ == "__main__":
    unittest.main()
