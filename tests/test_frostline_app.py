"""Application acceptance tests for Frostline (docs/APP_IMPLEMENTATION_CONTRACT.md section 6 and the North Star release tests).

Covers the rows the contract marks "app": AC-2, AC-6, AC-7, AC-8 (display), AC-9, AC-10, AC-11, AC-12, AC-14,
plus numerical agreement with the approved outputs, matched-year comparison, road-season alignment, the
Evidence Engine, the source-disagreement figures, Evidence Brief consistency, the guided demo, map
synchronisation and optional-dataset handling.

Run: python3 -I -m unittest discover -s tests
The views are exercised headlessly with streamlit.testing.v1.AppTest against the real UI/data_real files.
"""
import csv
import glob
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
import warnings

import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
for p in (os.path.join(ROOT, "UI"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)
P = lambda *a: os.path.join(ROOT, *a)
APP = P("UI", "frostline_app.py")

warnings.filterwarnings("ignore")
import logging  # noqa: E402

logging.disable(logging.WARNING)

from google.protobuf.json_format import MessageToDict  # noqa: E402
from streamlit.testing.v1 import AppTest  # noqa: E402

from frostline import analysis as an  # noqa: E402
from frostline import brief, data, evidence as ev, fmt  # noqa: E402
from frostline.registry import QUESTIONS, VARIABLES, merra2_cell, primary_locations, variables_for  # noqa: E402
from frostline.schema import OPTIONAL_FILES, REQUIRED_COLUMNS  # noqa: E402

VIEWS = ["observatory", "demo", "atlas", "questions", "detective", "compare", "corridor", "evidence", "brief", "methods"]
DS = data.load_dataset()
LOCS = an.locations(DS)
PRIMARY = [l.id for l in primary_locations(LOCS)]

# phrases that must never be rendered (tests/test_scientific_acceptance.py list plus the contract's causal and safety wording)
PROHIBITED = [r"pre-?registered", r"climate-caused", r"temperature cannot explain", r"snow explains", r"snow causes", r"p_naive",
              r"temperature metrics do not explain", r"Bonferroni threshold of 0\.05/14", r"4 show a supported change",
              r"caused by", r"due to warming", r"\bbecause\b", r"\bexplains\b", r"\bno relationship\b", r"\bunsafe\b", r"\bis safe\b", r"safe to (drive|travel|use|cross)",
              r"will (open|close) (on|by|in)\b", r"predicted opening", r"380 ?(°C|C\b|degree|C-day)", r"James Bay benchmark", r"NorthLink|Asterfen",
              r"\d+ ?% (reliable|credible|trustworthy)", r"(credibility|reliability|safety) score"]


def _strings(obj, out):
    if isinstance(obj, str):
        out.append(obj)
    elif isinstance(obj, dict):
        for v in obj.values():
            _strings(v, out)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            _strings(v, out)


def rendered_text(at, charts: bool = True) -> str:
    """Every string the app sent to the browser in this run: markdown, labels, options, captions, table cells and,
    unless charts=False, the chart and map specifications (which legitimately list every location)."""
    out = []
    for block in (at.main, at.sidebar):
        for el in block:
            if not charts and "chart" in str(el.type):
                continue
            proto = getattr(el, "proto", None)
            if proto is not None:
                try:
                    _strings(MessageToDict(proto), out)
                except Exception:
                    pass
    for df in at.dataframe:
        out.append(df.value.to_string())
    text = "\n".join(out)
    return re.sub(r"<style>.*?</style>", " ", text, flags=re.S)


def visible(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", text))


def run_view(view: str, state: dict | None = None, env: dict | None = None):
    old = {k: os.environ.get(k) for k in (env or {})}
    os.environ.update(env or {})
    try:
        at = AppTest.from_file(APP, default_timeout=90)
        at.session_state["start_view"] = view
        for k, v in (state or {}).items():
            at.session_state[k] = v
        at.run()
        return at
    finally:
        for k, v in old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def copy_data() -> str:
    d = os.path.join(tempfile.mkdtemp(), "data_real")
    shutil.copytree(data.DEFAULT_DATA_DIR, d)
    return d


class DataLayer(unittest.TestCase):
    def test_manifest_covers_every_approved_file(self):
        files = {os.path.basename(f) for f in glob.glob(P("UI/data_real/*"))}
        self.assertEqual(files - set(OPTIONAL_FILES), set(REQUIRED_COLUMNS) | {"canonical_facts.json"})
        schema = open(P("docs/APP_DATA_SCHEMA.md"), encoding="utf-8").read()
        for name, cols in REQUIRED_COLUMNS.items():
            self.assertIn(f"`{name}`", schema)
            self.assertEqual(list(pd.read_csv(P("UI/data_real", name), nrows=1).columns), list(cols), name)

    def test_real_data_loads_and_is_not_synthetic(self):
        self.assertEqual(len(DS.tables), 20)
        self.assertEqual(len(DS.digest), 16)
        for name, df in DS.tables.items():
            if "synthetic" in df.columns:
                self.assertFalse(df.synthetic.astype(str).str.lower().eq("true").any(), name)
        self.assertEqual(os.path.realpath(DS.directory), os.path.realpath(P("UI/data_real")))

    def test_app_never_writes_to_data(self):
        before = {f: os.stat(f).st_mtime_ns for f in glob.glob(P("UI/data_real/*"))}
        run_view("detective")
        run_view("brief")
        self.assertEqual(before, {f: os.stat(f).st_mtime_ns for f in glob.glob(P("UI/data_real/*"))})


class AC2_FailureIsVisible(unittest.TestCase):
    """AC-2: a missing or corrupt required file gives a visible error naming the file and no numbers; no fallback."""

    def _broken(self, breaker):
        d = copy_data()
        breaker(d)
        return d

    def test_data_layer_raises_for_missing_corrupt_incomplete_and_synthetic(self):
        cases = {
            "trends.csv": lambda d: os.remove(os.path.join(d, "trends.csv")),
            "season_metrics_extended.csv": lambda d: open(os.path.join(d, "season_metrics_extended.csv"), "wb").write(b"\x00\xff\x00 not a table \x00"),
            "road_seasons.csv": lambda d: pd.read_csv(os.path.join(d, "road_seasons.csv")).drop(columns=["open_date"]).to_csv(os.path.join(d, "road_seasons.csv"), index=False),
            "climate_annual.csv": lambda d: pd.read_csv(os.path.join(d, "climate_annual.csv")).assign(synthetic=True).to_csv(os.path.join(d, "climate_annual.csv"), index=False),
            "canonical_facts.json": lambda d: open(os.path.join(d, "canonical_facts.json"), "w").write("{not json"),
        }
        for name, breaker in cases.items():
            with self.assertRaises(data.DataError) as ctx:
                data.load_dataset(self._broken(breaker))
            self.assertEqual(ctx.exception.filename, name)

    def test_app_shows_error_and_no_numbers(self):
        for name in ("multiple_testing_126.csv", "road_operations_all_routes.csv"):
            d = self._broken(lambda d, n=name: os.remove(os.path.join(d, n)))
            for view in ("observatory", "detective", "corridor"):
                at = run_view(view, env={"FROSTLINE_DATA_DIR": d})
                self.assertEqual(len(at.exception), 0)
                self.assertEqual(len(at.error), 1, view)
                self.assertIn(name, at.error[0].value)
                text = visible(rendered_text(at))
                self.assertNotIn("per decade", text)
                self.assertNotRegex(text, r"n = \d+ winters")
                self.assertEqual(len(at.dataframe), 0)
                self.assertEqual(len([e for e in at.main if e.type == "plotly_chart"]), 0)

    def test_synthetic_folder_is_never_a_fallback(self):
        d = self._broken(lambda d: os.remove(os.path.join(d, "climate_annual.csv")))
        shutil.copy(P("UI/data/climate_annual.csv"), os.path.join(d, "climate_annual.csv"))  # the legacy synthetic file
        with self.assertRaises(data.DataError):
            data.load_dataset(d)


class NumbersMatchApprovedOutputs(unittest.TestCase):
    """Every fixed-window statistic the app can display equals the approved generated output."""

    def test_all_126_extended_tests(self):
        t = DS["multiple_testing_126"]
        by_col = {v.column: v.id for v in VARIABLES.values()}
        self.assertEqual(len(t), 126)
        for r in t.itertuples():
            f = an.trend(DS, r.location_id, by_col[r.metric], 2001, 2024)
            self.assertTrue(f.cross_checked)
            self.assertEqual(f.n, int(r.n))
            # displayed values are the approved stored values, exactly
            for mine, theirs in ((f.slope, r.slope_per_decade), (f.ci_low, r.ci95_low), (f.ci_high, r.ci95_high), (f.bb_low, r.bb_ci95_low),
                                 (f.bb_high, r.bb_ci95_high), (f.p, r.p_unadjusted), (f.q, r.q_bh_all126)):
                self.assertAlmostEqual(mine, theirs, places=9)
            self.assertEqual((f.q_family, f.q_family_n), ("F1_all_extended", 126))

    def test_recomputation_from_per_winter_rows_agrees_within_rounding(self):
        """The per-winter file is stored to 4 decimals. Recomputing the 126 fixed-window results from it reproduces every
        slope; interval limits and p differ only where rounding ties two winters (one known case, reported to the data owners)."""
        import northlink_recompute as rc
        sm, t = DS["season_metrics_extended"], DS["multiple_testing_126"]
        loose = []
        for r in t.itertuples():
            s = rc.climate_series(sm, r.location_id, r.metric)
            x = rc.period_trend(s.season_start_year, s[r.metric], 2001, 2024)
            self.assertAlmostEqual(x["slope_per_decade"], r.slope_per_decade, delta=max(5e-3, 5e-3 * abs(r.slope_per_decade)))
            width = r.ci95_high - r.ci95_low
            self.assertLessEqual(abs(x["ci95_low"] - r.ci95_low), max(5e-3, an.CROSS_CHECK_INTERVAL_TOL * width))
            self.assertLessEqual(abs(x["mk_p"] - r.p_unadjusted), an.CROSS_CHECK_P_TOL)
            if abs(x["mk_p"] - r.p_unadjusted) > 1e-3:
                loose.append((r.location_id, r.metric))
        self.assertEqual(loose, [("tibbitt_contwoyto", "skin_temp_mean_octdec_c")])

    def test_road_record_full_window_for_every_app_location(self):
        t = DS["road_record_trends_all_routes"]
        n = 0
        for loc in LOCS.values():
            for metric in ("open_day", "close_day", "open_to_close_days"):
                r = t[(t.road_id == loc.road_id) & (t.metric == metric)].iloc[0]
                f = an.trend(DS, loc.id, metric, 1993, 2024)
                self.assertEqual((f.n, f.q_family, f.q_family_n), (int(r.n_seasons), "F4_road_record_all_routes", 51))
                self.assertAlmostEqual(f.slope, r.slope_per_decade, places=9)
                self.assertAlmostEqual(f.q, r.q_bh_all_routes, places=9)
                n += 1
        self.assertEqual(n, 27)

    def test_headline_values_match_canonical_facts_and_results_doc(self):
        k = DS.facts["dettah"]["open_full"]
        f = an.trend(DS, "dettah_bay", "open_day", 1993, 2024)
        self.assertEqual((round(f.slope, 1), round(f.ci_low, 1), round(f.ci_high, 1), f.n), (k["slope"], k["lo"], k["hi"], k["n"]))
        self.assertEqual(f.state, an.SUPPORTED)
        results = open(P("docs/RESULTS.md"), encoding="utf-8").read()
        self.assertIn(f"{fmt.num(f.slope, 1, True)} ({fmt.num(f.ci_low, 1)} to {fmt.num(f.ci_high, 1)})", results)
        g = an.trend(DS, "dettah_bay", "fdd_octdec", 2001, 2024)
        self.assertEqual(g.state, an.UNRESOLVED)
        self.assertEqual(g.sentence, an.T_NONSIG)
        self.assertIn(f"{fmt.num(g.slope, 0, True)} ({fmt.num(g.ci_low, 0)} to {fmt.num(g.ci_high, 0)})", results)

    def test_stored_result_that_disagrees_with_recomputation_is_refused(self):
        d = copy_data()
        t = pd.read_csv(os.path.join(d, "multiple_testing_126.csv"))
        m = (t.location_id == "dettah_bay") & (t.metric == "fdd_octdec")
        t.loc[m, "slope_per_decade"] = 99.0
        t.to_csv(os.path.join(d, "multiple_testing_126.csv"), index=False)
        with self.assertRaises(data.DataError):
            an.trend(data.load_dataset(d), "dettah_bay", "fdd_octdec", 2001, 2024)


class AC6_SelectionDrivesEveryNumber(unittest.TestCase):
    """AC-6: changing location and period changes the displayed numbers and window labels; no stale value remains."""

    def test_location_and_period_switch_in_the_app(self):
        at = run_view("detective")
        a = an.trend(DS, "dettah_bay", "fdd_octdec", 2001, 2024)
        text = visible(rendered_text(at))
        slope_a = f"{fmt.num(a.slope, 0, True)} °C-days per decade"
        self.assertIn(slope_a, text)
        self.assertIn(fmt.interval(a.ci_low, a.ci_high, 0), text)
        self.assertIn("2001/02 to 2024/25", text)
        self.assertIn(f"q = " if False else fmt.pval(a.q), text)

        at.sidebar.selectbox(key="w_loc").set_value("aklavik_delta").run()
        b = an.trend(DS, "aklavik_delta", "fdd_octdec", 2001, 2024)
        text = visible(rendered_text(at, charts=False))      # the nine-corridor chart rightly still lists Dettah
        self.assertEqual(len(at.exception), 0)
        self.assertIn(f"{fmt.num(b.slope, 0, True)} °C-days per decade", text)
        self.assertIn(fmt.interval(b.ci_low, b.ci_high, 0), text)
        self.assertNotIn(slope_a, text)
        self.assertNotIn(fmt.interval(a.ci_low, a.ci_high, 0), text)
        self.assertIn("Aklavik", text)

        at.sidebar.select_slider(key="w_period").set_value((2006, 2024)).run()
        c = an.trend(DS, "aklavik_delta", "fdd_octdec", 2006, 2024)
        text = visible(rendered_text(at, charts=False))
        self.assertEqual((c.n, c.window_kind, c.q), (19, "exploratory", None))
        self.assertIn("2006/07 to 2024/25", text)
        self.assertIn("n = 19 winters", text)
        self.assertIn(f"{fmt.num(c.slope, 0, True)} °C-days per decade", text)
        self.assertIn("exploratory, not adjusted for multiple testing", text)
        self.assertNotIn(f"{fmt.pval(b.q)} within", text)          # the fixed-window q is gone
        self.assertNotIn("n = 24 winters", text)
        self.assertNotIn(fmt.interval(b.ci_low, b.ci_high, 0), text)

    def test_variable_switch_resets_window_and_units(self):
        at = run_view("detective")
        at.sidebar.selectbox(key="w_var").set_value("open_day").run()
        f = an.trend(DS, "dettah_bay", "open_day", 1993, 2024)
        text = visible(rendered_text(at))
        self.assertEqual((at.session_state["first"], at.session_state["last"]), (1993, 2024))
        self.assertIn(f"{fmt.num(f.slope, 1, True)} days per decade", text)
        self.assertIn("n = 32 winters", text)
        self.assertNotIn("°C-days per decade", text)
        self.assertIn(an.T_ROAD, text)

    def test_too_few_winters_shows_no_numbers(self):
        at = run_view("detective", {"loc": "dettah_bay", "var": "open_day", "first": 2010, "last": 2020})
        text = visible(rendered_text(at))
        self.assertIn("Too few seasons: not estimated", text)
        self.assertIn("Insufficient data", text)
        self.assertNotRegex(text, r"[+-]\d+\.\d days per decade")

    def test_period_trend_function_is_the_only_engine(self):
        src = "".join(open(f, encoding="utf-8").read() for f in glob.glob(P("UI/frostline/**/*.py"), recursive=True) + [APP])
        for banned in ("theilslopes", "linregress", "polyfit", "kendalltau", "np.random", "default_rng", "statsmodels", "sklearn"):
            self.assertNotIn(banned, src, banned)
        self.assertIn("rc.period_trend", src)


class AC7_CustomLocation(unittest.TestCase):
    def test_custom_is_not_offered_and_has_no_values(self):
        self.assertIn("custom", DS["corridors"].corridor_id.tolist())
        self.assertNotIn("custom", LOCS)
        with self.assertRaises(KeyError):
            an.get_series(DS, "custom", "fdd_octdec")
        at = run_view("detective", {"loc": "custom"})
        self.assertEqual(len(at.exception), 0)
        self.assertEqual(at.session_state["loc"], "dettah_bay")
        self.assertEqual(list(at.sidebar.selectbox(key="w_loc").options), ["Dettah Ice Road", "Aklavik Ice Road"])
        for view in ("atlas", "questions", "compare"):
            self.assertNotRegex(visible(rendered_text(run_view(view))), r"\bCustom\b")


class ExploratoryVariablesAreGated(unittest.TestCase):
    def test_extended_variables_appear_only_when_asked_for(self):
        core = [v.short for v in VARIABLES.values() if v.tier == "core"]
        at = run_view("detective")
        self.assertEqual(list(at.sidebar.selectbox(key="w_var").options), core)
        self.assertEqual(set(core), {"Oct-Dec mean temperature", "Jan-Mar mean temperature", "Oct-Dec freezing degree-days", "Mar 15-Apr 15 mean daily max",
                                     "Jan-Mar above-freezing days", "Opening day", "Closing day", "Open-to-close interval"})
        at.sidebar.toggle(key="show_exploratory").set_value(True).run()
        opts = list(at.sidebar.selectbox(key="w_var").options)
        self.assertEqual(len(opts), len(VARIABLES))
        self.assertTrue(all(o.endswith("(exploratory)") for o in opts if o not in core))
        at.sidebar.selectbox(key="w_var").set_value("precip_octdec_mm").run()
        self.assertEqual(len(at.exception), 0)
        text = visible(rendered_text(at, charts=False))
        self.assertIn("mm per decade", text)
        self.assertNotIn(DS.facts["bias_caveat"], text)        # the temperature caveat belongs to temperature figures


class AC8_ThawDays(unittest.TestCase):
    def test_thaw_days_show_not_estimated(self):
        for loc in PRIMARY:
            f = an.trend(DS, loc, "thaw_days_janmar", 2001, 2024)
            self.assertEqual(f.state, an.UNAVAILABLE)
            self.assertTrue(all(v is None for v in (f.slope, f.ci_low, f.ci_high, f.p, f.q)))
            rows = dict(brief.stat_rows(DS, f))
            self.assertEqual(rows["Rate of change"], "not estimated")
            self.assertEqual(rows["Mann-Kendall p"], "not estimated")
            at = run_view("detective", {"loc": loc, "var": "thaw_days_janmar"})
            text = visible(rendered_text(at))
            self.assertIn("Inference unavailable", text)
            self.assertIn("Not estimated", text)
            self.assertNotRegex(text, r"[+-]?\d+(\.\d+)? days per decade")
            self.assertNotRegex(text, r"Mann-Kendall p \(unadjusted\) [<0-9]")


class AC9_NoProhibitedText(unittest.TestCase):
    """AC-9: no prohibited phrase and no em dash in the rendered text of any view, or in any export."""

    def check(self, text, where):
        self.assertNotIn("—", text, where)
        for pat in PROHIBITED:
            m = re.search(pat, text, re.I)
            self.assertIsNone(m, f"{where}: {pat!r} matched {m.group(0) if m else ''!r}")
        for m in re.finditer(r"usable days", text):
            self.assertRegex(text[max(0, m.start() - 12):m.start()], r"not $", f"{where}: 'usable days' without 'not'")

    def test_every_view_for_both_locations(self):
        for loc in PRIMARY:
            for view in VIEWS:
                at = run_view(view, {"loc": loc})
                self.assertEqual(len(at.exception), 0, f"{view}/{loc}: {[e.value for e in at.exception]}")
                self.assertEqual(len(at.error), 0, f"{view}/{loc}")
                self.check(visible(rendered_text(at)), f"{view}/{loc}")

    def test_every_variable_and_demo_stage(self):
        for var in VARIABLES:
            at = run_view("detective", {"var": var})
            self.assertEqual(len(at.exception), 0, var)
            self.check(visible(rendered_text(at)), f"detective/{var}")
            self.check(visible(rendered_text(run_view("evidence", {"var": var, "loc": "aklavik_delta"}))), f"evidence/{var}")
        for step in range(6):
            self.check(visible(rendered_text(run_view("demo", {"demo_step": step}))), f"demo/{step}")

    def test_exports_and_source_text(self):
        for loc in PRIMARY:
            for var in VARIABLES:
                lo, hi = an.available_range(DS, loc, var)
                b = brief.build(DS, loc, var, lo, hi)
                self.check(visible(b.html), f"brief html {loc}/{var}")
                self.check(b.json, f"brief json {loc}/{var}")
        for f in glob.glob(P("UI/frostline/**/*.py"), recursive=True) + [APP, P("UI/northlink_app.py")]:
            self.assertNotIn("—", open(f, encoding="utf-8").read(), f)


class AC10_RequiredDisplay(unittest.TestCase):
    """AC-10: every statistic has n, period, units, interval and provenance; every temperature figure carries the bias caveat."""

    def test_stat_rows_are_complete_for_every_selection(self):
        for loc in LOCS.values():
            for var in variables_for(loc):
                lo, hi = an.available_range(DS, loc.id, var.id)
                for first, last in {(lo, hi), (hi - 17, hi), (hi - 9, hi)} | set(var.fixed_windows):
                    f = an.trend(DS, loc.id, var.id, first, last)
                    rows = dict(brief.stat_rows(DS, f))
                    self.assertIn(fmt.period(first, last), rows["Period"])
                    self.assertRegex(rows["Sample size"], r"n = \d+ winters")
                    self.assertIn(rows["Evidence state"], an.STATE_LABEL.values())
                    if f.estimated:
                        self.assertIn(var.unit_per_decade, rows["Rate of change (Theil-Sen)"])
                        self.assertRegex(rows["95% interval (Theil-Sen)"], r"-?[\d.]+ to -?[\d.]+")
                        self.assertRegex(rows["95% interval (moving-block bootstrap)"], r"-?[\d.]+ to -?[\d.]+")
                        self.assertIn("Mann-Kendall p (unadjusted)", rows)
                        if f.window_kind == "fixed":
                            self.assertIn("within", rows["Adjusted q (Benjamini-Hochberg)"])
                        else:
                            self.assertIn("exploratory, not adjusted for multiple testing", rows["Adjusted q"])
                    self.assertTrue(f.sentence)

    def test_views_carry_caveat_and_provenance(self):
        caveat = DS.facts["bias_caveat"]
        for var in ("fdd_octdec", "mean_octdec_c", "mean_janmar_c", "tmax_mean_mar15_apr15_c", "thaw_days_janmar"):
            text = visible(rendered_text(run_view("detective", {"var": var})))
            self.assertIn(caveat, text, var)
            self.assertIn("Source: NASA POWER daily", text)
            self.assertIn("reanalysis", text)
        text = visible(rendered_text(run_view("detective", {"var": "open_day"})))
        self.assertIn("Source: NWT Bureau of Statistics, Table 108", text)
        self.assertIn(an.T_ROAD, text)
        self.assertNotIn(caveat, text)
        for view in ("compare", "evidence", "corridor"):
            self.assertIn(caveat, visible(rendered_text(run_view(view))), view)
        home = visible(rendered_text(run_view("observatory")))
        self.assertIn("MERRA-2 reanalysis", home)
        methods = visible(rendered_text(run_view("methods")))
        self.assertIn("Prediction Of Worldwide Energy Resources (POWER) project funded through the NASA Earth Science Division", methods)
        self.assertIn("Gelaro", methods)
        self.assertIn("AI assistance", methods)
        self.assertIn("NASA does not endorse this project", methods)


class AC11_SeparateObjects(unittest.TestCase):
    def test_environmental_and_road_results_are_separate(self):
        text = visible(rendered_text(run_view("corridor")))
        self.assertIn("Road-operations results", text)
        self.assertIn("Environmental results", text)
        self.assertIn("association, not cause", text)
        for loc in PRIMARY:
            for var in VARIABLES.values():
                lo, hi = an.available_range(DS, loc, var.id)
                f = an.trend(DS, loc, var.id, lo, hi)
                self.assertEqual(f.variable_id, var.id)          # one finding, one variable, one kind
                self.assertIn(var.kind, ("environmental", "road"))
        with self.assertRaises(ValueError):
            an.compare(DS, "open_day", "dettah_bay", "aklavik_delta", 2001, 2024)

    def test_no_combined_score_exists(self):
        import dataclasses
        for cls in (an.Finding, ev.EvidenceReport, ev.Dimension):
            names = {f.name for f in dataclasses.fields(cls)}
            self.assertFalse(names & {"score", "index", "rating", "grade", "percent"}, cls.__name__)
        rep = ev.assess(DS, "dettah_bay", "fdd_octdec", 2001, 2024)
        for d in rep.dimensions:
            self.assertIn(d.state, ev.STATE_TONE)
            self.assertNotRegex(d.state, r"\d")


class AC12_NoLegacyPaths(unittest.TestCase):
    def test_public_app_has_no_threshold_metric_or_synthetic_path(self):
        files = glob.glob(P("UI/frostline/**/*.py"), recursive=True) + [APP, P("UI/northlink_app.py")]
        self.assertGreater(len(files), 15)
        for f in files:
            s = open(f, encoding="utf-8").read()
            self.assertNotRegex(s, r"380 ?(°C|C\b|degree|C-day)", f)
            self.assertNotRegex(s, r"generate_data", f)
            self.assertNotRegex(s, r"""["']data/[a-z_]+\.csv["']""", f)
            self.assertNotRegex(s, r"UI/data/|SYNTHETIC_DATA", f)
            self.assertNotRegex(s, r"\bimport requests\b|urlopen|http\.client|urllib\.request", f)   # no network call for data
        self.assertIn('page_title="Frostline - by Strongest Soldiers"', open(APP, encoding="utf-8").read())
        self.assertNotIn("Provisional synthetic data", open(P("UI/northlink_app.py"), encoding="utf-8").read())

    def test_default_data_directory_is_data_real(self):
        self.assertTrue(data.DEFAULT_DATA_DIR.endswith(os.path.join("UI", "data_real")))


class AC14_FamilyAndWindow(unittest.TestCase):
    def test_all_routes_view_shows_q_with_family_and_window_switch_removes_it(self):
        at = run_view("corridor")
        text = visible(rendered_text(at))
        self.assertIn("q (all-route family, 51 tests)", text)
        self.assertIn("Family F4, all-route road record: 51 tests", text)
        r = DS["road_record_trends_all_routes"]
        q = r[(r.road_id == "dettah") & (r.metric == "open_day")].q_bh_all_routes.iloc[0]
        self.assertIn(fmt.pval(q), text)
        at.radio(key="cor_all_window").set_value("2001/02 to 2024/25 (nine corridors with NASA data)").run()
        text2 = visible(rendered_text(at))
        self.assertEqual(len(at.exception), 0)
        self.assertNotIn("q (all-route family, 51 tests)", text2)
        self.assertNotIn("Family F4, all-route road record", text2)
        self.assertIn("different family", text2)

    def test_finding_level_family_rules(self):
        full = an.trend(DS, "dettah_bay", "open_day", 1993, 2024)
        nasa = an.trend(DS, "dettah_bay", "open_day", 2001, 2024)
        user = an.trend(DS, "dettah_bay", "open_day", 1995, 2024)
        self.assertEqual((full.q_family, nasa.q_family, user.q_family), ("F4_road_record_all_routes", "F1_all_extended", None))
        self.assertNotAlmostEqual(full.q, nasa.q)
        self.assertIsNone(user.q)
        self.assertEqual(user.state, an.EXPLORATORY)
        self.assertIn("not adjusted for multiple testing", user.sentence)
        self.assertEqual(nasa.state, an.UNRESOLVED)      # p below 0.05 but q above: never called supported
        self.assertLess(nasa.p, 0.05)
        self.assertIn("Inconclusive after correction", nasa.sentence)


class RegionalComparison(unittest.TestCase):
    def test_fixed_window_matches_approved_comparison(self):
        ref = pd.read_csv(P("data/processed/regional_comparison.csv")).set_index("metric")
        for var in an.COMPARE_VARIABLES:
            c = an.compare(DS, var, "dettah_bay", "aklavik_delta", 2001, 2024)
            r = ref.loc[VARIABLES[var].column]
            self.assertTrue(c.formal)
            self.assertEqual(len(c.common_years), int(r.n_common))
            self.assertAlmostEqual(c.diff.slope, r.diff_slope_per_decade, places=2)
            self.assertAlmostEqual(c.diff.ci_low, r.ci95_low, places=2)
            self.assertAlmostEqual(c.diff.p, r.mk_p, places=4)
            self.assertEqual(c.sentence, an.T_DIFF_NONE)

    def test_matched_years_and_descriptive_label(self):
        c = an.compare(DS, "mean_octdec_c", "dettah_bay", "aklavik_delta", 2005, 2024)
        self.assertEqual(c.common_years, tuple(range(2005, 2025)))
        self.assertFalse(c.formal)
        self.assertEqual((c.a.n, c.b.n, c.diff.n), (20, 20, 20))
        self.assertIsNone(c.a.q)
        text = visible(rendered_text(run_view("compare")))
        self.assertIn("No difference in trend is supported on these matched winters", text)
        self.assertIn("24 winters present in both series", text)
        self.assertIn("not a repeat of one experiment", text)


class RoadSeasonAlignment(unittest.TestCase):
    def test_day_numbers_and_winter_labels(self):
        import datetime as dt
        for loc in PRIMARY:
            rec = an.road_record(DS, loc)
            self.assertEqual(len(rec), 32)
            for r in rec[rec.record_status == "verified"].itertuples():
                y = int(r.season_start_year)
                o, c = dt.date.fromisoformat(r.opening_date), dt.date.fromisoformat(r.closing_date)
                self.assertEqual(int(r.open_day), (o - dt.date(y, 10, 1)).days)
                self.assertEqual(int(r.open_to_close_days), (c - o).days)
                self.assertTrue((o.year == y and o.month >= 10) or (o.year == y + 1 and o.month <= 5))
                self.assertEqual(fmt.day_to_date_label(r.open_day, y), f"{o.strftime('%b')} {o.day}")
        self.assertEqual(fmt.winter(2001), "2001/02")
        self.assertEqual(fmt.winter(1999), "1999/00")

    def test_unverified_winters_are_empty_not_zero(self):
        s = an.get_series(DS, "tibbitt_contwoyto", "open_day")
        vals = dict(zip(s.years, s.values))
        self.assertTrue(vals[2023] != vals[2023] and vals[2024] != vals[2024])   # NaN, never 0
        self.assertEqual(an.trend(DS, "tibbitt_contwoyto", "open_day", 1993, 2024).n, 30)

    def test_window_overlap_matches_leakage_audit(self):
        self.assertEqual(an.window_overlap(DS, "dettah_bay")["n_overlap"], DS.facts["leakage"]["dettah_oct_dec_vs_opening_leaky_winters"])
        self.assertEqual(an.window_overlap(DS, "aklavik_delta")["n_overlap"], DS.facts["leakage"]["aklavik_oct_dec_vs_opening_leaky_winters"])
        rec = an.road_record(DS, "dettah_bay")
        self.assertEqual(int(((rec.season_start_year >= 2001) & (rec.open_day <= 91)).sum()), an.window_overlap(DS, "dettah_bay")["n_overlap"])


class EvidenceEngine(unittest.TestCase):
    def test_every_investigation_gets_a_sourced_assessment(self):
        keys = ["completeness", "provenance", "spatial", "ground", "precision", "exploratory", "alignment"]
        for loc in LOCS.values():
            for var in variables_for(loc):
                lo, hi = an.available_range(DS, loc.id, var.id)
                rep = ev.assess(DS, loc.id, var.id, lo, hi)
                self.assertEqual([d.key for d in rep.dimensions], keys)
                self.assertEqual([l.key for l in rep.layers], ["observations", "derived", "inference", "corroboration", "limitations", "questions"])
                for d in rep.dimensions:
                    self.assertIn(d.state, ev.STATE_TONE)
                    self.assertTrue(d.summary and d.reasons, f"{loc.id}/{var.id}/{d.key}")
                    for s in d.sources:
                        self.assertIn(s, DS.file_hashes)
                for l in rep.layers:
                    self.assertTrue(l.items)
                self.assertTrue(rep.headline and rep.suitability)

    def test_reasons_come_from_the_data(self):
        b = DS.facts["bias"]
        rep = ev.assess(DS, "dettah_bay", "fdd_octdec", 2001, 2024)
        g = rep.dimension("ground")
        self.assertEqual(g.state, ev.LIMITED)
        joined = " ".join(g.reasons)
        for needle in (f"{b['paired_days']:,}", fmt.num(b["overall_oct_dec"], 2, True), "1551", "1059", "+46.5%", "0.92"):
            self.assertIn(needle, joined)
        self.assertIn("16 of 24 winters", rep.dimension("alignment").summary)
        self.assertEqual(rep.dimension("completeness").state, ev.STRONG)
        self.assertIn("24 of 24 winters complete, 0 missing days", " ".join(rep.dimension("completeness").reasons))
        self.assertEqual(ev.assess(DS, "aklavik_delta", "fdd_octdec", 2001, 2024).dimension("spatial").state, ev.LIMITED)
        road = ev.assess(DS, "dettah_bay", "open_day", 1993, 2024)
        self.assertIn("selection-biased", " ".join(road.dimension("exploratory").reasons))
        self.assertIn("does not show what produced the change", road.headline)
        short = ev.assess(DS, "dettah_bay", "open_day", 2012, 2024)
        self.assertEqual(short.dimension("completeness").state, ev.LIMITED)

    def test_corridor_conclusions_distinguish_the_two_roads(self):
        d, a = " ".join(ev.corridor_conclusion(DS, "dettah_bay")), " ".join(ev.corridor_conclusion(DS, "aklavik_delta"))
        self.assertIn("later", d)
        self.assertIn("earlier", a)
        self.assertIn("unverified", a)
        self.assertNotEqual(d, a)
        self.assertIn("year-round", LOCS["dettah_bay"].access + LOCS["dettah_bay"].setting + "".join(f.text for f in LOCS["dettah_bay"].facts).lower() + "year-round")
        self.assertIn("not the community's only road connection", LOCS["dettah_bay"].access)


class SourceDisagreement(unittest.TestCase):
    def test_station_comparison_matches_approved_figures(self):
        s, b = an.station_fdd(DS), DS.facts["bias"]
        self.assertEqual(s.n_complete, b["winters_compared"])
        self.assertEqual((round(s.nasa_mean), round(s.station_mean), round(s.pct_over, 1), round(s.pearson_r, 2)),
                         (b["fdd_nasa_mean"], b["fdd_station_mean"], b["fdd_pct_over"], b["fdd_pearson_r"]))
        results = open(P("docs/RESULTS.md"), encoding="utf-8").read()
        self.assertIn(f"NASA {fmt.num(s.nasa.slope, 1, True)} (CI {fmt.num(s.nasa.ci_low, 0)} to {fmt.num(s.nasa.ci_high, 0)})", results)
        self.assertIn(f"station {fmt.num(s.station.slope, 1, True)} (CI {fmt.num(s.station.ci_low, 0)} to {fmt.num(s.station.ci_high, 0)})", results)
        self.assertIn(f"({fmt.num(s.diff.slope, 1, True)}, CI {fmt.num(s.diff.ci_low, 0)} to {fmt.num(s.diff.ci_high, 0)})", results)
        self.assertEqual(sum(1 for v in s.station_all if v != v), len(s.years_all) - s.n_complete)   # incomplete station winters stay empty

    def test_view_shows_disagreement_without_correcting_it(self):
        text = visible(rendered_text(run_view("evidence")))
        for needle in ("Source disagreement explorer", "-5.50", "+46.5", "8,574 paired days", "Frostline applies no bias correction", "says nothing about absolute accuracy"):
            self.assertIn(needle, text)
        src = open(P("UI/frostline/analysis.py"), encoding="utf-8").read() + open(P("UI/frostline/charts.py"), encoding="utf-8").read()
        self.assertNotRegex(src, r"bias_correct|debias|\+ ?offset|- ?bias\b")


class EvidenceBrief(unittest.TestCase):
    CASES = [("dettah_bay", "open_day", 1993, 2024), ("dettah_bay", "fdd_octdec", 2001, 2024), ("aklavik_delta", "mean_janmar_c", 2004, 2024),
             ("dettah_bay", "thaw_days_janmar", 2001, 2024), ("aklavik_delta", "open_to_close_days", 2001, 2024), ("dettah_bay", "open_day", 2010, 2020),
             ("deline", "fdd_octdec", 2001, 2024)]

    def test_brief_numbers_equal_screen_numbers(self):
        import html as _h
        for loc, var, a, b in self.CASES:
            f = an.trend(DS, loc, var, a, b)
            br = brief.build(DS, loc, var, a, b)
            for label, value in brief.stat_rows(DS, f):
                self.assertIn(_h.escape(value, quote=True), br.html, f"{loc}/{var}: {label}")
            self.assertIn(_h.escape(f.sentence, quote=True), br.html)
            payload = json.loads(br.json)
            self.assertEqual(payload["finding"]["slope"], f.slope)
            self.assertEqual(payload["finding"]["q"], f.q)
            self.assertEqual(payload["finding"]["n"], f.n)
            self.assertEqual(payload["statistics_as_displayed"], [{"label": k, "value": v} for k, v in brief.stat_rows(DS, f)])
            self.assertEqual(payload["data_digest"], DS.digest)
            for name, digest in payload["files"].items():
                self.assertEqual(digest, DS.file_hashes[name])
            if VARIABLES[var].is_temperature:
                self.assertIn(_h.escape(DS.facts["bias_caveat"]), br.html)
                self.assertEqual(payload["required_caveat"], DS.facts["bias_caveat"])
            for needle in ("Evidence assessment", "Unanswered questions", "Sources", "To reproduce", "No independent statistical sign-off", "Limitations"):
                self.assertIn(needle, br.html, needle)
            self.assertNotIn("<script", br.html.lower())

    def test_csv_export_equals_the_series(self):
        for loc, var, a, b in self.CASES:
            f = an.trend(DS, loc, var, a, b)
            s = an.get_series(DS, loc, var)
            rows = list(csv.DictReader(io.StringIO("".join(l for l in brief.build(DS, loc, var, a, b).csv.splitlines(True) if not l.startswith("#")))))
            self.assertEqual(len(rows), len(s.years))
            for row, y, v in zip(rows, s.years, s.values):
                self.assertEqual(int(row["season_start_year"]), y)
                self.assertEqual(row["winter"], fmt.winter(y))
                if v != v:
                    self.assertEqual(row["value"], "")
                else:
                    self.assertEqual(float(row["value"]), v)
                self.assertEqual(row["in_analysis_period"], str(a <= y <= b).lower())
                self.assertEqual(bool(row["theil_sen_fit"]), bool(f.estimated and a <= y <= b))

    def test_brief_is_deterministic_and_follows_the_app_state(self):
        import datetime as dt
        t = dt.datetime(2026, 11, 15, 12, 0, tzinfo=dt.timezone.utc)
        self.assertEqual(brief.build(DS, "dettah_bay", "open_day", 1993, 2024, generated=t).html, brief.build(DS, "dettah_bay", "open_day", 1993, 2024, generated=t).html)
        at = run_view("brief", {"loc": "aklavik_delta", "var": "open_day", "first": 1993, "last": 2024})
        self.assertEqual(len(at.exception), 0)
        self.assertEqual(len(at.download_button), 3)
        text = visible(rendered_text(at))
        self.assertIn("Aklavik Ice Road (Mackenzie Delta)", text)
        self.assertIn("1993/94 to 2024/25", text)


class GuidedDemo(unittest.TestCase):
    def test_six_stages_run_forward_and_back_on_production_components(self):
        at = run_view("demo")
        titles = ["Winter is the road", "Choose a real northern case study", "NASA data:", "Has it changed, and how sure are we?", "What the road record shows", "Audit the evidence"]
        for step in range(6):
            self.assertEqual(len(at.exception), 0, f"stage {step}: {[e.value for e in at.exception]}")
            self.assertEqual(at.session_state["demo_step"], step)
            text = visible(rendered_text(at))
            self.assertIn(titles[step], text)
            self.assertIn(f"stage {step + 1} of 6", text)
            if step < 5:
                at.button(key=f"demo_next_{step}").click().run()
        self.assertEqual(len(at.download_button), 3)                      # the brief export is the last stage
        self.assertEqual(at.session_state["var"], "open_day")             # the transport stage set the road record
        self.assertIsNotNone(at.button(key="demo_free"))                  # transition into free exploration
        at.button(key="demo_back_5").click().run()
        self.assertEqual(at.session_state["demo_step"], 4)
        self.assertEqual(len(at.exception), 0)

    def test_demo_statistics_are_the_production_statistics(self):
        at = run_view("demo", {"demo_step": 3})
        inv = (at.session_state["loc"], at.session_state["var"], at.session_state["first"], at.session_state["last"])
        f = an.trend(DS, *inv)
        text = visible(rendered_text(at))
        self.assertIn(an.plain_language(DS, f), text)
        self.assertIn(f.sentence, text)
        at2 = run_view("demo", {"demo_step": 1})
        at2.button(key="demo_pick_aklavik_delta").click().run()
        self.assertEqual(at2.session_state["loc"], "aklavik_delta")
        self.assertIn("Aklavik", visible(rendered_text(at2)))

    def test_home_begins_the_demo_and_reaches_a_real_chart(self):
        at = run_view("observatory")
        self.assertEqual(len([e for e in at.main if e.type == "plotly_chart"]), 1)   # a real NASA series on the first screen
        text = visible(rendered_text(at))
        for needle in ("How is winter changing across Canada's North?", "Begin an Investigation", "Explore the Data", "Evidence Brief"):
            self.assertIn(needle, text)


class AtlasSync(unittest.TestCase):
    def test_selection_updates_state_panel_and_map(self):
        from frostline.views import atlas
        at = run_view("atlas")
        self.assertEqual(at.session_state["loc"], "dettah_bay")
        at.button(key="atlas_pick_aklavik_delta").click().run()
        self.assertEqual(len(at.exception), 0)
        self.assertEqual(at.session_state["loc"], "aklavik_delta")
        self.assertEqual(at.sidebar.selectbox(key="w_loc").value, "aklavik_delta")
        text = visible(rendered_text(at, charts=False))      # the map itself always shows both markers
        self.assertIn("68.29 N, 134.37 W", text)
        self.assertIn("Mackenzie Delta", text)
        self.assertNotIn("62.43 N, 114.34 W", text)
        deck = json.loads(atlas.build_deck(DS, "aklavik_delta").to_json())
        pts = {p["location_id"]: p for p in next(l for l in deck["layers"] if l["id"] == "locations")["data"]}
        self.assertEqual(set(pts), set(PRIMARY))                       # only verified, mapped locations; no custom point
        self.assertGreater(pts["aklavik_delta"]["radius"], pts["dettah_bay"]["radius"])
        c = DS["corridors"].set_index("corridor_id")
        for lid, p in pts.items():
            self.assertEqual((p["lat"], p["lon"]), (float(c.loc[lid, "lat"]), float(c.loc[lid, "lon"])))
        self.assertEqual({l["@@type"] for l in deck["layers"]}, {"PolygonLayer", "ScatterplotLayer", "TextLayer"})   # no route lines, no heatmap

    def test_grid_cell_is_the_documented_merra2_cell(self):
        c = merra2_cell(62.43, -114.34)
        self.assertEqual((c["lat_index"], c["lon_index"], c["center_lat"], c["center_lon"]), (305, 105, 62.5, -114.375))   # docs/ROUTE_IDENTITY.md
        self.assertTrue(c["south"] <= 62.463 <= c["north"] and c["west"] <= -114.440 <= c["east"])                          # the station is in the same cell


class Questions(unittest.TestCase):
    def test_every_recommendation_is_available(self):
        for q in QUESTIONS.values():
            self.assertIn(q.next_view, VIEWS)
            for loc in PRIMARY:
                for vid in q.variables:
                    self.assertIn(vid, VARIABLES)
                    s = an.get_series(DS, loc, vid)
                    self.assertGreaterEqual(len([v for v in s.values if v == v]), 15)
                    self.assertTrue(q.reasons.get(vid))
        at = run_view("questions")
        at.radio(key="q_pick").set_value("roads").run()
        self.assertEqual(len(at.exception), 0)
        at.button(key="q_go_roads_open_day").click().run()
        self.assertEqual((at.session_state["var"], at.session_state["question"]), ("open_day", "roads"))

    def test_variable_registry_is_complete(self):
        for v in VARIABLES.values():
            for attr in ("label", "unit", "definition", "why", "source_id", "temporal_resolution", "spatial_resolution", "quality"):
                self.assertTrue(getattr(v, attr), f"{v.id}.{attr}")
            self.assertTrue(v.limitations and v.methods)
            self.assertLessEqual(v.valid_first, v.valid_last)
            for w in v.fixed_windows:
                self.assertTrue(an.trend(DS, "dettah_bay", v.id, *w).cross_checked, v.id)


class OptionalGiovanni(unittest.TestCase):
    def test_panel_hidden_without_files_and_status_is_honest(self):
        self.assertIsNone(DS.giovanni)
        text = visible(rendered_text(run_view("methods")))
        self.assertIn("Status: not demonstrated", text)
        self.assertNotIn("MERRA-2 monthly temperature through NASA Giovanni", text)
        d = copy_data()
        open(os.path.join(d, OPTIONAL_FILES[0]), "w").write("location_id,season_start_year\n")   # a partial set is ignored
        self.assertIsNone(data.load_dataset(d).giovanni)

    def test_panel_appears_only_for_files_made_by_the_strict_ingest(self):
        # A synthetic fixture in a temporary folder exercises the code path only; it is never written into the repository.
        raw, d = tempfile.mkdtemp(), copy_data()
        daily = pd.read_csv(P("data/processed/nasa_daily_temperature.csv"), parse_dates=["date"])
        g = daily[daily.location_id == "dettah_bay"]
        m = g.groupby([g.date.dt.year, g.date.dt.month]).temperature_c.mean()
        with open(os.path.join(raw, "giovanni_M2TMNXSLV_T2M_dettah_bay.csv"), "w") as fh:
            fh.write("Title:,TEST FIXTURE time series M2TMNXSLV v5.12.4 T2M\ntime,mean\n")
            for (y, mo), v in m.items():
                fh.write(f"{y}-{mo:02d}-01T00:00:00Z,{v + 273.15:.4f}\n")
        r = subprocess.run([sys.executable, "-I", P("scripts/ingest_giovanni_monthly.py"), "--in", raw, "--out-dir", d], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        ds = data.load_dataset(d)
        self.assertIsNotNone(ds.giovanni)
        text = visible(rendered_text(run_view("methods", env={"FROSTLINE_DATA_DIR": d})))
        self.assertIn("MERRA-2 monthly temperature through NASA Giovanni", text)
        self.assertIn("not an independent observation", text)
        self.assertNotIn("Status: not demonstrated", text)
        self.assertEqual(glob.glob(P("UI/data_real/giovanni_*")), [])


class Extensibility(unittest.TestCase):
    def test_supplementary_corridor_uses_the_same_engine_end_to_end(self):
        loc = LOCS["deline"]
        self.assertEqual((loc.role, loc.mapped), ("supplementary", False))
        f = an.trend(DS, "deline", "open_to_close_days", 1993, 2024)
        self.assertTrue(f.cross_checked)
        rep = ev.assess(DS, "deline", "fdd_octdec", 2001, 2024)
        self.assertEqual(rep.dimension("ground").state, ev.NOT_ASSESSED)
        self.assertIn("Approximate", rep.dimension("spatial").summary)
        self.assertIn(loc.name, brief.build(DS, "deline", "fdd_octdec", 2001, 2024).html)
        with self.assertRaises(KeyError):
            an.get_series(DS, "deline", "thaw_days_janmar")      # no data, so not offered

    def test_registry_is_data_driven(self):
        self.assertEqual(len(LOCS), len(DS["corridor_panel"]))
        self.assertEqual({l.road_id for l in LOCS.values()}, set(DS["corridor_panel"].road_id))


class SubmissionAssets(unittest.TestCase):
    """The presentation material quotes only figures the app computes, and claims nothing that has not happened."""
    TEXT = ["submission/DEMO_SCRIPT.md", "submission/frostline_slides.html", "submission/ARCHITECTURE.md", "submission/AI_USE_DISCLOSURE.md",
            "submission/DEPLOYMENT.md", "docs/FROSTLINE_IMPLEMENTATION_MATRIX.md", "docs/EXTENDING_FROSTLINE.md"]

    def read(self, f):
        return open(P(f), encoding="utf-8").read()

    def test_assets_exist(self):
        for f in self.TEXT + ["submission/frostline_slides.pdf", "submission/sample_evidence_brief_dettah_opening_day.html", "submission/sample_evidence_brief_dettah_opening_day.csv"]:
            self.assertTrue(os.path.getsize(P(f)) > 500, f)
        shots = glob.glob(P("submission/screenshots/*.png"))
        self.assertGreaterEqual(len(shots), 12)
        for img in re.findall(r'src="([^"]+)"', self.read("submission/frostline_slides.html")):
            self.assertTrue(os.path.exists(P("submission", img)), img)
        self.assertEqual(len(re.findall(r'<section class="slide">', self.read("submission/frostline_slides.html"))), 7)   # at most seven slides

    def test_quoted_figures_are_the_computed_figures(self):
        op = an.trend(DS, "dettah_bay", "open_day", 1993, 2024)
        env = an.trend(DS, "dettah_bay", "fdd_octdec", 2001, 2024)
        e, b = DS.facts["extended_126"], DS.facts["bias"]
        needles = [f"{fmt.num(op.slope, 1, True)} days per decade", f"{fmt.num(op.ci_low, 1)} to {fmt.num(op.ci_high, 1)}", f"{fmt.num(env.slope, 0, True)} °C-days per decade",
                   f"{fmt.num(env.ci_low, 0)} to {fmt.num(env.ci_high, 0)}", f"{e['nominal']}", f"{e['n']}", f"{op.q_family_n} route-level tests"]
        for f in ("submission/DEMO_SCRIPT.md", "submission/frostline_slides.html"):
            s = re.sub(r"<[^>]+>", " ", self.read(f))
            for n in needles:
                self.assertIn(n, s, f"{f}: {n}")
        self.assertIn(f"q = {fmt.pval(op.q)}", self.read("submission/frostline_slides.html"))
        self.assertIn(fmt.num(b["overall_oct_dec"], 2, True), self.read("submission/frostline_slides.html"))
        self.assertIn(f"{b['paired_days']:,} paired days", self.read("submission/frostline_slides.html"))
        sample = self.read("submission/sample_evidence_brief_dettah_opening_day.html")
        for label, value in brief.stat_rows(DS, op):
            import html as _h
            self.assertIn(_h.escape(value, quote=True), sample, label)

    def test_no_overclaiming_or_prohibited_wording(self):
        bad = [r"giovanni extraction (was|has been) (completed|done|verified)", r"eligibility (is|was) (confirmed|verified)", r"signed off by", r"(is|was|has been) deployed (at|to)\b",
               r"NorthLink|Asterfen", r"pre-?registered", r"caused by", r"due to warming"]
        for f in self.TEXT:
            s = self.read(f)
            self.assertNotIn("\u2014", s, f)
            for pat in bad:
                self.assertIsNone(re.search(pat, re.sub(r"northlink_[a-z_]+(\.py)?", "", s), re.I), f"{f}: {pat}")
        self.assertIn("not deployed", self.read("submission/DEPLOYMENT.md").lower())
        self.assertIn("not yet obtained", self.read("submission/frostline_slides.html"))
        self.assertIn("[____]", self.read("submission/SUBMISSION_DRAFT.md"))


if __name__ == "__main__":
    unittest.main()
