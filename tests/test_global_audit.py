"""Regression tests for the global-award audit repairs (docs/FINAL_GLOBAL_AWARD_AUDIT.md).

1. Every road-date result at a selection-biased location carries the selection caveat, and every fixed-window road result whose
   verdict differs between the two approved windows carries a window-sensitivity caveat (docs/APPROVED_FINDINGS.md B and C).
   Both reach the on-screen card, the HTML Evidence Brief and the JSON record.
2. The headline Dettah opening-day trend is reproduced from the raw NWT workbook with an independent Theil-Sen / Mann-Kendall
   implementation (no repository pipeline code), so the headline does not depend only on the pipeline that produced it.
3. The guided demo returns the presenter to the top of each stage, and the Atlas draws no line other than the Arctic Circle.

Run: python3 -I -m unittest discover -s tests
"""
import datetime as dt
import json
import math
import os
import sys
import unittest
import warnings

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
for p in (os.path.join(ROOT, "UI"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)
warnings.filterwarnings("ignore")

from scipy import stats  # noqa: E402
from streamlit.testing.v1 import AppTest  # noqa: E402

from frostline import analysis as an  # noqa: E402
from frostline import brief, data  # noqa: E402

DS = data.load_dataset()
APP = os.path.join(ROOT, "UI", "frostline_app.py")
SELECTION = "Selection caveat"
FRAGILE = "Window sensitivity"


def _has(f, prefix):
    return any(s.startswith(prefix) for s in f.extra_sentences)


class RoadCaveats(unittest.TestCase):
    def test_dettah_headline_carries_selection_and_window_caveats(self):
        f = an.trend(DS, "dettah_bay", "open_day", 1993, 2024)
        self.assertEqual(f.state, an.SUPPORTED)
        self.assertTrue(_has(f, SELECTION))
        self.assertTrue(_has(f, FRAGILE))
        fr = next(s for s in f.extra_sentences if s.startswith(FRAGILE))
        self.assertIn("2001/02 to 2024/25", fr)
        self.assertIn("does not survive correction", fr)
        self.assertIn("q = 0.085", fr)   # docs/APPROVED_FINDINGS.md section C

    def test_nasa_window_points_back_to_full_record(self):
        f = an.trend(DS, "dettah_bay", "open_day", 2001, 2024)
        self.assertEqual(f.state, an.UNRESOLVED)
        fr = next(s for s in f.extra_sentences if s.startswith(FRAGILE))
        self.assertIn("survives correction", fr)
        self.assertIn("1993/94 to 2024/25", fr)

    def test_selection_caveat_on_every_estimated_dettah_road_result(self):
        for vid in ("open_day", "close_day", "open_to_close_days"):
            for w in ((1993, 2024), (2001, 2024), (1996, 2024)):
                f = an.trend(DS, "dettah_bay", vid, *w)
                self.assertTrue(_has(f, SELECTION), (vid, w))

    def test_aklavik_supported_results_are_marked_fragile(self):
        for vid in ("open_day", "open_to_close_days"):
            f = an.trend(DS, "aklavik_delta", vid, 1993, 2024)
            self.assertEqual(f.state, an.SUPPORTED, vid)
            self.assertTrue(_has(f, FRAGILE), vid)
            self.assertFalse(_has(f, SELECTION), vid)   # Aklavik was not the selected case

    def test_consistent_verdicts_and_climate_results_carry_no_window_caveat(self):
        self.assertFalse(_has(an.trend(DS, "aklavik_delta", "close_day", 1993, 2024), FRAGILE))
        for loc in ("dettah_bay", "aklavik_delta"):
            f = an.trend(DS, loc, "fdd_octdec", 2001, 2024)
            self.assertEqual(f.extra_sentences, ())

    def test_caveats_reach_the_brief_html_and_json(self):
        b = brief.build(DS, "dettah_bay", "open_day", 1993, 2024, generated=dt.datetime(2026, 11, 15, 12, 0))
        self.assertIn("Selection caveat", b.html)
        self.assertIn("Window sensitivity", b.html)
        rec = json.loads(b.json)
        self.assertTrue(any(s.startswith(SELECTION) for s in rec["finding"]["extra_sentences"]))
        self.assertAlmostEqual(rec["finding"]["slope"], 9.0, places=3)


class IndependentHeadline(unittest.TestCase):
    """Dettah opening day from the raw workbook, with no repository analysis code."""

    @staticmethod
    def _mk_p(y):
        y = np.asarray(y, float)
        n = len(y)
        s = sum(np.sign(y[j] - y[i]) for i in range(n - 1) for j in range(i + 1, n))
        _, c = np.unique(y, return_counts=True)
        var = (n * (n - 1) * (2 * n + 5) - sum(t * (t - 1) * (2 * t + 5) for t in c)) / 18.0
        z = (s - 1) / math.sqrt(var) if s > 0 else (s + 1) / math.sqrt(var) if s < 0 else 0.0
        return 2 * (1 - stats.norm.cdf(abs(z)))

    def test_raw_workbook_reproduces_stored_headline(self):
        import openpyxl

        path = os.path.join(ROOT, "data", "raw", "roads", "NWT_Table108_Winter_Road_Opening_and_Closing_Dates_1993_94_to_2024.xlsx")
        ws = openpyxl.load_workbook(path, data_only=True)["Ice Roads"]
        header = [r for r in ws.iter_rows(min_row=1, max_row=6, values_only=True)][4]
        col = next(i for i, v in enumerate(header) if v and "Dettah" in str(v))
        years, days = [], []
        for r in ws.iter_rows(min_row=8, values_only=True):
            if r[0] and str(r[0])[:2] in ("19", "20") and isinstance(r[col], dt.datetime):
                y = int(str(r[0])[:4])
                years.append(y)
                days.append((r[col] - dt.datetime(y, 10, 1)).days)
        self.assertEqual((len(years), min(years), max(years)), (32, 1993, 2024))
        slope, _, lo, hi = stats.theilslopes(days, years, 0.95)
        f = an.trend(DS, "dettah_bay", "open_day", 1993, 2024)
        self.assertAlmostEqual(10 * slope, f.slope, places=3)
        self.assertAlmostEqual(10 * lo, f.ci_low, places=3)
        self.assertAlmostEqual(10 * hi, f.ci_high, places=3)
        self.assertAlmostEqual(self._mk_p(days), f.p, places=4)
        self.assertEqual(f.n, 32)


class DemoAndAtlas(unittest.TestCase):
    def test_demo_next_requests_scroll_to_top_and_renders(self):
        at = AppTest.from_file(APP, default_timeout=60)
        at.session_state["start_view"] = "demo"
        at.run()
        self.assertEqual(len(at.exception), 0)
        at.button(key="demo_next_0").click().run()
        self.assertEqual(len(at.exception), 0)
        self.assertEqual(at.session_state["demo_step"], 1)
        self.assertNotIn("demo_scroll_top", at.session_state)   # consumed by the stage render

    def test_atlas_has_no_invented_geometry(self):
        from frostline.views import atlas

        html = atlas.build_map(DS, "dettah_bay").get_root().render()
        for banned in ("L.polyline", "L.heatLayer", "L.imageOverlay", "L.geoJson", "L.geoJSON"):
            self.assertNotIn(banned, html)
        self.assertIn("server.arcgisonline.com", html)        # a real, attributed basemap; no generated imagery
        self.assertIn("OpenStreetMap", html)
        self.assertNotIn("cartocdn", html)                     # CARTO now serves an "API key required" tile without a key


if __name__ == "__main__":
    unittest.main()
