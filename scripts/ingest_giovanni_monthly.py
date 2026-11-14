#!/usr/bin/env python3
"""Optional ingest of a REAL Giovanni MERRA-2 monthly 2 m temperature time series.

Does nothing (exit 0, writes nothing) unless a file exists at data/raw/nasa/giovanni/giovanni_M2TMNXSLV_T2M_<location_id>.csv.
Nothing in this repository fabricates such a file. A file is only accepted if its header names collection M2TMNXSLV and
variable T2M, so a mislabelled export cannot be attributed to the wrong product.

Monthly values are used ONLY for seasonal/annual mean-temperature trends and a provenance cross-check against the POWER daily
series (mean of monthly means). They NEVER replace daily values in FDD or thaw-day calculations (docs/SCIENTIFIC_METHODS.md).

Usage:  python3 -I scripts/ingest_giovanni_monthly.py [--in DIR] [--out-dir DIR]
"""
import argparse
import glob
import os
import re
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
import northlink_metrics as nm  # noqa: E402

SOURCE_ID = "giovanni_merra2_M2TMNXSLV_T2M"
NAME_RE = re.compile(r"giovanni_M2TMNXSLV_T2M_([a-z0-9_]+)\.csv$")
DATA_RE = re.compile(r"^\s*(\d{4})-(\d{2})(?:-\d{2})?(?:[T ][0-9:]+Z?)?\s*,\s*(-?[0-9.eE+]+)")


def parse(path):
    header, rows = [], []
    for line in open(path, encoding="utf-8-sig"):
        m = DATA_RE.match(line)
        if m:
            rows.append((int(m.group(1)), int(m.group(2)), float(m.group(3))))
        elif not rows:
            header.append(line.strip())
    htxt = "\n".join(header)
    if "M2TMNXSLV" not in htxt or not re.search(r"\bT2M\b", htxt):
        sys.exit(f"{path}: header must name collection M2TMNXSLV and variable T2M; refusing to attribute this file to MERRA-2")
    if not rows:
        sys.exit(f"{path}: no monthly data rows found")
    df = pd.DataFrame(rows, columns=["year", "month", "v"])
    if df.duplicated(["year", "month"]).any():
        sys.exit(f"{path}: duplicate months")
    df["t_c"] = df.v - 273.15 if df.v.median() > 100 else df.v  # Kelvin export is converted; Celsius export is used as is
    return df


def power_monthly(loc):
    d = pd.read_csv(os.path.join(ROOT, "data/processed/nasa_daily_temperature.csv"), parse_dates=["date"])
    d = d[d.location_id == loc]
    g = d.groupby([d.date.dt.year.rename("year"), d.date.dt.month.rename("month")]).temperature_c.mean()
    return g.rename("power_c").reset_index()


def seasons(df, col):
    out = []
    for y in range(int(df.year.min()) - 1, int(df.year.max()) + 1):
        def part(months, year):
            s = df[(df.year == year) & df.month.isin(months)]
            return (s[col].mean() if len(s) == len(months) else np.nan), len(s)
        od, nod = part([10, 11, 12], y)
        jm, njm = part([1, 2, 3], y + 1)
        out.append((y, od, jm, nod, njm))
    r = pd.DataFrame(out, columns=["season_start_year", "octdec_mean_c", "janmar_mean_c", "n_months_octdec", "n_months_janmar"])
    return r[(r.n_months_octdec == 3) | (r.n_months_janmar == 3)].reset_index(drop=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="indir", default=os.path.join(ROOT, "data/raw/nasa/giovanni"))
    ap.add_argument("--out-dir", dest="outdirs", action="append")
    a = ap.parse_args()
    outdirs = a.outdirs or [os.path.join(ROOT, "data/processed"), os.path.join(ROOT, "UI/data_real")]
    files = sorted(glob.glob(os.path.join(a.indir, "giovanni_M2TMNXSLV_T2M_*.csv")))
    if not files:
        print("no Giovanni files present: nothing ingested (see docs/CHALLENGE_ELIGIBILITY.md for the manual step)")
        return
    seas, trends, checks = [], [], []
    for f in files:
        m = NAME_RE.search(os.path.basename(f))
        if not m:
            sys.exit(f"{f}: file name must be giovanni_M2TMNXSLV_T2M_<location_id>.csv")
        loc = m.group(1)
        g = parse(f)
        s = seasons(g, "t_c")
        s.insert(0, "location_id", loc)
        s["source_id"] = SOURCE_ID
        seas.append(s)
        for metric in ("octdec_mean_c", "janmar_mean_c"):
            t = nm.trend(s.season_start_year, s[metric])
            trends.append(dict(location_id=loc, metric=metric, n=t.n, slope_per_decade=round(t.slope_per_decade, 3),
                               ci95_low=round(t.ci_low_per_decade, 3), ci95_high=round(t.ci_high_per_decade, 3), mk_p=round(t.mk_p, 4),
                               lag1=round(t.lag1_autocorr_resid, 3), status=t.status, source_id=SOURCE_ID))
        j = g.rename(columns={"t_c": "giovanni_c"})[["year", "month", "giovanni_c"]].merge(power_monthly(loc), on=["year", "month"])
        j["diff_c"] = j.giovanni_c - j.power_c
        checks.append(dict(location_id=loc, n_months=len(j), mean_diff_giovanni_minus_power_c=round(j.diff_c.mean(), 3),
                           max_abs_diff_c=round(j.diff_c.abs().max(), 3), pearson_r=round(float(np.corrcoef(j.giovanni_c, j.power_c)[0, 1]), 4)))
    for d in outdirs:
        os.makedirs(d, exist_ok=True)
        pd.concat(seas).to_csv(os.path.join(d, "giovanni_monthly_t2m_seasonal.csv"), index=False)
        pd.DataFrame(trends).to_csv(os.path.join(d, "giovanni_monthly_t2m_trends.csv"), index=False)
        pd.DataFrame(checks).to_csv(os.path.join(d, "giovanni_vs_power_check.csv"), index=False)
    print("ingested", len(files), "Giovanni file(s)")


if __name__ == "__main__":
    main()
