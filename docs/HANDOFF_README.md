# NorthLink data handoff (updated 2026-11-14)

## Bottom line
The scientific data package is built and checked: real NASA daily temperature for two ice-road locations, road dates, station validation, tested metric code and a first full set of results (`docs/RESULTS.md`). Still open: Yao's scientific sign-off, the challenge Resources-tab eligibility check, and verification of the research citations. Fable can implement the app from these inputs now.

## Authoritative files
| File | Status |
|---|---|
| `data/processed/nasa_daily_temperature.csv` | DONE. location_id, date, temperature_c, source_id. 2001-10-01 to 2025-06-30, 8,674 days x 2 locations, no missing values. |
| `data/processed/road_operations.csv` | DONE. 544 route-season rows, 514 verified. |
| `data/processed/locations.csv` | DONE (Inuvik coordinate still to verify). |
| `data/processed/station_validation.csv`, `station_summary.csv` | DONE for Dettah (ECCC Yellowknife A). No Aklavik station checked. |
| `data/processed/season_metrics.csv`, `trend_results.csv`, `regional_comparison.csv`, `road_climate_correlations.csv` | DONE (first run). |
| `data/processed/nasa_daily_precipitation.csv` | Extra (POWER PRECTOTCORR); not used in any approved analysis yet. |
| `docs/RESULTS.md` | The numbers to show. Read this first. |
| Other docs | GEOGRAPHIC_SCOPE, SCIENTIFIC_METHODS, DATA_QUALITY, VALIDATION_CASES, DATA_SOURCES, DATA_DICTIONARY, RESEARCH_EVIDENCE. |
| `scripts/`, `tests/` | 29 passing tests (`python3 -I -m unittest discover -s tests -v`). |

## Final selection
Primary: **Dettah Ice Road** (lake ice, Yellowknife Bay), location `dettah_bay` (62.43, -114.34). Comparison: **Aklavik ice road**, `aklavik_delta` (68.29, -134.37). NASA winters 2001/02 to 2024/25 (24); road records 1993/94 to 2024/25 (32). `season_start_year` = year of the preceding October.

## NASA source per analysis
- Daily FDD, thaw days, seasonal means: NASA POWER daily T2M (MERRA-2-derived), LST day definition, downloaded 2026-11-14 through the POWER API (`power_daily_T2M_<location>.csv` in `data/raw/nasa/`).
- Monthly cross-check: the user's POWER monthly file (T2M, T2M_MAX, 1993-2024); identical to the monthly mean of the daily file.
- Independent validation: ECCC Yellowknife A daily (`data/raw/weather_stations/`).
- POWER and MERRA-2 are not independent. The Giovanni MERRA-2 monthly file the team started to download has NOT been received.

## Headline findings (details and CIs in RESULTS.md)
1. No statistically supported 2001-2024 trend in the NASA temperature metrics at Dettah; only weak, uncertain warming and fewer freezing degree-days at Aklavik.
2. Dettah opens about 9 days later per decade (1993-2024) and its open-to-close interval is about 10 days shorter; the temperature metrics do not explain it.
3. Aklavik's earlier-opening trend is fragile (gone in 2001-2024).
4. NASA POWER is about 4.5 C colder than the station in Oct-Mar (correlation 0.96). Trends agree with the station; absolute values must not be used against thresholds.
5. Jan-Mar thaw days are almost always 0 (1 day in 24 winters at Dettah; 0 at Aklavik), so that metric is uninformative here.

## Reproduce
```
python3 -I scripts/build_road_operations.py data/raw/roads/NWT_Table108_Winter_Road_Opening_and_Closing_Dates_1993_94_to_2024.xlsx data/processed/road_operations.csv
python3 -I scripts/build_nasa_daily_temperature.py data/raw/nasa/power_daily_T2M_dettah_bay.csv data/raw/nasa/power_daily_T2M_aklavik_delta.csv -o data/processed/nasa_daily_temperature.csv --precip-out data/processed/nasa_daily_precipitation.csv
python3 -I scripts/audit_daily_temperature.py data/processed/nasa_daily_temperature.csv data/processed/season_audit.csv
python3 -I scripts/run_analysis.py
python3 -I -m unittest discover -s tests -v
```
Raw downloads came from `https://power.larc.nasa.gov/api/temporal/daily/point?parameters=T2M,PRECTOTCORR&community=SB&longitude=<lon>&latitude=<lat>&start=20011001&end=20250630&format=CSV` and from the ECCC bulk daily CSV (stationID 1706 for 2001-2012, 51058 for 2013 onward).

## Limitations the website must show
Not a safety or prediction tool; no usable-days claim; one grid cell is not the whole road; cold bias in NASA absolute temperatures; POWER and MERRA-2 not independent; unadjusted p-values and many tests; 24 winters of NASA data; opening depends on ice thickness, snow, overflow and decisions; Dettah has an all-season alternative road.

## Not done / open
1. Yao's review and sign-off of SCIENTIFIC_METHODS.md and RESULTS.md.
2. Challenge Resources tab eligibility check (official page unreachable; paste the tab text).
3. Giovanni MERRA-2 monthly file (for the eligibility story) not received.
4. Optional satellite variable (MODIS snow or SMAP) not added; no Aklavik station; Inuvik coordinates to verify.
5. RESEARCH_EVIDENCE.md citations need checking against full texts.
6. April-June closing-date analysis uses only the Mar 15 to Apr 15 mean temperature; no snow or precipitation analysis was run.

## Extended package (latest)
Run `python3 -I scripts/run_extended_analysis.py` to regenerate the extended outputs. See RESULTS.md "Extended analysis" for findings and caveats. For the app: show Dettah snow-depth vs opening-day as an exploratory chart, the 9-corridor panel (`corridor_panel.csv`), and clearly label supplementary corridor coordinates as approximate.

**Next step for any collaborator:** MODIS satellite pull from Microsoft Planetary Computer is scripted but not run. See docs/PLANETARY_COMPUTER_TODO.md.
