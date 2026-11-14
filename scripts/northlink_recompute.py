"""Reference data layer for the application: statistics for a USER-SELECTED period, using only the approved methods.

The app may import this module (copy it with northlink_metrics.py and northlink_stats.py) instead of re-implementing statistics.
Rules (docs/APP_IMPLEMENTATION_CONTRACT.md):
  * A window other than a precomputed one is recomputed here; precomputed numbers are shown only for their own window.
  * Multiplicity-adjusted values (q, Holm) belong to the declared fixed families and are NEVER returned for a user-chosen window.
  * Fewer than MIN_SEASONS seasons -> status "too_few_points" and no numbers.
Inputs are the real files in UI/data_real/ (season_metrics_extended.csv, road_operations_all_routes.csv).
"""
import datetime as dt
import os

import numpy as np
import pandas as pd

import northlink_metrics as nm
import northlink_stats as ns

MIN_SEASONS = 15
CAVEAT_ADJUSTED = "Adjusted significance (q) applies only to the fixed windows and families in docs/SCIENTIFIC_METHODS.md; it is not computed for user-selected windows."


def period_trend(years, values, first: int, last: int) -> dict:
    """Theil-Sen slope, Mann-Kendall p, lag-1 and block-bootstrap CI for winters first..last (season start years, inclusive)."""
    y = np.asarray(years, float)
    v = np.asarray(values, float)
    m = (y >= first) & (y <= last)
    t = nm.trend(y[m], v[m], min_points=MIN_SEASONS)
    out = dict(first_season=int(first), last_season=int(last), n=int(t.n), status=t.status, slope_per_decade=None, ci95_low=None, ci95_high=None,
               bb_ci95_low=None, bb_ci95_high=None, mk_p=None, lag1=None, q_adjusted=None, adjusted_note=CAVEAT_ADJUSTED)
    if t.status == "ok":
        _, lo, hi, _ = ns.block_bootstrap_slope(y[m], v[m])
        out.update(slope_per_decade=float(t.slope_per_decade), ci95_low=float(t.ci_low_per_decade), ci95_high=float(t.ci_high_per_decade),
                   bb_ci95_low=float(lo), bb_ci95_high=float(hi), mk_p=float(t.mk_p), lag1=float(t.lag1_autocorr_resid))
    return out


def road_series(road_ops: pd.DataFrame, road_id: str, metric: str) -> pd.DataFrame:
    """Per-winter road metric from verified rows only. metric: open_day | close_day | open_to_close_days."""
    d = road_ops[(road_ops.road_id == road_id) & (road_ops.record_status == "verified")]
    rows = []
    for _, r in d.iterrows():
        y = int(r.season_start_year)
        m = nm.road_metrics(dt.date.fromisoformat(r.opening_date), dt.date.fromisoformat(r.closing_date), y)
        rows.append((y, m[metric]))
    return pd.DataFrame(rows, columns=["season_start_year", metric])


def climate_series(season_metrics: pd.DataFrame, location_id: str, metric: str) -> pd.DataFrame:
    d = season_metrics[season_metrics.location_id == location_id][["season_start_year", metric]]
    return d.sort_values("season_start_year").reset_index(drop=True)
