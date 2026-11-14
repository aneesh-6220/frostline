#!/usr/bin/env python3
"""Convert raw NASA POWER daily CSVs to data/processed/nasa_daily_temperature.csv.

Usage: python3 -I scripts/build_nasa_daily_temperature.py data/raw/nasa/power_daily_T2M_<location_id>.csv ... -o out.csv
Input format (POWER CSV): header lines ending with '-END HEADER-', then columns YEAR,MO,DY,T2M.
Output: location_id,date,temperature_c,source_id ; one row per calendar day per location;
missing/invalid temperature -> EMPTY temperature_c (never 0). POWER T2M is already degrees C;
the -999 sentinel is treated as missing. MERRA-2 files in Kelvin need K - 273.15 (see northlink_metrics).
"""
import argparse, csv, datetime as dt, os, re, sys

p = argparse.ArgumentParser()
p.add_argument("files", nargs="+")
p.add_argument("-o", "--out", required=True)
a = p.parse_args()
rows = []
for f in a.files:
    loc = re.search(r"power_daily_T2M_(.+)\.csv$", os.path.basename(f)).group(1)
    lines = open(f, encoding="utf-8").read().splitlines()
    k = next(i for i, l in enumerate(lines) if "-END HEADER-" in l)
    rd = csv.DictReader(lines[k + 1:])
    seen = set()
    for r in rd:
        d = dt.date(int(r["YEAR"]), int(r["MO"]), int(r["DY"]))
        if (loc, d) in seen:
            print("DUPLICATE", loc, d, file=sys.stderr)
        seen.add((loc, d))
        t = float(r["T2M"])
        rows.append([loc, d.isoformat(), "" if t <= -990 else repr(t), "nasa_power_daily_t2m"])
with open(a.out, "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh); w.writerow(["location_id", "date", "temperature_c", "source_id"]); w.writerows(rows)
print("wrote", len(rows), "rows")
