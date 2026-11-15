# Extending Frostline

Frostline is built so that a new verified location or variable is added through the data pipeline and a registry entry. No view, and no statistical code, needs to change.

## Architecture in one page

```
data/raw/                 cached public sources (never edited; checksums in tests/raw_checksums.sha256)
scripts/                  the scientific pipeline and the approved statistics
  northlink_metrics.py      season definitions, FDD, thaw days, Theil-Sen, Mann-Kendall
  northlink_stats.py        block bootstrap, Benjamini-Hochberg, Holm
  northlink_recompute.py    period_trend, climate_series, road_series (the only statistics entry point the app uses)
  regenerate_all.py         rebuilds every derived file; --check proves the committed outputs match
UI/data_real/             the approved application data (generated; the only data the app reads)
UI/frostline_app.py       entrypoint: page config, data validation, navigation
UI/frostline/
  schema.py                 required files and columns
  data.py                   strict loader (DataError names the file; no fallback)
  registry.py               Location, Variable, Question and Source entries
  analysis.py               Series, Finding, Comparison objects built with northlink_recompute
  evidence.py               the Evidence Engine (EvidenceReport, Dimension, Layer)
  brief.py                  Evidence Brief (HTML, CSV, JSON) from the same objects
  charts.py                 Plotly figures
  ui.py                     theme, shared investigation state, shared components
  views/                    one module per view
tests/test_frostline_app.py application acceptance tests
```

One investigation state (location, variable, window, question) lives in `st.session_state` and is read through `ui.current()`. Every statistic on screen and in an export comes from `analysis.trend(ds, location, variable, first, last)`, so the screens and the brief cannot disagree.

## Add a location

A location may appear only after its data pass the quality gates in `docs/DATA_QUALITY.md`: complete daily coverage for every winter used, documented provenance, validated units and at least 15 winters.

1. Add the raw NASA file to `data/raw/nasa/` and update the checksum manifest (`docs/CHALLENGE_ELIGIBILITY.md` shows the command).
2. Add the location to the pipeline inputs (`data/processed/locations.csv` and the corridor list in `scripts/run_extended_analysis.py`) and run `python3 -I scripts/regenerate_all.py`. Its per-winter rows then appear in `UI/data_real/season_metrics_extended.csv` and its fixed-window results in `multiple_testing_126.csv`.
3. It is now available to the app as a supplementary corridor with no further code: `registry.build_locations` reads `corridor_panel.csv`. `tests/test_frostline_app.py::Extensibility` shows a supplementary corridor running through the trend engine, the Evidence Engine and the brief.
4. To promote it to a mapped case study, add its verified coordinates to `corridors.csv` through the generator and add its context to `_CASE_TEXT` in `registry.py` (setting, access, sampling point, station, facts with their verification status). Do not add a location whose route identity is unverified without saying so in its `caution` text.

Adding corridors changes the size of the 126-test family, so the adjusted q values of every existing result change. That is a statistical decision and needs the reviewer named in `docs/APP_IMPLEMENTATION_CONTRACT.md` section 7.

## Add a variable

1. Compute its per-winter value in the pipeline (one column in `extended_season_metrics.csv`) with a documented window and unit, and regenerate.
2. Add one `Variable` entry to `VARIABLES` in `registry.py`: identifier, label, units, definition, why it is relevant, source, POWER parameter, resolutions, valid period, the fixed windows that carry a q, limitations.
3. Optionally reference it from a `Question`.

The Trend Detective, comparison, Evidence Engine and brief pick it up from the registry. Mark `is_temperature=True` for any temperature so the required bias caveat is shown beside it.

## Add a qualifying NASA source (Giovanni)

`scripts/ingest_giovanni_monthly.py` accepts only files whose header names collection M2TMNXSLV and variable T2M. When real files are ingested, three `giovanni_*` files appear in `UI/data_real/` and the app shows a Giovanni panel under Methods, NASA resource status. Without them the panel is hidden and the status reads "not demonstrated". Monthly means are never used for freezing degree-days or thaw counts.

## What is deliberately not supported

- An arbitrary custom point. No data exist for one, and the app never generates values.
- Live NASA downloads inside the app. Results must not change under a presenter, and the contract forbids network calls for data.
- Any statistical method other than the approved ones, any bias correction, and any prediction or safety output.

## Commands

```
pip install -r UI/requirements.txt                 # Python 3.12
python3 -I scripts/regenerate_all.py --check       # derived data match the committed outputs
python3 -I -m unittest discover -s tests           # scientific and application tests
streamlit run UI/frostline_app.py                  # from the repository root
FROSTLINE_DATA_DIR=/path/to/copy streamlit run UI/frostline_app.py   # explicit alternative data directory (tests use this)
```
