#!/usr/bin/env python3
"""Diagnose the NASA POWER (MERRA-2 T2M) vs ECCC Yellowknife A temperature discrepancy.

Reproducible, read-only on raw data. Writes CSV + JSON to data/processed/diagnostics/.
Run:  python3 -I scripts/diagnose_temperature_bias.py

Hypotheses tested (each with a discriminating measurement):
  H1 time offset / date shift  -> compare NASA T2M to station mean at lag -1, 0, +1 day
  H2 daily-mean definition     -> NASA T2M vs (T2M_MAX+T2M_MIN)/2 vs station mean vs station (max+min)/2
  H3 Tmax vs Tmin asymmetry    -> bias of Tmax and Tmin separately (cold bias in which tail?)
  H4 state dependence          -> bias as function of station temperature (cold-tail / inversion mismatch)
  H5 seasonal / era dependence -> bias by calendar month, by era, drift over winters
  H6 unit/format error         -> bias should NOT be a constant offset or a sign-flip; checked via H1-H5
  H7 duplicate/padded rows     -> station series de-duplicated by date, counts reported
Effect on analysis metrics: FDD (Oct-Dec), thaw days (Jan-Mar, T>0), Theil-Sen slopes on
the same winters, NASA vs station.

Nothing here asserts a physical cause. Causes are listed only as hypotheses the data can or cannot support.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "processed" / "diagnostics"
OUT.mkdir(parents=True, exist_ok=True)

STATION_IDS_YK = {1706, 51058}  # ECCC Yellowknife A: 1706 to 2012, 51058 from 2013


def load_pair():
    nasa = pd.read_csv(ROOT / "data/processed/nasa_daily_variables.csv", parse_dates=["date"])
    nasa = nasa[nasa.location_id == "dettah_bay"].drop_duplicates("date").set_index("date").sort_index()
    st = pd.read_csv(ROOT / "data/raw/weather_stations/eccc_stations_daily_2001_2025.csv", parse_dates=["date"])
    st = st[st.station_id.isin(STATION_IDS_YK)]
    n_raw = len(st)
    # Prefer rows with an observed mean; where both station IDs give a value on one date keep the first (sorted by id)
    st = st.sort_values(["date", "station_id"])
    dup_dates = int(st.date.duplicated().sum())
    st = st.drop_duplicates("date").set_index("date").sort_index()
    meta = {"station_rows_raw": n_raw, "station_duplicate_dates_dropped": dup_dates, "station_unique_dates": len(st)}
    return nasa, st, meta


def stats_of(d: pd.Series) -> dict:
    d = d.dropna()
    return {
        "n": int(len(d)),
        "mean_bias": round(float(d.mean()), 3) if len(d) else None,
        "median_bias": round(float(d.median()), 3) if len(d) else None,
        "sd": round(float(d.std()), 3) if len(d) > 1 else None,
        "rmse": round(float(np.sqrt((d**2).mean())), 3) if len(d) else None,
        "p05": round(float(d.quantile(0.05)), 3) if len(d) else None,
        "p95": round(float(d.quantile(0.95)), 3) if len(d) else None,
    }


def winter_year(idx: pd.DatetimeIndex) -> np.ndarray:
    return np.where(idx.month >= 10, idx.year, idx.year - 1)


def fdd_thaw_by_winter(series: pd.Series, require_complete=True) -> pd.DataFrame:
    """FDD Oct-Dec = sum(max(0,-T)); thaw days Jan-Mar = count(T>0). Seasons with any missing day -> NaN."""
    rows = []
    for y in range(2001, 2025):
        a = series[(series.index >= f"{y}-10-01") & (series.index <= f"{y}-12-31")]
        b = series[(series.index >= f"{y+1}-01-01") & (series.index <= f"{y+1}-03-31")]
        full_a = 92
        full_b = 91 if (y + 1) % 4 == 0 else 90
        ok_a = a.notna().sum() == full_a
        ok_b = b.notna().sum() == full_b
        rows.append({
            "season_start_year": y,
            "fdd_octdec": float((-a.clip(upper=0)).sum()) if ok_a else np.nan,
            "thaw_days_janmar": float((b > 0).sum()) if ok_b else np.nan,
            "n_octdec": int(a.notna().sum()), "n_janmar": int(b.notna().sum()),
        })
    return pd.DataFrame(rows)


def ts_slope(y: pd.Series, x: pd.Series):
    m = y.notna()
    if m.sum() < 5:
        return None
    r = stats.theilslopes(y[m].values, x[m].values, 0.95)
    return {"n": int(m.sum()), "slope_per_decade": round(float(r[0]) * 10, 3),
            "ci_low": round(float(r[2]) * 10, 3), "ci_high": round(float(r[3]) * 10, 3)}


def main():
    nasa, st, meta = load_pair()
    out = {"meta": meta}
    # restrict to the NASA analysis window
    idx = nasa.index.intersection(st.index)
    N = nasa.loc[idx]
    S = st.loc[idx]
    out["meta"]["paired_days_any"] = int(len(idx))

    # ---------- H1: time offset
    h1 = []
    for lag in (-2, -1, 0, 1, 2):
        sh = nasa["T2M"].shift(lag)  # NASA value at date d+lag? shift(+k) moves values to later dates
        d = (sh - st["mean_temp_c"]).dropna()
        j = pd.concat([sh, st["mean_temp_c"]], axis=1, keys=["n", "s"], sort=True).dropna()
        h1.append({"nasa_shift_days": lag, "n": int(len(j)), "mean_bias": round(float(d.mean()), 3),
                   "rmse": round(float(np.sqrt((d**2).mean())), 3), "corr": round(float(j.n.corr(j.s)), 4)})
    out["H1_lag"] = h1
    pd.DataFrame(h1).to_csv(OUT / "h1_lag_test.csv", index=False)

    # ---------- H2: daily mean definition
    cmp = pd.DataFrame({
        "nasa_T2M": N["T2M"],
        "nasa_mid": (N["T2M_MAX"] + N["T2M_MIN"]) / 2,
        "st_mean": S["mean_temp_c"],
        "st_mid": (S["max_temp_c"] + S["min_temp_c"]) / 2,
        "nasa_tmax": N["T2M_MAX"], "nasa_tmin": N["T2M_MIN"],
        "st_tmax": S["max_temp_c"], "st_tmin": S["min_temp_c"],
    })
    cmp["winter_year"] = winter_year(cmp.index)
    cmp["month"] = cmp.index.month
    h2 = {
        "nasa_T2M_minus_station_mean": stats_of(cmp.nasa_T2M - cmp.st_mean),
        "nasa_mid_minus_station_mean": stats_of(cmp.nasa_mid - cmp.st_mean),
        "nasa_T2M_minus_nasa_mid": stats_of(cmp.nasa_T2M - cmp.nasa_mid),
        "station_mean_minus_station_mid": stats_of(cmp.st_mean - cmp.st_mid),
        "nasa_mid_minus_station_mid": stats_of(cmp.nasa_mid - cmp.st_mid),
    }
    out["H2_definition"] = h2
    # ---------- H3: Tmax / Tmin separately
    out["H3_tmax_tmin"] = {
        "nasa_tmax_minus_station_tmax": stats_of(cmp.nasa_tmax - cmp.st_tmax),
        "nasa_tmin_minus_station_tmin": stats_of(cmp.nasa_tmin - cmp.st_tmin),
        "diurnal_range_nasa_minus_station": stats_of((cmp.nasa_tmax - cmp.nasa_tmin) - (cmp.st_tmax - cmp.st_tmin)),
    }
    # ---------- H5: month / era / winter
    cmp["bias"] = cmp.nasa_T2M - cmp.st_mean
    cmp["bias_tmax"] = cmp.nasa_tmax - cmp.st_tmax
    cmp["bias_tmin"] = cmp.nasa_tmin - cmp.st_tmin
    by_month = cmp.groupby("month").agg(n=("bias", "count"), mean_bias=("bias", "mean"), median_bias=("bias", "median"),
                                        sd=("bias", "std"), bias_tmax=("bias_tmax", "mean"), bias_tmin=("bias_tmin", "mean"),
                                        station_mean_t=("st_mean", "mean")).round(3)
    by_month.to_csv(OUT / "bias_by_month.csv")
    cmp["era"] = np.where(cmp.index.year <= 2012, "2001-2012 (station 1706)", "2013-2025 (station 51058)")
    by_era_month = cmp.groupby(["era", "month"]).bias.agg(["count", "mean"]).round(3).reset_index()
    by_era_month.to_csv(OUT / "bias_by_era_month.csv", index=False)
    by_winter = cmp.groupby("winter_year").agg(n=("bias", "count"), mean_bias=("bias", "mean")).round(3)
    by_winter.to_csv(OUT / "bias_by_winter.csv")
    # drift: slope of annual-mean bias in Oct-Dec / Nov-Dec across winters
    drift = {}
    for name, months in {"Oct-Dec": [10, 11, 12], "Nov-Dec": [11, 12], "Jan-Mar": [1, 2, 3]}.items():
        g = cmp[cmp.month.isin(months)].groupby("winter_year").bias.agg(["mean", "count"])
        g = g[g["count"] >= 0.9 * (len(months) * 30)]
        drift[name] = ts_slope(g["mean"], pd.Series(g.index, index=g.index).astype(float))
    out["H5_bias_drift_per_decade"] = drift
    out["H5_by_month_table"] = by_month.reset_index().to_dict(orient="records")

    # ---------- H4: dependence on station temperature
    cut = pd.cut(cmp.st_mean, [-60, -35, -30, -25, -20, -15, -10, -5, 0, 5, 40])
    h4 = cmp.groupby(cut, observed=True).bias.agg(["count", "mean", "median"]).round(3).reset_index()
    h4["st_mean_bin"] = h4["st_mean"].astype(str)
    h4 = h4.drop(columns="st_mean")
    h4.to_csv(OUT / "bias_by_station_temperature_bin.csv", index=False)
    mm = cmp[["bias", "st_mean"]].dropna()
    lr = stats.linregress(mm.st_mean, mm.bias)
    out["H4_state_dependence"] = {"slope_bias_per_degC_of_station_temp": round(float(lr.slope), 4),
                                  "intercept": round(float(lr.intercept), 3), "r2": round(float(lr.rvalue**2), 4), "n": int(len(mm))}
    # winter-only (Oct-Mar) state dependence and diurnal-range dependence
    wm = cmp[cmp.month.isin([10, 11, 12, 1, 2, 3])][["bias", "st_mean"]].dropna()
    lw = stats.linregress(wm.st_mean, wm.bias)
    out["H4_state_dependence_winter_only"] = {"slope": round(float(lw.slope), 4), "intercept": round(float(lw.intercept), 3),
                                              "r2": round(float(lw.rvalue**2), 4), "n": int(len(wm))}

    # ---------- worst days
    worst = cmp.assign(abs_bias=cmp.bias.abs()).sort_values("abs_bias", ascending=False).head(25)
    worst[["nasa_T2M", "st_mean", "bias", "nasa_tmax", "st_tmax", "nasa_tmin", "st_tmin"]].round(2).to_csv(OUT / "worst_days.csv")
    out["worst_day_sample_n"] = int(len(worst))

    # ---------- effect on winter metrics and slopes (same winters, complete in BOTH series)
    fn = fdd_thaw_by_winter(nasa["T2M"])
    fs = fdd_thaw_by_winter(st["mean_temp_c"])
    fm = fn.merge(fs, on="season_start_year", suffixes=("_nasa", "_station"))
    both = fm.dropna(subset=["fdd_octdec_nasa", "fdd_octdec_station"])
    fm["fdd_diff"] = fm.fdd_octdec_nasa - fm.fdd_octdec_station
    fm.round(2).to_csv(OUT / "winter_metrics_nasa_vs_station.csv", index=False)
    eff = {
        "winters_with_complete_Oct_Dec_in_both": int(len(both)),
        "fdd_mean_nasa": round(float(both.fdd_octdec_nasa.mean()), 1),
        "fdd_mean_station": round(float(both.fdd_octdec_station.mean()), 1),
        "fdd_mean_diff_nasa_minus_station": round(float(both.fdd_octdec_nasa.mean() - both.fdd_octdec_station.mean()), 1),
        "fdd_pct_overestimate": round(float(100 * (both.fdd_octdec_nasa.mean() / both.fdd_octdec_station.mean() - 1)), 1),
        "fdd_nasa_station_pearson_r": round(float(both.fdd_octdec_nasa.corr(both.fdd_octdec_station)), 3),
        "fdd_nasa_station_spearman_r": round(float(both.fdd_octdec_nasa.corr(both.fdd_octdec_station, method="spearman")), 3),
        "fdd_slope_nasa_same_winters": ts_slope(both.fdd_octdec_nasa, both.season_start_year.astype(float)),
        "fdd_slope_station_same_winters": ts_slope(both.fdd_octdec_station, both.season_start_year.astype(float)),
        "fdd_diff_slope_nasa_minus_station": ts_slope(both.fdd_octdec_nasa - both.fdd_octdec_station, both.season_start_year.astype(float)),
    }
    bt = fm.dropna(subset=["thaw_days_janmar_nasa", "thaw_days_janmar_station"])
    eff.update({
        "winters_with_complete_Jan_Mar_in_both": int(len(bt)),
        "thaw_days_mean_nasa": round(float(bt.thaw_days_janmar_nasa.mean()), 2),
        "thaw_days_mean_station": round(float(bt.thaw_days_janmar_station.mean()), 2),
        "thaw_days_nasa_station_spearman_r": (round(float(bt.thaw_days_janmar_nasa.corr(bt.thaw_days_janmar_station, method="spearman")), 3)
                                              if bt.thaw_days_janmar_nasa.nunique() > 1 and bt.thaw_days_janmar_station.nunique() > 1 else None),
        "thaw_days_slope_nasa_same_winters": ts_slope(bt.thaw_days_janmar_nasa, bt.season_start_year.astype(float)),
        "thaw_days_slope_station_same_winters": ts_slope(bt.thaw_days_janmar_station, bt.season_start_year.astype(float)),
    })
    out["effect_on_metrics"] = eff


    # ---------- sensitivity: month-wise climatological offset (calibration IN-SAMPLE against the station; NOT a published correction)
    off = cmp.groupby("month").bias.mean()
    adj = nasa["T2M"] - nasa.index.month.map(off).values
    fa = fdd_thaw_by_winter(adj)
    fa = fa.merge(fm[["season_start_year", "fdd_octdec_station"]], on="season_start_year")
    ba = fa.dropna(subset=["fdd_octdec", "fdd_octdec_station"])
    out["sensitivity_monthly_offset_correction"] = {
        "note": "Offsets estimated from the same station record; in-sample, for sensitivity only.",
        "monthly_offsets_degC": {int(k): round(float(v), 3) for k, v in off.items()},
        "fdd_mean_adjusted_nasa": round(float(ba.fdd_octdec.mean()), 1),
        "fdd_mean_station": round(float(ba.fdd_octdec_station.mean()), 1),
        "fdd_slope_adjusted_nasa_same_winters": ts_slope(ba.fdd_octdec, ba.season_start_year.astype(float)),
        "fdd_slope_nasa_all_complete_winters": ts_slope(fn.fdd_octdec, fn.season_start_year.astype(float)),
        "fdd_slope_adjusted_nasa_all_complete_winters": ts_slope(fa.fdd_octdec, fa.season_start_year.astype(float)),
        "thaw_days_mean_adjusted_nasa": round(float(fa.thaw_days_janmar.mean()), 2),
        "thaw_days_nonzero_winters_adjusted_nasa": int((fa.thaw_days_janmar > 0).sum()),
        "thaw_days_nonzero_winters_raw_nasa": int((fn.thaw_days_janmar > 0).sum()),
        "thaw_days_nonzero_winters_station_complete": int((fs.thaw_days_janmar.dropna() > 0).sum()),
        "station_winters_complete_JanMar": int(fs.thaw_days_janmar.notna().sum()),
    }

    # ---------- headline overall
    out["overall_bias_all_days"] = stats_of(cmp.bias)
    out["overall_bias_Oct_Dec"] = stats_of(cmp[cmp.month.isin([10, 11, 12])].bias)
    out["overall_bias_Jan_Mar"] = stats_of(cmp[cmp.month.isin([1, 2, 3])].bias)
    out["n_days_station_missing_mean_in_window"] = int(S["mean_temp_c"].isna().sum())

    (OUT / "diagnostics_summary.json").write_text(json.dumps(out, indent=2, default=str))
    print(json.dumps({k: v for k, v in out.items() if k != "H5_by_month_table"}, indent=2, default=str))
    print("\nBy month:\n", by_month.to_string())
    print("\nBy station-temperature bin:\n", h4.to_string())
    return 0


if __name__ == "__main__":
    sys.exit(main())
