# Frostline UI design system

This describes how the interface is actually built. The tokens live in three places that must stay in step:
`UI/frostline/ui.py` (CSS), `.streamlit/config.toml` (native Streamlit widgets) and `UI/frostline/charts.py` (Plotly figures).
`UI/frostline/views/atlas.py` (`MAP_CSS`) restyles the Leaflet map controls with the same values.

## Principles

1. **Observatory, not dashboard.** Hierarchy comes from type, spacing and hairlines. Cards are used only where a surface holds one result.
2. **One accent.** Frost blue `#8CCBF0` marks focus, the current page, the primary action and the first step of a path. Nothing else.
3. **Status colour always ships with words.** Evidence states use a dot plus a text label (`Trend not statistically resolved`), never colour alone.
4. **Three levels of reading.** (1) a plain-language sentence and an evidence-state chip, (2) the chart with its interval band, (3) collapsed full statistics, methods and provenance. The interval, n, period, p and adjusted q stay on level 1 and are never hidden.

## Palette (dark)

| Token | Value | Use |
|---|---|---|
| `--bg` | `#0B0E13` | Page, map container while tiles load |
| `--bg-side` | `#0E1117` | Sidebar, phone tab bar |
| `--surface` / `-2` / `-3` | `#12161D` / `#151A22` / `#1B212B` | Panels, controls, hover |
| `--line` / `-soft` / `-strong` | `#232A35` / `#1C222C` / `#2E3644` | Hairlines and borders |
| `--ink` / `-2` / `-3` | `#E7ECF2` / `#A3AEBD` / `#7D8898` | Text: primary, secondary, tertiary (all pass WCAG AA on `--surface`) |
| `--frost` | `#8CCBF0` | The single accent |
| `--good` / `--warn` / `--alert` | `#4CC38A` / `#E5B454` / `#EC835A` | Evidence states and caveats only |

Chart series: Dettah / NASA `#4C9BE8`, Aklavik / station `#E0773F`, trend line `#E7ECF2`, interval band translucent neutral.

## Type and spacing

- Inter 400/500/600 with tabular numerals for values. Monospace (`ui-monospace`) only for digests, hashes and file names.
- Scale: hero 44px (36px below 1100px wide, 30 to 32px on phones), page title 28px, result value 34px, section 15px, body 14 to 15px, captions 12 to 12.5px.
- Spacing steps: 4, 8, 12, 16, 24, 32, 48 px (`--s1` to `--s7`). Radii: 6, 8, 12 px.
- Content max width 1240px. Side gutter 32px, 24px below 1100px, 16px on phones.

## Components (`UI/frostline/ui.py`)

| Helper | Purpose |
|---|---|
| `page_header` | Kicker, title, lede for every view |
| `section` | Small section heading with optional right-aligned aside |
| `journey` | The landing page's five-step investigation path (numbered, connected) |
| `steps` | Stage indicator with progress bar (map workflow, guided demo) |
| `finding_card` | Level-1 result: value, unit, direction, interval, n, period, p, q, sentence, source. Full record in a collapsed expander |
| `result_panel` | Same shape for non-trend results (comparisons, Giovanni, live POWER) |
| `metrics` | A ruled strip of values that share hairlines instead of floating cards |
| `chip` | Evidence state (dot + label) |
| `caveat` / `note` | Amber required qualification / neutral explanatory note, both with an icon and a bold label |
| `kv_table` | Key-value provenance and statistics tables |
| `brief_downloads` | HTML (primary), CSV and JSON exports |
| `.fl-legend` | One-line map legend under the map |

## Charts (`UI/frostline/charts.py`)

- Points and a thin connecting line in the series colour; Theil-Sen trend in `#E7ECF2`; 95% slope interval as a grey band. The live NASA POWER explorer chart uses the same encoding.
- Legends horizontal above the plot. Tick and axis-title labels 12.5px; hover labels 12.5px on a dark tooltip.
- Units in axis titles. Winter ticks formatted `2005/06`.
- `theme=None` so Streamlit does not override the figure styling.

## Map (`UI/frostline/views/atlas.py`)

- Real Leaflet map (folium + streamlit-folium), 560px tall. Esri Dark Gray Canvas with an Esri place-label layer by default; Esri World Topo and OpenStreetMap in the layer menu. All attributed on the map.
- Case studies: filled circles in their series colour; the selected one gets a light ring. Exploratory point: hollow light ring. MERRA-2 grid cells: translucent rectangles. Supported area: dashed frost outline.
- Map controls, layer menu, tooltips, scale and attribution restyled to the app's dark tokens. Attribution stays visible at every width.

## Navigation

Grouped top navigation, ordered along the investigation path:

- Top level: **Home**, **Map**, **Guided demo**, **Evidence Brief**
- **Explore** menu: Trend Detective, Giovanni record (1980 to 2025), Winter-road corridor, Compare regions, Guiding questions
- **Understand** menu: Evidence and uncertainty, Methods and sources

URL paths are unchanged (`/atlas`, `/detective`, ...). Phones use the bottom tab bar (Home, Map, Trends, Evidence, Brief) plus the Streamlit menu. The sidebar holds the shared investigation controls on every view.

## Rules for new UI

- Reuse a helper above before writing new HTML. Do not add new colours.
- Never hide an interval, an evidence state or a required caveat behind an expander.
- Copy is checked by `tests/test_frostline_app.py`: no em dashes and no causal or safety language.
