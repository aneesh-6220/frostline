"""Known-answer tests for docs/VALIDATION_CASES.md. Run: python3 -I -m unittest discover -s tests -v
(from the repository root; tests add ../scripts to the path)."""
import datetime as dt
import math
import os
import sys
import unittest

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import northlink_metrics as m  # noqa: E402


def season_df(y, temps_by_part=None, early=-10.0, mid=-10.0):
    """Complete Oct 1 y - Mar 31 y+1 frame at constant temperatures."""
    d = pd.date_range(dt.date(y, 10, 1), dt.date(y + 1, 3, 31), freq="D")
    t = np.where(d.month >= 10, early, mid).astype(float)
    return pd.DataFrame({"date": d, "temperature_c": t})


class TestSeasonsAndUnits(unittest.TestCase):
    def test_kelvin(self):
        self.assertAlmostEqual(float(m.kelvin_to_celsius(273.15)), 0.0)
        self.assertAlmostEqual(float(m.kelvin_to_celsius(263.15)), -10.0)

    def test_expected_days_and_leap(self):
        self.assertEqual(m.expected_days(2022, "early"), 92)
        self.assertEqual(m.expected_days(2022, "mid"), 90)    # 2023 not leap
        self.assertEqual(m.expected_days(2023, "mid"), 91)    # 2024 leap
        self.assertEqual(m.expected_days(2023, "full"), 183)
        self.assertEqual(m.expected_days(2024, "full"), 182)  # 2025 not leap

    def test_season_assignment(self):
        self.assertEqual(m.season_start_year_from_date(dt.date(2023, 12, 24)), 2023)
        self.assertEqual(m.season_start_year_from_date(dt.date(2024, 4, 9)), 2023)
        self.assertEqual(m.season_start_year_from_date(dt.date(2024, 1, 28)), 2023)
        self.assertEqual(m.season_start_year_from_date(dt.date(2024, 10, 1)), 2024)


class TestFDD(unittest.TestCase):
    def test_ten_days_minus10_is_100(self):
        df = pd.DataFrame({"date": pd.date_range("2001-10-01", periods=92), "temperature_c": 0.0})
        df.loc[:9, "temperature_c"] = -10.0
        self.assertEqual(m.fdd(df, 2001, "early"), 100.0)

    def test_ten_days_plus5_is_0(self):
        df = pd.DataFrame({"date": pd.date_range("2001-10-01", periods=92), "temperature_c": 0.0})
        df.loc[:9, "temperature_c"] = 5.0
        self.assertEqual(m.fdd(df, 2001, "early"), 0.0)

    def test_full_season_constant(self):
        df = season_df(2010, early=-10.0)
        self.assertEqual(m.fdd(df, 2010), 920.0)  # 92 days x 10 C

    def test_missing_day_gives_nan_not_zero(self):
        df = season_df(2010).drop(index=5)
        self.assertTrue(math.isnan(m.fdd(df, 2010)))
        cov = m.season_coverage(df, 2010, "early")
        self.assertEqual(cov.valid, 91)
        self.assertEqual(len(cov.missing_dates), 1)
        self.assertFalse(cov.complete)

    def test_nan_value_not_valid(self):
        df = season_df(2010)
        df.loc[3, "temperature_c"] = np.nan
        self.assertTrue(math.isnan(m.fdd(df, 2010)))

    def test_duplicate_date_flagged(self):
        df = season_df(2010)
        df = pd.concat([df, df.iloc[[7]]])
        cov = m.season_coverage(df, 2010, "early")
        self.assertFalse(cov.complete)
        self.assertEqual(len(cov.duplicate_dates), 1)

    def test_sentinel_invalid(self):
        df = season_df(2010)
        df.loc[9, "temperature_c"] = -9999.0
        self.assertTrue(math.isnan(m.fdd(df, 2010)))

    def test_leap_year_midwinter(self):
        df = season_df(2023)  # Feb 29, 2024 exists
        self.assertEqual(m.season_coverage(df, 2023, "mid").expected, 91)
        self.assertTrue(m.season_coverage(df, 2023, "mid").complete)


class TestThaw(unittest.TestCase):
    def test_thaw_count(self):
        df = season_df(2010, mid=-10.0)
        idx = df.index[(df["date"] >= "2011-02-01") & (df["date"] < "2011-02-04")]
        df.loc[idx, "temperature_c"] = 1.0
        self.assertEqual(m.thaw_days(df, 2010), 3.0)
        self.assertEqual(m.longest_thaw_run(df, 2010), 3.0)

    def test_zero_is_not_thaw(self):
        df = season_df(2010, mid=0.0)
        self.assertEqual(m.thaw_days(df, 2010), 0.0)


class TestMeans(unittest.TestCase):
    def test_seasonal_mean(self):
        df = season_df(2010, early=-10.0, mid=-20.0)
        self.assertAlmostEqual(m.seasonal_mean(df, 2010, "early"), -10.0)
        self.assertAlmostEqual(m.seasonal_mean(df, 2010, "mid"), -20.0)


class TestRoad(unittest.TestCase):
    def test_dec_open_april_close(self):
        r = m.road_metrics(dt.date(2023, 12, 24), dt.date(2024, 4, 9), 2023)
        self.assertEqual(r["open_day"], 84)        # Oct 1 -> Dec 24 = 31+30+23
        self.assertEqual(r["close_day"], 191)      # Oct 1 -> Apr 9
        self.assertEqual(r["open_to_close_days"], 107)

    def test_dettah_2024_hand_check(self):
        # Workbook row 2024/25 Dettah: 2024-12-21 -> 2025-04-08, 108 days (matches NWT 'Days' column)
        r = m.road_metrics(dt.date(2024, 12, 21), dt.date(2025, 4, 8), 2024)
        self.assertEqual(r["open_to_close_days"], 108)


class TestTrend(unittest.TestCase):
    years = np.arange(2001, 2025)

    def test_constant_series(self):
        t = m.trend(self.years, np.full(len(self.years), 5.0))
        self.assertEqual(t.status, "constant_series")
        self.assertEqual(t.slope_per_decade, 0.0)
        self.assertTrue(math.isnan(t.mk_p))

    def test_positive_linear(self):
        t = m.trend(self.years, 2.0 * (self.years - 2001))   # +2 per year
        self.assertAlmostEqual(t.slope_per_year, 2.0)
        self.assertAlmostEqual(t.slope_per_decade, 20.0)
        self.assertAlmostEqual(t.mk_tau, 1.0)
        self.assertLess(t.mk_p, 1e-6)
        self.assertLessEqual(t.ci_low_per_decade, 20.0)
        self.assertGreaterEqual(t.ci_high_per_decade, 20.0)

    def test_negative_linear(self):
        t = m.trend(self.years, -0.5 * (self.years - 2001))
        self.assertAlmostEqual(t.slope_per_decade, -5.0)
        self.assertEqual(t.mk_tau, -1.0)

    def test_too_few(self):
        self.assertEqual(m.trend([2001, 2002, 2003], [1, 2, 3]).status, "too_few_points")

    def test_nan_dropped_before_fit(self):
        v = 2.0 * (self.years - 2001).astype(float)
        v[3] = np.nan
        t = m.trend(self.years, v)
        self.assertEqual(t.n, len(self.years) - 1)
        self.assertAlmostEqual(t.slope_per_year, 2.0)

    def test_mann_kendall_hand_check(self):
        # y = [1,2,3,4,5,6,7,8,9,10]: S=45, Var=125, z=44/sqrt(125)
        tau, z, p = m.mann_kendall(np.arange(1, 11))
        self.assertAlmostEqual(tau, 1.0)
        self.assertAlmostEqual(z, 44 / math.sqrt(125), places=9)

    def test_mann_kendall_ties(self):
        # y = [1,1,2,2]: S=4, ties t=2,2 -> Var=(4*3*13 - 2*(2*1*9))/18 = (156-36)/18
        tau, z, p = m.mann_kendall([1, 1, 2, 2])
        self.assertAlmostEqual(z, 3 / math.sqrt((156 - 36) / 18), places=9)


class TestRegional(unittest.TestCase):
    def test_diff_series_zero_when_identical(self):
        y = np.arange(2001, 2025)
        a = np.linspace(0, 10, len(y))
        t = m.difference_series_trend(y, a, a)
        self.assertEqual(t.status, "constant_series")

    def test_one_significant_one_not_not_automatically_different(self):
        # Documented rule: compare slopes via the difference series, not by p-values.
        y = np.arange(2001, 2025)
        rng = np.random.default_rng(1)
        a = 0.3 * (y - 2001) + rng.normal(0, 1, len(y))
        b = 0.28 * (y - 2001) + rng.normal(0, 3, len(y))
        d = m.difference_series_trend(y, a, b)
        self.assertEqual(d.status, "ok")
        self.assertLess(abs(d.slope_per_decade), 3.0)  # no large difference in trend


if __name__ == "__main__":
    unittest.main()
