# NorthLink data handoff (version of 2026-11-14)

## Bottom line
Not ready for Fable to implement end-to-end yet: **the real NASA daily temperature file does not exist.** The road data, route selection, methods, data-quality policy, tested reference code and research notes are done. Everything else depends on downloading NASA data on a machine with internet access (steps below). The work in this folder is not committed to GitHub: there is no repository attached to this session, so no commit hash exists. Create the repo, add this folder, and commit.

## What is authoritative
| File | Status |
|---|---|
| `data/processed/road_operations.csv` | DONE. 544 rows, 17 routes, 514 verified. |
| `data/processed/locations.csv` | DONE (CHECK Inuvik coordinates, Aklavik station). |
| `data/processed/nasa_daily_temperature.csv` | NOT CREATED. Needs the NASA download. |
| `data/processed/station_validation.csv` | Not created (optional). |
| `docs/GEOGRAPHIC_SCOPE.md`, `SCIENTIFIC_METHODS.md`, `DATA_QUALITY.md`, `VALIDATION_CASES.md`, `DATA_SOURCES.md`, `DATA_DICTIONARY.md`, `RESEARCH_EVIDENCE.md` | DONE (first versions). Yao must review `SCIENTIFIC_METHODS.md`. |
| `scripts/northlink_metrics.py`, `tests/` | DONE: 26 tests pass. |

## Final selection
Primary road: **Dettah Ice Road** (lake ice, Yellowknife Bay). Location `dettah_bay` (62.43, -114.34). Comparison: **Aklavik ice road**, location `aklavik_delta` (68.29, -134.37). Winters 2001/02 to 2024/25 for NASA temperatures (road records 1993/94 to 2024/25). Season key: `season_start_year` = year of the preceding October.

## NASA source for each analysis
- Daily FDD, thaw days, seasonal mean: NASA POWER daily T2M (derived from MERRA-2), to be downloaded.
- Supporting monthly trend and challenge eligibility: MERRA-2 monthly T2M via Giovanni (user is downloading it).
- Independent check: ECCC Yellowknife A (optional).
- POWER and MERRA-2 are not independent.

## Reproduce data preparation (needs internet; Python 3 with pandas, scipy, openpyxl)
```
python3 -I scripts/build_road_operations.py data/raw/roads/NWT_Table108_Winter_Road_Opening_and_Closing_Dates_1993_94_to_2024.xlsx data/processed/road_operations.csv
python3 scripts/fetch_power_daily.py            # saves data/raw/nasa/power_daily_T2M_<location_id>.csv
python3 -I scripts/build_nasa_daily_temperature.py data/raw/nasa/power_daily_T2M_dettah_bay.csv data/raw/nasa/power_daily_T2M_aklavik_delta.csv -o data/processed/nasa_daily_temperature.csv
python3 -I scripts/audit_daily_temperature.py data/processed/nasa_daily_temperature.csv data/processed/season_audit.csv
python3 -I -m unittest discover -s tests -v
```
The POWER URL and CSV layout in the scripts were written from documentation and have not been tested against a live download; if the converter fails, send the first 30 lines of a raw file and it can be fixed quickly.

## Metrics Fable must calculate and approved methods
See `docs/SCIENTIFIC_METHODS.md`: FDD (Oct to Dec), thaw days (Jan to Mar), seasonal mean, road open/close day and interval; Theil-Sen per decade with 95% CI, tie-corrected Mann-Kendall, lag-1 autocorrelation, sensitivity runs, difference-series comparison, exploratory Spearman. Yao has NOT yet approved these; they are proposed.

## Confirmed data coverage
Road records: complete for Dettah and Aklavik (32 of 32 winters). Temperature: none confirmed.

## Unavailable or not done
ECCC station validation; MODIS and SMAP; daily temperature audit; hand-check of one real FDD; the 380 degree-C day benchmark (not applicable to NWT); April to May temperatures for closing-date analysis.

## Limitations the website must show
Not a safety or prediction tool; no usable-days claim; one grid cell is not the whole road; POWER and MERRA-2 not independent; unadjusted p-values; 24 to 32 winters; opening depends on ice thickness, snow, overflow and decisions; Dettah has an all-season alternative.

## Outstanding issues (decisions needed)
1. **Daily vs monthly:** the team earlier said monthly NASA data is enough; this handoff requires daily. Decide. Monthly fallback is in SCIENTIFIC_METHODS.md section G.
2. **Challenge Resources tab** not checked (the official page was not reachable): someone must paste it.
3. No GitHub repo yet.
4. Verify Inuvik coordinates and find an Aklavik station.
5. Record the POWER time standard once downloaded.
