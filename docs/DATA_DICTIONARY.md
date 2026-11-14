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

## data/processed/nasa_daily_temperature.csv (NOT YET CREATED)
location_id (text), date (YYYY-MM-DD), temperature_c (degrees C, empty = missing, never 0), source_id (`nasa_power_daily_t2m`). One row per location per calendar day, Oct 1 2001 to Mar 31 2025.

## data/processed/station_validation.csv (optional, NOT CREATED)
Planned: location_id, date, nasa_temperature_c, station_temperature_c, station_id.

## Season audit (generated)
See DATA_QUALITY.md section 2.
