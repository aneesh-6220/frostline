"""Regression tests for the final qualification pass (2026-11-15).

* Independent reproduction: scripts/independent_verification.py re-derives the Giovanni seasonal trends, their BH q-values and
  the Dettah opening-day trends from the raw files with code that shares nothing with the production engine.
* A NASA POWER retrieval error belongs to the point it was raised for; selecting another point never shows it.
* The landing page and guided demo report the Giovanni record as a whole family (supported AND unresolved seasons), from live numbers.
No test calls the network.
"""
import os
import subprocess
import sys
import tempfile
import unittest
import warnings

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
for p in (os.path.join(ROOT, "UI"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)
APP = os.path.join(ROOT, "UI", "frostline_app.py")
warnings.filterwarnings("ignore")

from streamlit.testing.v1 import AppTest  # noqa: E402

from frostline import data, fmt, giovanni as gv, power_api as pa  # noqa: E402
from frostline.views import atlas  # noqa: E402

DS = data.load_dataset()


def _text(at) -> str:
    return " ".join(m.value for m in at.markdown)


class IndependentReproduction(unittest.TestCase):
    def test_independent_script_agrees_with_the_app(self):
        r = subprocess.run([sys.executable, "-I", os.path.join(ROOT, "scripts", "independent_verification.py")], capture_output=True, text=True, timeout=300)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("all independent values agree with the app", r.stdout)
        self.assertIn("months 552, missing 0", r.stdout)

    def test_independent_code_does_not_import_the_production_engine(self):
        with open(os.path.join(ROOT, "scripts", "independent_verification.py"), encoding="utf-8") as fh:
            src = fh.read()
        for mod in ("northlink_metrics", "northlink_stats", "northlink_recompute", "frostline", "theilslopes", "scipy"):
            self.assertNotRegex(src, rf"^\s*(import|from)\s+[^\n]*{mod}", mod)


class PowerErrorIsScopedToItsPoint(unittest.TestCase):
    def test_error_for(self):
        self.assertEqual(atlas.error_for(((64.0, -120.0), "down"), (64.0, -120.0)), "down")
        self.assertIsNone(atlas.error_for(((64.0, -120.0), "down"), (65.0, -121.0)))
        self.assertIsNone(atlas.error_for(None, (64.0, -120.0)))
        self.assertIsNone(atlas.error_for("legacy string", (64.0, -120.0)))

    def test_failed_point_error_does_not_follow_the_user_to_a_new_point(self):
        pa.clear_memory_cache()
        os.environ["FROSTLINE_CACHE_DIR"] = tempfile.mkdtemp()
        real = pa._http_get_json
        pa._http_get_json = lambda url: (_ for _ in ()).throw(pa.PowerError("NASA POWER could not be reached (URLError)."))
        try:
            at = AppTest.from_file(APP, default_timeout=90)
            at.session_state["start_view"] = "atlas"
            at.session_state["xp_point"] = (64.0, -120.0)
            at.run()
            at.button(key="xp_fetch").click().run()
            self.assertIn("could not be reached", " ".join(e.value for e in at.error))
            at.session_state["xp_point"] = (66.0, -128.0)
            at.run()
            self.assertEqual(len(at.exception), 0)
            self.assertNotIn("could not be reached", " ".join(e.value for e in at.error))
            self.assertIn("Retrieve NASA POWER daily data for this point", " ".join(b.label for b in at.button))
        finally:
            pa._http_get_json = real
            os.environ.pop("FROSTLINE_CACHE_DIR", None)
            pa.clear_memory_cache()


class GiovanniOnLandingAndDemo(unittest.TestCase):
    def setUp(self):
        self.loc = gv.locations(DS)[0]
        self.full = {s: gv.trend(DS, self.loc, s) for s in gv.SEASON_ORDER}

    def test_landing_reports_the_whole_family_from_live_numbers(self):
        at = AppTest.from_file(APP, default_timeout=90).run()
        self.assertEqual(len(at.exception), 0)
        text = _text(at)
        son, octdec = self.full["SON"], self.full["octdec_mean_c"]
        self.assertIn(fmt.num(son.slope_per_decade, 2, True), text)
        self.assertIn(f"q = {fmt.pval(son.q)}", text)
        self.assertIn(f"q = {fmt.pval(octdec.q)}", text)          # the unresolved early-winter result is shown beside the supported one
        self.assertIn("1 of the 7 seasonal tests", text)
        self.assertIn("1980 to 2025", text)

    def test_demo_stage_four_adds_the_long_record_only_where_it_exists(self):
        at = AppTest.from_file(APP, default_timeout=90)
        at.session_state["start_view"] = "demo"
        at.session_state["demo_step"] = 3
        at.run()
        self.assertEqual(len(at.exception), 0)
        text = _text(at)
        self.assertIn("The longer NASA record", text)
        self.assertIn("1 of 7 supported", text)
        self.assertIn(f"q = {fmt.pval(self.full['octdec_mean_c'].q)}", text)
        at.session_state["loc"] = "aklavik_delta"
        at.run()
        self.assertEqual(len(at.exception), 0)
        self.assertNotIn("The longer NASA record", _text(at))


if __name__ == "__main__":
    unittest.main()
