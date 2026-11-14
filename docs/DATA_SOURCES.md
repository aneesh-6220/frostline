# Data sources

Retrieval date for web facts and downloads: 2026-11-14. NASA POWER and ECCC data were downloaded through a browser on that date; the analysis environment cannot reach NASA or ECCC, so everything here is reproducible from the cached raw files only (`scripts/regenerate_all.py`), not re-verified live.

| ID | Source | What | Status |
|---|---|---|---|
| `nwt_table108` | NWT Bureau of Statistics, Table 108, "Winter Road Opening and Closing Dates, 1993/94 to 2024/25" (data provided by GNWT Department of Infrastructure). https://www.statsnwt.ca/en/node/1073 | Open and close dates, 17 routes | HAVE; stored in `data/raw/roads/` |
| `nasa_power_daily_t2m` | NASA POWER daily API, variable T2M (2 m air temperature, degree C). https://power.larc.nasa.gov/docs/services/api/temporal/daily/ | Daily mean temperature at each location | DOWNLOADED 2026-11-14 (T2M and PRECTOTCORR, 2001-10-01 to 2025-06-30, via the POWER API from the browser); raw files in `data/raw/nasa/` |
| `merra2_m2sdnxslv` | MERRA-2 `M2SDNXSLV` v5.12.4 (GES DISC), variable `T2MMEAN`, daily, Kelvin. https://disc.gsfc.nasa.gov/datasets/M2SDNXSLV_5.12.4/summary | The original NASA collection POWER draws on | OPTIONAL original-source check |
| `merra2_m2tmnxslv_monthly` | MERRA-2 monthly T2M via Giovanni. https://giovanni.gsfc.nasa.gov/giovanni/ | Would verify that POWER T2M equals the MERRA-2 product | NOT OBTAINED. Extraction needs an Earthdata login; UNVERIFIED (`CHALLENGE_ELIGIBILITY.md`) |
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
- Not obtained yet: MODIS (see docs/PLANETARY_COMPUTER_TODO.md for the ready-to-run pull script), Giovanni MERRA-2 monthly.
