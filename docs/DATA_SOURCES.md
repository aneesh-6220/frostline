# Data sources

Retrieval date for web facts and downloads: 2026-11-14. NASA POWER and ECCC data were downloaded through a browser on that date; the analysis environment cannot reach NASA or ECCC, so everything here is reproducible from the cached raw files only (`scripts/regenerate_all.py`), not re-verified live.

| ID | Source | What | Status |
|---|---|---|---|
| `nwt_table108` | NWT Bureau of Statistics, Table 108, "Winter Road Opening and Closing Dates, 1993/94 to 2024/25" (data provided by GNWT Department of Infrastructure). https://www.statsnwt.ca/en/node/1073 | Open and close dates, 17 routes | HAVE; stored in `data/raw/roads/` |
| `nasa_power_daily_t2m` | NASA POWER daily API, variable T2M (2 m air temperature, degree C). https://power.larc.nasa.gov/docs/services/api/temporal/daily/ | Daily mean temperature at each location | DOWNLOADED 2026-11-14 (T2M and PRECTOTCORR, 2001-10-01 to 2025-06-30, via the POWER API from the browser); raw files in `data/raw/nasa/` |
| `merra2_m2sdnxslv` | MERRA-2 `M2SDNXSLV` v5.12.4 (GES DISC), variable `T2MMEAN`, daily, Kelvin. https://disc.gsfc.nasa.gov/datasets/M2SDNXSLV_5.12.4/summary | The original NASA collection POWER draws on | OPTIONAL original-source check |
| `merra2_m2tmnxslv_monthly` | MERRA-2 `M2TMNXSLV` (tavgM_2d_slv_Nx) v5.12.4, variable `T2M`, monthly, kelvin, through NASA Giovanni (Time Series, Area-Averaged). https://giovanni.gsfc.nasa.gov/giovanni/ ; doi:10.5067/AP1B0BA5PD2K | Monthly 2 m temperature for the Dettah / Yellowknife grid cell, 1980-01 to 2025-12 | HAVE (team export, 2026-11-15); raw CSV and NetCDF in `data/raw/nasa/giovanni/`; see the Giovanni section below |
| `eccc_station` | Environment and Climate Change Canada, Historical Climate Data. https://climate.weather.gc.ca/ ; station Yellowknife A (Climate ID 2204101, WMO 71936, 62.463 N, 114.440 W) | Independent ground check | DOWNLOADED 2026-11-14 (bulk daily CSV, station IDs 1706 and 51058); `data/raw/weather_stations/` |
| `smap_spl3ftp`, `modis_snow` | NSIDC; optional | Optional satellite context | NOT USED |

## Time standard and date definition
The POWER response header states "Source Native Resolution Daily Data ... in LST". The request did not set a time-standard parameter. Dates are the calendar day as provided. The user's POWER monthly file (T2M, 1993-2024) equals the monthly mean of our daily series (max difference 0.005 C over 138 months), so they are the same product. No POWER service version string appears in the file headers; note the version from the POWER service page when citing.

## Independence note
NASA POWER's meteorology comes from MERRA-2. POWER T2M and MERRA-2 T2M are therefore NOT independent observations, and at Yellowknife the POWER series is a reanalysis value colder than the station (`TEMPERATURE_BIAS_DIAGNOSIS.md`). The only independent check is the ECCC ground station.

## Challenge eligibility
See `CHALLENGE_ELIGIBILITY.md` (checked on the live pages 2026-11-14): no required dataset found; POWER is not on the Resources list; Giovanni is. Status: plausible, not confirmed by an organizer.

## Attribution and references
See `REFERENCES.md` for the required POWER acknowledgement wording, the MERRA-2 reference, NWT Bureau of Statistics and ECCC.

## Added sources
- NASA POWER daily, 10 variables (T2M, T2M_MAX, T2M_MIN, TS, PRECTOTCORR, WS10M, RH2M, PS, ALLSKY_SFC_SW_DWN, ALLSKY_SFC_LW_DWN), 9 corridors, 2001-10-01 to 2025-06-30: `data/raw/nasa/power_daily_ext_<id>.csv` (MERRA-2/CERES-derived; not independent of MERRA-2).
- ECCC multi-station daily (Yellowknife A 1706/51058, Aklavik A 1623/52962, Inuvik 1669/31470/41883/51477): `data/raw/weather_stations/eccc_stations_daily_2001_2025.csv` incl. snowfall and snow on ground.
- Not obtained yet: MODIS (see docs/PLANETARY_COMPUTER_TODO.md for the ready-to-run pull script). Giovanni MERRA-2 monthly was obtained on 2026-11-15 for the Dettah cell only (section below); no Aklavik extraction exists.

## NASA Giovanni MERRA-2 monthly T2M (added 2026-11-15)

What was inspected (not assumed):

| Property | Value found in the files |
|---|---|
| Files | `data/raw/nasa/giovanni/g4.areaAvgTimeSeries.M2TMNXSLV_5_12_4_T2M.19800101-20251231.114W_62N_113W_62N.csv` (17,672 bytes, SHA-256 `d38952225524e35360425d23eb941abd7fc44acf38540ae87f5621c55c812a7e`) and `.nc` (141,927 bytes, SHA-256 `be265b97b70bfd92490f40c03ab44d24cb2c866474d623af7b545aa3fbc02897`). Byte-identical copies of the files the team placed in `external_sources/giovanni/raw/`. |
| Product | NetCDF variable attributes: `product_short_name = M2TMNXSLV`, `product_version = 5.12.4`, `origname = T2M`, `long_name = 2-meter air temperature`, `units = K`, `cell_methods = time: mean lat, lon: mean`; CF-1.4, `temporal_resolution = monthly`. |
| Period and count | 552 consecutive monthly values, 1980-01 to 2025-12; CF time axis in seconds since 1970-01-01. No fill values (range 230.05 to 294.20 K). |
| Area | Requested box (west, south, east, north) -114.75, 62.20, -113.85, 62.75. Giovanni-resolved grid point -114.375, 62.5 (header "Data Bounding Box" and NetCDF `geospatial_*`), which is the MERRA-2 cell containing the Dettah / Yellowknife POWER point. A single grid point, so the "area average" is that one cell's value. |
| Fill value | CSV header 1e15; NetCDF `_FillValue` 9.99999987e14 (the same number in float32). Any such value would be treated as missing. |
| Provenance | CSV header "URL to Reproduce Results" (stored in `giovanni_provenance.csv`); NetCDF `history` shows NCO processing in a Giovanni session on 2026-11-15 14:57 UTC. |
| CSV vs NetCDF | Same 552 months; largest value difference 5e-7 K (`scripts/verify_giovanni_netcdf.py`, result in `data/processed/giovanni_netcdf_verification.json`). |
| vs POWER daily | 285 complete months (2001-10 to 2025-06): mean Giovanni minus POWER -0.001 C, largest monthly difference 0.394 C, r = 1.0000. Same MERRA-2 source, so this checks the access route, not the reanalysis. |

How it is used: monthly, seasonal (DJF, MAM, JJA, SON, Oct to Dec, Jan to Mar) and annual MEAN temperature; trends with Theil-Sen, Mann-Kendall and Benjamini-Hochberg over the seven seasonal tests (`giovanni_monthly_t2m_trends.csv`). It is shown in the app's "Giovanni record" view, in Methods and sources, and in the Dettah Evidence Brief source list. Monthly means are never used to reconstruct daily freezing-degree days or thaw days, and the Giovanni record carries no road-operation information.

Limitations: one grid cell (Dettah / Yellowknife) only; MERRA-2 is reanalysis, not observation, and is not independent of NASA POWER; at this cell MERRA-2 is colder than the Yellowknife station in the cold season (`TEMPERATURE_BIAS_DIAGNOSIS.md`); the 1980 to 2025 record is longer than the 2001 to 2024 daily record, so Giovanni trends are not directly comparable with the daily-metric trends.

## Live NASA POWER for exploratory points (added 2026-11-15)

The Map view can request NASA POWER daily data for any point inside 50 to 75 N, 170 to 55 W from the documented endpoint `https://power.larc.nasa.gov/api/temporal/daily/point` (parameter `T2M`, community `SB`, JSON, Oct 1 1981 to Mar 31 2025). No API key is used. Responses are validated (unit C, fill value -999 treated as missing, returned versus requested coordinates, date coverage, plausible range) and cached by canonical request in memory and on disk; live calls are spaced at least one second apart. The application reports the POWER API version (v2.10.3 when tested on 2026-11-15), source (MERRA2), time standard (LST), retrieval time and request URL. Results for these points are exploratory climate analysis only; no road records are attached.
