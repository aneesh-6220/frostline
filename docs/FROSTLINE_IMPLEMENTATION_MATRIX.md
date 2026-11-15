# Frostline implementation matrix

Requirement to code to test traceability for `docs/FROSTLINE_NORTH_STAR.md` and `docs/APP_IMPLEMENTATION_CONTRACT.md`.
Branch `frostline-implementation`, built from `fable-ready` at `4fefedc`. Entrypoint: `UI/frostline_app.py`.

Status words: **COMPLETE** means the workflow runs and was verified by the named automated test and in a real browser (Chrome, driven end to end). **PARTIAL** and **BLOCKED** state exactly what is missing. Nothing here is marked complete on the strength of reading code.

Verification layers used below:
- **Unit and app tests**: `tests/test_frostline_app.py` (56 tests, Streamlit `AppTest` against the real `UI/data_real`), run with the 99 existing scientific tests: `python3 -I -m unittest discover -s tests` gives 155 passing.
- **Browser run**: a scripted Chrome session (Playwright, 54 checks) covering the guided demo, selection changes, every view and tab, a map-marker click, brief download, operation with map tiles blocked, and a phone viewport. All 54 passed on the final build.
- **Regeneration**: `python3 -I scripts/regenerate_all.py --check` reports a no-op (Python 3.12 with the pinned versions in `UI/requirements.txt`).

## 1. North Star features

| # | Feature | Code | Source data (`UI/data_real/`) | Implemented behaviour | Verification | Status |
|---|---|---|---|---|---|---|
| 1 | Frostline Observatory | `UI/frostline/views/observatory.py` | `season_metrics_extended.csv`, `road_record_trends_all_routes.csv`, `multiple_testing_126.csv`, `canonical_facts.json` | Hero and supporting text as specified; Begin an Investigation (opens the guided demo) and Explore the Data (opens the Trend Detective); process strip; a live NASA chart on the first screen; four indicators computed at render time | `GuidedDemo.test_home_begins_the_demo_and_reaches_a_real_chart`; browser checks "home hero", "home has chart" | COMPLETE |
| 2 | Interactive Northern Atlas | `views/atlas.py`, `registry.py` (`merra2_cell`) | `corridors.csv`, `canonical_facts.json` | PyDeck map of the two documented locations with their calculated MERRA-2 grid cells; marker click or list selects a location; context, sampling point and verification status shown; keyless CARTO background that is optional | `AtlasSync` (2 tests); browser checks "map marker click selects Dettah", "atlas without tiles" | COMPLETE for the two approved locations. The seven supplementary corridors are listed, not mapped: their coordinates are not in the approved app data |
| 3 | Question-to-variable discovery | `views/questions.py`, `registry.py` (`QUESTIONS`, `VARIABLES`) | per-winter files | Five questions mapped deterministically to catalogued variables with a reason each; full variable catalogue with identifier, units, definition, source, resolutions, valid period, locations, methods, quality condition and limitations | `Questions` (2 tests) | COMPLETE |
| 4 | Advanced Trend Detective | `views/detective.py`, `analysis.py`, `charts.py` | `season_metrics_extended.csv`, `climate_annual.csv`, `road_operations_all_routes.csv`, `multiple_testing_126.csv`, `road_record_trends_all_routes.csv`, `headline_trend_sensitivity.csv` | Per-winter series, Theil-Sen line and 95% slope band, rate per decade, both intervals, unadjusted p, q with its family for fixed windows, n, period, lag-1 flag, five evidence states, plain-language sentence, winter inspector, robustness and method tabs | `NumbersMatchApprovedOutputs` (5 tests), `AC6_*` (4), `AC8_ThawDays`, `AC10_RequiredDisplay` (2), `ExploratoryVariablesAreGated` | COMPLETE |
| 5 | Regional trend comparison | `views/compare.py`, `analysis.compare` | `season_metrics_extended.csv`, `multiple_testing_126.csv` | Same variable, matched winters, separate trends with intervals, trend of the difference series, descriptive nine-corridor panel, settings contrast | `RegionalComparison` (2 tests, against `data/processed/regional_comparison.csv`) | COMPLETE |
| 6 | Corridor investigation | `views/corridor.py`, `evidence.corridor_conclusion` | `road_operations_all_routes.csv`, `road_climate_correlations.csv`, `leakage_audit.csv`, `snow_vs_opening.csv`, `yellowknife_snow_by_season.csv` | Context and access for each road; road history in both windows; environmental record; associations labelled "association, not cause"; snow hypothesis; all-route selection-adjusted view; generated evidence conclusion | `AC11_SeparateObjects`, `AC14_FamilyAndWindow` (2), `EvidenceEngine.test_corridor_conclusions_distinguish_the_two_roads` | COMPLETE |
| 7 | Environmental and operational timeline | `views/corridor.py` (Timeline tab), `charts.timeline_chart` | `road_operations_all_routes.csv`, `season_metrics_extended.csv`, `leakage_audit.csv` | Two panels on one winter axis with separate units (no second axis); winter inspector with source and date convention; per-winter statement of whether the Oct to Dec window ended before or after the opening | `RoadSeasonAlignment` (3 tests); browser check "corridor tab Timeline" | COMPLETE |
| 8 | Frostline Evidence Engine | `evidence.py`, `views/evidence_view.py` | all files named by each dimension | Six evidence layers and seven separately judged dimensions, each with a fixed-vocabulary state and reasons generated from the data; no overall score | `EvidenceEngine` (3 tests), `AC11_SeparateObjects.test_no_combined_score_exists` | COMPLETE |
| 9 | Source disagreement and sensitivity explorer | `views/evidence_view.py`, `analysis.station_fdd`, `charts.bias_month_chart`, `charts.station_fdd_chart` | `bias_by_month.csv`, `station_fdd_by_season.csv`, `station_summary_aklavik_inuvik.csv`, `canonical_facts.json` | Monthly bias chart, matched-winter freezing degree-days, trend sensitivity on matched winters, Aklavik and Inuvik stations, plain consequences; no bias correction | `SourceDisagreement` (2 tests, against `docs/RESULTS.md`) | COMPLETE |
| 10 | Reproducible Evidence Brief | `brief.py`, `views/brief_view.py` | same objects as the screens | Self-contained HTML report with inline chart, CSV of the series and fit, JSON analysis record with file hashes, method identifier, generation time, code and data versions | `EvidenceBrief` (3 tests); browser check "brief downloaded", "brief has svg" | COMPLETE for HTML, CSV and JSON. PDF is by printing the HTML from a browser; no PDF generator is bundled |
| 11 | Guided judge demo | `views/demo.py` | production data and components | Six stages (problem, geography, NASA data, finding, transportation evidence, Evidence Brief), Back and Next, live sidebar throughout, exit into free exploration | `GuidedDemo` (3 tests); browser checks "demo stage 1" to "demo stage 6", "demo exits to detective" | COMPLETE |
| 12 | Research mode and extensibility | `registry.py`, `analysis.py`, `docs/EXTENDING_FROSTLINE.md` | `corridor_panel.csv` | Locations, variables and questions are registry entries; supplementary corridors run through the same engine, Evidence Engine and brief with no new statistical code | `Extensibility` (2 tests) | COMPLETE for the architecture. Live NASA POWER acquisition is deliberately not offered: the contract forbids network calls for data |

## 2. Contract acceptance tests (`docs/APP_IMPLEMENTATION_CONTRACT.md` section 6)

| AC | Requirement | Test | Status |
|---|---|---|---|
| AC-1 | Required files exist, have their columns, none synthetic | [repo] `test_handoff_layer.py`; also `DataLayer` (3 tests) | PASS |
| AC-2 | Missing or corrupt file gives a visible error and no numbers, no fallback | `AC2_FailureIsVisible` (3 tests) | PASS |
| AC-3 | Recomputing fixed windows reproduces stored results | [repo]; also `NumbersMatchApprovedOutputs` | PASS |
| AC-4 | Another period gives different numbers and no q | [repo]; also `AC14_FamilyAndWindow.test_finding_level_family_rules` | PASS |
| AC-5 | Fewer than 15 winters returns "not estimated" | [repo]; also `AC6.test_too_few_winters_shows_no_numbers` | PASS |
| AC-6 | Changing location and period changes numbers and labels; nothing stale | `AC6_SelectionDrivesEveryNumber` (4 tests) | PASS |
| AC-7 | `custom` not selectable, no value shown | `AC7_CustomLocation` | PASS |
| AC-8 | Thaw days show "not estimated" | [repo] data; `AC8_ThawDays` display | PASS |
| AC-9 | No prohibited phrase and no em dash in any view or export | `AC9_NoProhibitedText` (3 tests: 10 views x 2 locations, 15 variables, 6 demo stages, every brief) | PASS |
| AC-10 | n, period, units, interval, provenance on every statistic; bias caveat on every temperature figure | `AC10_RequiredDisplay` (2 tests) | PASS |
| AC-11 | Environmental and road results separate; no combined score | `AC11_SeparateObjects` (2 tests) | PASS |
| AC-12 | No 380 threshold metric, no `UI/data/` import, no `generate_data` call | `AC12_NoLegacyPaths` (2 tests) | PASS |
| AC-13 | Full suite passes and regeneration is a no-op | 155 tests pass; `--check` no-op | PASS |
| AC-14 | All-routes view shows q with its family; switching window removes it | `AC14_FamilyAndWindow` (2 tests) | PASS |

## 3. Handoff page list (`docs/FABLE_HANDOFF_FINAL.md` section 12)

| Page | Where it lives |
|---|---|
| 1 Overview map | Atlas |
| 2 Variable selector, core variables only by default | Sidebar; extended variables appear only after "Include exploratory NASA variables" |
| 3 Time series with Theil-Sen line and interval | Trend Detective |
| 4 Trend cards | Trend Detective result card and table |
| 5 Road-date view, both windows, all 17 routes | Corridor: Road history and All NWT routes |
| 6 Multiple testing | Evidence: Multiple testing (with CSV download) |
| 7 Exploratory associations and snow chart | Corridor: Associations |
| 8 Evidence audit, bias, provenance, eligibility, AI disclosure | Evidence and Methods |

## 4. Release gates

| Gate | Status | Evidence |
|---|---|---|
| 1 Working scientific foundation | DONE | 99 baseline tests and regeneration verified before any change; synthetic production path removed (`UI/northlink_app.py` is now a launcher for the real app) |
| 2 NASA challenge functionality | DONE | Features 3, 4, 5 |
| 3 Genuine user utility | DONE | Features 6, 7 |
| 4 Signature features | DONE | Features 8, 9, 10 |
| 5 Presentation-quality application | DONE | Features 1, 2, 11; screenshots in `submission/screenshots/` |
| 6 Scientific and engineering validation | DONE | 155 tests, 54 browser checks, regeneration no-op |
| 7 Deployment and submission readiness | BLOCKED on human credentials | Assets are prepared (`submission/`); pushing the branch and creating the public app need a GitHub and Streamlit login (see `submission/DEPLOYMENT.md`) |

## 5. Open items and blockers

| Item | Status | Owner |
|---|---|---|
| Public deployment URL | BLOCKED: this build machine has no GitHub credentials, so the branch could not be pushed and no hosted app could be created or verified. Steps: `submission/DEPLOYMENT.md` | Captain / Shaurya |
| Remote state | NOT VERIFIED: `git fetch` failed for the same reason. The build started from the locally cached `origin/fable-ready` (`4fefedc`); confirm nothing newer exists before merging | Captain |
| NASA listed-resource requirement | NOT DEMONSTRATED: no Giovanni extraction exists. The app states this and shows the Giovanni panel only when real ingested files are present | Cason |
| Statistical sign-off | PENDING: none recorded; the app labels every result exploratory | Yao |
| Rounding in the per-winter file | FOUND during this build: `season_metrics_extended.csv` is stored to 4 decimals, which ties two Tibbitt-Contwoyto skin-temperature winters. Recomputing that one fixed-window result (of 126) gives CI -1.41 to 1.22 and p 0.691 against the stored -1.43 to 1.23 and p 0.710; slopes agree. The app displays the stored approved value. Raising the file's precision would remove the difference | Cason / Yao |
| Aklavik access context | The app says no all-season road alternative is documented in the project's sources, pending confirmation against territorial route definitions | Cason |
| Demonstration video | NOT PRODUCED: a slide deck from real screens is provided instead (`submission/frostline_slides.html`); a 30-second shot list is in `submission/DEMO_SCRIPT.md` | Ethan / Louie |
| Legacy synthetic prototype files | `UI/data/`, `UI/generate_data.py`, `UI/standalone_prototype.html` remain in the repository because existing tests require them; the app never reads them. Removing them is a team decision | Captain |

## 6. Decisions made during implementation

1. **One statistical engine.** The app contains no estimator. `analysis.trend` calls `northlink_recompute.period_trend`; a test greps the app for any other fitting or resampling call.
2. **Stored values for fixed windows, with a live cross-check.** For an approved window the displayed numbers are the stored approved values and q comes from the stored family; a recomputation must agree first or the view stops with an error naming the file.
3. **Evidence states are derived, not typed.** Supported requires q below 0.05 in the declared family (the rule in `docs/APPROVED_FINDINGS.md`). A fixed-window result with p below 0.05 and q above it reads "Inconclusive after correction", never "supported".
4. **Per-view failure is whole-app failure for required files.** All required files are validated at start-up, which is stricter than the contract's per-view rule.
5. **Python 3.12 pin.** Under Python 3.9 with older SciPy the regeneration check rewrites files with cosmetic differences (`-0` against `0`). The pinned versions are the ones under which it is a byte-for-byte no-op.
