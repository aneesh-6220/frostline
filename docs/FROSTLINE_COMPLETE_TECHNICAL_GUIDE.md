# Frostline: the complete technical guide

For the six members of Strongest Soldiers. Written on 2026-11-15 from the source code on branch `frostline-final-qualification` (commit `f3edb22` and the documentation commit after it). It describes what the code **does**, not what earlier plans said it would do. Where something is planned but not built, it says so.

How to read this guide: every section starts with a plain-English explanation, then the technical detail, then the files and functions involved, a worked example with real numbers from our data, and a question that tests whether you really understood it. If you can answer every "Check your understanding" question without looking, you can defend Frostline in front of judges.

## Table of contents

1. [Product and problem](#1-product-and-problem)
2. [Every user-facing feature](#2-every-user-facing-feature)
3. [Complete architecture](#3-complete-architecture)
4. [Data sources](#4-data-sources)
5. [Map implementation](#5-map-implementation)
6. [NASA POWER API](#6-nasa-power-api)
7. [Giovanni pipeline](#7-giovanni-pipeline)
8. [Mathematics and statistics](#8-mathematics-and-statistics)
9. [Evidence Engine](#9-evidence-engine)
10. [Evidence Brief](#10-evidence-brief)
11. [Reliability and testing](#11-reliability-and-testing)
12. [Deployment](#12-deployment)
13. [Actual limitations](#13-actual-limitations)
14. [Development history and human contributions](#14-development-history-and-human-contributions)
15. [Glossary](#15-glossary)

---

## 1. Product and problem

**Plain English.** In Canada's Northwest Territories (NWT), some roads are built every winter on frozen lakes and rivers. They exist only while the cold holds. People often say "winters are changing", but checking that claim properly is hard: you need NASA climate data, you need to clean daily records, compute winter indicators, fit a trend, test whether it could be chance, correct for running many tests, compare with ground stations, and be honest about what the data can't tell you. Frostline does that whole workflow in one app and exports a report anyone can check.

**Technical detail.** Frostline answers the NASA Space Apps 2026 challenge "Be An Earth System Trend Detective!": choose Earth-science variables, acquire them for a region, build a time series and report a rate of change with a significance test. Its specific angle is northern winters and seasonal roads. It combines:

- NASA POWER daily 2 m air temperature (MERRA-2 reanalysis) for two curated ice-road locations and for any user-selected point;
- NASA Giovanni monthly MERRA-2 2 m temperature (1980 to 2025) for the Dettah grid cell;
- ECCC weather-station observations for ground comparison;
- NWT government records of winter-road opening and closing dates (1993/94 to 2024/25).

**Intended users.** Students and educators learning how to test a climate claim; analysts doing a first-pass trend check; northern adaptation stakeholders who want the historical record with its caveats. Frostline has **no** user study and **no** adopting community; do not claim either.

**What competing approaches offer.** NASA Giovanni and KNMI Climate Explorer plot and download time series; NASA POWER's Data Access Viewer downloads point data; spreadsheet or Python notebooks can fit trends. What none of them does in one place: derive a winter-specific indicator from daily data, fit a robust trend with an interval and a test that always match the user's selection, control multiple testing, put the reanalysis-versus-station disagreement beside the result, keep road records separate from climate data, and export a reproducible brief. That integration and its honesty is Frostline's contribution. It is not a new statistical method.

**Files.** `README.md`, `docs/FROSTLINE_NORTH_STAR.md` (product vision), `docs/SCIENTIFIC_METHODS.md` (rules for what may be claimed), `docs/APPROVED_FINDINGS.md` (generated list of claimable results).

**Example.** A teacher wants to know whether autumn has warmed near Yellowknife. In Frostline: open "Giovanni record", choose "Autumn (Sep to Nov)". The answer: about +0.60 °C per decade since 1980, 95% interval +0.23 to +0.97, and after correcting for the seven seasons tested it is still supported (q = 0.013). The same page shows that early winter (Oct to Dec) is not resolved. The teacher downloads the brief.

**Check your understanding.** A judge says "Giovanni already does this." Name three things Frostline does that Giovanni's time-series plot does not.

---

## 2. Every user-facing feature

**Plain English.** The app has eleven pages in the top navigation (on phones, the five most important are in a bottom tab bar). A sidebar on every page holds the "current investigation": a location, a variable and a range of winters. Most pages read that shared selection, so changing it in one place changes every number everywhere.

**Technical detail.** Pages are registered in `UI/frostline_app.py` (`VIEWS` list) and rendered by modules in `UI/frostline/views/`.

| Page (nav title) | Module | What the user sees and does | What powers it |
|---|---|---|---|
| Observatory (landing) | `views/observatory.py` | Title question, two buttons ("Begin an Investigation" starts the guided demo; "Explore the Data on the map" opens the Map), a live chart of Dettah Oct to Dec freezing degree-days, four evidence cards (Dettah road record, Giovanni seasonal family, NASA versus station, 126 tests corrected), a three-step workflow summary and a scope note | `analysis.trend`, `giovanni.trend`, `canonical_facts.json` |
| Guided demo | `views/demo.py` | Six stages with Back/Next: the problem; the geography (map, pick Dettah or Aklavik); the NASA data (chart); the scientific finding (trend, interval, q; plus the 46-year Giovanni family for Dettah); the transportation evidence (road timeline, opening-day finding); the Evidence Brief (seven-dimension assessment, downloads) | Same functions as free exploration; the stage only fixes the starting selection |
| Map | `views/atlas.py` | Interactive Leaflet map: curated markers, grid-cell rectangles, dashed supported area. Click a curated marker to select it, or click anywhere in the area to create an exploratory point, retrieve live NASA POWER data, choose one of four questions and a range of winters, see the trend, chart, statistical details, winter-by-winter values, and download HTML/CSV/JSON. A coordinate form works without the map | `power_api.fetch_daily`, `explore.analyze`, folium + streamlit-folium |
| Questions | `views/questions.py` | Plain questions ("Is early winter delivering less freezing?"); each recommends variables with reasons | `registry.QUESTIONS` |
| Trend Detective | `views/detective.py` | The main research view for the sidebar selection: chart with trend and slope band, plain-language sentence, finding card with full statistics, winter-by-winter table, variable definition, nine-corridor robustness chart, methods | `analysis.trend`, `charts.trend_chart` |
| Compare | `views/compare.py` | Same variable at two locations on matched winters; trend of the difference series | `analysis.compare` |
| Giovanni record | `views/giovanni_view.py` | Season selector, period slider, trend panel, series chart, statistical-details table of all seven seasonal tests, monthly climatology, anomaly bars, first-decade versus last-decade contrast, Giovanni-versus-POWER check, provenance, exports | `giovanni.py` |
| Corridor | `views/corridor.py` | Road-record timeline beside NASA data, status counts, sensitivity variants, snow hypothesis | `analysis.road_record`, `sensitivity`, `associations` |
| Evidence | `views/evidence_view.py` | Evidence Engine: seven quality dimensions, six evidence layers, NASA-versus-station comparison, declared test families | `evidence.assess`, `analysis.station_fdd` |
| Brief | `views/brief_view.py` | Preview and download of the Evidence Brief for the current investigation | `brief.build` |
| Methods | `views/methods.py` | Methods, sources, Giovanni section, AI-use disclosure, limitations, review status | `registry.SOURCES`, `LITERATURE` |

**Sidebar ("Current investigation")**, `ui.console`: Location (Dettah or Aklavik), Variable (8 core plus 7 exploratory when the toggle is on), Analysis period slider, "Approved window" buttons for windows that carry a multiplicity-adjusted q, an evidence-state chip, and the data digest.

**Implemented versus planned.** Implemented: everything in the table. Not implemented: user accounts, saved investigations, variables other than T2M for live points, Giovanni for Aklavik, MODIS/AppEEARS satellite data (a script exists, `docs/PLANETARY_COMPUTER_TODO.md`, but its output is not in the app), any forecast.

**Example.** On Trend Detective with Dettah, Oct to Dec freezing degree-days, 2001/02 to 2024/25, the finding card shows +15 °C-days per decade, interval -108 to 111, q = 0.899, state "Trend not statistically resolved". Drag the period to 2006/07 to 2024/25: the q disappears and the state becomes "Exploratory window", because that window was not pre-declared.

**Check your understanding.** Why does the q-value disappear when you move the period slider, but the slope and interval stay?

---

## 3. Complete architecture

**Plain English.** Frostline is a Python web app made with Streamlit. Heavy science was done ahead of time by scripts that turn raw files into clean tables. The app reads those tables, recomputes statistics for whatever the user selects, and draws pages. Only one thing goes to the internet at run time: live NASA POWER requests for new map points (plus map tiles and fonts).

**Technical detail.**

```
                         OFFLINE PIPELINE (scripts/, run by regenerate_all.py)
 data/raw/                                                         data/processed/  ──copied──►  UI/data_real/
  nasa/power_daily_T2M_*.csv ─► build_nasa_daily_temperature ─► nasa_daily_temperature.csv          (approved app data,
  nasa/power_daily_ext_*.csv    audit_daily_temperature        season_audit.csv                       hashed into the
  roads/NWT_Table108_*.xlsx ──► build_road_operations ───────► road_operations.csv                    data digest)
  weather_stations/*.csv ─────► run_analysis / run_extended_analysis / run_remediation_analysis
                                diagnose_temperature_bias ───► trends, 126-test table, families, station bias ...
  nasa/giovanni/g4.*.csv ─────► ingest_giovanni_monthly ─────► giovanni_*.csv
                                generate_approved_findings / generate_results_md / generate_data_schema_doc ─► docs/

                         RUN TIME (streamlit run UI/frostline_app.py)
 frostline_app.py ─► data.load_dataset()  (strict loader: required files, columns, no synthetic rows, SHA-256 digest)
        │          ─► ui.init_state()      (session state: loc, var, first, last, question, demo_step)
        │          ─► st.navigation(11 pages) ─► views/*.render(ds)
        │                                         │
        │          analysis.py ── scripts/northlink_recompute.py ── northlink_metrics.py (Theil-Sen, MK, FDD...)
        │                                                        └─ northlink_stats.py   (BH, Holm, block bootstrap)
        │          giovanni.py (monthly record)   evidence.py (assessment)   brief.py (HTML/CSV/JSON)
        │          explore.py (live point analysis) ◄── power_api.py ──HTTPS──► power.larc.nasa.gov (cached)
        └─ atlas.py: folium map ──► streamlit-folium (Leaflet in an iframe) ──► Esri / OSM tiles
```

**Framework and entrypoint.** `UI/frostline_app.py`. It adds `UI/` to `sys.path`, sets the page config, injects the theme CSS (`ui.inject_theme`), loads the dataset, initialises session state, registers pages with `st.Page` and `st.navigation(position="top")`, renders the sidebar (`ui.console`), runs the chosen page, and adds the footer and phone tab bar. A `DataError` anywhere stops the page with a message naming the bad file; no fallback data exist.

**State management.** Streamlit reruns the whole script on every interaction. Persistent state lives in `st.session_state`: `loc`, `var`, `first`, `last`, `question`, `demo_step`, plus map keys `xp_point` (the exploratory point), `xp_power` (retrieved results keyed by point), `xp_error` (an error tied to the point it was raised for) and `xp_prev_obj` / `xp_prev_map` (the last clicks already handled). All changes to the shared investigation go through `ui.set_investigation`, which also resets the window to the full record when the location or variable changes.

**Caching.** `data._load` and `analysis.get_series`, `trend`, `compare`, `station_fdd` use `functools.lru_cache`. They are keyed on the `Dataset` object, whose hash is its directory plus SHA-256 digest, so a changed data file can never return a stale result. POWER responses are cached in memory and on disk (section 6).

**Scientific engine.** The app does not implement its own statistics. `analysis.py` imports `scripts/northlink_recompute.py`, `northlink_metrics.py` and `northlink_stats.py`: the same code that produced the approved offline results. The live map and Giovanni modules call `northlink_metrics.trend` directly.

**Charts.** Plotly figures built in `charts.py` (`trend_chart`, `timeline_chart`) and in view modules; theme tokens shared with the CSS in `ui.py`.

**Exports.** `brief.py` (curated investigations), `giovanni.brief_html/export_csv/record_json`, `explore.brief_html/export_csv/record_json`. Delivered with `st.download_button`.

**Dependencies** (`UI/requirements.txt`, pinned): streamlit 1.67.0, pandas 3.1.1, numpy 2.5.4, scipy 1.18.1, plotly 7.1.0, pydeck 0.9.3, openpyxl 3.1.5, folium 1.0.0, streamlit-folium 0.27.4, branca 0.8.2, xyzservices 2026.9.1. Python 3.12. No database, no AI model at run time, no secrets.

**Hidden runtime dependencies.** Map tiles (Esri, OSM), Google Fonts (Inter) from `.streamlit/config.toml`, and NASA POWER for live points. Everything else works offline.

**Example.** You change Location to Aklavik. Streamlit calls `ui._on_loc`, which calls `set_investigation(location_id="aklavik_delta")`; `loc` changes and `first/last` reset to Aklavik's full range for the current variable. The script reruns; Trend Detective calls `analysis.trend(ds, "aklavik_delta", var, first, last)` (a cache miss), which recomputes and returns a new `Finding`; the chart, card, brief and sidebar chip all read that same object.

**Check your understanding.** Why is it safe for `analysis.trend` to be cached forever with `lru_cache`, even if someone edits a CSV in `UI/data_real/`?

---

## 4. Data sources

**Plain English.** We use NASA model data (MERRA-2) two ways (daily through POWER, monthly through Giovanni), a Canadian weather station to see how far NASA is from the ground, and the territorial government's record of when roads opened and closed. Each answers a different question, and we never blend them into one number.

**Technical detail.**

| Source | What it is | Resolution | Coverage in Frostline | Files | Suitable for | Not suitable for |
|---|---|---|---|---|---|---|
| NASA POWER daily T2M | MERRA-2 reanalysis 2 m air temperature, served by NASA Langley's POWER API | Daily, local solar time; 0.5° × 0.625° grid cell | Curated: Dettah and Aklavik cells, 2001-10-01 to 2025-06-30 (8,674 days each), plus 7 supplementary corridors. Live: any point 50 to 75 N, 170 to 55 W, winters 1981/82 to 2024/25 | `data/raw/nasa/power_daily_*.csv`; live cache | Year-to-year change, trends, freezing degree-days | Absolute local temperatures (runs cold), road conditions |
| NASA Giovanni MERRA-2 monthly | Product M2TMNXSLV v5.12.4, variable T2M, "Time Series, Area-Averaged" export | Monthly mean; one grid cell (62.5 N, 114.375 W) | January 1980 to December 2025, 552 months, 0 missing | `data/raw/nasa/giovanni/g4.*.csv` and `.nc` | Monthly, seasonal, annual mean temperature trends | Daily indicators (FDD, thaw days): never computed from monthly means |
| ECCC Yellowknife A (and Aklavik, Inuvik) | Weather-station daily observations | Daily, one point | 2001 to 2025; 8,574 paired days at Yellowknife | `data/raw/weather_stations/*.csv` | Measuring how far NASA is from the ground | Correcting NASA (no bias correction is applied) |
| NWT Bureau of Statistics Table 108 | Government opening and closing dates for winter roads, ice roads and crossings | One date pair per route per winter | 17 routes, 1993/94 to 2024/25: 544 route-winters, 512 verified | `data/raw/roads/NWT_Table108_*.xlsx` | Describing how operating dates changed | Ice thickness, safety, usable days, causes |

**What MERRA-2 is.** A "reanalysis": a weather model run over the past that continuously absorbs real observations (stations, balloons, satellites). The result is a complete, gridded, consistent record, but it is a model estimate for a whole grid cell, not a thermometer reading at a place.

**Why POWER and Giovanni are not independent.** Both serve MERRA-2. Our check (`giovanni_vs_power_check.csv`) over 285 months: mean difference -0.001 °C, largest 0.394 °C, correlation 1.0. That checks our download and processing; it does not validate the science.

**Station disagreement.** At Yellowknife, NASA averages 5.5 °C colder than the airport in Oct to Dec and 3.57 °C colder in Jan to Mar. NASA Oct to Dec freezing degree-days average 1,551 °C-days versus 1,059 at the station (46.5% higher), but the year-to-year correlation is 0.92. Hence the rule: use NASA for change over time, not for absolute cold. `docs/TEMPERATURE_BIAS_DIAGNOSIS.md` explains the investigation.

**Road record caveats.** "Open" means open to light vehicles first; temporary closures are not recorded, so open-to-close is not usable days. Four rows are flagged inconsistent, 24 missing, 4 note-only; none is filled. The Aklavik route segment is not verified (`docs/ROUTE_IDENTITY.md`). Dettah's 2024 opening date differs by one day from a press report.

**Files.** `docs/DATA_SOURCES.md`, `docs/DATA_DICTIONARY.md`, `docs/DATA_QUALITY.md`, `docs/GEOGRAPHIC_SCOPE.md`, `UI/frostline/registry.py` (`SOURCES`, `VARIABLES`).

**Example.** Dettah, winter 2017/18: NASA Oct to Dec FDD and station FDD both appear in `station_fdd_by_season.csv`. Even if the NASA value is hundreds of °C-days higher, the two series rise and fall together across winters (r = 0.92). That is why the trend in NASA FDD is meaningful while the level is not.

**Check your understanding.** Why is "Giovanni and POWER agree" not evidence that MERRA-2 is accurate at Dettah? What would be independent evidence?

---

## 5. Map implementation

**Plain English.** The map is a real interactive web map (Leaflet), with genuine basemap tiles. Coloured dots are our two documented ice roads; the shaded square around each is the NASA grid cell the data describe. Click anywhere inside the dashed outline and that spot becomes a new investigation using live NASA data.

**Technical detail.**

- **Library.** `folium` builds a Leaflet map in Python; `streamlit_folium.st_folium` renders it in an iframe and returns what the user clicked.
- **Tiles** (`TILES` in `atlas.py`): Esri Dark Gray Canvas (default) plus an Esri place-label overlay; Esri World Topo and OpenStreetMap as alternatives in the layer control. All attributed on the map. CARTO was removed because it now requires a key.
- **Static layers** (`build_map`): dashed rectangle for the supported area (`power_api.COVERAGE`: 50 to 75 N, 170 to 55 W); for each curated location a grid-cell rectangle and a circle marker (larger and white-ringed when selected).
- **Dynamic layer** (`selection_layer`): the exploratory point and its calculated MERRA-2 cell, passed as `feature_group_to_add` so it updates without rebuilding the map.
- **Nothing invented.** No road lines, risk layers or raster surfaces are drawn.

**How a click becomes an investigation** (`atlas.render`):

1. `st_folium(..., returned_objects=["last_clicked", "last_object_clicked"])` returns `{"last_clicked": {"lat":…, "lng":…}, "last_object_clicked": …}`.
2. `new_click(out)` compares those with `xp_prev_map` / `xp_prev_obj` in session state, so a click already handled on an earlier rerun is not applied again. A marker click wins over the map click it also produces.
3. `resolve_click(ds, lat, lng)` returns `("curated", location_id)` if the click is on a curated marker (within 0.0001°), otherwise rounds to 0.01° and returns `("explore", point)` or `("outside", point)`.
4. `apply_selection` sets the shared investigation (curated) or `xp_point` (explore), or records `xp_outside` for a warning. Then `st.rerun()`.
5. With `xp_point` set, `_run_explorer` shows steps 2 to 6: question and winters, the Retrieve button, the result, the evidence, the exports.

**Without the map.** The "Case studies and coordinates" expander has buttons for the curated cases and a latitude/longitude form (`_use_coords`) that goes through the same `resolve_click` and `apply_selection`.

**Synchronisation.** The curated marker highlighted on the map is `inv.location_id` from session state, so selecting Aklavik in the sidebar also moves the highlight. An exploratory point never changes the shared investigation; "Back to the curated case studies" clears it.

**Example.** Today's browser test clicked an empty spot that resolved to 66.93 N, 125.31 W. `merra2_cell` placed it in the cell centred at 67.000 N, 125.000 W (because 125.31 is closer to 125.000 than to 125.625). The right panel switched to "Exploratory point · climate analysis only".

**Check your understanding.** Why does `new_click` remember the previous click? What bug would appear without it?

---

## 6. NASA POWER API

**Plain English.** For a new map point, Frostline asks NASA's POWER service for every daily temperature from 1 October 1981 to 31 March 2025, checks the answer carefully, saves it so the same question isn't asked twice, and then computes winter indicators.

**Technical detail** (`UI/frostline/power_api.py`).

**Endpoint and parameters** (`request_params`, `request_url`):

```
GET https://power.larc.nasa.gov/api/temporal/daily/point
    ?parameters=T2M&community=SB&longitude=-125.31&latitude=66.93
    &start=19811001&end=20250331&format=JSON
```

No API key. Only `T2M` is offered, deliberately: it's the variable the metric engine was validated on. Winters are 1981/82 (POWER's MERRA-2 daily record starts 1981-01-01) to 2024/25.

**Validation before any request** (`validate_request`): parameter supported; coordinates finite and inside the coverage box; winters in range. A failure raises `PowerError` with a message shown to the user.

**Response structure.** A GeoJSON-like object: `geometry.coordinates = [lon, lat, elevation]`, `properties.parameter.T2M = {"YYYYMMDD": value, …}`, `header` (title, api name/version, sources, fill_value, time_standard), `parameters.T2M.units`, `messages`.

**Response validation** (`parse`): must contain `properties`; unit must be `C`; values parse as numbers; values equal to the fill value (-999) or non-finite become missing; values outside -70 to 45 °C become missing and are counted as implausible; dates must be unique; returned coordinates must match the request within 0.01°. Missing dates in the requested range are counted. The metadata record keeps the URL, API version, sources, time standard, requested and returned coordinates, elevation, the calculated grid cell, day counts and messages.

**Caching** (`fetch_daily`): a cache key is the first 24 hex characters of the SHA-256 of the sorted request parameters. Lookup order: memory (`_MEM`), then disk (`$FROSTLINE_CACHE_DIR` or the system temp folder, `frostline_power_cache/<key>.json`), then a live request. Live calls are spaced at least 1 s apart. A response that fails validation is never cached. The result reports `served_from` ("live NASA POWER request", "memory cache" or "disk cache") and the original `retrieved_utc`.

**Timeouts and errors** (`_http_get_json`): 60 s timeout; HTTP errors, network errors and invalid JSON become `PowerError` with a readable message. The UI shows "No data retrieved: …", tied to the point it was raised for (`atlas.error_for`).

**From response to result** (`explore.analyze`): `winter_table` computes, for each winter, Oct to Dec FDD, Oct to Dec mean, Jan to Mar mean, Jan to Mar thaw days and valid-day counts, using `northlink_metrics` (a season with any missing day is NaN); `northlink_metrics.trend` fits the chosen question (minimum 15 winters).

**Traced request (real, 2026-11-15).** Point 66.93 N, 125.31 W. Response: POWER v2.10.3, source MERRA2, 15,888 daily values, 0 missing or fill, returned coordinates [-125.31, 66.93, 312.61 m]. The first three days of winter 2024/25 were -3.75, -6.01 and -6.65 °C; the 92 days of Oct to Dec 2024 sum to an FDD of 1,889.3 °C-days. Over 44 winters the Oct to Dec FDD trend is **-68.1 °C-days per decade**, 95% interval -111.8 to -19.6, Mann-Kendall p = 0.002. A separate script fetched the same URL and recomputed it with independent Theil-Sen and Mann-Kendall code: identical. A second point, 64.32 N, 96.02 W (entered through the coordinate form), gave -51.5 (interval -100.8 to -3.3, p = 0.040) in both the app and the independent code, and the downloaded Evidence Brief carried the same numbers.

**Check your understanding.** What exactly happens, step by step, if NASA returns `-999` for 15 November 1997 at your point? Which winter is affected, and how does the trend change?

---

## 7. Giovanni pipeline

**Plain English.** A team member used NASA Giovanni's website to export 46 years of monthly temperature for the Dettah grid cell, as a CSV and a NetCDF file. A script checks the file really is the product it claims, converts kelvin to Celsius, builds seasonal averages from complete sets of months only, fits a trend for each of seven seasons and corrects for having tested seven.

**Technical detail.**

**Raw files** (never edited): `data/raw/nasa/giovanni/g4.areaAvgTimeSeries.M2TMNXSLV_5_12_4_T2M.19800101-20251231.114W_62N_113W_62N.csv` (SHA-256 `d3895222…`) and the `.nc` companion (`be265b97…`). Both hashes are in `tests/raw_checksums.sha256`. The CSV header records the title, user dates, the requested box (-114.75, 62.2, -113.85, 62.75), the **data bounding box** (the grid point Giovanni actually used: 62.5 N, -114.375) and a reproduce URL. An untracked copy of the same two files is in `external_sources/giovanni/raw/` (byte-identical; left untouched).

**Ingest** (`scripts/ingest_giovanni_monthly.py`):

1. Refuse any file whose header doesn't name M2TMNXSLV and T2M.
2. Assign the file to a study location by matching the header's data-bounding-box point to the MERRA-2 cell centre of each location (not by file name). Refuse it if nothing matches.
3. Parse months; values ≥ 1e14, equal to the fill value or non-finite are missing (none occur). Convert: °C = K − 273.15.
4. Seasonal aggregates, complete months only: calendar year, Dec to Feb (labelled by the year of its Jan and Feb), Mar to May, Jun to Aug, Sep to Nov, Oct to Dec, Jan to Mar (labelled by the winter start year).
5. Theil-Sen trend, Mann-Kendall p, lag-1 for each of the 7 full-record aggregates; Benjamini-Hochberg q across the 7 (`giovanni_monthly_t2m_trends.csv`, `family_size` 7).
6. Cross-check against POWER daily data averaged by month for the overlapping months (`giovanni_vs_power_check.csv`).
7. Provenance key/value table (`giovanni_provenance.csv`).

`scripts/verify_giovanni_netcdf.py` (needs `h5py`, dev-only) compares the NetCDF values with the CSV value by value; result in `data/processed/giovanni_netcdf_verification.json`.

**App module** (`UI/frostline/giovanni.py`): `season_series` reads one aggregate; `trend` recomputes the Theil-Sen trend for the selected window, attaching the stored q only when the window equals the full record; `evidence_state` gives "supported" (full record, q < 0.05), "unresolved" (full record, q ≥ 0.05) or "exploratory" (any other window); `plain_language` writes the sentence; `climatology`, `anomalies` (vs 1991 to 2020) and `period_contrast` (Welch interval, first decade vs last) power the secondary charts; `brief_html`, `export_csv`, `record_json` build the exports.

**Traced observation.** The raw CSV row `1980-09-01 00:00:00,278.399475` becomes `t2m_c = 5.2495` (278.399475 − 273.15). With October 1980 (271.392639 K → -1.7574 °C) and November 1980 (253.313278 K → -19.8367 °C), the autumn 1980 mean is (5.2495 − 1.7574 − 19.8367) / 3 = **-5.4482 °C**, the first of 46 points in the autumn series. The Theil-Sen slope through those 46 points is +0.0603 °C per year, shown as **+0.60 °C per decade**.

**Results (full record, all seven):**

| Aggregate | Years | n | °C per decade | 95% interval | p | q (BH, 7) |
|---|---|---|---|---|---|---|
| Calendar year | 1980 to 2025 | 46 | +0.18 | -0.07 to +0.49 | 0.185 | 0.350 |
| Dec to Feb | 1981 to 2025 | 45 | +0.42 | -0.21 to +0.95 | 0.200 | 0.350 |
| Mar to May | 1980 to 2025 | 46 | -0.19 | -0.66 to +0.34 | 0.508 | 0.613 |
| Jun to Aug | 1980 to 2025 | 46 | +0.09 | -0.19 to +0.36 | 0.526 | 0.613 |
| **Sep to Nov** | 1980 to 2025 | 46 | **+0.60** | **+0.23 to +0.97** | **0.0018** | **0.013** |
| Oct to Dec | 1980 to 2025 | 46 | +0.54 | -0.01 to +1.02 | 0.051 | 0.179 |
| Jan to Mar | 1979 to 2024 | 46 | +0.11 | -0.52 to +0.61 | 0.733 | 0.733 |

All seven were reproduced from the raw CSV by `scripts/independent_verification.py`. One subtlety it found: Jun to Aug 2008 and 2013 are equal at the 4 decimals stored in the CSV, creating a tie that moves the summer p from 0.520 (full precision) to 0.526 (stored). No verdict changes.

**Check your understanding.** Why does Frostline never compute freezing degree-days from the Giovanni monthly means, even though FDD is the main winter indicator?

---

## 8. Mathematics and statistics

### 8.1 Time series and the winter year

**Plain English.** A time series is one number per time step, here one number per winter. Winter *y* runs from 1 October of year *y* to 31 March of *y + 1* and is labelled "y/y+1" (for example 2017/18).

**Technical.** `northlink_metrics.early_winter_range(y)` = Oct 1 to Dec 31 of *y*; `midwinter_range(y)` = Jan 1 to Mar 31 of *y + 1*. Road dates become day-of-winter numbers with Oct 1 = day 1 (`day_of_winter`).

### 8.2 Freezing degree-days (FDD)

**Plain English.** Add up how far below 0 °C each day's average temperature was. A day at -10 °C adds 10; a day at +2 °C adds 0. More FDD = more cold accumulated = more potential for ice to grow.

**Equation.**

$$\mathrm{FDD}_y=\sum_{d=\text{Oct 1}}^{\text{Dec 31}}\max(0,\,-T_d)$$

**Code.** `northlink_metrics.fdd` returns NaN unless every one of the 92 days is present exactly once and lies in -70 to 45 °C (`season_coverage`). Missing days are never filled.

**Example.** Days at -10, -4 and +2 °C: FDD = 10 + 4 + 0 = 14 °C-days. At 66.93 N, 125.31 W, Oct to Dec 2024 totals 1,889.3 °C-days.

Note: the 380 °C-day "ice-road threshold" seen in some literature is deliberately **not** used, because NASA's level runs far above the station (section 4).

### 8.3 Theil-Sen regression

**Plain English.** Draw a line between every pair of winters and measure each line's slope. The trend is the middle (median) slope. One freak winter changes only a few of those slopes, so it can't drag the answer much. Ordinary least squares can be pulled a long way by one outlier.

**Equation.** For points $(x_i, y_i)$ with $x_i \ne x_j$:

$$\hat\beta=\operatorname{median}\left\{\frac{y_j-y_i}{x_j-x_i}: i<j\right\}$$

Intercept (for drawing): $\hat\alpha=\operatorname{median}(y_i-\hat\beta x_i)$. Slopes are reported per decade (×10).

**Code.** `scipy.stats.theilslopes` inside `northlink_metrics.trend`; independent re-implementation in `scripts/independent_verification.py::theil_sen`.

**Example.** n = 46 Giovanni autumns give 46 × 45 / 2 = 1,035 pairwise slopes; their median is 0.0603 °C per year.

### 8.4 Confidence intervals

**Plain English.** A 95% interval is the range of trends compatible with the data. If it includes 0, the data can't rule out "no change". If it is all positive, they can.

**Technical.** The Theil-Sen interval (Sen 1968) uses the ranks of the sorted pairwise slopes. With $N$ slopes and Kendall variance $\operatorname{Var}(S)$, take $C = 1.96\sqrt{\operatorname{Var}(S)}$; the lower and upper limits are the slopes at ranks about $(N - C)/2$ and $(N + C)/2$. Frostline also reports a **moving-block bootstrap** interval for curated results (`northlink_stats.block_bootstrap_slope`): resample blocks of consecutive residuals (block length $\lceil n^{1/3}\rceil$, 2,000 resamples, seed 20261114), refit, take the 2.5th and 97.5th percentiles. Blocks keep short-range year-to-year dependence that the plain interval ignores.

**Example.** Dettah Oct to Dec FDD 2001/02 to 2024/25: +15 °C-days per decade, interval -108 to +111. The interval is so wide that the data are compatible with a large decrease, no change or a large increase.

### 8.5 Mann-Kendall test and p-values

**Plain English.** Look at every pair of winters and ask: did the later one go up or down? If there's no trend, ups and downs should roughly balance. The p-value is the chance of seeing an imbalance at least this large if there really were no trend.

**Equations.**

$$S=\sum_{i<j}\operatorname{sign}(y_j-y_i),\qquad \operatorname{Var}(S)=\frac{n(n-1)(2n+5)-\sum_t t(t-1)(2t+5)}{18}$$

(the sum over $t$ corrects for groups of tied values), then

$$z=\begin{cases}(S-1)/\sqrt{\operatorname{Var}(S)} & S>0\\ 0 & S=0\\ (S+1)/\sqrt{\operatorname{Var}(S)} & S<0\end{cases},\qquad p=2\,(1-\Phi(|z|))$$

**Code.** `northlink_metrics.mann_kendall`.

**Example.** Giovanni autumn: p = 0.0018. A p-value is **not** the probability that the trend is real, and p = 0.06 does not mean "no trend".

**Guards** (`northlink_metrics.trend`): fewer than 15 values → "too_few_points"; all equal → "constant_series"; one value in ≥ 75% of years → "mostly_tied" (for example thaw days, which are zero in almost every NASA winter). In each case no slope, interval or p is shown.

### 8.6 Multiple-testing corrections

**Plain English.** Run 100 tests on pure noise and about 5 will have p < 0.05 by luck. Correcting for the number of tests stops us from celebrating those lucky ones.

**Benjamini-Hochberg (BH) q-values** (`northlink_stats.bh_adjust`): sort the *m* p-values; $q_{(k)}=\min_{j\ge k}\, p_{(j)}\, m/j$. Declaring "supported" whenever q < 0.05 keeps the expected share of false discoveries among supported results at or below 5%. **Holm** (`holm_adjust`) is stricter: it controls the chance of even one false positive.

**Declared families in Frostline** (`hypothesis_families.csv`):

| Family | Tests | What it covers |
|---|---|---|
| F1_all_extended | 126 | 14 metrics × 9 corridors, winters 2001/02 to 2024/25 |
| F2_climate | 99 | Climate metrics only, same window |
| F3_road_2001_2024 | 27 | Road metrics, same window |
| F4_road_record_all_routes | 51 | Road dates (3 metrics × 17 routes), 1993/94 to 2024/25 |
| F5_road_climate_associations | 11 | Leak-free climate-versus-road correlations |
| Giovanni seasons | 7 | Seven seasonal aggregates, 1980 to 2025 |

A q is shown **only** for a pre-declared fixed window. Any user-chosen window is labelled exploratory with no q (`analysis.trend`, `giovanni.trend`, and every live map point).

**Example.** Across the 126 extended tests, 20 have p < 0.05 but about 6.3 are expected by chance, and none has q < 0.05. Dettah opening day 2001/02 to 2024/25: q = 0.085 in F1 (the app's choice) but 0.018 if corrected only within F3. Choosing the family is a judgement, which is why it awaits statistical sign-off.

### 8.7 Statistical power and sample size

**Plain English.** A short, noisy record can only detect large trends. Not detecting a trend in 24 winters often just means the record is too short.

**Technical.** The minimum is 15 complete winters (`MIN_SEASONS`). Interval width shrinks roughly like $n^{-3/2}$ for a trend, which is why the 46-year Giovanni series (interval ±0.37 °C per decade) can resolve what the 24-winter POWER series cannot. Every "not resolved" result carries "That is not proof of no change."

### 8.8 Seasonal dependence and serial correlation

**Plain English.** One winter can resemble the next (for example during multi-year ocean patterns). That makes the data carry less independent information than their count suggests, so p-values can look better than they are.

**Technical.** Each result reports the lag-1 autocorrelation of the Theil-Sen residuals (`lag1_autocorr`); above 0.3 in size, a flag says "p may be optimistic". The block-bootstrap interval is the dependence-aware alternative. Seasonal aggregates overlap (Sep to Nov and Oct to Dec share two months), so tests within the Giovanni family are positively dependent. BH stays valid under that kind of positive dependence, but q values are best read as indicative.

### 8.9 Selection bias

**Plain English.** If you look at many places and then present the one with the most dramatic trend, it will look more significant than it is.

**In Frostline.** Dettah was chosen as the primary case after its road-date trend had been seen. The app prints that caveat on every Dettah road result (`analysis._road_context_sentences`) and uses the all-route family of 51 tests as the adjustment. In the Giovanni record, all seven seasons are shown, not just autumn.

### 8.10 Correlation versus causation

**Plain English.** Two things changing together doesn't mean one causes the other.

**In Frostline.** Late-November snow on the ground at Yellowknife correlates with Dettah's opening day (Spearman ρ = +0.64, interval 0.39 to 0.85, n = 23, q = 0.005 in a 5-predictor family). It is labelled a **hypothesis**. Climate-versus-road correlations are restricted to **leak-free** windows that end before the road opens: the Oct to Dec window reached the Dettah opening date in 16 of 24 winters, so it was removed (`leakage_audit.csv`). All leak-free climate predictors have intervals that include zero. The app never says warming caused later openings.

**Check your understanding (section 8).** (a) The Oct to Dec Giovanni trend has p = 0.051 and q = 0.179. Write the one sentence the app would say about it, and explain why "it isn't warming" is wrong. (b) Compute the BH q for the smallest of three p-values 0.01, 0.04 and 0.30.

---

## 9. Evidence Engine

**Plain English.** For any investigation, the Evidence Engine asks seven separate questions about how far the evidence can be trusted, and answers each with a plain label and specific reasons taken from the data. It deliberately gives **no overall score**, because one number would hide which part is weak.

**Technical** (`UI/frostline/evidence.py`, `assess`). Seven dimensions, each a `Dimension(key, title, state, summary, reasons, sources)`:

| Dimension | Function | What it checks |
|---|---|---|
| Temporal completeness | `_completeness` | Winters with values versus winters in the window; missing days; verified road rows |
| Source provenance | `_provenance` | Primary record or documented NASA product; version and eligibility caveats; Giovanni status |
| Spatial representativeness | `_representativeness` | Grid cell versus the road; single crossing versus long delta road |
| Ground-observation agreement | `_ground_agreement` | NASA versus station bias and correlation |
| Statistical precision | `_precision` | Interval width, q, lag-1 flag |
| Exploratory status | `_exploratory` | Fixed window with a family, or user-selected |
| Temporal alignment with road operations | `_alignment` | Whether the climate window overlaps the road outcome (leakage) |

States come from a fixed vocabulary: "Meets the standard", "Use with caution", "Material limitation", "Not assessed", "Not applicable". Six evidence layers are kept apart: A observations, B derived indicators, C statistical inference, D external corroboration, E limitations, F unanswered questions (`_layers`, `_questions`). `_headline` and `_suitability` write the top sentences ("Suitable for describing how recorded operating dates changed. Not suitable for inferring ice conditions, road safety or the reason for any change.").

**How unsupported interpretations are prevented.** All result sentences are templates filled from computed numbers (`analysis.T_*`, `giovanni.plain_language`, `explore.headline`); no generative model writes text. Road results always carry `T_ROAD` ("government records of operations, not measurements of ice thickness"). Tests scan the app and documents for prohibited wording ("caused by", "due to warming", "pre-registered", deployment claims; `tests/test_frostline_app.py::test_no_overclaiming_or_prohibited_wording`).

**Example.** Dettah, opening day, 1993/94 to 2024/25: headline "The record supports a change in opening day at Dettah over 1993/94 to 2024/25 (+9.0 days per decade, later). It is exploratory and does not show what produced the change."

**Check your understanding.** Why would a single "evidence score" out of 100 be worse than seven separate labels? Give a concrete case where it would mislead.

---

## 10. Evidence Brief

**Plain English.** Every investigation can be downloaded as a self-contained web page (HTML), the data behind it (CSV) and a machine-readable record (JSON). The numbers in the brief are the same objects the screen shows, so they can't disagree.

**Technical.**

- Curated investigations: `brief.build(ds, location_id, variable_id, first, last, question_id)` calls the same `analysis.trend` and `evidence.assess` as the page, renders `stat_rows` (the same label/value list the finding card uses), an inline SVG chart, the evidence assessment, limitations, sources, the data digest, code version and file hashes. No scripts, no network; prints to PDF.
- Giovanni: `giovanni.brief_html` (inputs, finding, all seven seasonal tests, POWER cross-check, provenance, citation, methods).
- Live points: `explore.brief_html` (exploratory caveat first, finding, inputs and source metadata including the exact request URL and retrieval time, winter-by-winter values with valid-day counts, methods).
- Download: `st.download_button(..., on_click="ignore")`, so clicking doesn't rerun the app.

**Consistency guarantees.** (1) One source of numbers per result: the `Finding`, `GTrend` or `ExploreResult` object. (2) Shared formatting through `fmt.py`. (3) Tests compare brief and screen numbers (`test_brief_numbers_equal_screen_numbers`, `test_brief_csv_json_and_headline_agree`, `test_brief_and_exports_carry_the_same_numbers`). (4) Determinism: the same inputs and timestamp produce the same brief (`test_brief_is_deterministic_and_follows_the_app_state`).

**Example (browser-verified today).** The brief downloaded for 64.32 N, 96.02 W was served with HTTP 200, titled "Frostline Evidence Brief - exploratory point 64.32 N 96.02 W", and contained slope -51.5, interval -100.8 to -3.3, p = 0.040, 44 complete winters, cell 64.500 N, 96.250 W, elevation 85.32 m: the same as the screen and the independent computation.

**Check your understanding.** If someone edits `brief.py` to round slopes to whole numbers but forgets the screen, which test fails and why?

---

## 11. Reliability and testing

**Plain English.** We check Frostline four ways: automated tests, a full rebuild of every result from raw data that must match exactly, an independent recalculation with different code, and clicking through the real app in a browser.

**Technical.**

- **Automated tests**: `python3 -I -m unittest discover -s tests`: **204 tests, all passing** on 2026-11-15 (198 baseline plus 6 added today). Files: `test_metrics.py`, `test_pipeline.py`, `test_real_data.py`, `test_scientific_acceptance.py`, `test_handoff_layer.py`, `test_frostline_app.py` (app behaviour through Streamlit's `AppTest`), `test_global_audit.py`, `test_map_giovanni_power.py` (Giovanni ingest, POWER adapter with real cached values, map), `test_final_qualification.py` (today's regressions and the independent reproduction). **No test calls the network**; POWER responses are built from our cached real daily values in the documented JSON layout.
- **Deterministic regeneration**: `python3 -I scripts/regenerate_all.py --check` rebuilds `data/processed/`, `UI/data_real/` and the generated documents from raw files and fails if anything differs. Result today: "regeneration is a no-op"; raw-data digest `2f4bc4f02926fbc2` unchanged.
- **Original-data integrity**: `tests/raw_checksums.sha256` holds SHA-256 hashes of every raw file; the app's data digest (`a1f1cd6387875487`) is the hash of all approved app files and is printed in the sidebar and every brief.
- **Cross-checks inside the app**: a precomputed result is displayed only after a live recomputation agrees with it (`analysis.trend`, tolerances `CROSS_CHECK_*`); a disagreement raises `DataError` and nothing is shown.
- **Independent scientific verification**: `scripts/independent_verification.py` (no import of production code or `scipy.stats.theilslopes`) re-derives the 7 Giovanni trends, their q-values and the two Dettah opening-day windows from the raw Giovanni CSV and the raw NWT workbook. All agree.
- **Live API checks** (manual, today): two new points fetched by the app and separately by `curl`, recomputed independently, identical.
- **Browser testing** (today, in-app browser, 1440 × 900 and 375 × 812): landing, Map click and coordinate-form selection, live retrieval, Evidence Brief download, Giovanni season and period changes, all six demo stages forward and back with no exceptions.

**Lesson learned today.** A Streamlit server started at 11:17 kept serving a module edited at 11:18, so its page showed an outdated label. Always restart the server after changing code before a demo.

**Check your understanding.** What is the difference between "the tests pass" and "regeneration is a no-op"? Could one pass while the other fails?

---

## 12. Deployment

**Plain English.** Frostline is a normal Streamlit app. Anyone can run it on a laptop with two commands; for judges we deploy it to Streamlit Community Cloud from the public GitHub repository.

**Technical.**

- **Repository**: `https://github.com/aneesh-6220/frostline` (public). Release branch `frostline-map-giovanni-release` (`fe04f73`) is pushed; `frostline-final-qualification` (today's work) is local until the team approves a push.
- **Local run**: Python 3.12; `pip install -r UI/requirements.txt`; `streamlit run UI/frostline_app.py` from the repository root. Theme and settings come from `.streamlit/config.toml`.
- **Hosted (Streamlit Community Cloud)**: repository `aneesh-6220/frostline`, branch as approved, main file `UI/frostline_app.py`, Python 3.12, no secrets. Streamlit Cloud reads `UI/requirements.txt` (next to the main file). After the build, set the app to public and open it in a private window. Pushing new commits to the deployed branch redeploys automatically.
- **External services at run time**: NASA POWER (live points only), Esri/OSM tiles, Google Fonts. If any fails, the curated analyses, Giovanni record, guided demo and all curated briefs still work.
- **Secrets**: none. `.env` is git-ignored and only used by the optional Giovanni API fetch script (`EARTHDATA_TOKEN`), which the app never needs.
- **Failure conditions**: a missing or altered data file stops the app with a message naming the file; NASA POWER unreachable shows an error for that point only; a cold start on Streamlit Cloud takes a minute ("waking up").
- **Status**: **not deployed** as of this writing. See `submission/DEPLOYMENT.md`.

**Check your understanding.** The deployed app shows "NASA POWER could not be reached" for every point, but works on your laptop. What are two likely causes and how would you check?

---

## 13. Actual limitations

| Category | Item |
|---|---|
| **Supported** (tested, browser-verified, numbers independently reproduced) | Giovanni seven-season trends for the Dettah cell; Dettah opening-day trends in both windows; live POWER retrieval and analysis for any point in the supported area; exports; guided demo |
| **Exploratory** (works, but results are labelled exploratory by design) | Every user-selected window; every live map point (not corrected for multiple testing); road-climate associations (hypotheses); seven supplementary corridors (approximate points) |
| **Unresolved** (open scientific or factual questions) | Statistical sign-off (Yao); the 126 versus 27 test family for Dettah 2001/02 to 2024/25; Aklavik route identity and segment; four flagged road rows; whether Giovanni use satisfies the Global Award rule; Esri tile terms for this use |
| **Unavailable** (not built) | Ice thickness, road safety, opening-date prediction, causal attribution; live variables other than T2M; Giovanni for Aklavik; satellite (MODIS) data in the app; any user study; public deployment (as of writing) |

Scientific limits that apply everywhere: reanalysis is a grid-cell model estimate and runs 3.4 to 7.3 °C colder than the Yellowknife station in Oct to Dec; 24 winters is short; the road record is operations, not ice; no bias correction; no causal inference.

**Check your understanding.** Which of these limitations could the team realistically remove in one week, and which need new data or new science?

---

## 14. Development history and human contributions

**What the repository shows** (`git log`):

- **2026-11-14**: the repository began with a Streamlit UI and prototype under an earlier project name (commit `ffc0dbe`, author `seetheseaagain-dev`). The same day, a sequence of AI-authored commits (author "Claude") added the real NASA POWER data, station validation, extended variables, nine-corridor analysis, a scientific remediation (bias diagnosis, leak-free windows, multiplicity families, route identity), and the handoff documents.
- **2026-11-14 to 15**: AI-authored commits built the Frostline application on the approved data layer, verified it in a browser and redesigned the frontend.
- **2026-11-15**: Shaurya Veer Singh committed credential ignores and `.env.example` (`3feb9a8`). Aneesh Mahatekar committed the global audit, caveat repairs, the Giovanni integration with the interactive map and live POWER exploration, release documentation, and today's final qualification (`f3edb22` and the documentation commit). Those commits were made in AI-assisted sessions.
- Commit counts up to `f3edb22`: 16 by "Claude", 7 by Aneesh Mahatekar, 1 by Shaurya Veer Singh, 1 by `seetheseaagain-dev`.

**How AI was used.** A large share of the code, analysis scripts and documentation was generated with Claude (Claude Code; Claude Fable 5.2 for the application build). This is disclosed in the app (Methods) and in `submission/AI_USE_DISCLOSURE.md`.

**Human review and validation that the repository records.** The Giovanni export was obtained by a team member through the Giovanni website (credentials are never handled by an AI). The team set the question, approved the scope rules and requested the audits. Independent numerical reproduction and browser testing were performed today. **Not recorded**: an independent statistician's sign-off, and a written account of which team member reviewed which part.

**What the repository does not tell us.** Individual contributions outside git (research, design decisions, data export, testing, presentation). The team must write those into `submission/AI_USE_DISCLOSURE.md` (it still has bracketed placeholders) and must not let anyone, human or AI, invent them.

**Check your understanding.** A judge asks, "Which part did you personally build or verify?" What is your honest answer, and where in the app or repository can you show it?

---

## 15. Glossary

- **Reanalysis**: a weather model run over the past, constrained by observations, producing a complete gridded record (MERRA-2).
- **Grid cell**: the area a gridded value represents; MERRA-2 is 0.5° × 0.625° (about 55 km × 25 to 32 km at these latitudes).
- **T2M**: air temperature 2 m above the ground.
- **FDD**: freezing degree-days, the sum of daily degrees below 0 °C.
- **Theil-Sen**: median of all pairwise slopes; a robust trend.
- **Mann-Kendall**: rank-based test for a monotonic trend.
- **p-value**: probability of data at least this extreme if there were no trend.
- **q-value (BH)**: p-value adjusted for the number of tests in a declared family.
- **Family**: the set of tests corrected together.
- **Exploratory**: not pre-declared and not adjusted for multiple testing; describe, don't conclude.
- **Lag-1 autocorrelation**: how much each year's residual resembles the previous year's.
- **Block bootstrap**: resampling consecutive blocks to keep dependence when estimating uncertainty.
- **Leakage**: using information from after the outcome to "explain" it.
- **Data digest**: a short SHA-256 fingerprint of every approved data file.
