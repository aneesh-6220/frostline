"""Tests for the final handoff layer: canonical facts, generated docs, app data contract, recomputation, document consistency.
Run: python3 -I -m unittest discover -s tests -v
"""
import glob
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest

import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
P = lambda *a: os.path.join(ROOT, *a)
UI = P("UI/data_real")
FACTS = json.load(open(os.path.join(UI, "canonical_facts.json")))

import northlink_recompute as rc  # noqa: E402


def read_doc(f):
    with open(P(f), encoding="utf-8") as fh:
        return fh.read()


class RoadStatusCounts(unittest.TestCase):
    def test_statuses_are_exclusive_and_sum_to_total(self):
        ro = pd.read_csv(P("data/processed/road_operations.csv"))
        c = ro.record_status.value_counts().to_dict()
        self.assertEqual(c, {"verified": 512, "missing_not_available": 24, "not_applicable_note": 4, "flagged_inconsistent": 4})
        self.assertEqual(sum(c.values()), len(ro))
        self.assertEqual(len(ro), ro.road_id.nunique() * ro.season_start_year.nunique())
        self.assertEqual(int(ro.duplicated(["road_id", "season_start_year"]).sum()), 0)
        self.assertEqual(FACTS["status_counts"]["total_rows"], len(ro))

    def test_docs_state_544_not_540(self):
        for f in ("docs/DATA_QUALITY.md", "docs/DATA_DICTIONARY.md", "docs/APPROVED_FINDINGS.md"):
            self.assertIn("544", read_doc(f), f)
        self.assertNotRegex(read_doc("docs/DATA_QUALITY.md"), r"\b540\b")

    def test_only_verified_rows_have_dates(self):
        ro = pd.read_csv(P("data/processed/road_operations.csv"))
        self.assertTrue(ro[ro.record_status != "verified"][["opening_date", "closing_date"]].isna().all().all())
        self.assertTrue(ro[ro.record_status == "verified"][["opening_date", "closing_date"]].notna().all().all())


class AppDataContract(unittest.TestCase):
    def test_required_files_exist_not_synthetic_and_documented(self):
        schema = read_doc("docs/APP_DATA_SCHEMA.md")
        files = sorted(glob.glob(os.path.join(UI, "*")))
        self.assertGreaterEqual(len(files), 20)
        for f in files:
            n = os.path.basename(f)
            self.assertIn(f"`{n}`", schema, n)
            if n.endswith(".csv"):
                d = pd.read_csv(f)
                self.assertGreater(len(d), 0, n)
                if "synthetic" in d.columns:
                    self.assertFalse(d.synthetic.astype(str).str.lower().eq("true").any(), n)

    def test_primary_ids_and_custom_has_no_data(self):
        c = pd.read_csv(os.path.join(UI, "corridors.csv"))
        self.assertEqual(c[c.has_road_records].corridor_id.tolist(), ["dettah_bay", "aklavik_delta"])
        self.assertFalse(c[c.corridor_id == "custom"].has_road_records.iloc[0])
        ca = pd.read_csv(os.path.join(UI, "climate_annual.csv"))
        self.assertEqual(set(ca.corridor_id), {"dettah_bay", "aklavik_delta"})
        self.assertEqual(sorted(ca.season_year.unique())[0], 2001)
        self.assertEqual(sorted(ca.season_year.unique())[-1], 2024)

    def test_winter_labels_consistent(self):
        rs = pd.read_csv(os.path.join(UI, "road_seasons.csv"))
        rs["o"], rs["c"] = pd.to_datetime(rs.open_date), pd.to_datetime(rs.close_date)
        # opening falls in Oct-Dec of season_year or Jan-May of season_year+1; closing after opening
        ok = ((rs.o.dt.year == rs.season_year) & (rs.o.dt.month >= 10)) | ((rs.o.dt.year == rs.season_year + 1) & (rs.o.dt.month <= 5))
        self.assertTrue(ok.all())
        self.assertTrue((rs.c > rs.o).all())
        self.assertTrue(((rs.c - rs.o).dt.days == rs.season_length_days).all())

    def test_canonical_facts_match_data(self):
        k = FACTS["dettah"]["open_full"]
        rr = pd.read_csv(os.path.join(UI, "road_record_trends_all_routes.csv"))
        r = rr[(rr.road_id == "dettah") & (rr.metric == "open_day")].iloc[0]
        self.assertAlmostEqual(k["slope"], r.slope_per_decade, 1)
        self.assertEqual(k["n"], int(r.n_seasons))
        self.assertIn("colder than the airport station", FACTS["bias_caveat"])
        self.assertIn(FACTS["bias_caveat"], read_doc("docs/SCIENTIFIC_METHODS.md"))

    def test_extra_files_regenerate_identically(self):
        for a, b in [("data/processed/extended_season_metrics.csv", "UI/data_real/season_metrics_extended.csv"),
                     ("data/processed/road_operations.csv", "UI/data_real/road_operations_all_routes.csv")]:
            self.assertEqual(open(P(a), "rb").read(), open(P(b), "rb").read(), b)


class Recomputation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sm = pd.read_csv(os.path.join(UI, "season_metrics_extended.csv"))
        cls.ro = pd.read_csv(os.path.join(UI, "road_operations_all_routes.csv"))

    def test_fixed_windows_reproduce_stored_results(self):
        s = rc.climate_series(self.sm, "dettah_bay", "fdd_octdec")
        t = rc.period_trend(s.season_start_year, s.fdd_octdec, 2001, 2024)
        stored = pd.read_csv(os.path.join(UI, "trends.csv")).query("corridor_id == 'dettah_bay' and metric == 'fdd'").iloc[0]
        self.assertAlmostEqual(t["slope_per_decade"], stored.slope_per_decade, 2)
        self.assertAlmostEqual(t["ci95_low"], stored.ci_low, 2)
        self.assertAlmostEqual(t["mk_p"], stored.p_value, 3)
        o = rc.road_series(self.ro, "dettah", "open_day")
        t = rc.period_trend(o.season_start_year, o.open_day, 1993, 2024)
        rr = pd.read_csv(os.path.join(UI, "road_record_trends_all_routes.csv")).query("road_id == 'dettah' and metric == 'open_day'").iloc[0]
        self.assertEqual(t["n"], int(rr.n_seasons))
        for mine, theirs in [("slope_per_decade", "slope_per_decade"), ("ci95_low", "ci95_low"), ("ci95_high", "ci95_high"),
                             ("bb_ci95_low", "bb_ci95_low"), ("bb_ci95_high", "bb_ci95_high")]:
            self.assertAlmostEqual(t[mine], rr[theirs], 2, mine)
        t = rc.period_trend(o.season_start_year, o.open_day, 2001, 2024)
        mt = pd.read_csv(os.path.join(UI, "multiple_testing_126.csv")).query("location_id == 'dettah_bay' and metric == 'open_day'").iloc[0]
        self.assertAlmostEqual(t["slope_per_decade"], mt.slope_per_decade, 2)
        self.assertAlmostEqual(t["mk_p"], mt.p_unadjusted, 4)

    def test_other_period_differs_and_has_no_adjusted_q(self):
        o = rc.road_series(self.ro, "dettah", "open_day")
        a = rc.period_trend(o.season_start_year, o.open_day, 1993, 2024)
        b = rc.period_trend(o.season_start_year, o.open_day, 2005, 2024)
        self.assertEqual(b["n"], 20)
        self.assertNotEqual(round(a["slope_per_decade"], 3), round(b["slope_per_decade"], 3))
        self.assertIsNone(b["q_adjusted"])
        self.assertIn("fixed windows", b["adjusted_note"])

    def test_too_few_seasons_gives_no_numbers(self):
        o = rc.road_series(self.ro, "dettah", "open_day")
        t = rc.period_trend(o.season_start_year, o.open_day, 2010, 2020)
        self.assertEqual((t["n"], t["status"]), (11, "too_few_points"))
        self.assertTrue(all(t[k] is None for k in ("slope_per_decade", "ci95_low", "ci95_high", "mk_p", "bb_ci95_low")))

    def test_thaw_days_not_estimated(self):
        ca = pd.read_csv(os.path.join(UI, "climate_annual.csv"))
        for cid in ("dettah_bay", "aklavik_delta"):
            s = ca[(ca.corridor_id == cid) & (ca.metric == "thaw_days")]
            t = rc.period_trend(s.season_year, s.value, 2001, 2024)
            self.assertIn(t["status"], ("mostly_tied", "constant_series"))
            self.assertIsNone(t["slope_per_decade"] if t["status"] == "mostly_tied" else None)
        tr = pd.read_csv(os.path.join(UI, "trends.csv"))
        self.assertTrue(tr[tr.metric == "thaw_days"][["slope_per_decade", "p_value"]].isna().all().all())

    def test_road_series_uses_verified_rows_only(self):
        o = rc.road_series(self.ro, "tibbitt_contwoyto", "open_day")
        self.assertEqual(len(o), 30)
        self.assertNotIn(2023, o.season_start_year.tolist())
        self.assertNotIn(2024, o.season_start_year.tolist())


class GiovanniIngest(unittest.TestCase):
    def test_noop_without_files_and_strict_with_wrong_header(self):
        r = subprocess.run([sys.executable, "-I", P("scripts/ingest_giovanni_monthly.py"), "--in", tempfile.mkdtemp(), "--out-dir", tempfile.mkdtemp()],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0)
        self.assertIn("nothing ingested", r.stdout)
        d = tempfile.mkdtemp()
        open(os.path.join(d, "giovanni_M2TMNXSLV_T2M_dettah_bay.csv"), "w").write("Title,some other product\n2001-10-01T00:00:00Z,260\n")
        r = subprocess.run([sys.executable, "-I", P("scripts/ingest_giovanni_monthly.py"), "--in", d, "--out-dir", tempfile.mkdtemp()], capture_output=True, text=True)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("refusing to attribute", r.stderr + r.stdout)

    def test_repo_contains_no_giovanni_data_until_real_extraction(self):
        raw = glob.glob(P("data/raw/nasa/giovanni/*"))
        out = glob.glob(os.path.join(UI, "giovanni_*"))
        self.assertEqual(bool(raw), bool(out))  # derived files exist only if a raw file exists
        if not raw:
            self.assertIn("NOT DEMONSTRATED", read_doc("docs/CHALLENGE_ELIGIBILITY.md"))

    def test_monthly_data_never_feeds_fdd(self):
        s = open(P("scripts/ingest_giovanni_monthly.py")).read()
        self.assertNotIn("fdd(", s)
        self.assertNotIn("thaw_days(", s)


class GeneratedDocs(unittest.TestCase):
    def test_generated_docs_match_generators(self):
        for script, flag, target in [("generate_approved_findings.py", "--out-docs", "docs/APPROVED_FINDINGS.md")]:
            out = os.path.join(tempfile.mkdtemp(), "o.md")
            subprocess.check_call([sys.executable, "-I", P("scripts", script), flag, out], stdout=subprocess.DEVNULL)
            self.assertEqual(open(out).read(), read_doc(target))

    def test_schema_doc_mentions_every_file(self):
        self.assertIn("generated file; do not edit by hand", read_doc("docs/APP_DATA_SCHEMA.md"))


class HandoffDocs(unittest.TestCase):
    DOCS = ["docs/FABLE_52_START_HERE.md", "docs/APP_IMPLEMENTATION_CONTRACT.md", "docs/APPROVED_FINDINGS.md", "docs/APP_DATA_SCHEMA.md",
            "submission/SUBMISSION_DRAFT.md", "docs/FABLE_HANDOFF_FINAL.md", "docs/CHALLENGE_ELIGIBILITY.md"]

    def test_paths_referenced_in_handoff_docs_exist(self):
        allowed_missing = {"pooled_anomaly_correlations.csv"}  # intentionally removed; named only in prohibitions
        pat = re.compile(r"`([A-Za-z0-9_./\-]+\.(?:md|py|csv|json|txt|sha256|html|xlsx))`")
        bases = ["", "docs", "scripts", "tests", "UI", "UI/data_real", "data/processed", "data/raw/nasa/giovanni"]
        for d in self.DOCS:
            for ref in set(pat.findall(read_doc(d))):
                if ref in allowed_missing or "giovanni" in ref.lower() or "<" in ref or ref.startswith("..."):
                    continue
                self.assertTrue(any(os.path.exists(P(b, ref)) for b in bases), f"{d} references missing {ref}")

    def test_start_here_has_all_sections_and_base_commit(self):
        s = read_doc("docs/FABLE_52_START_HERE.md")
        for i in range(1, 16):
            self.assertRegex(s, rf"(?m)^## {i}\. ", f"section {i}")
        self.assertIn("a8675ec2e9a0965d98dbdee3c96aa219f75b6416", s)
        if os.path.isdir(P(".git")):
            r = subprocess.run(["git", "cat-file", "-t", "a8675ec2e9a0965d98dbdee3c96aa219f75b6416"], cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(r.stdout.strip(), "commit")

    def test_no_em_dashes(self):
        for d in self.DOCS + ["docs/PLANETARY_COMPUTER_TODO.md"]:
            self.assertNotIn("—", read_doc(d), d)

    def test_no_false_verification_claims(self):
        bad = [r"giovanni extraction (was|has been) (completed|done|verified)", r"eligibility (is|was) (confirmed|verified)", r"signed off by yao",
               r"yao (has )?(signed off|approved|reviewed)", r"we (interviewed|surveyed) (stakeholders|communit)"]
        for d in self.DOCS:
            s = read_doc(d)
            for pat in bad:
                self.assertIsNone(re.search(pat, s, re.I), f"{d}: {pat}")

    def test_eligibility_status_is_honest(self):
        s = read_doc("docs/CHALLENGE_ELIGIBILITY.md")
        self.assertIn("NOT DEMONSTRATED", s)
        self.assertIn("BLOCKED, owner Cason", s)
        self.assertIn("M2TMNXSLV", s)

    def test_start_here_links_authoritative_files(self):
        s = read_doc("docs/FABLE_52_START_HERE.md")
        for k in ("SCIENTIFIC_METHODS.md", "FABLE_HANDOFF_FINAL.md", "APP_IMPLEMENTATION_CONTRACT.md", "APPROVED_FINDINGS.md", "northlink_recompute.py"):
            self.assertIn(k, s)

    def test_contract_has_all_acceptance_rows(self):
        s = read_doc("docs/APP_IMPLEMENTATION_CONTRACT.md")
        for i in range(1, 15):
            self.assertIn(f"| AC-{i} |", s)

    def test_superseded_docs_point_to_new_entry(self):
        for f in ("docs/FABLE_BRIEF.md", "docs/HANDOFF_README.md"):
            s = read_doc(f)
            self.assertTrue(s.startswith("# SUPERSEDED"), f)
            self.assertIn("FABLE_52_START_HERE.md", s, f)


class SubmissionDraft(unittest.TestCase):
    def test_numbers_match_canonical_facts(self):
        s = read_doc("submission/SUBMISSION_DRAFT.md")
        d, e, b = FACTS["dettah"]["open_full"], FACTS["extended_126"], FACTS["bias"]
        for needle in (f"{d['slope']:.1f} days per decade", f"{d['lo']:.1f} to {d['hi']:.1f} days", f"n = {d['n']}", f"q = {d['q']:.3f}",
                       f"{FACTS['all_routes_family']['n_tests']} route-level tests", f"{e['nominal']} of {e['n']} trend tests", f"{b['oct_dec_monthly_abs_min']} to {b['oct_dec_monthly_abs_max']} C"):
            self.assertIn(needle, s, needle)

    def test_required_sections_and_placeholders(self):
        s = read_doc("submission/SUBMISSION_DRAFT.md")
        for h in ("Problem statement", "Challenge alignment", "Scientific contribution", "Prior work and originality limits", "NASA data use", "Other sources",
                  "Real finding and its uncertainty", "Real-world relevance", "What Frostline does not claim", "AI-use disclosure", "Links to fill in after deployment"):
            self.assertIn(f"## {h}", s)
        self.assertIn("not yet done", s)
        self.assertIn("[____]", s)


class Branding(unittest.TestCase):
    """Public product is Frostline by Strongest Soldiers. Legacy names may survive only as technical identifiers
    (northlink_*.py module names) and in the North Star's migration note."""
    LEGACY = re.compile(r"Asterfen|NorthLink|NORTHLINK|North Link|North-Link", re.I)
    # lowercase code identifiers such as northlink_metrics / northlink_app.py are preserved on purpose
    IDENT = re.compile(r"northlink_[a-z_]+(\.py)?|load_northlink_data")

    def public_files(self):
        out = ["README.md", "UI/README.md", "UI/northlink_app.py", "UI/standalone_prototype.html", "submission/SUBMISSION_DRAFT.md"]
        out += [f"docs/{n}" for n in sorted(os.listdir(os.path.join(ROOT, "docs"))) if n.endswith(".md") and n != "FROSTLINE_NORTH_STAR.md"]
        return out

    def test_no_legacy_branding_in_public_files(self):
        for f in self.public_files():
            lines = open(os.path.join(ROOT, f), encoding="utf-8").read().splitlines()
            # a line tagged "[legacy-name note]" is an accurately labelled historical migration note
            text = self.IDENT.sub("", "\n".join(l for l in lines if "[legacy-name note]" not in l))
            m = self.LEGACY.search(text)
            self.assertIsNone(m, f"{f}: legacy name {m.group(0) if m else ''}")

    def test_north_star_exists_with_required_scope(self):
        s = read_doc("docs/FROSTLINE_NORTH_STAR.md").lower()
        for k in ("strongest soldiers", "frostline", "be an earth system trend detective", "guided judge demo", "northern atlas", "variable discovery",
                  "trend detective", "regional trend comparison", "corridor investigation", "timeline", "evidence engine", "source disagreement",
                  "evidence brief", "nasa data eligibility"):
            self.assertIn(k, s, k)

    def test_start_here_names_product_team_and_north_star(self):
        s = read_doc("docs/FABLE_52_START_HERE.md")
        for k in ("Frostline", "Strongest Soldiers", "docs/FROSTLINE_NORTH_STAR.md", "Cason owns Giovanni", "Yao owns scientific sign-off"):
            self.assertIn(k, s, k)

    def test_app_title_is_frostline(self):
        app = open(os.path.join(ROOT, "UI/northlink_app.py"), encoding="utf-8").read()
        self.assertIn('page_title="Frostline - by Strongest Soldiers"', app)


if __name__ == "__main__":
    unittest.main()
