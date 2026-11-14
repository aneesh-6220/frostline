#!/usr/bin/env python3
"""Run the NorthLink analysis defined in docs/SCIENTIFIC_METHODS.md.

Usage (from repo root): python3 -I scripts/run_analysis.py
Reads  data/processed/nasa_daily_temperature.csv, road_operations.csv, locations.csv,
       data/raw/weather_stations/eccc_yellowknife_daily_2001_2025.csv, data/raw/nasa/power_monthly_*.csv
Writes data/processed/season_metrics.csv, trend_results.csv, regional_comparison.csv,
       road_climate_correlations.csv, station_validation.csv, station_summary.csv
"""
import datetime as dt
import os
import sys

import numpy as np
import pandas as pd
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)
import northlink_metrics as m  # noqa: E402

P = lambda *a: os.path.join(ROOT, *a)
temps = pd.read_csv(P("data/processed/nasa_daily_temperature.csv"), parse_dates=["date"])
roads = pd.read_csv(P("data/processed/road_operations.csv"))
LOC_ROAD = {"dettah_bay": "dettah", "aklavik_delta": "aklavik"}
CUTOFF = {"dettah_bay": dt.date(1, 11, 28), "aklavik_delta": dt.date(1, 12, 2)}  # month/day: last day before earliest opening
YEARS = range(2001, 2025)


def window_mean(g, a, b):
    s = g[(g["date"] >= pd.Timestamp(a)) & (g["date"] <= pd.Timestamp(b))]["temperature_c"]
    need = (b - a).days + 1
    return float(s.mean()) if s.notna().sum() == need else float("nan")


def fdd_window(g, a, b):
    s = g[(g["date"] >= pd.Timestamp(a)) & (g["date"] <= pd.Timestamp(b))]["temperature_c"]
    need = (b - a).days + 1
    return float(np.maximum(0, -s).sum()) if s.notna().sum() == need else float("nan")


rows = []
for loc, g in temps.groupby("location_id"):
    rid = LOC_ROAD[loc]
    rr = roads[(roads.road_id == rid) & (roads.record_status == "verified")].set_index("season_start_year")
    for y in YEARS:
        c = CUTOFF[loc]
        r = dict(location_id=loc, season_start_year=y,
                 fdd_octdec=m.fdd(g, y, "early"), thaw_days_janmar=m.thaw_days(g, y),
                 longest_thaw_run_janmar=m.longest_thaw_run(g, y),
                 mean_octdec_c=m.seasonal_mean(g, y, "early"), mean_janmar_c=m.seasonal_mean(g, y, "mid"),
                 mean_full_c=m.seasonal_mean(g, y, "full"),
                 fdd_pre_cutoff=fdd_window(g, dt.date(y, 10, 1), dt.date(y, c.month, c.day)),
                 mean_mar15_apr15_c=window_mean(g, dt.date(y + 1, 3, 15), dt.date(y + 1, 4, 15)))
        if y in rr.index:
            od, cd = dt.date.fromisoformat(rr.loc[y, "opening_date"]), dt.date.fromisoformat(rr.loc[y, "closing_date"])
            r.update(m.road_metrics(od, cd, y))
        rows.append(r)
sm = pd.DataFrame(rows)
sm.to_csv(P("data/processed/season_metrics.csv"), index=False, float_format="%.4f")

METRICS = ["fdd_octdec", "thaw_days_janmar", "longest_thaw_run_janmar", "mean_octdec_c", "mean_janmar_c",
           "mean_full_c", "fdd_pre_cutoff"]
out = []


def add(loc, metric, sub, years, vals, label):
    t = m.trend(years, vals)
    out.append(dict(location_id=loc, metric=metric, variant=label, n_seasons=t.n,
                    slope_per_decade=t.slope_per_decade, ci95_low=t.ci_low_per_decade, ci95_high=t.ci_high_per_decade,
                    mk_tau=t.mk_tau, mk_z=t.mk_z, mk_p=t.mk_p, lag1_resid_autocorr=t.lag1_autocorr_resid, status=t.status))


for loc, g in sm.groupby("location_id"):
    y = g.season_start_year.to_numpy()
    for met in METRICS:
        v = g[met].to_numpy()
        add(loc, met, None, y, v, "main (2001-2024)")
        add(loc, met, None, y[5:], v[5:], "drop first 5 winters")
        add(loc, met, None, y[:-5], v[:-5], "drop last 5 winters")
        ok = ~np.isnan(v)
        ols = stats.linregress(y[ok], v[ok])
        out.append(dict(location_id=loc, metric=met, variant="OLS slope (comparison only)", n_seasons=int(ok.sum()),
                        slope_per_decade=ols.slope * 10, ci95_low=(ols.slope - 1.96 * ols.stderr) * 10,
                        ci95_high=(ols.slope + 1.96 * ols.stderr) * 10, mk_tau=np.nan, mk_z=np.nan, mk_p=ols.pvalue,
                        lag1_resid_autocorr=np.nan, status="ols"))
# road metrics over the FULL road record 1993-2024 and the 2001-2024 NASA window
for rid, loc in [("dettah", "dettah_bay"), ("aklavik", "aklavik_delta")]:
    rr = roads[(roads.road_id == rid) & (roads.record_status == "verified")].copy()
    rr["od"] = [(dt.date.fromisoformat(a) - dt.date(y, 10, 1)).days for a, y in zip(rr.opening_date, rr.season_start_year)]
    rr["cd"] = [(dt.date.fromisoformat(a) - dt.date(y, 10, 1)).days for a, y in zip(rr.closing_date, rr.season_start_year)]
    rr["span"] = (pd.to_datetime(rr.closing_date) - pd.to_datetime(rr.opening_date)).dt.days
    for met, col in [("road_open_day", "od"), ("road_close_day", "cd"), ("road_open_to_close_days", "span")]:
        add(loc, met, None, rr.season_start_year.to_numpy(), rr[col].to_numpy(), "road record 1993-2024")
        s = rr[rr.season_start_year >= 2001]
        add(loc, met, None, s.season_start_year.to_numpy(), s[col].to_numpy(), "road record 2001-2024")
tr = pd.DataFrame(out)
tr.to_csv(P("data/processed/trend_results.csv"), index=False, float_format="%.5g")

# regional comparison: Dettah minus Aklavik on common complete years
comp = []
d = sm[sm.location_id == "dettah_bay"].set_index("season_start_year")
a = sm[sm.location_id == "aklavik_delta"].set_index("season_start_year")
for met in METRICS:
    common = d.index.intersection(a.index)
    diff = (d.loc[common, met] - a.loc[common, met]).to_numpy()
    t = m.trend(common.to_numpy(), diff)
    comp.append(dict(metric=met, n_common=t.n, diff_slope_per_decade=t.slope_per_decade, ci95_low=t.ci_low_per_decade,
                     ci95_high=t.ci_high_per_decade, mk_p=t.mk_p, status=t.status))
pd.DataFrame(comp).to_csv(P("data/processed/regional_comparison.csv"), index=False, float_format="%.5g")

# exploratory road-climate correlations (Spearman)
cor = []
for loc, g in sm.groupby("location_id"):
    for xm, ym in [("fdd_octdec", "open_day"), ("fdd_pre_cutoff", "open_day"), ("mean_octdec_c", "open_day"),
                   ("mean_mar15_apr15_c", "close_day")]:
        r, p, n = m.spearman(g[xm], g[ym])
        cor.append(dict(location_id=loc, climate_metric=xm, road_metric=ym, spearman_rho=r, p=p, n=n,
                        note="exploratory; association only"
                        + ("; Oct-Dec FDD includes days after some openings (retrospective)" if xm == "fdd_octdec" else "")))
pd.DataFrame(cor).to_csv(P("data/processed/road_climate_correlations.csv"), index=False, float_format="%.5g")

# station validation (Dettah / Yellowknife A)
st = pd.read_csv(P("data/raw/weather_stations/eccc_yellowknife_daily_2001_2025.csv"), parse_dates=["date"])
st["mean_temp_c"] = pd.to_numeric(st["mean_temp_c"], errors="coerce")
st = st.dropna(subset=["mean_temp_c"]).sort_values(["date", "station_id"]).drop_duplicates("date", keep="last")
nd = temps[temps.location_id == "dettah_bay"][["date", "temperature_c"]]
mt = nd.merge(st[["date", "station_id", "mean_temp_c"]], on="date", how="inner")
mt.insert(0, "location_id", "dettah_bay")
mt = mt.rename(columns={"temperature_c": "nasa_temperature_c", "mean_temp_c": "station_temperature_c"})
mt.to_csv(P("data/processed/station_validation.csv"), index=False)
mt["diff"] = mt.nasa_temperature_c - mt.station_temperature_c
rows = []
for name, sub in [("all matched days", mt), ("Oct-Mar only", mt[mt.date.dt.month.isin([10, 11, 12, 1, 2, 3])]),
                  ("station 1706 era (to 2012)", mt[mt.station_id == 1706]), ("station 51058 era (2013+)", mt[mt.station_id == 51058])]:
    rows.append(dict(subset=name, n_days=len(sub), bias_nasa_minus_station_c=sub["diff"].mean(),
                     mae_c=sub["diff"].abs().mean(), rmse_c=float(np.sqrt((sub["diff"] ** 2).mean())),
                     pearson_r=sub[["nasa_temperature_c", "station_temperature_c"]].corr().iloc[0, 1]))
# seasonal FDD, station vs NASA
fd = []
stg = st.rename(columns={"mean_temp_c": "temperature_c"})[["date", "temperature_c"]]
for y in YEARS:
    sf = m.fdd(stg, y, "early")
    fd.append(dict(season_start_year=y, fdd_nasa=sm[(sm.location_id == "dettah_bay") & (sm.season_start_year == y)].fdd_octdec.iloc[0], fdd_station=sf))
fd = pd.DataFrame(fd)
okf = fd.dropna()
rows.append(dict(subset=f"Oct-Dec FDD, seasons with complete station data (n={len(okf)})", n_days=len(okf),
                 bias_nasa_minus_station_c=(okf.fdd_nasa - okf.fdd_station).mean(), mae_c=(okf.fdd_nasa - okf.fdd_station).abs().mean(),
                 rmse_c=float(np.sqrt(((okf.fdd_nasa - okf.fdd_station) ** 2).mean())),
                 pearson_r=okf[["fdd_nasa", "fdd_station"]].corr().iloc[0, 1]))
pd.DataFrame(rows).to_csv(P("data/processed/station_summary.csv"), index=False, float_format="%.4g")
fd.to_csv(P("data/processed/station_fdd_by_season.csv"), index=False, float_format="%.2f")
print("done")
