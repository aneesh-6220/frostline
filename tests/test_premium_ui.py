"""Regression tests for the premium UI refinement (docs/FROSTLINE_FINAL_UX_AUDIT.md).

Covers presentation guarantees that the redesign introduced: every view stays reachable from the grouped
navigation, the summary-level result keeps its multiplicity-adjusted q visible while the full statistical
record is collapsed, the map keeps its tile attribution and legend, and the exploratory map chart uses the
same encoding as every other trend chart.

Run: python3 -I -m unittest discover -s tests
"""
import os
import re
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(ROOT, "UI"))

from streamlit.testing.v1 import AppTest  # noqa: E402

from frostline import charts as ch, data  # noqa: E402

APP = os.path.join(ROOT, "UI", "frostline_app.py")
ALL_VIEWS = {"observatory", "demo", "atlas", "questions", "detective", "compare", "giovanni", "corridor", "evidence", "brief", "methods"}


def run(view: str, state: dict | None = None) -> AppTest:
    at = AppTest.from_file(APP, default_timeout=90)
    at.session_state["start_view"] = view
    for k, v in (state or {}).items():
        at.session_state[k] = v
    at.run()
    return at


def markdown(at) -> str:
    return "\n".join(m.value for m in at.markdown)


class PremiumUI(unittest.TestCase):
    def test_navigation_groups_cover_every_view(self):
        src = open(APP, encoding="utf-8").read()
        rows = re.findall(r'\("(\w+)", "[^"]+", \w+, ":material/\w+:", "(\w*)"\)', src)
        self.assertEqual({k for k, _ in rows}, ALL_VIEWS)
        groups = {g for _, g in rows}
        self.assertLessEqual(groups, {"", "Explore", "Understand"})
        top = [k for k, g in rows if g == ""]
        self.assertLessEqual(len(top), 5, "the top-level navigation must stay short enough to fit a laptop header")
        for k in ("observatory", "atlas", "brief"):
            self.assertIn(k, top, f"{k} belongs on the primary path")

    def test_summary_keeps_q_visible_with_record_collapsed(self):
        at = run("detective")
        self.assertEqual(len(at.exception), 0)
        exp = [e for e in at.expander if e.label.startswith("Full statistical record")]
        self.assertTrue(exp)
        self.assertFalse(exp[0].proto.expanded)
        self.assertRegex(markdown(at), r"q = \d\.\d{3} across \d+ tests")

    def test_landing_journey(self):
        at = run("observatory")
        self.assertEqual(len(at.exception), 0)
        md = markdown(at)
        self.assertIn("fl-journey", md)
        for step in ("Choose a place", "Retrieve NASA data", "Measure the trend", "Weigh the evidence", "Export a brief"):
            self.assertIn(step, md)

    def test_map_keeps_attribution_and_legend(self):
        from frostline.views import atlas
        ds = data.load_dataset()
        page = atlas.build_map(ds, "dettah_bay").get_root().render()
        self.assertIn("leaflet-control-attribution", page)
        self.assertIn("Esri", page)
        self.assertNotIn("display:none", re.search(r"\.leaflet-control-attribution\{[^}]*\}", atlas.MAP_CSS).group(0))
        self.assertIn("fl-legend", markdown(run("atlas")))

    def test_exploratory_chart_matches_trend_encoding(self):
        from frostline.views import atlas
        src = open(atlas.__file__, encoding="utf-8").read()
        body = src[src.index("def result_chart"):src.index("def _curated_panel")]
        self.assertIn("ch.C_PRIMARY", body)      # observations in the primary series colour
        self.assertIn("ch.TREND", body)          # trend line in the shared trend colour
        self.assertEqual(ch.TREND, "#E7ECF2")


if __name__ == "__main__":
    unittest.main()
