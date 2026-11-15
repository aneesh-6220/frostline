"""Acceptance tests for the web API that serves the React frontend (UI/api).

The API must expose exactly what the frostline package computes: the same findings, the same Evidence Brief, and
figures whose data are unchanged by the light-theme recolouring. Skipped when FastAPI is not installed.
"""
import json
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "UI"))

try:
    from fastapi.testclient import TestClient
    HAVE_FASTAPI = True
except ImportError:  # pragma: no cover
    HAVE_FASTAPI = False


@unittest.skipUnless(HAVE_FASTAPI, "fastapi not installed (pip install -r UI/api/requirements.txt)")
class WebApiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from UI.api.server import app
        from frostline import analysis as an
        from frostline import brief, charts, data
        cls.c = TestClient(app)
        cls.ds = data.load_dataset()
        cls.an, cls.brief, cls.charts = an, brief, charts

    def get(self, url):
        r = self.c.get(url)
        self.assertEqual(r.status_code, 200, f"{url}: {r.text[:300]}")
        return r

    def test_every_endpoint_answers(self):
        for url in ["/api/health", "/api/bootstrap", "/api/observatory", "/api/investigation?loc=dettah_bay&var=fdd_octdec",
                    "/api/investigation?loc=aklavik_delta&var=thaw_days_janmar", "/api/status?loc=dettah_bay&var=open_day&first=1998&last=2024",
                    "/api/questions/roads?loc=aklavik_delta", "/api/compare?var=mean_janmar_c", "/api/corridor/dettah_bay",
                    "/api/corridor/dettah_bay/road?measure=close_day", "/api/corridor/aklavik_delta/environment?var=mean_octdec_c",
                    "/api/corridor/dettah_bay/timeline?year=2010", "/api/corridor/dettah_bay/associations", "/api/routes?metric=open_day&window=2001",
                    "/api/corridor/aklavik_delta/conclusion", "/api/demo/road/dettah_bay", "/api/evidence?loc=dettah_bay&var=open_day",
                    "/api/evidence/disagreement", "/api/evidence/multiple-testing", "/api/methods"]:
            body = self.get(url).json()
            json.dumps(body, allow_nan=False)   # strict JSON: no NaN reaches the browser

    def test_finding_matches_the_package(self):
        for loc, var, a, b in [("dettah_bay", "open_day", 1993, 2024), ("dettah_bay", "fdd_octdec", 2001, 2024), ("aklavik_delta", "mean_janmar_c", 2004, 2019)]:
            f = self.an.trend(self.ds, loc, var, a, b)
            got = self.get(f"/api/investigation?loc={loc}&var={var}&first={a}&last={b}").json()["finding"]
            self.assertEqual(got["state"], f.state)
            self.assertEqual(got["n"], f.n)
            self.assertAlmostEqual(got["slope"], f.slope)
            self.assertAlmostEqual(got["ci_low"], f.ci_low)
            self.assertEqual(got["sentence"], f.sentence)

    def test_headline_numbers(self):
        o = self.get("/api/observatory").json()
        self.assertEqual(o["metrics"][0]["value"], "+9.0")
        self.assertEqual(o["metrics"][3]["value"], "0 of 126")

    def test_window_rules(self):
        s = self.get("/api/status?loc=dettah_bay&var=open_day&first=1998&last=2024").json()
        self.assertEqual(s["state"], "exploratory")
        self.assertFalse(s["fixed"])
        s = self.get("/api/status?loc=dettah_bay&var=fdd_octdec&first=1900&last=2100").json()
        self.assertEqual((s["selection"]["first"], s["selection"]["last"]), (2001, 2024))   # clamped to the record
        self.assertEqual(self.c.get("/api/investigation?loc=deline&var=fdd_octdec").status_code, 422)
        self.assertEqual(self.c.get("/api/investigation?loc=dettah_bay&var=nope").status_code, 422)

    def test_brief_is_the_package_brief(self):
        b = self.brief.build(self.ds, "dettah_bay", "open_day", 1993, 2024)
        self.assertEqual(self.get("/api/brief?loc=dettah_bay&var=open_day&first=1993&last=2024&format=csv").text, b.csv)
        r = self.get("/api/brief?loc=dettah_bay&var=open_day&first=1993&last=2024&format=html&download=true")
        self.assertIn("attachment", r.headers["content-disposition"])

    def test_theme_changes_colours_only(self):
        f = self.an.trend(self.ds, "dettah_bay", "fdd_octdec", 2001, 2024)
        raw = json.loads(self.charts.trend_chart(self.ds, f).to_json())
        themed = self.get("/api/investigation?loc=dettah_bay&var=fdd_octdec").json()["chart"]
        self.assertEqual(len(raw["data"]), len(themed["data"]))
        for a, b in zip(raw["data"], themed["data"]):
            self.assertEqual(a.get("x"), b.get("x"))
            self.assertEqual(a.get("y"), b.get("y"))
            self.assertEqual(a.get("hovertemplate"), b.get("hovertemplate"))
        self.assertNotIn("#0B0E13", json.dumps(themed))   # no dark surface colour survives


if __name__ == "__main__":
    unittest.main()
