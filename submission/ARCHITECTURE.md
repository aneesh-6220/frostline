# Frostline: technical architecture summary

## What it is

A Streamlit application over a reproducible scientific pipeline. A user chooses a location, an Earth-system variable and a period; Frostline shows the historical series, the rate of change per decade with two confidence intervals, a Mann-Kendall significance test, a multiple-testing adjustment where one is defined, the government road record beside it, an assessment of the evidence, and a downloadable brief.

## Layers

```
Public sources (cached, checksummed)       NASA POWER daily (MERRA-2, CERES) · NWT Table 108 road dates · ECCC stations
        |
Scientific pipeline (scripts/)             season metrics, Theil-Sen, Mann-Kendall, block bootstrap, BH and Holm, leakage audit
        |   python3 -I scripts/regenerate_all.py  (deterministic; --check proves committed outputs match)
Approved application data (UI/data_real/)  20 CSV files and canonical_facts.json; the only data the app reads
        |
Application (UI/frostline/)
   data.py        strict loader: a missing, unreadable or synthetic file is a named, visible error; no fallback
   registry.py    locations, variables, questions, sources
   analysis.py    Series, Finding, Comparison: every estimate from scripts/northlink_recompute.py
   evidence.py    Evidence Engine: six evidence layers, seven separately judged quality dimensions, no overall score
   brief.py       Evidence Brief: HTML, CSV, JSON from the same Finding objects as the screens
   charts.py      Plotly figures      ui.py  theme, shared state, components      views/  ten views
```

## Design decisions that protect the science

1. **One statistical engine.** The application implements no estimator. A test fails if any fitting or resampling call appears in the app.
2. **Statistics always match the selection.** An approved fixed window shows its stored result and its q, after a live recomputation agrees with it. Any other window is recomputed and shows an unadjusted p labelled exploratory, with no q.
3. **Evidence states, not a binary verdict.** Supported historical trend, trend not statistically resolved, exploratory window, insufficient data, inference unavailable. Each is derived from the computed result.
4. **No hidden disagreement.** The cold bias of the NASA reanalysis against the Yellowknife station is a first-class view, and the required caveat sits beside every temperature figure.
5. **Separate objects.** Environmental results and road-operation results are never merged into one number.
6. **Offline core.** The app makes no network request for data. Only the optional map background and web fonts use the network, and the app works without them.
7. **Exports cannot drift.** The brief and the screens render the same list of statistic rows through the same formatting functions; tests compare them.

## Stack

Python 3.12, Streamlit, Plotly, PyDeck, pandas, NumPy, SciPy. Tests: `unittest` with Streamlit `AppTest`, plus a scripted Chrome session for end-to-end checks.

## Reproduce

```bash
pip install -r UI/requirements.txt
python3 -I scripts/regenerate_all.py --check     # derived data equal the committed outputs
python3 -I -m unittest discover -s tests         # scientific and application tests
streamlit run UI/frostline_app.py
```

Reproducibility is from the cached public sources in `data/raw/`. A live re-download has not been compared (`docs/SCIENTIFIC_METHODS.md` section K). More detail: `docs/EXTENDING_FROSTLINE.md` and `docs/FROSTLINE_IMPLEMENTATION_MATRIX.md`.
