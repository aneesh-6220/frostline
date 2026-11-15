"""Tests for the Giovanni integration, the live NASA POWER adapter, the exploratory engine and the interactive map.

No test calls the network. POWER responses are built from Frostline's own cached NASA POWER daily series (real values) in the
documented POWER JSON layout, so parsing, caching and analysis are exercised on genuine numbers.
"""
import glob
import hashlib
import importlib.util
import json
import os
import re
import sys
import tempfile
import unittest
import warnings

import numpy as np
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
for p in (os.path.join(ROOT, "UI"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)
P = lambda *a: os.path.join(ROOT, *a)  # noqa: E731
APP = P("UI", "frostline_app.py")
warnings.filterwarnings("ignore")
import logging  # noqa: E402

logging.disable(logging.WARNING)

from streamlit.testing.v1 import AppTest  # noqa: E402

from frostline import analysis as an  # noqa: E402
from frostline import data, explore as ex, fmt, giovanni as gv, power_api as pa  # noqa: E402
from frostline import brief  # noqa: E402

DS = data.load_dataset()
RAW = P("data/raw/nasa/giovanni")
G4 = "g4.areaAvgTimeSeries.M2TMNXSLV_5_12_4_T2M.19800101-20251231.114W_62N_113W_62N"
DAILY = pd.read_csv(P("data/processed/nasa_daily_temperature.csv"), parse_dates=["date"])
DETTAH = (62.43, -114.34)


def power_payload(lat, lon, start="20011001", end="20250331", loc="dettah_bay", fill_days=(), unit="C", returned=None):
    d = DAILY[(DAILY.location_id == loc) & (DAILY.date >= pd.Timestamp(start)) & (DAILY.date <= pd.Timestamp(end))]
    vals = {t.strftime("%Y%m%d"): (-999.0 if t.strftime("%Y%m%d") in fill_days else float(v)) for t, v in zip(d.date, d.temperature_c)}
    rl = returned or (lon, lat)
    return {"type": "Feature", "geometry": {"type": "Point", "coordinates": [rl[0], rl[1], 204.71]},
            "properties": {"parameter": {"T2M": vals}},
            "header": {"title": "NASA/POWER Source Native Resolution Daily Data", "api": {"version": "v2.10.3", "name": "POWER Daily API"}, "sources": ["MERRA2"],
                       "fill_value": -999.0, "time_standard": "LST", "start": start, "end": end},
            "messages": [], "parameters": {"T2M": {"units": unit, "longname": "Temperature at 2 Meters"}}}


def params(lat, lon, first, last):
    return pa.request_params(lat, lon, first, last)


class GiovanniIngestAndProvenance(unittest.TestCase):
    def test_raw_files_are_the_verified_originals(self):
        self.assertEqual(hashlib.sha256(open(os.path.join(RAW, G4 + ".csv"), "rb").read()).hexdigest(),
                         "d38952225524e35360425d23eb941abd7fc44acf38540ae87f5621c55c812a7e")
        self.assertEqual(hashlib.sha256(open(os.path.join(RAW, G4 + ".nc"), "rb").read()).hexdigest(),
                         "be265b97b70bfd92490f40c03ab44d24cb2c866474d623af7b545aa3fbc02897")

    def test_provenance_records_header_facts(self):
        p = gv.provenance(DS, "dettah_bay")
        self.assertEqual(p["source_file"], G4 + ".csv")
        self.assertEqual(p["n_months"], "552")
        self.assertEqual(p["n_missing"], "0")
        self.assertEqual((p["first_month"], p["last_month"]), ("1980-01", "2025-12"))
        self.assertEqual(p["user_bounding_box_wsen"], "-114.75,62.2,-113.85,62.75")
        self.assertEqual(p["data_grid_point_wsen"], "-114.375,62.5,-114.375,62.5")
        self.assertEqual(p["units_as_published"], "K")
        self.assertTrue(p["reproduce_url"].startswith("https://giovanni.gsfc.nasa.gov/giovanni/#service=ArAvTs"))
        self.assertIn("data=M2TMNXSLV_5_12_4_T2M", p["reproduce_url"])
        self.assertEqual(float(p["fill_value"]), 1e15)

    def test_grid_point_is_the_dettah_power_cell(self):
        c = pa.merra2_cell(*DETTAH)
        self.assertEqual((c["center_lat"], c["center_lon"]), (62.5, -114.375))

    def test_netcdf_verification_record_passes(self):
        rec = json.load(open(P("data/processed/giovanni_netcdf_verification.json")))
        self.assertEqual(len(rec), 1)
        r = rec[0]
        self.assertTrue(r["all_checks_pass"])
        self.assertEqual((r["n_months"], r["units"], r["first_month"], r["last_month"]), (552, "K", "1980-01", "2025-12"))
        self.assertEqual((r["grid_point_lat"], r["grid_point_lon"]), ("62.5", "-114.375"))
        self.assertLess(r["max_abs_diff_csv_vs_netcdf_K"], 1e-4)

    @unittest.skipUnless(importlib.util.find_spec("h5py"), "h5py not installed (requirements-dev.txt)")
    def test_netcdf_reverification(self):
        sys.path.insert(0, P("scripts"))
        import verify_giovanni_netcdf as v
        r = v.verify(os.path.join(RAW, G4 + ".nc"), os.path.join(RAW, G4 + ".csv"))
        self.assertTrue(r["all_checks_pass"], r["checks"])

    def test_monthly_values_trace_to_raw_rows_with_unit_conversion(self):
        raw = {}
        for ln in open(os.path.join(RAW, G4 + ".csv")):
            if ln[:4].isdigit():
                t, v = ln.strip().split(",")
                raw[(int(t[:4]), int(t[5:7]))] = float(v)
        m = gv.monthly(DS, "dettah_bay")
        self.assertEqual(len(m), 552)
        for r in m.itertuples():
            self.assertAlmostEqual(r.t2m_k_as_published, raw[(r.year, r.month)], places=6)
            self.assertAlmostEqual(r.t2m_c, raw[(r.year, r.month)] - 273.15, places=4)

    def test_seasonal_aggregation_rules(self):
        m = gv.monthly(DS, "dettah_bay").set_index(["year", "month"]).t2m_c
        ann = gv.season_series(DS, "dettah_bay", "ANN").set_index("year")
        self.assertAlmostEqual(ann.loc[1981, "value_c"], np.mean([m[(1981, k)] for k in range(1, 13)]), places=3)
        djf = gv.season_series(DS, "dettah_bay", "DJF").set_index("year")
        self.assertTrue(np.isnan(djf.loc[1980, "value_c"]))          # Dec 1979 is not in the record: incomplete, not filled
        self.assertEqual(djf.loc[1980, "n_months"], 2)
        self.assertAlmostEqual(djf.loc[1981, "value_c"], np.mean([m[(1980, 12)], m[(1981, 1)], m[(1981, 2)]]), places=3)
        od = gv.season_series(DS, "dettah_bay", "octdec_mean_c").set_index("year")
        self.assertAlmostEqual(od.loc[2001, "value_c"], np.mean([m[(2001, k)] for k in (10, 11, 12)]), places=3)

    def test_fill_values_become_missing_and_seasons_stay_incomplete(self):
        d, out = tempfile.mkdtemp(), tempfile.mkdtemp()
        lines = open(os.path.join(RAW, G4 + ".csv")).read().splitlines()
        lines = [("1990-07-01 00:00:00,1000000000000000" if ln.startswith("1990-07-01") else ln) for ln in lines]
        open(os.path.join(d, G4 + ".csv"), "w").write("\n".join(lines) + "\n")
        import subprocess
        r = subprocess.run([sys.executable, "-I", P("scripts/ingest_giovanni_monthly.py"), "--in", d, "--out-dir", out], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        mon = pd.read_csv(os.path.join(out, "giovanni_monthly_t2m.csv"))
        row = mon[(mon.year == 1990) & (mon.month == 7)].iloc[0]
        self.assertTrue(bool(row.missing))
        self.assertTrue(np.isnan(row.t2m_c))
        cal = pd.read_csv(os.path.join(out, "giovanni_t2m_calendar_seasons.csv"))
        for s in ("ANN", "JJA"):
            self.assertTrue(np.isnan(cal[(cal.year == 1990) & (cal.season == s)].mean_c.iloc[0]), s)
        prov = pd.read_csv(os.path.join(out, "giovanni_provenance.csv")).set_index("key").value
        self.assertEqual(prov["n_missing"], "1")

    def test_grid_point_matching_no_study_location_is_refused(self):
        d = tempfile.mkdtemp()
        s = open(os.path.join(RAW, G4 + ".csv")).read().replace('Data Bounding Box:,"-114.375,62.5,-114.375,62.5"', 'Data Bounding Box:,"-100.0,50.0,-100.0,50.0"')
        open(os.path.join(d, G4 + ".csv"), "w").write(s)
        import subprocess
        r = subprocess.run([sys.executable, "-I", P("scripts/ingest_giovanni_monthly.py"), "--in", d, "--out-dir", tempfile.mkdtemp()], capture_output=True, text=True)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("refusing to guess", r.stderr)


class GiovanniAnalysis(unittest.TestCase):
    def test_live_full_record_trend_equals_stored_trend(self):
        st = gv.stored_trends(DS, "dettah_bay").set_index("metric")
        for s in gv.SEASON_ORDER:
            t = gv.trend(DS, "dettah_bay", s)
            self.assertTrue(t.full_record)
            self.assertAlmostEqual(t.slope_per_decade, st.loc[s, "slope_per_decade"], places=3)
            self.assertAlmostEqual(t.p, st.loc[s, "mk_p"], places=4)
            self.assertEqual(t.n, st.loc[s, "n"])
            self.assertEqual(t.q, st.loc[s, "q_bh_within_location"])

    def test_window_is_exploratory_and_too_short_is_not_estimated(self):
        t = gv.trend(DS, "dettah_bay", "ANN", 1990, 2020)
        self.assertFalse(t.full_record)
        self.assertIsNone(t.q)
        self.assertEqual(gv.evidence_state(t), an.EXPLORATORY)
        short = gv.trend(DS, "dettah_bay", "ANN", 2010, 2020)
        self.assertEqual(short.status, "too_few_points")
        self.assertIn("Not estimated", gv.plain_language(short))

    def test_plain_language_and_state_follow_the_numbers(self):
        ann = gv.trend(DS, "dettah_bay", "ANN")
        self.assertLess(ann.ci_low, 0)
        self.assertIn("includes no change", gv.plain_language(ann))
        self.assertEqual(gv.evidence_state(ann), an.UNRESOLVED)
        son = gv.trend(DS, "dettah_bay", "SON")
        self.assertGreater(son.ci_low, 0)
        self.assertLess(son.q, 0.05)
        self.assertIn("excludes no change", gv.plain_language(son))
        self.assertEqual(gv.evidence_state(son), an.SUPPORTED)

    def test_power_cross_check_is_reported_from_complete_months(self):
        c = gv.power_check(DS, "dettah_bay")
        self.assertEqual((c["first"], c["last"]), ("2001-10", "2025-06"))
        self.assertLess(abs(c["mean_diff_giovanni_minus_power_c"]), 0.05)
        self.assertGreater(c["pearson_r"], 0.999)

    def test_brief_and_exports_carry_the_same_numbers(self):
        t = gv.trend(DS, "dettah_bay", "SON")
        h = gv.brief_html(DS, t, "2026-11-15 12:00 UTC")
        self.assertIn(fmt.num(t.slope_per_decade, 3, True), h)
        self.assertIn(fmt.interval(t.ci_low, t.ci_high, 3), h)
        self.assertIn("d38952225524e35360425d23eb941abd7fc44acf38540ae87f5621c55c812a7e", h)
        self.assertIn("never used here to reconstruct daily freezing-degree days", h)
        csv = pd.read_csv(__import__("io").StringIO(gv.export_csv(DS, t)), comment="#")
        self.assertEqual(csv.included_in_trend.sum(), t.n)
        self.assertAlmostEqual(json.loads(gv.record_json(DS, t, "x"))["slope_per_decade"], t.slope_per_decade)

    def test_monthly_values_never_feed_daily_metrics(self):
        for f in ("UI/frostline/giovanni.py", "UI/frostline/views/giovanni_view.py", "scripts/ingest_giovanni_monthly.py"):
            s = open(P(f)).read()
            self.assertNotRegex(s, r"\bfdd\(|thaw_days\(", f)

    def test_curated_dettah_brief_cites_giovanni_and_aklavik_does_not(self):
        b = brief.build(DS, "dettah_bay", "fdd_octdec", 2001, 2024)
        self.assertIn("M2TMNXSLV", b.html)
        self.assertIn("does not enter the daily metrics", b.html)
        self.assertNotIn("does not enter the daily metrics", brief.build(DS, "aklavik_delta", "fdd_octdec", 2001, 2024).html)   # a different grid cell


class PowerParsing(unittest.TestCase):
    def setUp(self):
        self.pp = params(*DETTAH, 2001, 2024)

    def test_valid_response(self):
        r = pa.parse(power_payload(*DETTAH), self.pp)
        self.assertEqual(r.meta["n_days_expected"], len(r.daily))
        self.assertEqual(r.meta["n_fill_or_missing"], 0)
        self.assertEqual((r.meta["returned_lat"], r.meta["returned_lon"]), DETTAH)
        self.assertEqual(r.meta["api_version"], "v2.10.3")
        self.assertEqual(r.meta["grid_cell"]["center_lon"], -114.375)

    def test_fill_values_are_missing(self):
        r = pa.parse(power_payload(*DETTAH, fill_days=("20031105", "20031106")), self.pp)
        self.assertEqual(int(r.daily.temperature_c.isna().sum()), 2)
        self.assertEqual(r.meta["n_fill_or_missing"], 2)

    def test_wrong_unit_wrong_point_and_error_payloads_fail(self):
        with self.assertRaisesRegex(pa.PowerError, "unit"):
            pa.parse(power_payload(*DETTAH, unit="K"), self.pp)
        with self.assertRaisesRegex(pa.PowerError, "instead of the requested"):
            pa.parse(power_payload(*DETTAH, returned=(-120.0, 60.0)), self.pp)
        with self.assertRaisesRegex(pa.PowerError, "no data"):
            pa.parse({"messages": ["The start date is before the data availability"]}, self.pp)
        with self.assertRaises(pa.PowerError):
            pa.parse([], self.pp)

    def test_request_validation(self):
        with self.assertRaisesRegex(pa.PowerError, "outside"):
            pa.validate_request(40.0, -100.0, 2001, 2024)
        with self.assertRaisesRegex(pa.PowerError, "Winters"):
            pa.validate_request(*DETTAH, 1975, 2024)
        with self.assertRaisesRegex(pa.PowerError, "not supported"):
            pa.validate_request(*DETTAH, 2001, 2024, parameter="PRECTOTCORR")
        u = pa.request_url(params(66.256, -128.6349, 1981, 2024))
        self.assertTrue(u.startswith("https://power.larc.nasa.gov/api/temporal/daily/point?"))
        for part in ("parameters=T2M", "latitude=66.26", "longitude=-128.63", "start=19811001", "end=20250331", "format=JSON"):
            self.assertIn(part, u)
        self.assertNotRegex(u, r"(?i)key|token")


class PowerCache(unittest.TestCase):
    def setUp(self):
        pa.clear_memory_cache()
        self.dir = tempfile.mkdtemp()
        os.environ["FROSTLINE_CACHE_DIR"] = self.dir
        self.calls = []

    def tearDown(self):
        os.environ.pop("FROSTLINE_CACHE_DIR", None)
        pa.clear_memory_cache()

    def fetcher(self, url):
        self.calls.append(url)
        q = dict(x.split("=") for x in url.split("?")[1].split("&"))
        return power_payload(float(q["latitude"]), float(q["longitude"]))

    def test_equivalent_requests_hit_the_cache(self):
        a = pa.fetch_daily(62.4301, -114.3399, 2001, 2024, fetcher=self.fetcher)
        b = pa.fetch_daily(62.43, -114.34, 2001, 2024, fetcher=self.fetcher)   # same canonical request
        self.assertEqual(len(self.calls), 1)
        self.assertEqual((a.meta["served_from"], b.meta["served_from"]), ("live NASA POWER request", "memory cache"))
        pa.clear_memory_cache()
        c = pa.fetch_daily(62.43, -114.34, 2001, 2024, fetcher=self.fetcher)
        self.assertEqual((len(self.calls), c.meta["served_from"]), (1, "disk cache"))
        pd.testing.assert_frame_equal(a.daily, c.daily)

    def test_new_point_or_period_is_a_new_request(self):
        pa.fetch_daily(62.43, -114.34, 2001, 2024, fetcher=self.fetcher)
        pa.fetch_daily(62.43, -114.34, 2002, 2024, fetcher=self.fetcher)
        pa.fetch_daily(62.53, -114.34, 2001, 2024, fetcher=self.fetcher)
        self.assertEqual(len(self.calls), 3)

    def test_invalid_response_is_not_cached_and_errors_propagate(self):
        bad = lambda url: {"messages": ["server busy"]}  # noqa: E731
        with self.assertRaises(pa.PowerError):
            pa.fetch_daily(62.43, -114.34, 2001, 2024, fetcher=bad)
        self.assertEqual(glob.glob(os.path.join(self.dir, "*.json")), [])

        def down(url):
            raise pa.PowerError("NASA POWER could not be reached (URLError).")
        with self.assertRaisesRegex(pa.PowerError, "could not be reached"):
            pa.fetch_daily(62.43, -114.34, 2001, 2024, fetcher=down)


class ExploreEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.power = pa.parse(power_payload(*DETTAH), params(*DETTAH, 2001, 2024))

    def test_reproduces_curated_dettah_results_from_the_same_daily_values(self):
        ext = pd.read_csv(P("UI/data_real/extended_trends.csv"))
        for q in ("fdd_octdec", "mean_octdec_c", "mean_janmar_c"):
            r = ex.analyze(self.power, *DETTAH, q, 2001, 2024)
            row = ext[(ext.location_id == "dettah_bay") & (ext.metric == q) & (ext.window == "2001-2024")].iloc[0]
            self.assertEqual(r.n, row.n, q)
            self.assertAlmostEqual(r.slope_per_decade, row.slope_per_decade, places=2, msg=q)
            self.assertAlmostEqual(r.p, row.mk_p, places=4, msg=q)

    def test_changing_question_and_period_recomputes(self):
        a = ex.analyze(self.power, *DETTAH, "fdd_octdec", 2001, 2024)
        b = ex.analyze(self.power, *DETTAH, "fdd_octdec", 2005, 2024)
        c = ex.analyze(self.power, *DETTAH, "mean_janmar_c", 2001, 2024)
        self.assertNotEqual(a.slope_per_decade, b.slope_per_decade)
        self.assertEqual((a.n, b.n), (24, 20))
        self.assertNotEqual(a.q["unit"], c.q["unit"])
        short = ex.analyze(self.power, *DETTAH, "fdd_octdec", 2015, 2024)
        self.assertEqual(short.status, "too_few_points")
        self.assertIn("Not estimated", ex.headline(short))

    def test_missing_days_exclude_seasons_not_fill_them(self):
        p = pa.parse(power_payload(*DETTAH, fill_days=("20031105",)), params(*DETTAH, 2001, 2024))
        r = ex.analyze(p, *DETTAH, "fdd_octdec", 2001, 2024)
        self.assertEqual((r.n, r.excluded), (23, 1))
        self.assertTrue(np.isnan(r.table.set_index("season_start_year").loc[2003, "fdd_octdec"]))

    def test_brief_csv_json_and_headline_agree(self):
        r = ex.analyze(self.power, *DETTAH, "mean_octdec_c", 2001, 2024)
        r.meta.update(retrieved_utc="2026-11-15T15:00:00Z", served_from="test", url=pa.request_url(params(*DETTAH, 2001, 2024)))
        h = ex.brief_html(r, "2026-11-15 15:00 UTC")
        import html as _h
        self.assertIn(_h.escape(ex.headline(r)), h)
        self.assertIn(fmt.interval(r.ci_low, r.ci_high, 3), h)
        self.assertIn("Exploratory", h)
        self.assertIn("No road-operation records", h)
        self.assertIn("power.larc.nasa.gov", h)
        csv = pd.read_csv(__import__("io").StringIO(ex.export_csv(r)), comment="#")
        self.assertEqual(int(csv.included_in_trend.sum()), r.n)
        pd.testing.assert_series_equal(csv.mean_octdec_c.round(6), r.table.mean_octdec_c.round(6), check_names=False)
        j = json.loads(ex.record_json(r, "x"))
        self.assertAlmostEqual(j["slope_per_decade"], r.slope_per_decade)
        self.assertEqual(j["headline"], ex.headline(r))
        self.assertNotIn("road opens on", h.lower())


class MapSelection(unittest.TestCase):
    def test_click_resolution(self):
        from frostline.views import atlas
        loc = an.locations(DS)["aklavik_delta"]
        self.assertEqual(atlas.resolve_click(DS, loc.lat, loc.lon), ("curated", "aklavik_delta"))
        self.assertEqual(atlas.resolve_click(DS, 66.25612, -128.63487), ("explore", (66.26, -128.63)))
        self.assertEqual(atlas.resolve_click(DS, 40.0, -100.0)[0], "outside")

    def test_map_is_real_leaflet_with_attributed_tiles(self):
        from frostline.views import atlas
        h = atlas.build_map(DS, "dettah_bay").get_root().render()
        self.assertIn("L.map", h)
        self.assertIn("server.arcgisonline.com", h)
        self.assertIn("Esri", h)
        self.assertIn("OpenStreetMap", h)
        import folium
        m = folium.Map()
        atlas.selection_layer((66.26, -128.63)).add_to(m)
        sel = m.get_root().render()
        self.assertIn("Exploratory point 66.26 N, 128.63 W", sel)

    def _app(self, state, env=None):
        old = {k: os.environ.get(k) for k in (env or {})}
        os.environ.update(env or {})
        try:
            at = AppTest.from_file(APP, default_timeout=90)
            at.session_state["start_view"] = "atlas"
            for k, v in state.items():
                at.session_state[k] = v
            at.run()
            return at, old
        except Exception:
            raise

    def test_curated_button_updates_investigation_and_clears_point(self):
        at, _ = self._app({"xp_point": (66.26, -128.63)})
        self.assertEqual(len(at.exception), 0)
        at.button(key="atlas_pick_aklavik_delta").click().run()
        self.assertEqual(len(at.exception), 0)
        self.assertEqual(at.session_state["loc"], "aklavik_delta")
        self.assertIsNone(at.session_state["xp_point"])

    def test_coordinate_form_selects_an_exploratory_point(self):
        at, _ = self._app({})
        at.number_input(key="xp_lat").set_value(65.0)
        at.number_input(key="xp_lon").set_value(-125.5)
        at.button(key="xp_use").click().run()
        self.assertEqual(len(at.exception), 0)
        self.assertEqual(at.session_state["xp_point"], (65.0, -125.5))
        text = " ".join(m.value for m in at.markdown)
        self.assertIn("65.00 N, 125.50 W", text)
        self.assertIn("Retrieve", " ".join(b.label for b in at.button))

    def test_retrieve_runs_the_engine_and_offers_the_brief(self):
        cache = tempfile.mkdtemp()
        pa.clear_memory_cache()
        pt = (62.43, -114.34)
        prm = pa.request_params(*pt, pa.FIRST_WINTER, pa.LAST_WINTER)
        with open(os.path.join(cache, pa.cache_key(prm) + ".json"), "w") as fh:
            json.dump({"retrieved_utc": "2026-11-15T15:00:00Z", "params": prm, "payload": power_payload(*pt)}, fh)
        os.environ["FROSTLINE_CACHE_DIR"] = cache
        try:
            at = AppTest.from_file(APP, default_timeout=90)
            at.session_state["start_view"] = "atlas"
            at.session_state["xp_point"] = pt
            at.run()
            at.button(key="xp_fetch").click().run()
            self.assertEqual(len(at.exception), 0, [e.value for e in at.exception])
            text = " ".join(m.value for m in at.markdown)
            self.assertIn("disk cache", text)
            r = ex.analyze(pa.fetch_daily(*pt, pa.FIRST_WINTER, pa.LAST_WINTER), *pt, "fdd_octdec", pa.FIRST_WINTER, pa.LAST_WINTER)
            self.assertIn(fmt.num(r.slope_per_decade, 1, True), text)          # the panel shows the engine's number
            self.assertIn("Exploratory climate analysis", text)
            self.assertEqual(len([e for e in at.main if e.type == "plotly_chart"]), 1)
        finally:
            os.environ.pop("FROSTLINE_CACHE_DIR", None)
            pa.clear_memory_cache()

    def test_offline_failure_is_reported_and_curated_cases_still_work(self):
        pa.clear_memory_cache()
        os.environ["FROSTLINE_CACHE_DIR"] = tempfile.mkdtemp()
        real = pa._http_get_json
        pa._http_get_json = lambda url: (_ for _ in ()).throw(pa.PowerError("NASA POWER could not be reached (URLError). The curated case studies still work offline."))
        try:
            at = AppTest.from_file(APP, default_timeout=90)
            at.session_state["start_view"] = "atlas"
            at.session_state["xp_point"] = (64.0, -120.0)
            at.run()
            at.button(key="xp_fetch").click().run()
            self.assertEqual(len(at.exception), 0)
            self.assertIn("could not be reached", " ".join(e.value for e in at.error))
            at.button(key="atlas_pick_dettah_bay").click().run()
            self.assertEqual(len(at.exception), 0)
            self.assertEqual(at.session_state["loc"], "dettah_bay")
        finally:
            pa._http_get_json = real
            os.environ.pop("FROSTLINE_CACHE_DIR", None)


class GiovanniView(unittest.TestCase):
    def test_view_renders_traceable_numbers(self):
        at = AppTest.from_file(APP, default_timeout=90)
        at.session_state["start_view"] = "giovanni"
        at.run()
        self.assertEqual(len(at.exception), 0)
        text = " ".join(m.value for m in at.markdown)
        t = gv.trend(DS, "dettah_bay", "ANN")
        self.assertIn(fmt.num(t.slope_per_decade, 2, True), text)
        self.assertIn("-114.375,62.5", text)
        self.assertIn("not the daily NASA POWER values", text)
        at.selectbox(key="gv_season").set_value("SON").run()
        self.assertEqual(len(at.exception), 0)
        self.assertIn(fmt.num(gv.trend(DS, "dettah_bay", "SON").slope_per_decade, 2, True), " ".join(m.value for m in at.markdown))


if __name__ == "__main__":
    unittest.main()
