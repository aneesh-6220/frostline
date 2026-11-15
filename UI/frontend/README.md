# Frostline web frontend

The user-facing Frostline application: React, TypeScript, Tailwind CSS and Motion, served together with a thin
JSON API over the unchanged `frostline` analysis package. It replaces the Streamlit interface; the Streamlit app
(`UI/frostline_app.py`) stays in the repository only because its acceptance tests still run against it.

## Run it

From the repository root, Python 3.12 and Node 22:

```bash
pip install -r UI/api/requirements.txt          # the pinned analysis stack + FastAPI/uvicorn
cd UI/frontend && npm ci && npm run build && cd ../..
uvicorn UI.api.server:app --port 8000           # open http://localhost:8000
```

Development with hot reload: run the API as above, then `cd UI/frontend && npm run dev` and open http://localhost:5173
(Vite proxies `/api` to port 8000).

One-container deployment (Render, Railway, Fly.io, Hugging Face Spaces with the Docker SDK): the repository-root
`Dockerfile` builds the frontend and starts the server on `$PORT`. No secrets are needed.

## Architecture

```
frostline/ (unchanged)  ──►  UI/api (FastAPI, read-only)  ──►  UI/frontend (React SPA)
analysis, evidence,          presenters.py: one view model       routes, investigation state in
brief, charts, fmt           per Streamlit view, same text       the URL, design system, charts
                             chart_theme.py: recolours the
                             charts.py figures for light UI
```

* **No statistic is computed outside `frostline`.** The API calls the same functions the Streamlit views called and
  formats every value with `frostline.fmt`. `tests/test_web_api.py` checks findings, the Evidence Brief and chart data
  against the package.
* **Charts** are the `frostline/charts.py` Plotly figures. `chart_theme.py` swaps dark-surface colours for the light
  palette token by token; data, hover text and geometry are untouched (tested). plotly.js 4.1.1 matches the version
  bundled with the pinned Python plotly, and loads only when the first chart is shown.
* **The investigation** (location, variable, period, question) lives in the URL: `?loc=&var=&from=&to=&q=`. Links
  reproduce a selection and the back button undoes a change. Validation follows `ui.init_state`/`set_investigation`.
* **Errors**: if a data file fails the strict loader or a cross-check, the API answers with the file name and the view
  shows it. Nothing is substituted.

## Feature parity with the Streamlit app

| Streamlit view | Web route | Everything carried over |
|---|---|---|
| Sidebar console | Investigation bar (desktop), sheet (tablet/phone) | location, variable, exploratory toggle, period slider, approved-window presets, evidence state and window meta, data digest |
| Observatory | `/` | hero, live Dettah chart and state, 4 indicators, guided steps, entry rows, why it matters, release counts, scope note |
| Guided demo | `/demo?step=0..5` | six stages with the same variable/question changes per stage, map and location pick, charts, finding cards, timeline, conclusion, evidence dimensions, brief downloads, Back / Next / Explore freely |
| Atlas | `/atlas` | map of sampling points and MERRA-2 cells (click to select), zoom to cell, location list, location record, caution, continue buttons, verified facts, supplementary corridors |
| Questions | `/questions` | five questions, location choice, recommendations with state/n/range, open next view with question+location+variable, thaw note, variable catalogue |
| Trend Detective | `/trends` | trend chart, plain language, finding card with full record, reanalysis caveat, exploratory-window caveat, thaw note, winters table, why this variable, robustness (table or nine-corridor forest), method and provenance, continue buttons |
| Compare | `/compare` | variable choice, matched winters, comparison chart, difference result, both finding cards, table, difference series, nine corridors, settings and caveat |
| Corridor | `/corridor` | overview and cautions; road history (3 measures, two windows, record table); environmental record (4 variables); timeline with winter inspector and season record; associations and snow hypothesis; all NWT routes (2 windows, forest, table); evidence conclusion |
| Evidence | `/evidence` | assessment, seven dimensions, six layers and files, source disagreement (metrics, two charts, tables, guidance), multiple testing (metrics, chart, families, all 126 tests, CSV download) |
| Brief | `/brief` | HTML, CSV and JSON downloads, sandboxed preview |
| Methods | `/methods` | methods, data and citations, sources, POWER acknowledgement, literature, software, file hashes, NASA resource status (Giovanni panel when ingested), AI-use disclosure, limits and review, extending Frostline |
| Footer | every page | the same disclaimer |

Wording changed in three places only, because the colours changed: "white line" is now "dark line", "grey band" is
now "blue band", and "the buttons in the sidebar" is now "the approved-window buttons in the period control".

## Design system

Blue and white: `#2563EB` for navigation, actions and data; deep navy `#0B1736` for type and the brand band; cool
neutrals for surfaces and rules. Status colours are reserved for evidence states and always carry a text label.
Type is Geist (self-hosted, no network). Icons are a single in-house 20 px, 1.5 px stroke set. Motion is short and
functional (page and tab transitions, shared-layout indicators) and is switched off under `prefers-reduced-motion`.
Layouts are built phone-first: bottom tab bar and investigation sheet below 768 px, drawer navigation below 1024 px,
touch targets of 44 px, wide tables scroll inside their card.
