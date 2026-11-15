# Frostline web app (MVP)

A Starlette API (`api/server.py`) over the approved scientific modules in `UI/frostline/` plus a static client in `web/`
(ECharts and MapLibre GL JS vendored in `web/vendor/`, OpenStreetMap raster tiles for the atlas background).
The API computes nothing itself: series, trends, comparisons, evidence and briefs come from `frostline.analysis`,
`frostline.evidence` and `frostline.brief`, which read only `UI/data_real/` and call `scripts/northlink_recompute.py`.

## Run
```
pip install -r requirements-web.txt
python3 -m uvicorn api.server:app --port 8765
```
Open http://127.0.0.1:8765

## Views
Overview, Explore (location, variable, period; chart, statistics, interpretation, bias caveat), Atlas (MapLibre, Dettah and
Aklavik sampling points; clicking a marker sets the active location everywhere), Compare (matched winters, A, B and the
difference series), Road history (NWT Table 108 opening and closing dates, road-operations trends kept separate from
environmental trends, exploratory associations labelled association not cause), Evidence (evidence dimensions, NASA POWER
versus ECCC station disagreement, sources, POWER acknowledgement), Reports (HTML brief, CSV, JSON generated from the current
selection by `frostline.brief.build`).

## API
`/api/meta`, `/api/investigation`, `/api/compare`, `/api/road`, `/api/station`, `/api/brief.html`, `/api/series.csv`,
`/api/brief.json`, `/api/health`. Unsupported selections return HTTP 422 with a readable message; data-file problems return 503
and no numbers.

## Known limitations
- PDF export is not offered; print the HTML brief to PDF from the browser.
- The atlas basemap needs network access to tile.openstreetmap.org; markers and all analysis work without it.
- No route geometry is drawn (none is verified). Supplementary corridors have no verified coordinates and are not mapped.
- No frontend unit tests or Playwright suite yet; verification so far is a manual browser pass of acceptance tests A to H.
