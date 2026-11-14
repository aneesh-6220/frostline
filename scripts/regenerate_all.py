#!/usr/bin/env python3
"""Deterministic regeneration of every derived file from the cached raw data. No network access.

Usage (repo root):  python3 -I scripts/regenerate_all.py [--check]
  default  rebuild data/processed/, UI/data_real/ and docs/RESULTS.md in place
  --check  rebuild into the working tree, then fail (exit 1) if `git diff` shows any derived file changed
           (use after a clean checkout to prove the committed outputs match the committed raw data)

This proves reproducibility from CACHED sources only. It does not re-download anything; see docs/SCIENTIFIC_METHODS.md
section 'Reproducibility levels' for what "live verification" would mean.
Raw inputs are only read: data/raw/nasa/power_daily_T2M_*.csv, data/raw/roads/*.xlsx, data/raw/weather_stations/*.csv,
data/raw/nasa/power_daily_ext_*.csv.
"""
import glob
import hashlib
import os
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
PY = [sys.executable, "-I"]


def run(args):
    print("+", " ".join(args), flush=True)
    r = subprocess.run(PY + args, cwd=ROOT)
    if r.returncode:
        sys.exit(f"step failed: {' '.join(args)}")


def raw_digest():
    h = hashlib.sha256()
    for f in sorted(glob.glob(os.path.join(ROOT, "data/raw/**/*"), recursive=True)):
        if os.path.isfile(f):
            h.update(os.path.relpath(f, ROOT).encode())
            h.update(open(f, "rb").read())
    return h.hexdigest()


before = raw_digest()
daily = [f"data/raw/nasa/power_daily_T2M_{loc}.csv" for loc in ("dettah_bay", "aklavik_delta")]  # fixed order = committed row order
assert all(os.path.exists(os.path.join(ROOT, f)) for f in daily), daily
run(["scripts/build_nasa_daily_temperature.py", *daily,
     "-o", "data/processed/nasa_daily_temperature.csv", "--precip-out", "data/processed/nasa_daily_precipitation.csv"])
run(["scripts/audit_daily_temperature.py", "data/processed/nasa_daily_temperature.csv", "data/processed/season_audit.csv"])
xlsx = sorted(glob.glob(os.path.join(ROOT, "data/raw/roads/*.xlsx")))
assert len(xlsx) == 1, xlsx
run(["scripts/build_road_operations.py", os.path.relpath(xlsx[0], ROOT), "data/processed/road_operations.csv"])
for s in ["run_analysis", "run_extended_analysis", "run_remediation_analysis", "diagnose_temperature_bias", "build_ui_data_real", "generate_results_md"]:
    run([f"scripts/{s}.py"])
after = raw_digest()
if before != after:
    sys.exit("RAW DATA CHANGED during regeneration: this must never happen")
print("raw data digest unchanged:", after[:16])

if "--check" in sys.argv:
    d = subprocess.run(["git", "status", "--porcelain", "--", "data/processed", "UI/data_real", "docs/RESULTS.md"], cwd=ROOT, capture_output=True, text=True).stdout
    if d.strip():
        print("DERIVED FILES DIFFER FROM COMMITTED VERSIONS:\n" + d)
        sys.exit(1)
    print("regeneration is a no-op: committed outputs match")
