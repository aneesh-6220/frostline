#!/usr/bin/env python3
"""Season coverage audit -> docs table. Usage: python3 -I scripts/audit_daily_temperature.py data/processed/nasa_daily_temperature.csv out_audit.csv"""
import sys, os
import pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
import northlink_metrics as m
df = pd.read_csv(sys.argv[1], parse_dates=["date"])
out = []
for loc, g in df.groupby("location_id"):
    for y in range(g["date"].dt.year.min(), g["date"].dt.year.max()):
        c = m.season_coverage(g, y, "full")
        out.append([loc, y, c.expected, c.valid, ";".join(map(str, c.missing_dates)),
                    ";".join(map(str, c.duplicate_dates)), c.invalid_values, round(c.percent, 2), c.complete,
                    "" if c.complete else "incomplete coverage; excluded from trends"])
pd.DataFrame(out, columns=["location_id","season_start_year","expected_days","valid_days","missing_dates",
    "duplicate_dates","invalid_values","coverage_percent","included_in_trend","exclusion_reason"]).to_csv(sys.argv[2], index=False)
print("seasons audited:", len(out))
