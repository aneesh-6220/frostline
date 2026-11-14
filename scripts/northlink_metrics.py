"""Frostline reference implementation of every metric in docs/SCIENTIFIC_METHODS.md.

Pure functions, only numpy/pandas/scipy. Shaurya/Fable should reuse or re-implement
these and must pass tests/test_metrics.py (docs/VALIDATION_CASES.md).

Conventions
-----------
* Winter y = Oct 1 of year y through Mar 31 of year y+1 ("season_start_year").
* Daily mean temperature in degrees Celsius. Kelvin -> Celsius: C = K - 273.15.
* No silent gap filling: incomplete seasons return NaN plus a coverage flag.
"""
from __future__ import annotations

import datetime as dt
import math
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import stats

K_TO_C = 273.15
MOSTLY_TIED_FRACTION = 0.75  # trend() refuses to estimate when this share of values is identical


def kelvin_to_celsius(k):
    return np.asarray(k, dtype=float) - K_TO_C


# ---------------------------------------------------------------- seasons
def season_start_year_from_date(d: dt.date) -> int:
    """Winter a calendar date belongs to for OPENING/CLOSING dates.

    Oct-Dec belong to the winter that starts that year; Jan-Sep belong to the
    winter that started the previous October. (No NWT road opens Jul-Sep.)
    """
    return d.year if d.month >= 10 else d.year - 1


def early_winter_range(y: int):
    return dt.date(y, 10, 1), dt.date(y, 12, 31)


def midwinter_range(y: int):
    return dt.date(y + 1, 1, 1), dt.date(y + 1, 3, 31)


def expected_days(y: int, part: str = "full") -> int:
    """Expected number of daily records. early=92 always; mid=90 or 91; full=182 or 183."""
    def n(r):
        return (r[1] - r[0]).days + 1
    e, m = n(early_winter_range(y)), n(midwinter_range(y))
    return {"early": e, "mid": m, "full": e + m}[part]


def day_of_winter(d: dt.date, y: int) -> int:
    """Days since Oct 1 of winter y (Oct 1 = 0)."""
    return (d - dt.date(y, 10, 1)).days


# ---------------------------------------------------------------- coverage
@dataclass
class Coverage:
    expected: int
    valid: int
    missing_dates: list
    duplicate_dates: list
    invalid_values: int
    complete: bool

    @property
    def percent(self):
        return 100.0 * self.valid / self.expected if self.expected else float("nan")


def season_coverage(df: pd.DataFrame, y: int, part: str = "full",
                    lo_c: float = -70.0, hi_c: float = 45.0) -> Coverage:
    """df has columns date (datetime-like) and temperature_c (NaN = missing).

    A day counts as valid if it appears exactly once, is not NaN, and lies in
    [lo_c, hi_c]. Duplicates are NOT counted as valid (the season is flagged).
    """
    rng = {"early": [early_winter_range(y)], "mid": [midwinter_range(y)],
           "full": [early_winter_range(y), midwinter_range(y)]}[part]
    want = pd.DatetimeIndex(sorted(set(
        d for a, b in rng for d in pd.date_range(a, b, freq="D"))))
    d = df.copy()
    d["date"] = pd.to_datetime(d["date"])
    d = d[d["date"].isin(want)]
    dup = d["date"][d["date"].duplicated(keep=False)].drop_duplicates().dt.date.tolist()
    first = d.drop_duplicates("date", keep=False)
    bad = first["temperature_c"].isna() | ~first["temperature_c"].between(lo_c, hi_c)
    ok_dates = set(first.loc[~bad, "date"])
    missing = [x.date() for x in want if x not in ok_dates]
    exp = len(want)
    valid = len(ok_dates)
    return Coverage(exp, valid, missing, dup, int(bad.sum()), valid == exp and not dup)


# ---------------------------------------------------------------- metrics
def _clean_series(df, y, part):
    cov = season_coverage(df, y, part)
    return cov


def fdd(df: pd.DataFrame, y: int, part: str = "early") -> float:
    """Freezing degree-days Oct-Dec (default): sum(max(0, -T)). NaN if incomplete."""
    cov = season_coverage(df, y, part)
    if not cov.complete:
        return float("nan")
    rng = early_winter_range(y) if part == "early" else midwinter_range(y)
    d = df.assign(date=pd.to_datetime(df["date"]))
    t = d[(d["date"] >= pd.Timestamp(rng[0])) & (d["date"] <= pd.Timestamp(rng[1]))]["temperature_c"]
    return float(np.maximum(0.0, -t.to_numpy()).sum())


def thaw_days(df: pd.DataFrame, y: int) -> float:
    """Jan-Mar count of days with daily mean > 0 C. NaN if incomplete."""
    cov = season_coverage(df, y, "mid")
    if not cov.complete:
        return float("nan")
    a, b = midwinter_range(y)
    d = df.assign(date=pd.to_datetime(df["date"]))
    t = d[(d["date"] >= pd.Timestamp(a)) & (d["date"] <= pd.Timestamp(b))]["temperature_c"]
    return float((t > 0).sum())


def longest_thaw_run(df: pd.DataFrame, y: int) -> float:
    cov = season_coverage(df, y, "mid")
    if not cov.complete:
        return float("nan")
    a, b = midwinter_range(y)
    d = df.assign(date=pd.to_datetime(df["date"]))
    t = d[(d["date"] >= pd.Timestamp(a)) & (d["date"] <= pd.Timestamp(b))].sort_values("date")["temperature_c"]
    best = cur = 0
    for v in (t > 0):
        cur = cur + 1 if v else 0
        best = max(best, cur)
    return float(best)


def seasonal_mean(df: pd.DataFrame, y: int, part: str) -> float:
    """Mean daily temperature for 'early' (Oct-Dec), 'mid' (Jan-Mar) or 'full'."""
    cov = season_coverage(df, y, part)
    if not cov.complete:
        return float("nan")
    rng = {"early": [early_winter_range(y)], "mid": [midwinter_range(y)],
           "full": [early_winter_range(y), midwinter_range(y)]}[part]
    d = df.assign(date=pd.to_datetime(df["date"]))
    m = np.zeros(len(d), bool)
    for a, b in rng:
        m |= ((d["date"] >= pd.Timestamp(a)) & (d["date"] <= pd.Timestamp(b))).to_numpy()
    return float(d.loc[m, "temperature_c"].mean())


# ----------------------------------------------------- road-operation metrics
def road_metrics(open_date: dt.date, close_date: dt.date, y: int) -> dict:
    """Opening/closing day relative to Oct 1 and the open-to-close interval.

    The interval is NOT total usable days (temporary closures are not recorded).
    """
    return {
        "open_day": day_of_winter(open_date, y),
        "close_day": day_of_winter(close_date, y),
        "open_to_close_days": (close_date - open_date).days,
    }


# ----------------------------------------------------------------- trends
@dataclass
class TrendResult:
    n: int
    slope_per_year: float
    slope_per_decade: float
    ci_low_per_decade: float
    ci_high_per_decade: float
    mk_tau: float
    mk_z: float
    mk_p: float
    lag1_autocorr_resid: float
    status: str  # ok | too_few_points | constant_series | mostly_tied


def mann_kendall(y) -> tuple[float, float, float]:
    """Mann-Kendall test with tie correction. Returns (tau, z, two-sided p).

    S = sum over i<j of sign(y_j - y_i); Var(S) = [n(n-1)(2n+5) - sum t(t-1)(2t+5)]/18.
    z = (S-1)/sqrt(Var) if S>0, (S+1)/sqrt(Var) if S<0, 0 if S=0 (continuity correction).
    """
    y = np.asarray(y, float)
    n = len(y)
    s = 0
    for i in range(n - 1):
        s += np.sign(y[i + 1:] - y[i]).sum()
    _, counts = np.unique(y, return_counts=True)
    var = (n * (n - 1) * (2 * n + 5) - np.sum(counts * (counts - 1) * (2 * counts + 5))) / 18.0
    if var <= 0:
        return float("nan"), float("nan"), float("nan")
    z = 0.0 if s == 0 else (s - 1) / math.sqrt(var) if s > 0 else (s + 1) / math.sqrt(var)
    p = 2 * (1 - stats.norm.cdf(abs(z)))
    tau = s / (n * (n - 1) / 2)
    return float(tau), float(z), float(p)


def lag1_autocorr(resid) -> float:
    r = np.asarray(resid, float)
    r = r - r.mean()
    den = (r ** 2).sum()
    return float((r[1:] * r[:-1]).sum() / den) if den > 0 and len(r) > 2 else float("nan")


def trend(years, values, min_points: int = 15, alpha: float = 0.05) -> TrendResult:
    """Theil-Sen slope with (1-alpha) CI, Mann-Kendall p, residual lag-1 autocorrelation.

    NaN values (excluded seasons) are dropped BEFORE the calculation; callers must
    report how many seasons were dropped. Constant series -> slope 0, p undefined (NaN).
    """
    ys = np.asarray(years, float)
    v = np.asarray(values, float)
    ok = ~np.isnan(v)
    ys, v = ys[ok], v[ok]
    n = len(v)
    if n < min_points:
        return TrendResult(n, *[float("nan")] * 8, "too_few_points")
    if np.all(v == v[0]):
        return TrendResult(n, 0.0, 0.0, 0.0, 0.0, float("nan"), float("nan"), float("nan"),
                           float("nan"), "constant_series")
    # Degenerate series: when >= 75% of the values are identical (e.g. thaw-day counts that are
    # zero in almost every winter) Theil-Sen returns slope 0 with a zero-width CI and the
    # Mann-Kendall p-value is dominated by ties. No slope or p-value is reported.
    if np.unique(v, return_counts=True)[1].max() / n >= MOSTLY_TIED_FRACTION:
        return TrendResult(n, *[float("nan")] * 8, "mostly_tied")
    slope, intercept, lo, hi = stats.theilslopes(v, ys, alpha=1 - alpha)
    tau, z, p = mann_kendall(v)
    resid = v - (intercept + slope * ys)
    return TrendResult(n, slope, slope * 10, lo * 10, hi * 10, tau, z, p,
                       lag1_autocorr(resid), "ok")


def spearman(x, y) -> tuple[float, float, int]:
    """Exploratory rank correlation on pairs with both values present."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    ok = ~(np.isnan(x) | np.isnan(y))
    if ok.sum() < 8 or np.all(x[ok] == x[ok][0]) or np.all(y[ok] == y[ok][0]):
        return float("nan"), float("nan"), int(ok.sum())
    r, p = stats.spearmanr(x[ok], y[ok])
    return float(r), float(p), int(ok.sum())


def difference_series_trend(years, a, b, min_points: int = 15) -> TrendResult:
    """Regional comparison: trend of (a - b) on common, complete years."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    return trend(years, a - b, min_points)
