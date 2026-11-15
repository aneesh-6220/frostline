#!/usr/bin/env python3
"""Render docs/APP_DATA_SCHEMA.md from the actual files in UI/data_real/ (columns, dtypes, row counts). Generated; do not edit by hand.
Every file in UI/data_real must have a description here; a test fails if one is missing, so the contract cannot drift from the data.
Usage (repo root): python3 -I scripts/generate_data_schema_doc.py
"""
import glob
import os

import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
D = os.path.join(ROOT, "UI/data_real")

# file -> (required by the app?, grain, what it is, display limitation)
DESC = {
    "corridors.csv": ("required", "one row per selectable location", "Location ids, names and coordinates. `kind` is a data class (verified = has real road records), NOT a statement that the route identity is verified. The `custom` row has no data and must not be offered as a data location.", "Aklavik point is a calculated midpoint; supplementary corridors are approximate."),
    "climate_annual.csv": ("required", "corridor x winter x metric (fdd, thaw_days), 2 primary corridors", "NASA POWER per-winter FDD (Oct-Dec) and thaw days (Jan-Mar) with coverage counts. Source: NASA POWER daily T2M (MERRA-2).", "Reanalysis, colder than the station; thaw_days is mostly zeros and has no trend estimate."),
    "road_seasons.csv": ("required", "corridor x winter, Dettah and Aklavik only", "Government opening and closing dates 1993-2024; `season_length_days` = close minus open (an interval, not usable days).", "Operations record, not ice measurement."),
    "trends.csv": ("required", "corridor x metric (fdd, thaw_days)", "Precomputed 2001-2024 NASA trends with plain-language takeaway (locked schema from the original prototype). Valid only for the 2001-2024 window.", "Fixed window; thaw_days row has empty numbers (not estimated)."),
    "season_metrics_extended.csv": ("required", "location x winter (9 corridors x 24 winters)", "Per-winter values of all 14 extended metrics (NASA climate plus road day numbers) for recomputing trends for user-selected windows.", "Day numbers count days since Oct 1; interval is not usable days."),
    "road_operations_all_routes.csv": ("required", "route x winter (17 routes x 32 winters = 544 rows)", "Full road-operations record with one `record_status` per row. Only `verified` rows carry dates.", "Four flagged rows are excluded, not corrected."),
    "extended_trends.csv": ("required", "location x metric x window", "Precomputed Theil-Sen trends for the 2001-2024 window (126 tests).", "Fixed window."),
    "multiple_testing_126.csv": ("required", "126 tests", "The 126-test family with unadjusted p, BH q (all and within family), Holm, block CIs and status.", "q valid only for this family and window."),
    "road_record_trends_all_routes.csv": ("required", "17 routes x 3 metrics (51 tests)", "Full-record (1993-2024) road-date trends with selection-adjusted BH q and Holm.", "q valid only for this family and window. Routes other than Dettah/Aklavik have workbook-name identity only."),
    "hypothesis_families.csv": ("required", "5 families", "Declared families and their corrections.", ""),
    "corridor_panel.csv": ("required", "9 corridors", "Compact slope/p panel for the nine corridors (2001-2024).", "Exploratory; unadjusted p."),
    "headline_trend_sensitivity.csv": ("required", "route x metric x variant", "Robustness variants of the Dettah/Aklavik road-date trends (windows, drop-early, drop-late).", ""),
    "road_climate_correlations.csv": ("required", "11 tests", "Leak-free Spearman associations between predictor windows and road dates, with block CI and BH q in family F5.", "Associations, never causes."),
    "leakage_audit.csv": ("required", "window x road", "How often a predictor window overlapped the outcome date (why earlier correlations were removed).", ""),
    "snow_vs_opening.csv": ("required", "5 snow predictors", "Yellowknife A snow predictors versus Dettah opening day (Spearman, block CI, q).", "Exploratory hypothesis; airport measurement."),
    "snow_trends.csv": ("required", "5 snow series", "Trends of the snow predictors; shows the snow record has no detectable trend.", ""),
    "yellowknife_snow_by_season.csv": ("required", "winter", "Per-winter snow predictors, Dettah opening day, FDD and precipitation.", "Station values (ECCC)."),
    "station_summary_aklavik_inuvik.csv": ("required", "station", "NASA vs ECCC station bias for Aklavik and Inuvik stations.", "Station sits at an end of the road, not at the sampling point."),
    "bias_by_month.csv": ("required", "month", "NASA minus Yellowknife A mean bias by calendar month with station mean temperature.", "Source of the required bias caveat."),
    "station_fdd_by_season.csv": ("required", "winter", "Per-winter FDD from the station for comparison with NASA FDD.", "17 winters with complete Oct-Dec in both series."),
    "canonical_facts.json": ("required", "single object", "Machine-readable canonical numbers (status counts, periods, bias, headline trends, caveat text) generated from the data.", "Use for text; tables and charts should read the CSVs."),
    "giovanni_monthly_t2m_seasonal.csv": ("optional", "location x winter", "ONLY if a real Giovanni MERRA-2 M2TMNXSLV T2M file was ingested: Oct-Dec and Jan-Mar mean of monthly means.", "Hide the panel when absent; never fill from synthetic data."),
    "giovanni_monthly_t2m_trends.csv": ("optional", "location x metric", "ONLY if ingested: Theil-Sen trends of the Giovanni monthly seasonal means.", "Mean temperature only; never FDD or thaw days."),
    "giovanni_vs_power_check.csv": ("optional", "location", "ONLY if ingested: month-by-month Giovanni minus POWER agreement check (complete POWER months only).", "Same MERRA-2 source: a check on access routes, not independent validation."),
    "giovanni_monthly_t2m.csv": ("optional", "location x month", "ONLY if ingested: every monthly value exactly as published by Giovanni (kelvin) plus its Celsius conversion and a missing flag.", "Monthly reanalysis means; never used to reconstruct daily FDD or thaw days."),
    "giovanni_t2m_calendar_seasons.csv": ("optional", "location x year x season", "ONLY if ingested: calendar-year and meteorological seasonal (DJF, MAM, JJA, SON) means from complete sets of months; DJF is labelled with the year of its January.", "Incomplete seasons are left empty, not filled."),
    "giovanni_provenance.csv": ("optional", "location x key", "ONLY if ingested: source file names, SHA-256 checksums, Giovanni header fields (title, dates, requested box, resolved grid point, reproduce URL, fill value) and the location match rule.", ""),
}

L = ["# App data schema (generated file; do not edit by hand)\n",
     "Generated by `python3 -I scripts/generate_data_schema_doc.py` from the files in `UI/data_real/`. Rules for using these files are in `docs/APP_IMPLEMENTATION_CONTRACT.md`. "
     "Every file is real data or derived from real data; none is synthetic. A file marked optional exists only if its real source was obtained.\n"]
for f in sorted(glob.glob(os.path.join(D, "*"))):
    n = os.path.basename(f)
    if n not in DESC:
        raise SystemExit(f"UI/data_real/{n} has no description in generate_data_schema_doc.py")
    req, grain, what, lim = DESC[n]
    L.append(f"## `{n}` ({req})\n")
    L.append(f"- Grain: {grain}\n- Content: {what}")
    if lim:
        L.append(f"- Display limitation: {lim}")
    if n.endswith(".csv"):
        df = pd.read_csv(f)
        L.append(f"- Rows: {len(df)}\n\n| Column | dtype |\n|---|---|")
        L += [f"| {c} | {t} |" for c, t in df.dtypes.astype(str).items()]
    L.append("")
for n, v in DESC.items():
    if v[0] == "required" and not os.path.exists(os.path.join(D, n)):
        raise SystemExit(f"required file missing: UI/data_real/{n}")
open(os.path.join(ROOT, "docs/APP_DATA_SCHEMA.md"), "w").write("\n".join(L).replace(chr(8212), "-") + "\n")
