# Data dictionary

All CSVs: UTF-8, comma-separated, header row, ISO dates (YYYY-MM-DD), load with `pandas.read_csv`.

## data/processed/road_operations.csv (exists)
| Column | Type | Meaning |
|---|---|---|
| road_id | text | Stable route key, e.g. `dettah`, `aklavik` (17 values) |
| season_start_year | int | Year containing the preceding October; 2024/25 is 2024 |
| opening_date | date or empty | First opening date, only if record_status = verified |
| closing_date | date or empty | Final closing date, only if verified |
| record_status | text | `verified`, `missing_not_available` (workbook "..") , `not_applicable_note` (workbook "**"), `flagged_inconsistent` (dates fail checks) |
| source_url | text | https://www.statsnwt.ca/en/node/1073 |
| road_type | text | winter_road, ice_road, ice_crossing, mining_road |
| road_name | text | Name as printed in the workbook |
| source_sheet | text | Workbook sheet |
| record_note | text | Explanation for any non-verified row |
Required columns are the first six; the last four are extras.

## data/processed/locations.csv (exists)
location_id, name, role (primary/comparison), road_id, latitude, longitude (degrees, WGS84), coord_basis, coord_source, nasa_grid_note, station_id, station_distance_km.

## data/processed/nasa_daily_temperature.csv (exists)
location_id (text), date (YYYY-MM-DD), temperature_c (degrees C, empty = missing, never 0), source_id (`nasa_power_daily_t2m`). One row per location per calendar day, Oct 1 2001 to Mar 31 2025.

## data/processed/station_validation.csv (exists)
location_id, date, nasa_temperature_c, station_temperature_c, station_id (1706 or 51058). Matched days only.

## Other generated files
`nasa_daily_precipitation.csv` (location_id, date, precip_mm_per_day, source_id); `season_audit.csv`; `season_metrics.csv` (one row per location and winter: fdd_octdec, thaw_days_janmar, longest_thaw_run_janmar, mean_octdec_c, mean_janmar_c, mean_full_c, fdd_pre_cutoff, mean_mar15_apr15_c, open_day, close_day, open_to_close_days); `trend_results.csv`; `regional_comparison.csv`; `road_climate_correlations.csv`; `station_summary.csv`; `station_fdd_by_season.csv`. Results are explained in `docs/RESULTS.md`.

## Season audit (generated)
See DATA_QUALITY.md section 2.
