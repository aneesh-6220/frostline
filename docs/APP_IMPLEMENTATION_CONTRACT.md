# App implementation contract

Binding rules for any application built on this repository. If this file conflicts with `docs/SCIENTIFIC_METHODS.md` (science) or `docs/FABLE_HANDOFF_FINAL.md` (scope), those win and this file is wrong; report it. Column-level schemas are generated in `docs/APP_DATA_SCHEMA.md` from the real files, so they cannot drift.

## 1. Data the app may consume
- **Only** files in `UI/data_real/` (listed with columns and dtypes in `docs/APP_DATA_SCHEMA.md`). `UI/data/` and `UI/generate_data.py` are a synthetic prototype and must not be read by the public app.
- Required files must exist at start-up and contain no row with `synthetic == True`. If any required file is missing, unreadable, has a missing required column, or has a true `synthetic` value, the app must show a visible error naming the file and stop that view. It must **not** fall back to other data, cached demo values, or generated numbers.
- Optional files (`giovanni_*`) exist only if a real Giovanni extraction was ingested (`docs/CHALLENGE_ELIGIBILITY.md`). When absent the panel is hidden, with no placeholder numbers.
- The app makes no network call for data and never writes into `UI/data_real/`. Regenerate with `python3 -I scripts/regenerate_all.py`.

## 2. Supported locations
| `corridor_id` / `location_id` | Role | Notes |
|---|---|---|
| `dettah_bay` | Primary. Road `dettah` | 62.43 N, -114.34 W, calculated midpoint of a 6.5 km lake crossing. Climate 2001-2024; road dates 1993-2024. |
| `aklavik_delta` | Comparison. Road `aklavik` | 68.29 N, -134.37 W, straight-line midpoint of Aklavik and Inuvik. Road length and segment ambiguous. Label "different setting", never "replication". |
| seven supplementary corridors | Exploratory | Ids in `corridor_panel.csv`. Approximate team-chosen points; label "approximate location". Only the precomputed 2001-2024 results and the per-winter rows are available. |
| `custom` (row in `corridors.csv`) | NOT supported | No data exist for an arbitrary point. Remove it from the selector, or show "no data for this location". Never generate values for it. |

Location names come from `corridors.csv`. The `kind` column means data class, not verified identity.

## 3. Supported metrics
Environmental (NASA POWER daily T2M and companions, reanalysis, 24 winters 2001/02 to 2024/25): Oct-Dec mean temperature, Jan-Mar mean temperature, Oct-Dec FDD, Mar 15 to Apr 15 mean daily max, and (exploratory tab only) the other extended variables in `season_metrics_extended.csv`. Jan-Mar thaw days are shown as counts per winter but have **no trend** ("not estimated").
Road operations (NWT Table 108): opening day, closing day, open-to-close interval (days since Oct 1; the interval is not usable days).
Not supported and never to be added: ice thickness, safety or usability scores, any prediction, any threshold test (the 380 C-day metric in the legacy app is to be deleted), monthly-data-based FDD.

## 4. Statistics must match the selection
1. Statistics shown must always correspond to the exact location, metric and period displayed. A fixed-window result is never shown for a different window.
2. **Precomputed** results (`trends.csv`, `extended_trends.csv`, `multiple_testing_126.csv`, `road_record_trends_all_routes.csv`, `corridor_panel.csv`) may be shown only when the user's selection equals that result's window: climate 2001-2024; road dates either 2001-2024 (`multiple_testing_126.csv`, `extended_trends.csv`) or 1993-2024 (`road_record_trends_all_routes.csv`). Show the window next to the number.
3. For any other window the app recomputes from the per-winter rows with the approved functions: use `scripts/northlink_recompute.py` (`period_trend`, `climate_series`, `road_series`), which calls `northlink_metrics.trend` (Theil-Sen, Mann-Kendall) and `northlink_stats.block_bootstrap_slope` (seed 20261114). Do not write a different method (no OLS headline, no new test, no smoothing, no bias correction).
4. Windows with fewer than 15 winters return "too few seasons: not estimated", with no slope, CI or p. A `mostly_tied` or `constant_series` status is shown as "not estimated" with the reason.
5. **Adjusted significance (BH q, Holm) belongs only to the fixed families and windows** in `hypothesis_families.csv`. For a user-selected window show the unadjusted p labelled "exploratory, not adjusted for multiple testing" and hide q. Never recompute q for a window the family did not contain.
6. Changing the location, metric, period, or road must recompute or re-lookup every number, interval, sample size and sentence on screen. No number may persist from the previous selection.
7. The text sentence next to a result is chosen from the computed status: "Not statistically distinguishable from no change in this record. That is not proof of no change." or the supported-in-family wording in `FABLE_HANDOFF_FINAL.md` section 13. It must be regenerated from the computed values, never typed per example.
8. Environmental trends and road-operations trends are separate objects: separate sections or cards, separate titles, never combined into one index, score or single "trend" number. An exploratory page may show them side by side only if labelled "association, not cause".

## 4a. Required display on every result
Sample size n (winters), period in winter labels ("2001/02 to 2024/25"; winter y = Oct 1 y to Mar 31 y+1), units, 95% interval (Theil-Sen and block bootstrap), unadjusted p, q only if allowed, status, data source and provenance (NASA POWER daily T2M, MERRA-2 reanalysis; ECCC station; NWT Bureau of Statistics Table 108), and the bias caveat from `canonical_facts.json` (`bias_caveat`) next to every temperature figure. Citations and the POWER acknowledgement from `docs/REFERENCES.md` go on the evidence page. Provide a visible link or text for the AI-use disclosure.

## 5. Prohibited in the interface
Road-safety statements or predictions; causal wording ("caused by", "due to warming", "because", "explains"); synthetic or placeholder values; unlabelled reanalysis temperatures presented as local observations; "usable days"; pooled significance tests; images generated by AI used as evidence; naming individual people.

## 6. Acceptance tests (the app is not done until all pass)
Data-layer tests that already exist in this repository are marked [repo]; the rest must be added by the implementer (stack-neutral; for Streamlit use `streamlit.testing.v1.AppTest`, for a web build use Playwright).

| # | Test | Where |
|---|---|---|
| AC-1 | Every required file in `docs/APP_DATA_SCHEMA.md` exists, has the listed columns, and has no `synthetic == True` | [repo] `tests/test_handoff_layer.py` |
| AC-2 | Deleting or corrupting a required file makes the app show a visible error and render no numbers for that view (no fallback) | app |
| AC-3 | Recomputing the fixed windows from per-winter rows reproduces the stored results (Dettah FDD 2001-2024; Dettah opening day 1993-2024 and 2001-2024) | [repo] |
| AC-4 | A different period (e.g. 2005-2024) gives different numbers from the stored window and returns no q | [repo] |
| AC-5 | Fewer than 15 winters returns "not estimated" with no slope or p | [repo] |
| AC-6 | In the app, changing location and period changes the displayed numbers and window labels; no stale value remains | app |
| AC-7 | `custom` is not selectable with data, and no value is displayed for it | app |
| AC-8 | Thaw days show "not estimated", never a slope or p | [repo] data, app for display |
| AC-9 | Rendered text of every page contains none of the prohibited phrases (see `tests/test_scientific_acceptance.py` list) and no em dash | app |
| AC-10 | Every displayed statistic has n, period, units, interval, provenance; every temperature figure carries the bias caveat | app |
| AC-11 | Environmental and road results are in separate components; no combined score exists | app |
| AC-12 | No `380` threshold metric, no `UI/data/` import, no `generate_data` call in the public app | app (grep test) |
| AC-13 | `python3 -I -m unittest discover -s tests` passes and `python3 -I scripts/regenerate_all.py --check` is a no-op | [repo] |
| AC-14 | Switching to the 51-test all-routes view shows q with the family name; switching window removes q | app |

## 7. Changing this contract
Any change to a statistical rule needs a named reviewer (Yao for statistics) and an update to `docs/SCIENTIFIC_METHODS.md` first. Document changes in the same commit as the code.
