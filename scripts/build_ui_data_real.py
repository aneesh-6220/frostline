#!/usr/bin/env python3
"""Regenerate UI/data_real/ from data/processed/ (single source of truth). Does NOT touch UI/northlink_app.py.

Usage (repo root): python3 -I scripts/build_ui_data_real.py
Locked-schema files (derived): corridors.csv, climate_annual.csv, road_seasons.csv, trends.csv
Mirrored files (byte copies): extended_trends, corridor_panel, snow_vs_opening, snow_trends, station_summary_aklavik_inuvik,
yellowknife_snow_by_season, multiple_testing_126, road_record_trends_all_routes, hypothesis_families

Schema notes: `season_length_days` in road_seasons.csv is the open-to-close INTERVAL, not usable days.
NASA values are MERRA-2 reanalysis, not observations; see docs/TEMPERATURE_BIAS_DIAGNOSIS.md.
"""
import datetime as dt
import os
import shutil
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)
import northlink_metrics as m  # noqa: E402

P = lambda *a: os.path.join(ROOT, *a)
OUT = P("UI", "data_real")
os.makedirs(OUT, exist_ok=True)
sm = pd.read_csv(P("data/processed/season_metrics.csv"))
roads = pd.read_csv(P("data/processed/road_operations.csv"))
temps = pd.read_csv(P("data/processed/nasa_daily_temperature.csv"), parse_dates=["date"])
LOC = {"dettah_bay": "dettah", "aklavik_delta": "aklavik"}

pd.DataFrame([
    ["dettah_bay", "Dettah Ice Road (Yellowknife Bay)", "verified", 62.43, -114.34, "true"],
    ["aklavik_delta", "Aklavik Ice Road (Mackenzie Delta)", "verified", 68.29, -134.37, "true"],
    ["custom", "Custom", "custom", 65.0, -120.0, "false"],
], columns=["corridor_id", "name", "kind", "lat", "lon", "has_road_records"]).to_csv(P(OUT, "corridors.csv"), index=False)

rows = []
for loc, g in sm.groupby("location_id"):
    t = temps[temps.location_id == loc]
    for y in range(2001, 2025):
        c = m.season_coverage(t, y, "full")
        r = g[g.season_start_year == y].iloc[0]
        for met, col in [("fdd", "fdd_octdec"), ("thaw_days", "thaw_days_janmar")]:
            rows.append([loc, y, met, round(float(r[col]), 2), c.expected, c.expected - c.valid, "false"])
pd.DataFrame(rows, columns=["corridor_id", "season_year", "metric", "value", "n_days", "missing_days", "synthetic"]).sort_values(
    ["corridor_id", "season_year", "metric"], key=lambda s: s.map({"fdd": 0, "thaw_days": 1}) if s.name == "metric" else s
).to_csv(P(OUT, "climate_annual.csv"), index=False)

rr = []
for loc, rid in LOC.items():
    g = roads[(roads.road_id == rid) & (roads.record_status == "verified")]
    for _, r in g.iterrows():
        od, cd = dt.date.fromisoformat(r.opening_date), dt.date.fromisoformat(r.closing_date)
        rr.append([loc, int(r.season_start_year), r.opening_date, r.closing_date, (cd - od).days, "false"])
pd.DataFrame(rr, columns=["corridor_id", "season_year", "open_date", "close_date", "season_length_days", "synthetic"]).to_csv(P(OUT, "road_seasons.csv"), index=False)

SUFFIX = " NASA reanalysis, not an observation; see docs/TEMPERATURE_BIAS_DIAGNOSIS.md."
tr = []
for loc in ["dettah_bay", "aklavik_delta"]:
    g = sm[sm.location_id == loc]
    for met, col, label in [("fdd", "fdd_octdec", "Oct-Dec freezing degree-days"), ("thaw_days", "thaw_days_janmar", "Mid-winter thaw days")]:
        t = m.trend(g.season_start_year, g[col])
        if t.status != "ok":
            text = (f"{label}: no trend estimated (status {t.status}). The daily mean is above 0 C on very few days in 2001-2024 in NASA reanalysis, "
                    "and the reanalysis runs colder than the Yellowknife station, so zero NASA thaw days does not mean no thaw." + SUFFIX)
            tr.append([loc, met, "", "", "", t.n, "", "", text, "false"])
            continue
        spans = t.ci_low_per_decade <= 0 <= t.ci_high_per_decade
        verdict = ("Not statistically distinguishable from no change in this 24-winter record; that is not proof of no change."
                   if spans else "The 95% CI excludes zero; exploratory, not adjusted for multiple testing.")
        text = (f"{label} changed by about {t.slope_per_decade:+.0f} C-days per decade (95% CI {t.ci_low_per_decade:.0f} to {t.ci_high_per_decade:+.0f}). "
                + verdict + SUFFIX)
        tr.append([loc, met, round(t.slope_per_decade, 2), round(t.ci_low_per_decade, 2), round(t.ci_high_per_decade, 2), t.n,
                   round(t.mk_tau, 3), round(t.mk_p, 3), text, "false"])
pd.DataFrame(tr, columns=["corridor_id", "metric", "slope_per_decade", "ci_low", "ci_high", "n_seasons", "kendall_tau", "p_value",
                          "plain_takeaway", "synthetic"]).to_csv(P(OUT, "trends.csv"), index=False)

for f in ["extended_trends", "corridor_panel", "snow_vs_opening", "snow_trends", "station_summary_aklavik_inuvik", "yellowknife_snow_by_season",
          "multiple_testing_126", "road_record_trends_all_routes", "hypothesis_families"]:
    shutil.copyfile(P("data/processed", f + ".csv"), P(OUT, f + ".csv"))
print("UI/data_real regenerated")
