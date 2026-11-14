# Data sources

Retrieval date for web facts: 2026-11-14. NASA products were NOT downloaded (the workspace cannot reach NASA sites); NASA rows say what to download.

| ID | Source | What | Status |
|---|---|---|---|
| `nwt_table108` | NWT Bureau of Statistics, Table 108, "Winter Road Opening and Closing Dates, 1993/94 to 2024/25" (data provided by GNWT Department of Infrastructure). https://www.statsnwt.ca/en/node/1073 | Open and close dates, 17 routes | HAVE; stored in `data/raw/roads/` |
| `nasa_power_daily_t2m` | NASA POWER daily API, variable T2M (2 m air temperature, degree C). https://power.larc.nasa.gov/docs/services/api/temporal/daily/ | Daily mean temperature at each location | TO DOWNLOAD with `scripts/fetch_power_daily.py` |
| `merra2_m2sdnxslv` | MERRA-2 `M2SDNXSLV` v5.12.4 (GES DISC), variable `T2MMEAN`, daily, Kelvin. https://disc.gsfc.nasa.gov/datasets/M2SDNXSLV_5.12.4/summary | The original NASA collection POWER draws on | OPTIONAL original-source check |
| `merra2_m2tmnxslv_monthly` | MERRA-2 `M2TMNXSLV` v5.12.4, monthly T2M via Giovanni. https://giovanni.gsfc.nasa.gov/giovanni/ | Genuine supporting monthly series and challenge-eligibility evidence | USER HAS BEEN WORKING ON THIS (Time Series, Area-Averaged, 1993-2024, box -114.8,62.2,-113.9,62.7); file not yet received |
| `eccc_station` | Environment and Climate Change Canada, Historical Climate Data. https://climate.weather.gc.ca/ ; station Yellowknife A (Climate ID 2204101, WMO 71936, 62.463 N, 114.440 W) | Independent ground check | NOT DOWNLOADED |
| `smap_spl3ftp`, `modis_snow` | NSIDC; optional | Optional satellite context | NOT USED |

## Time standard and date definition (to fill in after download)
Record here: the API time-standard parameter used, and whether POWER's daily value is UTC or local solar time (read the POWER documentation page above; do not assume). Until recorded, say "calendar day as provided by the product".

## Independence note
NASA POWER's meteorology comes from MERRA-2-derived inputs. POWER T2M and MERRA-2 T2M are therefore NOT independent observations. The only independent check is the ECCC ground station.

## Challenge eligibility (OPEN)
We could not open the official challenge page. Someone must copy the Resources tab for "Be An Earth System Trend Detective!" and confirm that at least one listed NASA source is meaningfully used. Giovanni (MERRA-2) is believed to be listed; confirm. If the Resources tab does not list POWER, use the Giovanni MERRA-2 series as the qualifying analysis.

## Attribution
Cite NASA POWER ("These data were obtained from the NASA Langley Research Center (LaRC) POWER Project funded through the NASA Earth Science/Applied Science Program"), MERRA-2 with its DOI (10.5067/AP1B0BA5PD2K for M2TMNXSLV, as shown on the GES DISC page), and the NWT Bureau of Statistics. Confirm exact wording on each source's page.
