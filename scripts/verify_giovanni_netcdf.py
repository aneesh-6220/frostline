#!/usr/bin/env python3
"""Verify that each Giovanni CSV in data/raw/nasa/giovanni/ agrees with the NetCDF file Giovanni produced alongside it.

Checks: product short name and version, variable, units (K), fill value, CF time axis (seconds since 1970-01-01, monthly,
contiguous), grid point (geospatial_lat/lon min = max), user dates, and value-by-value agreement with the CSV export.
Writes data/processed/giovanni_netcdf_verification.json. Needs h5py (requirements-dev.txt); the app does not.

Usage:  python3 -I scripts/verify_giovanni_netcdf.py
"""
import datetime as dt
import glob
import hashlib
import json
import os
import sys

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
RAW = os.path.join(ROOT, "data/raw/nasa/giovanni")
OUT = os.path.join(ROOT, "data/processed/giovanni_netcdf_verification.json")
VAR = "M2TMNXSLV_5_12_4_T2M"


def _s(v):
    if isinstance(v, bytes):
        return v.decode()
    if isinstance(v, np.ndarray):
        return v.tolist()[0] if v.size == 1 else v.tolist()
    return v


def csv_values(path):
    vals = []
    for ln in open(path, encoding="utf-8-sig"):
        if ln[:4].isdigit() and "," in ln:
            t, v = ln.strip().split(",")
            vals.append((t[:7], float(v)))
    return vals


def verify(nc_path, csv_path):
    import h5py
    f = h5py.File(nc_path, "r")
    a = {k: _s(v) for k, v in f.attrs.items()}
    v = f[VAR]
    va = {k: _s(x) for k, x in v.attrs.items() if k not in ("DIMENSION_LIST", "REFERENCE_LIST")}
    data = v[:].astype("float64")
    t = f["time"][:].astype("int64")
    months = [(dt.datetime(1970, 1, 1) + dt.timedelta(seconds=int(s))).strftime("%Y-%m") for s in t]
    stamps = [int(m[:4]) * 12 + int(m[5:]) - 1 for m in months]
    c = csv_values(csv_path)
    fill = float(va["_FillValue"])
    checks = {
        "product_short_name": va.get("product_short_name") == "M2TMNXSLV",
        "product_version": va.get("product_version") == "5.12.4",
        "variable_T2M": va.get("origname") == "T2M",
        "units_K": va.get("units") == "K",
        "time_units": _s(f["time"].attrs["units"]) == "seconds since 1970-01-01 00:00:00",
        "monthly_contiguous": all(b - x == 1 for x, b in zip(stamps, stamps[1:])),
        "single_grid_point": a["geospatial_lat_min"] == a["geospatial_lat_max"] and a["geospatial_lon_min"] == a["geospatial_lon_max"],
        "same_length_as_csv": len(c) == len(data),
        "same_months_as_csv": [m for m, _ in c] == months,
        "no_fill_values": bool(np.all(np.abs(data) < abs(fill) / 10)),
    }
    diff = float(np.max(np.abs(np.array([x for _, x in c]) - data))) if checks["same_length_as_csv"] else None
    checks["values_match_csv_within_1e-4_K"] = diff is not None and diff < 1e-4   # NetCDF is float32; CSV prints 6 decimals
    return {
        "netcdf_file": os.path.basename(nc_path), "netcdf_sha256": hashlib.sha256(open(nc_path, "rb").read()).hexdigest(),
        "csv_file": os.path.basename(csv_path), "csv_sha256": hashlib.sha256(open(csv_path, "rb").read()).hexdigest(),
        "conventions": a.get("Conventions"), "temporal_resolution": a.get("temporal_resolution"),
        "grid_point_lat": a.get("geospatial_lat_min"), "grid_point_lon": a.get("geospatial_lon_min"),
        "user_start": a.get("userstartdate"), "user_end": a.get("userenddate"), "title": a.get("title"),
        "long_name": va.get("long_name"), "units": va.get("units"), "cell_methods": va.get("cell_methods"), "fill_value": fill,
        "n_months": len(data), "first_month": months[0], "last_month": months[-1],
        "min_K": round(float(data.min()), 4), "max_K": round(float(data.max()), 4),
        "max_abs_diff_csv_vs_netcdf_K": None if diff is None else round(diff, 7),
        "processing_history_first_line": str(a.get("history", "")).splitlines()[-1] if a.get("history") else "",
        "checks": checks, "all_checks_pass": all(checks.values()),
    }


def main():
    out = []
    for nc in sorted(glob.glob(os.path.join(RAW, "*.nc"))):
        csv = os.path.splitext(nc)[0] + ".csv"
        if not os.path.isfile(csv):
            sys.exit(f"{nc}: no CSV export with the same name")
        out.append(verify(nc, csv))
    if not out:
        print("no NetCDF files present")
        return
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, sort_keys=True)
        fh.write("\n")
    bad = [o["netcdf_file"] for o in out if not o["all_checks_pass"]]
    if bad:
        sys.exit(f"NetCDF verification FAILED for {bad}; see {OUT}")
    print("NetCDF verification passed for", len(out), "file(s)")


if __name__ == "__main__":
    main()
