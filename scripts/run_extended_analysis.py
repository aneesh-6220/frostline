#!/usr/bin/env python3
"""Extended Frostline analysis: more NASA POWER variables, 9 corridors, station snow data.

Usage (from repo root): python3 -I scripts/run_extended_analysis.py
Reads  data/raw/nasa/power_daily_ext_<id>.csv, data/raw/weather_stations/eccc_stations_daily_2001_2025.csv,
       data/processed/road_operations.csv
Writes data/processed/nasa_daily_variables.csv, extended_season_metrics.csv, extended_trends.csv,
       corridor_panel.csv, yellowknife_snow_by_season.csv, station_validation_aklavik_inuvik.csv
"""
import datetime as dt
import glob
import io
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
ROAD = {"dettah_bay": "dettah", "aklavik_delta": "aklavik", "wrigley_tulita": "wrigley_tulita",
        "norman_wells_fgh": "norman_wells_fort_good_hope", "deline": "deline",
        "liard_fort_simpson": "liard_fort_simpson", "tibbitt_contwoyto": "tibbitt_contwoyto",
        "sambaa_ke": "sambaa_ke", "nahanni_butte": "nahanni_butte"}
KIND = {"dettah_bay": "ice_road", "aklavik_delta": "ice_road", "liard_fort_simpson": "ice_crossing",
        "tibbitt_contwoyto": "mining_road"}  # others: winter_road (land)
YEARS = range(2001, 2025)

# ---- load POWER extended files
frames = []
for f in sorted(glob.glob(P("data/raw/nasa/power_daily_ext_*.csv"))):
    loc = os.path.basename(f)[len("power_daily_ext_"):-4]
    lines = open(f, encoding="utf-8").read().splitlines()
    k = next(i for i, l in enumerate(lines) if "-END HEADER-" in l)
    d = pd.read_csv(io.StringIO("\n".join(lines[k + 1:])))
    d["date"] = pd.to_datetime(dict(year=d.YEAR, month=d.MO, day=d.DY))
    d = d.drop(columns=["YEAR", "MO", "DY"]).replace(-999, np.nan)
    d.insert(0, "location_id", loc)
    frames.append(d)
allv = pd.concat(frames, ignore_index=True)
allv.to_csv(P("data/processed/nasa_daily_variables.csv"), index=False, float_format="%.3f")
chk = allv[allv.location_id == "dettah_bay"].set_index("date").T2M
base = pd.read_csv(P("data/processed/nasa_daily_temperature.csv"), parse_dates=["date"])
base = base[base.location_id == "dettah_bay"].set_index("date").temperature_c
assert (chk - base).abs().max() < 1e-9, "extended T2M does not match the earlier T2M file"

roads = pd.read_csv(P("data/processed/road_operations.csv"))


def win(g, col, a, b, how):
    s = g[(g.date >= pd.Timestamp(a)) & (g.date <= pd.Timestamp(b))][col]
    need = (b - a).days + 1
    if s.notna().sum() != need:
        return np.nan
    return {"mean": s.mean, "sum": s.sum, "fdd": lambda: np.maximum(0, -s).sum()}[how]()


rows = []
for loc, g in allv.groupby("location_id"):
    g = g.rename(columns={"T2M": "temperature_c"})
    rr = roads[(roads.road_id == ROAD[loc]) & (roads.record_status == "verified")].set_index("season_start_year")
    for y in YEARS:
        r = dict(location_id=loc, road_id=ROAD[loc], road_kind=KIND.get(loc, "winter_road"), season_start_year=y)
        r["fdd_octdec"] = m.fdd(g, y, "early")
        r["mean_octdec_c"] = m.seasonal_mean(g, y, "early")
        r["mean_janmar_c"] = m.seasonal_mean(g, y, "mid")
        r["tmax_mean_mar15_apr15_c"] = win(g, "T2M_MAX", dt.date(y + 1, 3, 15), dt.date(y + 1, 4, 15), "mean")
        r["skin_temp_mean_octdec_c"] = win(g, "TS", dt.date(y, 10, 1), dt.date(y, 12, 31), "mean")
        r["precip_octdec_mm"] = win(g, "PRECTOTCORR", dt.date(y, 10, 1), dt.date(y, 12, 31), "sum")
        r["precip_oct_nov_mm"] = win(g, "PRECTOTCORR", dt.date(y, 10, 1), dt.date(y, 11, 30), "sum")
        r["wind_mean_octdec_ms"] = win(g, "WS10M", dt.date(y, 10, 1), dt.date(y, 12, 31), "mean")
        r["rh_mean_octdec_pct"] = win(g, "RH2M", dt.date(y, 10, 1), dt.date(y, 12, 31), "mean")
        r["lw_down_mean_octdec"] = win(g, "ALLSKY_SFC_LW_DWN", dt.date(y, 10, 1), dt.date(y, 12, 31), "mean")
        r["sw_down_mean_mar15_apr15"] = win(g, "ALLSKY_SFC_SW_DWN", dt.date(y + 1, 3, 15), dt.date(y + 1, 4, 15), "mean")
        r["lw_down_mean_mar15_apr15"] = win(g, "ALLSKY_SFC_LW_DWN", dt.date(y + 1, 3, 15), dt.date(y + 1, 4, 15), "mean")
        r["mean_mar15_apr15_c"] = win(g, "temperature_c", dt.date(y + 1, 3, 15), dt.date(y + 1, 4, 15), "mean")
        if y in rr.index:
            od, cd = dt.date.fromisoformat(rr.loc[y, "opening_date"]), dt.date.fromisoformat(rr.loc[y, "closing_date"])
            r.update(m.road_metrics(od, cd, y))
        rows.append(r)
em = pd.DataFrame(rows)
em.to_csv(P("data/processed/extended_season_metrics.csv"), index=False, float_format="%.4f")

# ---- trends for all corridors / metrics (road + climate)
MET = ["fdd_octdec", "mean_octdec_c", "mean_janmar_c", "tmax_mean_mar15_apr15_c", "skin_temp_mean_octdec_c",
       "precip_octdec_mm", "wind_mean_octdec_ms", "rh_mean_octdec_pct", "lw_down_mean_octdec",
       "sw_down_mean_mar15_apr15", "lw_down_mean_mar15_apr15", "open_day", "close_day", "open_to_close_days"]
out = []
for loc, g in em.groupby("location_id"):
    for met in MET:
        sub = g.dropna(subset=[met])
        t = m.trend(sub.season_start_year, sub[met])
        out.append(dict(location_id=loc, road_kind=g.road_kind.iloc[0], metric=met, window="2001-2024", n=t.n,
                        slope_per_decade=t.slope_per_decade, ci95_low=t.ci_low_per_decade, ci95_high=t.ci_high_per_decade,
                        mk_p=t.mk_p, lag1=t.lag1_autocorr_resid, status=t.status))
et = pd.DataFrame(out)
et.to_csv(P("data/processed/extended_trends.csv"), index=False, float_format="%.5g")

# ---- corridor panel: climate trend vs road-date trend per corridor
pan = []
for loc, g in em.groupby("location_id"):
    row = dict(location_id=loc, road_id=ROAD[loc], road_kind=g.road_kind.iloc[0])
    for met in ["mean_octdec_c", "fdd_octdec", "open_day", "close_day", "open_to_close_days"]:
        t = et[(et.location_id == loc) & (et.metric == met)].iloc[0]
        row[met + "_slope_per_dec"] = t.slope_per_decade
        row[met + "_p"] = t.mk_p
    row["n_road_seasons"] = int(g.open_day.notna().sum())
    pan.append(row)
pan = pd.DataFrame(pan)
pan.to_csv(P("data/processed/corridor_panel.csv"), index=False, float_format="%.4g")

# ---- pooled within-corridor correlations: REMOVED (remediation). The pooled pairs shared weather across corridors
# (not independent, so p-values were invalid) and used predictor windows that extend past opening/closing dates.

# ---- station snow by season (Yellowknife A: ids 1706 + 51058). Association statistics are computed in run_remediation_analysis.py
st = pd.read_csv(P("data/raw/weather_stations/eccc_stations_daily_2001_2025.csv"), parse_dates=["date"])
yk = st[st.station_id.isin([1706, 51058])].sort_values("date").drop_duplicates("date", keep="last").set_index("date")
sn = []
for y in YEARS:
    def span(col, a, b, how, min_frac=0.9):
        s_ = yk.loc[pd.Timestamp(a):pd.Timestamp(b), col]
        need = (pd.Timestamp(b) - pd.Timestamp(a)).days + 1
        if s_.notna().sum() < min_frac * need:
            return np.nan
        return float(s_.sum() if how == "sum" else s_.mean())
    def day(col, d):
        s_ = yk[col].get(pd.Timestamp(d), np.nan)
        return float(s_) if pd.notna(s_) else np.nan
    sn.append(dict(season_start_year=y,
                   snowfall_octdec_cm=span("total_snow_cm", dt.date(y, 10, 1), dt.date(y, 12, 31), "sum"),
                   snowfall_oct1_nov28_cm=span("total_snow_cm", dt.date(y, 10, 1), dt.date(y, 11, 28), "sum"),
                   sog_mean_nov1_28_cm=span("snow_on_ground_cm", dt.date(y, 11, 1), dt.date(y, 11, 28), "mean", 0.8),
                   sog_nov28_cm=day("snow_on_ground_cm", dt.date(y, 11, 28)),
                   sog_dec1_cm=day("snow_on_ground_cm", dt.date(y, 12, 1))))
sn = pd.DataFrame(sn).merge(em[em.location_id == "dettah_bay"][["season_start_year", "open_day", "precip_octdec_mm", "fdd_octdec"]], on="season_start_year")
sn.to_csv(P("data/processed/yellowknife_snow_by_season.csv"), index=False, float_format="%.3f")

# ---- Aklavik delta station validation (Inuvik Climate and Aklavik A)
nd = allv[allv.location_id == "aklavik_delta"][["date", "T2M"]]
rows = []
vv = []
for sid, name in [(41883, "INUVIK CLIMATE"), (1623, "AKLAVIK A (to 2014)"), (52962, "AKLAVIK A (2018+)"), (51477, "INUVIK A (2018+)")]:
    s = st[st.station_id == sid][["date", "mean_temp_c"]].dropna()
    mt = nd.merge(s, on="date")
    mt["diff"] = mt.T2M - mt.mean_temp_c
    win_ = mt[mt.date.dt.month.isin([10, 11, 12, 1, 2, 3])]
    rows.append(dict(station_id=sid, station=name, n_days=len(mt), bias_all_c=mt["diff"].mean(), mae_all_c=mt["diff"].abs().mean(),
                     r_all=mt[["T2M", "mean_temp_c"]].corr().iloc[0, 1], bias_octmar_c=win_["diff"].mean(),
                     mae_octmar_c=win_["diff"].abs().mean(), r_octmar=win_[["T2M", "mean_temp_c"]].corr().iloc[0, 1]))
    if sid in (41883, 1623):
        x = mt.rename(columns={"T2M": "nasa_temperature_c", "mean_temp_c": "station_temperature_c"})[["date", "nasa_temperature_c", "station_temperature_c"]]
        x.insert(0, "station_id", sid); x.insert(0, "location_id", "aklavik_delta"); vv.append(x)
pd.concat(vv).to_csv(P("data/processed/station_validation_aklavik_inuvik.csv"), index=False)
pd.DataFrame(rows).to_csv(P("data/processed/station_summary_aklavik_inuvik.csv"), index=False, float_format="%.4g")
print("done")
