"""Investigation objects: per-winter series, trend findings, regional comparisons and associations.

This module contains no statistical method. Every estimate is produced by the approved functions in
scripts/northlink_recompute.py (which call northlink_metrics.trend and northlink_stats.block_bootstrap_slope).

Statistics always match the selection (docs/APP_IMPLEMENTATION_CONTRACT.md section 4):
  * a precomputed result is used only for its own fixed window, and is cross-checked against a live
    recomputation before it is shown;
  * any other window is recomputed and carries no multiplicity-adjusted q;
  * fewer than 15 winters, or a mostly tied series, yields no slope, interval or p.
"""
from __future__ import annotations

import functools
import os
import sys
from dataclasses import asdict, dataclass, field

import numpy as np
import pandas as pd

from . import fmt
from .data import REPO_ROOT, DataError, Dataset
from .registry import VARIABLES, Variable, build_locations

_SCRIPTS = os.path.join(REPO_ROOT, "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import northlink_metrics as nm  # noqa: E402
import northlink_recompute as rc  # noqa: E402
import northlink_stats as ns  # noqa: E402

MIN_SEASONS = rc.MIN_SEASONS
AUTOCORR_FLAG = 0.3
CROSS_CHECK_INTERVAL_TOL = 0.02   # share of the stored interval width
CROSS_CHECK_P_TOL = 0.03
ALPHA = 0.05

# evidence states shown instead of a binary significant / not significant label
SUPPORTED = "supported"
UNRESOLVED = "unresolved"
EXPLORATORY = "exploratory"
INSUFFICIENT = "insufficient"
UNAVAILABLE = "unavailable"

STATE_LABEL = {
    SUPPORTED: "Supported historical trend",
    UNRESOLVED: "Trend not statistically resolved",
    EXPLORATORY: "Exploratory window",
    INSUFFICIENT: "Insufficient data",
    UNAVAILABLE: "Inference unavailable",
}

# wording templates (docs/FABLE_HANDOFF_FINAL.md section 13); the sentence is always generated from the computed status
T_NONSIG = "Not statistically distinguishable from no change in this record. That is not proof of no change."
T_SUPPORTED = "Evidence of a monotonic change in this record (q = {q} within the stated family). Exploratory; this does not show what caused it."
T_INCONCLUSIVE = ("Inconclusive after correction for multiple testing (unadjusted p = {p}, q = {q} within the stated family). "
                  "This is not evidence of no change.")
T_EXPL_SMALL_P = ("Unadjusted p = {p} for a user-selected window. Exploratory, not adjusted for multiple testing: this is not a supported "
                  "finding and does not show what produced any change.")
T_EXPL_NONSIG = T_NONSIG + " Exploratory, not adjusted for multiple testing."
T_TOO_FEW = "Too few seasons: not estimated. At least {m} complete winters are required and this selection has {n}."
T_TIED = "Not estimated: one value fills at least 75% of the winters in this selection, so a slope or p-value would be meaningless."
T_CONSTANT = "Not estimated: every winter in this selection has the same value."
T_ROAD = "Opening and closing dates are government records of operations, not measurements of ice thickness. The interval is not usable days."

FAMILY_LABEL = {
    "F1_all_extended": "all 126 extended trend tests (14 metrics x 9 corridors, winters 2001/02 to 2024/25)",
    "F4_road_record_all_routes": "all 51 road-date tests across 17 NWT routes (winters 1993/94 to 2024/25)",
}


@dataclass(frozen=True)
class Series:
    location_id: str
    variable_id: str
    years: tuple
    values: tuple          # NaN marks a winter without a usable value; never zero-filled
    expected_years: tuple  # every winter the source record spans for this variable
    source_file: str
    note: str = ""

    def frame(self) -> pd.DataFrame:
        return pd.DataFrame({"season_start_year": list(self.years), "value": list(self.values)})

    def window(self, first: int, last: int) -> pd.DataFrame:
        f = self.frame()
        return f[(f.season_start_year >= first) & (f.season_start_year <= last)].reset_index(drop=True)


@dataclass(frozen=True)
class Finding:
    location_id: str
    variable_id: str
    first: int
    last: int
    n: int
    n_expected: int
    status: str            # ok | too_few_points | mostly_tied | constant_series
    state: str
    window_kind: str       # fixed | exploratory
    slope: float | None = None
    ci_low: float | None = None
    ci_high: float | None = None
    bb_low: float | None = None
    bb_high: float | None = None
    p: float | None = None
    lag1: float | None = None
    autocorr_flag: bool = False
    q: float | None = None
    q_family: str | None = None
    q_family_n: int | None = None
    holm: float | None = None
    intercept: float | None = None     # display only: median(y) - slope * median(x), as in the approved estimator
    pivot_year: float | None = None
    pivot_value: float | None = None
    stored_source: str | None = None   # file that holds the precomputed fixed-window result
    cross_checked: bool = False
    sentence: str = ""
    direction: str = ""
    extra_sentences: tuple = ()

    @property
    def state_label(self) -> str:
        return STATE_LABEL[self.state]

    @property
    def estimated(self) -> bool:
        return self.status == "ok"

    def as_dict(self) -> dict:
        d = asdict(self)
        d["state_label"] = self.state_label
        return d


def locations(ds: Dataset) -> dict:
    return _locations(ds)


@functools.lru_cache(maxsize=8)
def _locations(ds: Dataset) -> dict:
    return build_locations(ds)


# --------------------------------------------------------------------- series
@functools.lru_cache(maxsize=512)
def get_series(ds: Dataset, location_id: str, variable_id: str) -> Series:
    """Per-winter values for a location and variable, from the approved per-winter files only."""
    locs = locations(ds)
    if location_id not in locs:
        raise KeyError(f"no data for location '{location_id}'")
    loc, var = locs[location_id], VARIABLES[variable_id]
    if var.locations == "primary" and not loc.is_primary_pair:
        raise KeyError(f"{var.short} is not available for {loc.name}")
    if var.kind == "road":
        ops = ds["road_operations_all_routes"]
        s = rc.road_series(ops, loc.road_id, var.column)
        expected = tuple(sorted(int(y) for y in ops[ops.road_id == loc.road_id].season_start_year.unique()))
        got = dict(zip(s.season_start_year.astype(int), s[var.column].astype(float)))
        values = tuple(got.get(y, float("nan")) for y in expected)
        return Series(location_id, variable_id, expected, values, expected, "road_operations_all_routes.csv",
                      "Verified rows only; winters without a verified record are left empty.")
    if var.table == "climate_annual":
        ca = ds["climate_annual"]
        d = ca[(ca.corridor_id == location_id) & (ca.metric == var.column)].sort_values("season_year")
        if d.empty:
            raise KeyError(f"{var.short} is not available for {loc.name}")
        # a winter with missing days carries no value (docs/DATA_QUALITY.md); it is never treated as zero
        vals = [float(v) if int(m) == 0 else float("nan") for v, m in zip(d.value, d.missing_days)]
        years = tuple(int(y) for y in d.season_year)
        return Series(location_id, variable_id, years, tuple(vals), years, "climate_annual.csv")
    sm = ds["season_metrics_extended"]
    d = rc.climate_series(sm, location_id, var.column)
    if d.empty:
        raise KeyError(f"{var.short} is not available for {loc.name}")
    years = tuple(int(y) for y in d.season_start_year)
    return Series(location_id, variable_id, years, tuple(float(v) for v in d[var.column]), years, "season_metrics_extended.csv")


def available_range(ds: Dataset, location_id: str, variable_id: str) -> tuple:
    s = get_series(ds, location_id, variable_id)
    return min(s.expected_years), max(s.expected_years)


def default_window(ds: Dataset, location_id: str, variable_id: str) -> tuple:
    return available_range(ds, location_id, variable_id)


def is_fixed_window(variable_id: str, first: int, last: int) -> bool:
    return (int(first), int(last)) in VARIABLES[variable_id].fixed_windows


# ------------------------------------------------------------- stored results
def _stored_fixed(ds: Dataset, loc, var: Variable, first: int, last: int) -> dict | None:
    """The precomputed result for a fixed window with its multiplicity family, or None."""
    if (first, last) == (1993, 2024) and var.kind == "road":
        t = ds["road_record_trends_all_routes"]
        r = t[(t.road_id == loc.road_id) & (t.metric == var.column)]
        if r.empty:
            return None
        r = r.iloc[0]
        return dict(n=int(r.n_seasons), slope=float(r.slope_per_decade), ci_low=float(r.ci95_low), ci_high=float(r.ci95_high),
                    bb_low=float(r.bb_ci95_low), bb_high=float(r.bb_ci95_high), p=float(r.p_unadjusted), lag1=float(r.lag1),
                    q=float(r.q_bh_all_routes), holm=float(r.holm_all_routes), family="F4_road_record_all_routes",
                    source="road_record_trends_all_routes.csv", status=str(r.status))
    if (first, last) == (2001, 2024):
        t = ds["multiple_testing_126"]
        r = t[(t.location_id == loc.id) & (t.metric == var.column)]
        if r.empty:
            return None
        r = r.iloc[0]
        return dict(n=int(r.n), slope=float(r.slope_per_decade), ci_low=float(r.ci95_low), ci_high=float(r.ci95_high),
                    bb_low=float(r.bb_ci95_low), bb_high=float(r.bb_ci95_high), p=float(r.p_unadjusted), lag1=float(r.lag1),
                    q=float(r.q_bh_all126), holm=float(r.holm_all126), family="F1_all_extended",
                    source="multiple_testing_126.csv", status=str(r.status))
    return None


def _close(a, b, rel=5e-3, abs_tol=5e-3) -> bool:
    return abs(float(a) - float(b)) <= max(abs_tol, rel * max(abs(float(a)), abs(float(b))))


def _direction(var: Variable, slope) -> str:
    if not fmt.is_num(slope) or round(float(slope), var.slope_decimals) == 0:
        return "no net change in the estimate"
    return var.up_word if slope > 0 else var.down_word


# --------------------------------------------------------------------- trends
@functools.lru_cache(maxsize=2048)
def trend(ds: Dataset, location_id: str, variable_id: str, first: int, last: int) -> Finding:
    """The statistical finding for exactly this location, variable and window."""
    first, last = int(first), int(last)
    loc, var = locations(ds)[location_id], VARIABLES[variable_id]
    s = get_series(ds, location_id, variable_id)
    w = s.window(first, last)
    n_expected = len(w)
    t = rc.period_trend(w.season_start_year.to_numpy(float), w.value.to_numpy(float), first, last)
    base = dict(location_id=location_id, variable_id=variable_id, first=first, last=last, n=int(t["n"]), n_expected=n_expected, status=t["status"])
    extra = []
    if var.kind == "road":
        extra.append(T_ROAD)
    if t["status"] == "too_few_points":
        return Finding(**base, state=INSUFFICIENT, window_kind="exploratory", sentence=T_TOO_FEW.format(m=MIN_SEASONS, n=t["n"]), extra_sentences=tuple(extra))
    if t["status"] in ("mostly_tied", "constant_series"):
        return Finding(**base, state=UNAVAILABLE, window_kind="fixed" if (first, last) == (var.valid_first, var.valid_last) else "exploratory",
                       sentence=T_TIED if t["status"] == "mostly_tied" else T_CONSTANT, extra_sentences=tuple(extra))

    ok = w.dropna(subset=["value"])
    x, y = ok.season_start_year.to_numpy(float), ok.value.to_numpy(float)
    slope_year = t["slope_per_decade"] / 10.0
    pivot_x, pivot_y = float(np.median(x)), float(np.median(y))
    nums = dict(slope=t["slope_per_decade"], ci_low=t["ci95_low"], ci_high=t["ci95_high"], bb_low=t["bb_ci95_low"], bb_high=t["bb_ci95_high"],
                p=t["mk_p"], lag1=t["lag1"], autocorr_flag=bool(abs(t["lag1"]) > AUTOCORR_FLAG) if fmt.is_num(t["lag1"]) else False,
                intercept=pivot_y - slope_year * pivot_x, pivot_year=pivot_x, pivot_value=pivot_y, direction=_direction(var, t["slope_per_decade"]))

    stored = _stored_fixed(ds, loc, var, first, last) if is_fixed_window(variable_id, first, last) else None
    if stored is not None:
        # the approved precomputed result is displayed only for its own window, after agreeing with the live recomputation
        # The slope and n must agree closely. Interval limits and p are allowed the small difference that arises when the
        # per-winter file (stored to 4 decimals) ties two winters that differ at full precision (one known case of 126).
        width = abs(stored["ci_high"] - stored["ci_low"])
        if not _close(nums["slope"], stored["slope"]) or int(stored["n"]) != int(t["n"]):
            raise DataError(stored["source"], f"stored slope or n for {loc.id} {var.column} {first}-{last} does not match recomputation")
        for key in ("ci_low", "ci_high", "bb_low", "bb_high"):
            if abs(nums[key] - stored[key]) > max(5e-3, CROSS_CHECK_INTERVAL_TOL * width):
                raise DataError(stored["source"], f"stored {key} for {loc.id} {var.column} {first}-{last} does not match recomputation")
        if abs(stored["p"] - nums["p"]) > CROSS_CHECK_P_TOL:
            raise DataError(stored["source"], f"stored p for {loc.id} {var.column} {first}-{last} does not match recomputation")
        q = stored["q"]
        fam_n = {f["family_id"]: f["n_tests"] for f in ds.facts["families"]}[stored["family"]]
        if q < ALPHA:
            state, sentence = SUPPORTED, T_SUPPORTED.format(q=fmt.pval(q))
        elif nums["p"] < ALPHA:
            state, sentence = UNRESOLVED, T_INCONCLUSIVE.format(p=fmt.pval(nums["p"]), q=fmt.pval(q))
        else:
            state, sentence = UNRESOLVED, T_NONSIG
        nums.update(slope=stored["slope"], ci_low=stored["ci_low"], ci_high=stored["ci_high"], bb_low=stored["bb_low"], bb_high=stored["bb_high"],
                    p=stored["p"], lag1=stored["lag1"])
        return Finding(**base, state=state, window_kind="fixed", q=q, q_family=stored["family"], q_family_n=int(fam_n), holm=stored["holm"],
                       stored_source=stored["source"], cross_checked=True, sentence=sentence, extra_sentences=tuple(extra), **nums)
    sentence = T_EXPL_SMALL_P.format(p=fmt.pval(nums["p"])) if nums["p"] < ALPHA else T_EXPL_NONSIG
    return Finding(**base, state=EXPLORATORY, window_kind="exploratory", sentence=sentence, extra_sentences=tuple(extra), **nums)


def fitted_line(f: Finding, years) -> list:
    if not f.estimated:
        return []
    return [f.intercept + (f.slope / 10.0) * float(y) for y in years]


def slope_band(f: Finding, years) -> tuple:
    """Lines through the median point with the lower and upper 95% Theil-Sen slope limits (a display of slope uncertainty)."""
    if not f.estimated:
        return [], []
    lo = [f.pivot_value + (f.ci_low / 10.0) * (float(y) - f.pivot_year) for y in years]
    hi = [f.pivot_value + (f.ci_high / 10.0) * (float(y) - f.pivot_year) for y in years]
    return [min(a, b) for a, b in zip(lo, hi)], [max(a, b) for a, b in zip(lo, hi)]


def plain_language(ds: Dataset, f: Finding) -> str:
    """One deterministic sentence stating the estimate in words, built from the finding."""
    loc, var = locations(ds)[f.location_id], VARIABLES[f.variable_id]
    where = loc.short
    if not f.estimated:
        return f"{var.short} at {where}, winters {fmt.period(f.first, f.last)}: {f.sentence}"
    d = var.slope_decimals
    return (f"Across {f.n} winters ({fmt.period(f.first, f.last)}), the estimated change in {var.phrase} at {where} is "
            f"{fmt.num(f.slope, d, signed=True)} {var.unit_per_decade} ({f.direction}), with a 95% interval of {fmt.interval(f.ci_low, f.ci_high, d)}.")


# ------------------------------------------------------------------ comparison
@dataclass(frozen=True)
class Comparison:
    variable_id: str
    loc_a: str
    loc_b: str
    first: int
    last: int
    common_years: tuple
    a: Finding
    b: Finding
    diff: Finding            # trend of the difference series a - b on the matched winters
    formal: bool             # True only when the window is the approved fixed comparison window
    sentence: str = ""


T_DIFF_NONE = "No difference in trend is supported on these matched winters. Do not describe the two locations as trending differently."
T_DIFF_EXPL = ("The difference series has unadjusted p = {p}. This comparison is not adjusted for multiple testing and is descriptive: "
               "it does not establish that the two locations are trending differently.")
T_DIFF_NA = "The difference between the two series could not be estimated for this selection, so the comparison is descriptive only."
COMPARE_VARIABLES = ("fdd_octdec", "mean_octdec_c", "mean_janmar_c")


@functools.lru_cache(maxsize=512)
def compare(ds: Dataset, variable_id: str, loc_a: str, loc_b: str, first: int, last: int) -> Comparison:
    """Same variable, same units, matched winters. Difference inference follows docs/SCIENTIFIC_METHODS.md section D."""
    first, last = int(first), int(last)
    var = VARIABLES[variable_id]
    if var.kind != "environmental":
        raise ValueError("regional comparison is defined for environmental variables only")
    sa, sb = get_series(ds, loc_a, variable_id).window(first, last), get_series(ds, loc_b, variable_id).window(first, last)
    m = sa.merge(sb, on="season_start_year", suffixes=("_a", "_b")).dropna()
    years = m.season_start_year.to_numpy(float)
    t = rc.period_trend(years, (m.value_a - m.value_b).to_numpy(float), first, last)
    fa, fb = trend(ds, loc_a, variable_id, first, last), trend(ds, loc_b, variable_id, first, last)
    formal = (first, last) == (2001, 2024) and {loc_a, loc_b} == {"dettah_bay", "aklavik_delta"} and variable_id in COMPARE_VARIABLES
    base = dict(location_id=f"{loc_a} minus {loc_b}", variable_id=variable_id, first=first, last=last, n=int(t["n"]), n_expected=len(m), status=t["status"])
    if t["status"] != "ok":
        state = INSUFFICIENT if t["status"] == "too_few_points" else UNAVAILABLE
        diff = Finding(**base, state=state, window_kind="exploratory", sentence=T_DIFF_NA)
        return Comparison(variable_id, loc_a, loc_b, first, last, tuple(int(y) for y in years), fa, fb, diff, False, T_DIFF_NA)
    x, y = years, (m.value_a - m.value_b).to_numpy(float)
    px, py = float(np.median(x)), float(np.median(y))
    sentence = T_DIFF_NONE if t["mk_p"] >= ALPHA else T_DIFF_EXPL.format(p=fmt.pval(t["mk_p"]))
    diff = Finding(**base, state=UNRESOLVED if t["mk_p"] >= ALPHA else EXPLORATORY, window_kind="fixed" if formal else "exploratory",
                   slope=t["slope_per_decade"], ci_low=t["ci95_low"], ci_high=t["ci95_high"], bb_low=t["bb_ci95_low"], bb_high=t["bb_ci95_high"],
                   p=t["mk_p"], lag1=t["lag1"], autocorr_flag=bool(abs(t["lag1"]) > AUTOCORR_FLAG), intercept=py - t["slope_per_decade"] / 10 * px,
                   pivot_year=px, pivot_value=py, sentence=sentence, direction=_direction(var, t["slope_per_decade"]))
    return Comparison(variable_id, loc_a, loc_b, first, last, tuple(int(v) for v in years), fa, fb, diff, formal, sentence)


# ------------------------------------------------------------ source agreement
@dataclass(frozen=True)
class StationFdd:
    years_all: tuple
    nasa_all: tuple
    station_all: tuple       # NaN where the station winter is incomplete; never filled
    n_complete: int
    nasa_mean: float
    station_mean: float
    pct_over: float
    pearson_r: float
    nasa: Finding
    station: Finding
    diff: Finding


def _simple_finding(label: str, variable_id: str, years, values) -> Finding:
    years, values = np.asarray(years, float), np.asarray(values, float)
    first, last = int(years.min()), int(years.max())
    t = rc.period_trend(years, values, first, last)
    base = dict(location_id=label, variable_id=variable_id, first=first, last=last, n=int(t["n"]), n_expected=len(years), status=t["status"])
    if t["status"] != "ok":
        return Finding(**base, state=INSUFFICIENT if t["status"] == "too_few_points" else UNAVAILABLE, window_kind="exploratory",
                       sentence=T_TOO_FEW.format(m=MIN_SEASONS, n=t["n"]) if t["status"] == "too_few_points" else T_TIED)
    ok = ~np.isnan(values)
    px, py = float(np.median(years[ok])), float(np.median(values[ok]))
    return Finding(**base, state=EXPLORATORY, window_kind="exploratory", slope=t["slope_per_decade"], ci_low=t["ci95_low"], ci_high=t["ci95_high"],
                   bb_low=t["bb_ci95_low"], bb_high=t["bb_ci95_high"], p=t["mk_p"], lag1=t["lag1"], autocorr_flag=bool(abs(t["lag1"]) > AUTOCORR_FLAG),
                   intercept=py - t["slope_per_decade"] / 10 * px, pivot_year=px, pivot_value=py,
                   sentence=T_EXPL_NONSIG if t["mk_p"] >= ALPHA else T_EXPL_SMALL_P.format(p=fmt.pval(t["mk_p"])))


@functools.lru_cache(maxsize=8)
def station_fdd(ds: Dataset) -> StationFdd:
    """NASA versus ECCC Yellowknife A Oct-Dec freezing degree-days on winters complete in both series."""
    d = ds["station_fdd_by_season"].sort_values("season_start_year")
    both = d.dropna(subset=["fdd_nasa", "fdd_station"])
    y = both.season_start_year.to_numpy(float)
    return StationFdd(
        years_all=tuple(int(v) for v in d.season_start_year), nasa_all=tuple(float(v) for v in d.fdd_nasa), station_all=tuple(float(v) for v in d.fdd_station),
        n_complete=len(both), nasa_mean=float(both.fdd_nasa.mean()), station_mean=float(both.fdd_station.mean()),
        pct_over=float(100 * (both.fdd_nasa.mean() / both.fdd_station.mean() - 1)), pearson_r=float(np.corrcoef(both.fdd_nasa, both.fdd_station)[0, 1]),
        nasa=_simple_finding("NASA POWER (Yellowknife cell)", "fdd_octdec", y, both.fdd_nasa.to_numpy(float)),
        station=_simple_finding("ECCC Yellowknife A station", "fdd_octdec", y, both.fdd_station.to_numpy(float)),
        diff=_simple_finding("NASA minus station", "fdd_octdec", y, (both.fdd_nasa - both.fdd_station).to_numpy(float)))


# ---------------------------------------------------------------- road context
def road_record(ds: Dataset, location_id: str) -> pd.DataFrame:
    """Every winter of the government record for a location's road, with status and day numbers for verified rows."""
    loc = locations(ds)[location_id]
    ops = ds["road_operations_all_routes"]
    d = ops[ops.road_id == loc.road_id].sort_values("season_start_year").copy()
    for metric in ("open_day", "close_day", "open_to_close_days"):
        s = rc.road_series(ops, loc.road_id, metric).set_index("season_start_year")[metric]
        d[metric] = d.season_start_year.map(s)
    return d.reset_index(drop=True)


def road_status_counts(ds: Dataset, location_id: str, first: int | None = None, last: int | None = None) -> dict:
    d = road_record(ds, location_id)
    if first is not None:
        d = d[(d.season_start_year >= first) & (d.season_start_year <= last)]
    c = d.record_status.value_counts().to_dict()
    return dict(total=len(d), verified=int(c.get("verified", 0)), other={k: int(v) for k, v in c.items() if k != "verified"})


def window_overlap(ds: Dataset, location_id: str) -> dict:
    """How often the Oct 1 to Dec 31 environmental window reached or passed the recorded opening date (from the leakage audit)."""
    la = ds["leakage_audit"]
    r = la[(la.location_id == location_id) & (la.outcome == "opening_date") & la.predictor_window.str.startswith("Oct 1 - Dec 31")]
    if r.empty:
        return {}
    r = r.iloc[0]
    return dict(n_winters=int(r.n_winters), n_overlap=int(r.n_winters_window_reaches_outcome), verdict=str(r.verdict))


def associations(ds: Dataset, location_id: str) -> pd.DataFrame:
    """Leak-free exploratory associations between climate predictors and road dates for one location."""
    c = ds["road_climate_correlations"]
    return c[c.location_id == location_id].reset_index(drop=True)


def all_ci_include_zero(df: pd.DataFrame) -> bool:
    return bool(((df.ci95_low <= 0) & (df.ci95_high >= 0)).all()) if len(df) else True


def sensitivity(ds: Dataset, location_id: str, variable_id: str) -> pd.DataFrame:
    """Stored robustness variants of a road-date trend (windows, dropping early or late winters)."""
    loc = locations(ds)[location_id]
    h = ds["headline_trend_sensitivity"]
    return h[(h.road_id == loc.road_id) & (h.metric == VARIABLES[variable_id].column)].reset_index(drop=True)


def coverage(ds: Dataset, location_id: str, first: int, last: int) -> dict | None:
    """Daily coverage of the NASA series for the two documented locations, from the per-winter day counts."""
    ca = ds["climate_annual"]
    d = ca[(ca.corridor_id == location_id) & (ca.metric == "fdd") & (ca.season_year >= first) & (ca.season_year <= last)]
    if d.empty:
        return None
    return dict(winters=len(d), complete=int((d.missing_days == 0).sum()), missing_days=int(d.missing_days.sum()), days=int(d.n_days.sum()))
