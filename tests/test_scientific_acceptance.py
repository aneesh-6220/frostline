"""Acceptance and regression tests for the scientific remediation (all run on committed files, no network)."""
import datetime as dt
import glob
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest

import numpy as np
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import northlink_metrics as m  # noqa: E402
import northlink_stats as st  # noqa: E402
import build_road_operations as bro  # noqa: E402

P = lambda *a: os.path.join(ROOT, *a)
rd = lambda f: pd.read_csv(P("data/processed", f))


class RawDataImmutable(unittest.TestCase):
    def test_checksums_match_manifest(self):
        lines = open(P("tests/raw_checksums.sha256")).read().strip().splitlines()
        self.assertEqual(len(lines), 15)
        for ln in lines:
            digest, rel = ln.split(None, 1)
            rel = rel.strip().lstrip("*")
            h = hashlib.sha256(open(P("data/raw", rel), "rb").read()).hexdigest()
            self.assertEqual(h, digest, rel)

    def test_no_untracked_raw_files(self):
        listed = {ln.split(None, 1)[1].strip().lstrip("*")[2:] for ln in open(P("tests/raw_checksums.sha256")).read().strip().splitlines()}
        actual = {os.path.relpath(f, P("data/raw")) for f in glob.glob(P("data/raw/**/*"), recursive=True) if os.path.isfile(f)}
        self.assertEqual(listed, actual)


class RoadDateValidator(unittest.TestCase):
    def test_tibbitt_rows_rejected(self):
        d = dt.datetime
        self.assertFalse(bro.validate_dates(d(2023, 2, 12), d(2024, 3, 31), 2023)[0])
        self.assertFalse(bro.validate_dates(d(2024, 2, 4), d(2025, 3, 26), 2024)[0])

    def test_normal_rows_accepted(self):
        d = dt.datetime
        self.assertTrue(bro.validate_dates(d(2023, 12, 24), d(2024, 4, 9), 2023)[0])
        self.assertTrue(bro.validate_dates(d(2024, 1, 28), d(2024, 4, 5), 2023)[0])

    def test_close_before_open_rejected(self):
        d = dt.datetime
        self.assertFalse(bro.validate_dates(d(2007, 11, 9), d(2007, 5, 9), 2006)[0])

    def test_flagged_rows_in_data(self):
        ro = rd("road_operations.csv")
        bad = ro[ro.record_status == "flagged_inconsistent"]
        self.assertEqual(len(bad), 4)
        self.assertTrue(bad.opening_date.isna().all() and bad.closing_date.isna().all())
        v = ro[ro.record_status == "verified"]
        iv = (pd.to_datetime(v.closing_date) - pd.to_datetime(v.opening_date)).dt.days
        self.assertTrue((iv > 0).all() and (iv < 300).all(), iv.describe())


class Multiplicity(unittest.TestCase):
    def test_bh_known(self):
        q = st.bh_adjust([0.01, 0.04, 0.03, 0.005])
        np.testing.assert_allclose(q, [0.02, 0.04, 0.04, 0.02])

    def test_holm_known(self):
        q = st.holm_adjust([0.01, 0.04, 0.03, 0.005])
        np.testing.assert_allclose(q, [0.03, 0.06, 0.06, 0.02])

    def test_126_family_reproduces(self):
        t = rd("multiple_testing_126.csv")
        self.assertEqual(len(t), 126)
        ok = t.p_unadjusted.notna()
        self.assertEqual(int(ok.sum()), 126)
        q = st.bh_adjust(t.p_unadjusted.values)
        np.testing.assert_allclose(q, t.q_bh_all126.values, atol=2e-5)
        self.assertEqual(int((t.q_bh_all126 < 0.05).sum()), 0)
        self.assertEqual(int((t.q_bh_all126 < 0.10).sum()), 3)
        self.assertEqual(int((t.p_unadjusted < 0.05).sum()), 20)

    def test_all_routes_family(self):
        r = rd("road_record_trends_all_routes.csv")
        self.assertEqual(len(r), 51)
        q = st.bh_adjust(r.p_unadjusted.values)
        np.testing.assert_allclose(q, r.q_bh_all_routes.values, atol=2e-5)
        d = r[(r.road_id == "dettah") & (r.metric == "open_day")].iloc[0]
        self.assertLess(d.q_bh_all_routes, 0.05)

    def test_families_file(self):
        f = rd("hypothesis_families.csv")
        self.assertEqual(sorted(f.family_id.str[:2]), ["F1", "F2", "F3", "F4", "F5"])

    def test_no_pooled_tests(self):
        self.assertFalse(os.path.exists(P("data/processed/pooled_anomaly_correlations.csv")))
        self.assertFalse(os.path.exists(P("UI/data_real/pooled_anomaly_correlations.csv")))
        for f in glob.glob(P("scripts/*.py")):
            if f.endswith("test_scientific_acceptance.py"):
                continue
            self.assertNotIn("pooled_anomaly", open(f).read(), f)


class TrendGuards(unittest.TestCase):
    yrs = list(range(2001, 2025))

    def test_mostly_tied(self):
        v = [0.0] * 23 + [1.0]
        r = m.trend(self.yrs, v)
        self.assertEqual(r.status, "mostly_tied")
        self.assertTrue(np.isnan(r.slope_per_decade) and np.isnan(r.mk_p))

    def test_constant(self):
        self.assertEqual(m.trend(self.yrs, [0.0] * 24).status, "constant_series")

    def test_normal_series_ok(self):
        rng = np.random.default_rng(1)
        r = m.trend(self.yrs, np.arange(24) * 0.5 + rng.normal(0, 1, 24))
        self.assertEqual(r.status, "ok")
        self.assertGreater(r.slope_per_decade, 0)

    def test_dettah_thaw_not_estimated(self):
        t = rd("trend_results.csv")
        r = t[(t.location_id == "dettah_bay") & (t.metric == "thaw_days_janmar") & (t.variant == "main (2001-2024)")].iloc[0]
        self.assertEqual(r.status, "mostly_tied")
        self.assertTrue(np.isnan(r.mk_p))

    def test_block_bootstrap_deterministic(self):
        y = np.arange(2001, 2025)
        v = np.sin(y) * 3 + (y - 2001) * 0.2
        a = st.block_bootstrap_slope(y, v)
        b = st.block_bootstrap_slope(y, v)
        self.assertEqual(a, b)


class LeakageControl(unittest.TestCase):
    def test_windows_end_before_every_outcome(self):
        w = rd("analysis_windows.csv")
        ro = rd("road_operations.csv")
        ro = ro[ro.record_status == "verified"].copy()
        for _, r in w.iterrows():
            g = ro[ro.road_id == r.road_id]
            for col, end_md in (("opening_date", r.pre_open_window_end_md), ("closing_date", r.pre_close_window_end_md)):
                dates = pd.to_datetime(g[col])
                if col == "opening_date":  # window belongs to the season-start year (Oct-Dec) even if opening is in Jan-May
                    ends = [pd.Timestamp(f"{d.year if d.month >= 10 else d.year - 1}-{end_md}") for d in dates]
                else:
                    ends = [pd.Timestamp(f"{d.year}-{end_md}") for d in dates]
                self.assertTrue(all(e < d for e, d in zip(ends, dates)), (r.road_id, col))

    def test_leakage_audit_documents_old_windows(self):
        a = rd("leakage_audit.csv")
        self.assertGreater(len(a), 0)
        self.assertTrue((a.n_winters_window_reaches_outcome > 0).any())

    def test_associations_leak_free_only(self):
        c = rd("road_climate_correlations.csv")
        self.assertEqual(len(c), 6)
        self.assertTrue(c.q_bh_family.notna().all())
        self.assertTrue((c.ci95_low < c.spearman_rho).all() and (c.spearman_rho < c.ci95_high).all())


class BiasDiagnostic(unittest.TestCase):
    def test_summary_values(self):
        d = json.load(open(P("data/processed/diagnostics/diagnostics_summary.json")))
        self.assertEqual(d["overall_bias_all_days"]["n"], 8574)
        self.assertAlmostEqual(d["overall_bias_all_days"]["mean_bias"], -2.255, places=2)
        self.assertLess(d["overall_bias_Oct_Dec"]["mean_bias"], -5.0)

    def test_caveat_present(self):
        s = open(P("docs/TEMPERATURE_BIAS_DIAGNOSIS.md")).read()
        self.assertIn("NASA POWER T2M is MERRA-2 reanalysis for a 0.5 x 0.625 degree cell", s)
        self.assertIn("3.4 to 7.3 C colder", s)

    def test_ui_trends_carry_caveat(self):
        t = pd.read_csv(P("UI/data_real/trends.csv"))
        self.assertTrue(t.plain_takeaway.str.contains("reanalysis").all())


class ResultsAndDocs(unittest.TestCase):
    def test_results_md_is_generated_output(self):
        out = os.path.join(tempfile.mkdtemp(), "r.md")
        subprocess.check_call([sys.executable, "-I", P("scripts/generate_results_md.py"), "--out", out], stdout=subprocess.DEVNULL)
        self.assertEqual(open(out).read(), open(P("docs/RESULTS.md")).read())

    SCAN = ["README.md", "docs/RESULTS.md", "docs/GEOGRAPHIC_SCOPE.md", "docs/DATA_DICTIONARY.md", "docs/DATA_SOURCES.md", "docs/DATA_QUALITY.md",
            "docs/RESEARCH_EVIDENCE.md", "docs/ROUTE_IDENTITY.md", "docs/CHALLENGE_ELIGIBILITY.md", "docs/TEMPERATURE_BIAS_DIAGNOSIS.md",
            "docs/REFERENCES.md", "UI/README.md"]
    PROHIBITED = [r"pre-?registered", r"climate-caused", r"temperature cannot explain", r"snow explains", r"snow causes", r"p_naive",
                  r"temperature metrics do not explain", r"Bonferroni threshold of 0\.05/14", r"4 show a supported change"]

    def test_no_prohibited_phrases(self):
        for f in self.SCAN:
            s = open(P(f)).read()
            for pat in self.PROHIBITED:
                self.assertIsNone(re.search(pat, s, re.I), f"{f}: {pat}")

    def test_no_em_dashes(self):
        for f in glob.glob(P("docs/*.md")) + [P("README.md"), P("UI/README.md")]:
            self.assertNotIn("\u2014", open(f).read(), f)

    def test_superseded_docs_marked(self):
        for f in ("docs/FABLE_BRIEF.md", "docs/HANDOFF_README.md"):
            self.assertTrue(open(P(f)).read().startswith("# SUPERSEDED"), f)

    def test_handoff_exists_and_has_prohibitions(self):
        s = open(P("docs/FABLE_HANDOFF_FINAL.md")).read()
        for k in ("Prohibited", "synthetic", "pooled", "road-safety", "AI-use", "SUPERSEDED"):
            self.assertIn(k, s)

    def test_handoff_headline_numbers_match_results(self):
        r = open(P("docs/RESULTS.md")).read()
        for needle in ("+9.0 (3.6 to 12.4)", "-10.2 (-15.8 to -5.3)", "+10.3 (3.3 to 17.2)", "0 tests have q < 0.05", "20 have p < 0.05",
                       "+0.64 (0.39 to 0.85)", "16 of 24"):
            self.assertIn(needle, r, needle)
        h = open(P("docs/FABLE_HANDOFF_FINAL.md")).read()
        for needle in ("+9.0 days per decade (95% CI 3.6 to 12.4)", "-10.2 days per decade (CI -15.8 to -5.3)", "+10.3 (CI 3.3 to 17.2)",
                       "20 have p < 0.05", "Spearman +0.64", "16 of 24"):
            self.assertIn(needle, h, needle)

    def test_results_states_exploratory_and_no_cause(self):
        s = open(P("docs/RESULTS.md")).read()
        self.assertIn("exploratory", s.lower())
        self.assertIn("Nothing here is a statement of cause", s)


class LegacyUiContainment(unittest.TestCase):
    def test_legacy_data_all_synthetic(self):
        for f in ("climate_annual", "road_seasons", "trends"):
            d = pd.read_csv(P("UI/data", f + ".csv"))
            self.assertTrue(d.synthetic.astype(str).str.lower().eq("true").all(), f)
        self.assertTrue(os.path.exists(P("UI/data/SYNTHETIC_DATA_README.md")))

    def test_real_data_not_synthetic(self):
        for f in ("climate_annual", "road_seasons", "trends"):
            d = pd.read_csv(P("UI/data_real", f + ".csv"))
            self.assertTrue(d.synthetic.astype(str).str.lower().eq("false").all(), f)

    def test_no_380_metric_in_real_data(self):
        for f in glob.glob(P("UI/data_real/*.csv")):
            self.assertNotRegex(open(f).read(), r"\b380 ?(C|°C)", f)

    def test_readme_warns_and_app_keeps_banner_while_on_synthetic_data(self):
        self.assertTrue(open(P("UI/README.md")).read().startswith("> **WARNING"))
        app = open(P("UI/northlink_app.py")).read()
        if '"data/corridors.csv"' in app:  # still loading the synthetic folder
            self.assertIn("Provisional synthetic data", app)

    def test_real_data_regenerated_from_processed(self):
        a = pd.read_csv(P("UI/data_real/extended_trends.csv"))
        b = rd("extended_trends.csv")
        pd.testing.assert_frame_equal(a, b)
        c = pd.read_csv(P("UI/data_real/road_seasons.csv"))
        self.assertEqual(set(c.corridor_id), {"dettah_bay", "aklavik_delta"})
        self.assertEqual(len(c), 64)


class DataIntegrity(unittest.TestCase):
    def test_nasa_complete(self):
        d = rd("nasa_daily_temperature.csv")
        self.assertEqual(d.groupby("location_id").size().to_dict(), {"aklavik_delta": 8674, "dettah_bay": 8674})
        self.assertEqual(int(d.temperature_c.isna().sum()), 0)
        self.assertTrue(d.temperature_c.between(-70, 45).all())

    def test_season_audit_complete(self):
        a = rd("season_audit.csv")
        self.assertEqual(len(a), 48)
        self.assertTrue(a.included_in_trend.all())

    def test_road_season_interval_label(self):
        s = open(P("docs/SCIENTIFIC_METHODS.md")).read()
        self.assertIn("**not** usable days", s)


if __name__ == "__main__":
    unittest.main()
