#!/usr/bin/env python3
"""Download NASA POWER daily T2M CSVs for both Frostline locations into data/raw/nasa/.

Run on a machine with internet access (the Claude workspace cannot reach NASA):
    python3 scripts/fetch_power_daily.py
Preserves each response unmodified. The POWER 'daily' endpoint documentation
(https://power.larc.nasa.gov/docs/services/api/temporal/daily/) must be checked for the
current time-standard option; record the value used in docs/DATA_SOURCES.md.
"""
import csv, os, urllib.request

START, END = "20011001", "20250331"   # Oct 1 2001 .. Mar 31 2025
BASE = ("https://power.larc.nasa.gov/api/temporal/daily/point?parameters=T2M&community=SB"
        "&longitude={lon}&latitude={lat}&start={s}&end={e}&format=CSV")
root = os.path.join(os.path.dirname(__file__), "..")
with open(os.path.join(root, "data/processed/locations.csv"), newline="", encoding="utf-8") as fh:
    for row in csv.DictReader(fh):
        url = BASE.format(lon=row["longitude"], lat=row["latitude"], s=START, e=END)
        out = os.path.join(root, "data/raw/nasa", f"power_daily_T2M_{row['location_id']}.csv")
        print("GET", url)
        urllib.request.urlretrieve(url, out)
        print("saved", out)
