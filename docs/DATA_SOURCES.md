# Data sources

Retrieval date for web facts: 2026-11-14. NASA products were NOT downloaded (the workspace cannot reach NASA sites); NASA rows say what to download.

| ID | Source | What | Status |
|---|---|---|---|
| `nwt_table108` | NWT Bureau of Statistics, Table 108, "Winter Road Opening and Closing Dates, 1993/94 to 2024/25" (data provided by GNWT Department of Infrastructure). https://www.statsnwt.ca/en/node/1073 | Open and close dates, 17 routes | HAVE; stored in `data/raw/roads/` |
| `nasa_power_daily_t2m` | NASA POWER daily API, variable T2M (2 m air temperature, degree C). https://power.larc.nasa.gov/docs/services/api/temporal/daily/ | Daily mean temperature at each location | DOWNLOADED 2026-11-14 (T2M and PRECTOTCORR, 2001-10-01 to 2025-06-30, via the POWER API from the browser); raw files in `data/raw/nasa/` |
| `merra2_m2sdnxslv` | MERRA-2 `M2SDNXSLV` v5.12.4 (GES DISC), variable `T2MMEAN`, daily, Kelvin. https://disc.gsfc.nasa.gov/datasets/M2SDNXSLV_5.12.4/summary | The original NASA collection POWER draws on | OPTIONAL original-source check |
| `merra2_m2tmnxslv_monthly` | MERRA-2 `M2TMNXSLV` v5.12.4, monthly T2M via Giovanni. https://giovanni.gsfc.nasa.gov/giovanni/ | Genuine supporting monthly series and challenge-eligibility evidence | USER HAS BEEN WORKING ON THIS (Time Series, Area-Averaged, 1993-2024, box -114.8,62.2,-113.9,62.7); file not yet received |
| `eccc_station` | Environment and Climate Change Canada, Historical Climate Data. https://climate.weather.gc.ca/ ; station Yellowknife A (Climate ID 2204101, WMO 71936, 62.463 N, 114.440 W) | Independent ground check | DOWNLOADED 2026-11-14 (bulk daily CSV, station IDs 1706 and 51058); `data/raw/weather_stations/` |
| `smap_spl3ftp`, `modis_snow` | NSIDC; optional | Optional satellite context | NOT USED |

## Time standard and date definition (to fill in after download)
The POWER response header states: "Source Native Resolution Daily Data ... in LST". The request did not set a time-standard parameter, so the default (LST, local solar time) was used. Dates are the calendar day as provided. The user's separate POWER monthly file (T2M, T2M_MAX, 1993-2024, point 62.45 N 114.37 W) equals the monthly mean of our daily series (max difference 0.005 C over 138 months), confirming they are the same product.

## Independence note
NASA POWER's meteorology comes from MERRA-2-derived inputs. POWER T2M and MERRA-2 T2M are therefore NOT independent observations. The only independent check is the ECCC ground station.

## Challenge eligibility (OPEN)
We could not open the official challenge page. Someone must copy the Resources tab for "Be An Earth System Trend Detective!" and confirm that at least one listed NASA source is meaningfully used. Giovanni (MERRA-2) is believed to be listed; confirm. If the Resources tab does not list POWER, use the Giovanni MERRA-2 series as the qualifying analysis.

## Attribution
Cite NASA POWER ("These data were obtained from the NASA Langley Research Center (LaRC) POWER Project funded through the NASA Earth Science/Applied Science Program"), MERRA-2 with its DOI (10.5067/AP1B0BA5PD2K for M2TMNXSLV, as shown on the GES DISC page), and the NWT Bureau of Statistics. Confirm exact wording on each source's page.
