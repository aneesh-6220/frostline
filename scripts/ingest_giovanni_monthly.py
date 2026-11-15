#!/usr/bin/env python3
"""Ingest REAL NASA Giovanni MERRA-2 monthly 2 m temperature time series (collection M2TMNXSLV, variable T2M).

Accepted inputs in data/raw/nasa/giovanni/ (raw files are never modified):
  * the original Giovanni "Time Series, Area-Averaged" CSV export, kept under its Giovanni name
    g4.areaAvgTimeSeries.M2TMNXSLV_5_12_4_T2M.<dates>.<region>.csv. The study location is NOT taken from the file name:
    it is the location whose MERRA-2 0.5 x 0.625 degree grid cell centre equals the "Data Bounding Box" point that
    Giovanni reports in the header. A file whose grid point matches no study location is refused.
  * a file named giovanni_M2TMNXSLV_T2M_<location_id>.csv (route used by scripts/fetch_giovanni_monthly.py).

A file is only accepted if its header names collection M2TMNXSLV and variable T2M, so a mislabelled export cannot be
attributed to the wrong product. Values equal to the header's fill value (or >= 1e14, or non-finite) are treated as missing;
no gap is filled. Seasons and years are computed only from complete sets of months.

Monthly values are used ONLY for monthly/seasonal/annual mean-temperature analysis and for a provenance cross-check against
the POWER daily series (mean of daily values per month). They NEVER replace daily values in freezing-degree-day or thaw-day
calculations (docs/SCIENTIFIC_METHODS.md).

The companion NetCDF file is verified separately by scripts/verify_giovanni_netcdf.py (needs h5py), so that this script
stays dependency-free and byte-for-byte reproducible.

Usage:  python3 -I scripts/ingest_giovanni_monthly.py [--in DIR] [--out-dir DIR]
"""
import argparse
import glob
import hashlib
import math
import os
import re
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
import northlink_metrics as nm  # noqa: E402
import northlink_stats as ns  # noqa: E402

SOURCE_ID = "giovanni_merra2_M2TMNXSLV_T2M"
NAME_RE = re.compile(r"giovanni_M2TMNXSLV_T2M_([a-z0-9_]+)\.csv$")
G4_RE = re.compile(r"^g4\.areaAvgTimeSeries\.M2TMNXSLV_5_12_4_T2M\.\d{8}-\d{8}\..+\.csv$")
DATA_RE = re.compile(r"^\s*(\d{4})-(\d{2})(?:-\d{2})?(?:[T ][0-9:]+Z?)?\s*,\s*(\S+)\s*$")
FILL_FLOOR = 1e14                       # Giovanni fill is 1e15; anything this large is not a temperature
K_RANGE = (180.0, 340.0)                # physically plausible monthly mean 2 m temperature, kelvin
MERRA2_DLAT, MERRA2_DLON = 0.5, 0.625  # same grid definition as UI/frostline/registry.py
SEASONS = {"DJF": (12, 1, 2), "MAM": (3, 4, 5), "JJA": (6, 7, 8), "SON": (9, 10, 11)}
SEASON_LABEL = {"ANN": "Calendar year (Jan to Dec)", "DJF": "Winter (Dec to Feb)", "MAM": "Spring (Mar to May)", "JJA": "Summer (Jun to Aug)",
                "SON": "Autumn (Sep to Nov)", "octdec_mean_c": "Oct to Dec", "janmar_mean_c": "Jan to Mar"}


def sha256(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def cell_centre(lat, lon):
    return round(round(lat / MERRA2_DLAT) * MERRA2_DLAT, 4), round(-180 + round((lon + 180) / MERRA2_DLON) * MERRA2_DLON, 4)


def header_fields(lines):
    out = {}
    for ln in lines:
        k, sep, v = ln.partition(":,")
        if sep:
            out[k.strip()] = v.strip().strip('"').strip()
    return out


def parse(path):
    header, rows = [], []
    for line in open(path, encoding="utf-8-sig"):
        m = DATA_RE.match(line)
        if m:
            rows.append((int(m.group(1)), int(m.group(2)), m.group(3)))
        elif not rows:
            header.append(line.strip())
    htxt = "\n".join(header)
    if "M2TMNXSLV" not in htxt or not re.search(r"(?<![A-Za-z0-9])T2M(?![A-Za-z0-9])", htxt):
        sys.exit(f"{path}: header must name collection M2TMNXSLV and variable T2M; refusing to attribute this file to MERRA-2")
    if not rows:
        sys.exit(f"{path}: no monthly data rows found")
    h = header_fields(header)
    fill = None
    for k, v in h.items():
        if k.lower().startswith("fill value"):
            fill = float(v)
    df = pd.DataFrame(rows, columns=["year", "month", "raw"])
    if df.duplicated(["year", "month"]).any():
        sys.exit(f"{path}: duplicate months")
    if not df.month.between(1, 12).all():
        sys.exit(f"{path}: invalid month")
    stamps = df.year * 12 + df.month - 1
    if not (stamps.diff().dropna() == 1).all():
        sys.exit(f"{path}: months are not consecutive and ascending")
    v = pd.to_numeric(df.raw, errors="coerce")
    missing = v.isna() | ~np.isfinite(v) | (v.abs() >= FILL_FLOOR)
    if fill is not None:
        missing |= np.isclose(v, fill, rtol=1e-6)
    v = v.where(~missing)
    kelvin = v.median() > 100
    df["value_raw"] = v
    df["t_c"] = v - 273.15 if kelvin else v   # a kelvin export is converted; a Celsius export is used as is
    tk = df.t_c + 273.15
    if (tk.dropna() < K_RANGE[0]).any() or (tk.dropna() > K_RANGE[1]).any():
        sys.exit(f"{path}: values outside the plausible range {K_RANGE} K; refusing to ingest")
    df["missing"] = missing
    return df.drop(columns="raw"), h, header, ("K" if kelvin else "C"), fill


def location_points():
    loc = pd.read_csv(os.path.join(ROOT, "data/processed/locations.csv"))
    return {r.location_id: (float(r.latitude), float(r.longitude)) for r in loc.itertuples()}


def location_for_g4(path, h):
    box = h.get("Data Bounding Box", "")
    try:
        w, s, e, n = [float(x) for x in box.split(",")]
    except ValueError:
        sys.exit(f"{path}: header has no usable 'Data Bounding Box'; cannot tell which grid cell the series describes")
    if not (math.isclose(w, e) and math.isclose(s, n)):
        sys.exit(f"{path}: the data cover more than one grid point ({box}); this ingest handles single-cell series only")
    hits = [lid for lid, (la, lo) in location_points().items() if cell_centre(la, lo) == (round(s, 4), round(w, 4))]
    if len(hits) != 1:
        sys.exit(f"{path}: grid point {s}N {w}E matches {len(hits)} study locations; refusing to guess")
    return hits[0], (s, w)


def power_monthly(loc):
    d = pd.read_csv(os.path.join(ROOT, "data/processed/nasa_daily_temperature.csv"), parse_dates=["date"])
    d = d[d.location_id == loc]
    g = d.groupby([d.date.dt.year.rename("year"), d.date.dt.month.rename("month")]).temperature_c.agg(["mean", "count"])
    g = g[g["count"] == g.index.map(lambda ym: pd.Period(year=ym[0], month=ym[1], freq="M").days_in_month)]   # complete months only
    return g["mean"].rename("power_c").reset_index()


def winter_parts(df, col):
    """Oct-Dec and Jan-Mar means for each winter (same winter convention as the daily analysis); complete months only."""
    out = []
    for y in range(int(df.year.min()) - 1, int(df.year.max()) + 1):
        def part(months, year):
            s = df[(df.year == year) & df.month.isin(months)][col].dropna()
            return (s.mean() if len(s) == len(months) else np.nan), len(s)
        od, nod = part([10, 11, 12], y)
        jm, njm = part([1, 2, 3], y + 1)
        out.append((y, od, jm, nod, njm))
    r = pd.DataFrame(out, columns=["season_start_year", "octdec_mean_c", "janmar_mean_c", "n_months_octdec", "n_months_janmar"])
    return r[(r.n_months_octdec == 3) | (r.n_months_janmar == 3)].reset_index(drop=True)


def calendar_seasons(df):
    """Annual (Jan-Dec) and meteorological seasonal means. DJF is labelled with the year of its January and February."""
    rows = []
    vals = {(int(r.year), int(r.month)): r.t_c for r in df.itertuples() if not pd.isna(r.t_c)}
    for y in range(int(df.year.min()), int(df.year.max()) + 1):
        a = [vals.get((y, m)) for m in range(1, 13)]
        a = [x for x in a if x is not None]
        rows.append((y, "ANN", float(np.mean(a)) if len(a) == 12 else np.nan, len(a)))
        for s, months in SEASONS.items():
            keys = [((y - 1) if (s == "DJF" and m == 12) else y, m) for m in months]
            x = [vals[k] for k in keys if k in vals]
            rows.append((y, s, float(np.mean(x)) if len(x) == 3 else np.nan, len(x)))
    r = pd.DataFrame(rows, columns=["year", "season", "mean_c", "n_months"])
    return r


def trend_row(loc, metric, years, values, first, last):
    t = nm.trend(years, values)
    return dict(location_id=loc, metric=metric, first_year=first, last_year=last, n=t.n, slope_per_decade=round(t.slope_per_decade, 3),
                ci95_low=round(t.ci_low_per_decade, 3), ci95_high=round(t.ci_high_per_decade, 3), mk_p=round(t.mk_p, 4),
                lag1=round(t.lag1_autocorr_resid, 3), status=t.status, source_id=SOURCE_ID)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="indir", default=os.path.join(ROOT, "data/raw/nasa/giovanni"))
    ap.add_argument("--out-dir", dest="outdirs", action="append")
    a = ap.parse_args()
    outdirs = a.outdirs or [os.path.join(ROOT, "data/processed"), os.path.join(ROOT, "UI/data_real")]
    files = sorted(glob.glob(os.path.join(a.indir, "*.csv")))
    files = [f for f in files if NAME_RE.search(os.path.basename(f)) or G4_RE.match(os.path.basename(f))]
    if not files:
        print("no Giovanni files present: nothing ingested (see docs/CHALLENGE_ELIGIBILITY.md for the manual step)")
        return
    monthly, seas, cal, trends, checks, prov = [], [], [], [], [], []
    seen = set()
    for f in files:
        base = os.path.basename(f)
        g, h, header, unit, fill = parse(f)
        m = NAME_RE.search(base)
        if m:
            loc, point = m.group(1), None
        else:
            loc, point = location_for_g4(f, h)
        if loc in seen:
            sys.exit(f"{f}: a second Giovanni file for {loc}; keep exactly one per location")
        seen.add(loc)
        mon = g.assign(location_id=loc)[["location_id", "year", "month", "value_raw", "t_c", "missing"]]
        mon = mon.rename(columns={"value_raw": f"t2m_{unit.lower()}_as_published", "t_c": "t2m_c"})
        mon["t2m_c"] = mon.t2m_c.round(4)
        monthly.append(mon)
        s = winter_parts(g, "t_c").round({"octdec_mean_c": 4, "janmar_mean_c": 4})   # trends use exactly the published values
        s.insert(0, "location_id", loc)
        s["source_id"] = SOURCE_ID
        seas.append(s)
        c = calendar_seasons(g).round({"mean_c": 4})
        c.insert(0, "location_id", loc)
        cal.append(c)
        y0, y1 = int(g.year.min()), int(g.year.max())
        for sname in ("ANN", "DJF", "MAM", "JJA", "SON"):
            cs = c[c.season == sname].dropna(subset=["mean_c"])
            trends.append(trend_row(loc, sname, cs.year, cs.mean_c, int(cs.year.min()), int(cs.year.max())))
        for metric in ("octdec_mean_c", "janmar_mean_c"):
            ss = s.dropna(subset=[metric])
            trends.append(trend_row(loc, metric, ss.season_start_year, ss[metric], int(ss.season_start_year.min()), int(ss.season_start_year.max())))
        fam = [r for r in trends if r["location_id"] == loc]
        for r, q in zip(fam, ns.bh_adjust([r["mk_p"] for r in fam])):
            r["q_bh_within_location"] = round(float(q), 4)
            r["family_size"] = len(fam)
        j = g.rename(columns={"t_c": "giovanni_c"})[["year", "month", "giovanni_c"]].dropna().merge(power_monthly(loc), on=["year", "month"])
        j["diff_c"] = j.giovanni_c - j.power_c
        checks.append(dict(location_id=loc, n_months=len(j), first=f"{int(j.year.iloc[0])}-{int(j.month.iloc[0]):02d}", last=f"{int(j.year.iloc[-1])}-{int(j.month.iloc[-1]):02d}",
                           mean_diff_giovanni_minus_power_c=round(j.diff_c.mean(), 3), max_abs_diff_c=round(j.diff_c.abs().max(), 3),
                           pearson_r=round(float(np.corrcoef(j.giovanni_c, j.power_c)[0, 1]), 4)))
        nc = os.path.splitext(f)[0] + ".nc"
        rows = [("source_file", base), ("source_sha256", sha256(f)),
                ("netcdf_file", os.path.basename(nc) if os.path.isfile(nc) else ""), ("netcdf_sha256", sha256(nc) if os.path.isfile(nc) else ""),
                ("title", h.get("Title", "")), ("user_start", h.get("User Start Date", "")), ("user_end", h.get("User End Date", "")),
                ("user_bounding_box_wsen", h.get("User Bounding Box", "")), ("data_grid_point_wsen", h.get("Data Bounding Box", "")),
                ("reproduce_url", h.get("URL to Reproduce Results", "")), ("fill_value", "" if fill is None else repr(fill)),
                ("units_as_published", unit), ("product", "MERRA-2 M2TMNXSLV (tavgM_2d_slv_Nx) version 5.12.4, variable T2M"),
                ("n_months", str(len(g))), ("n_missing", str(int(g.missing.sum()))),
                ("first_month", f"{y0}-{int(g.month.iloc[0]):02d}"), ("last_month", f"{y1}-{int(g.month.iloc[-1]):02d}"),
                ("matched_by", "Data Bounding Box point equals the MERRA-2 cell centre of the study location" if point else "file name")]
        prov.extend(dict(location_id=loc, key=k, value=v) for k, v in rows)
    for d in outdirs:
        os.makedirs(d, exist_ok=True)
        pd.concat(seas).round({"octdec_mean_c": 4, "janmar_mean_c": 4}).to_csv(os.path.join(d, "giovanni_monthly_t2m_seasonal.csv"), index=False)
        pd.DataFrame(trends).to_csv(os.path.join(d, "giovanni_monthly_t2m_trends.csv"), index=False)
        pd.DataFrame(checks).to_csv(os.path.join(d, "giovanni_vs_power_check.csv"), index=False)
        pd.concat(monthly).to_csv(os.path.join(d, "giovanni_monthly_t2m.csv"), index=False)
        pd.concat(cal).round({"mean_c": 4}).to_csv(os.path.join(d, "giovanni_t2m_calendar_seasons.csv"), index=False)
        pd.DataFrame(prov).to_csv(os.path.join(d, "giovanni_provenance.csv"), index=False)
    print("ingested", len(files), "Giovanni file(s)")


if __name__ == "__main__":
    main()
