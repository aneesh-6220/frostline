# Release verification (local release candidate, 2026-11-15)

Status vocabulary: **implemented** (code exists), **tested** (automated test passes here), **verified locally** (exercised in a real browser on this machine), **deployed** (public URL opened from a clean browser), **scientifically approved** (named reviewer sign-off), **externally verified** (confirmed by an organizer or source owner).

| Item | Status |
|---|---|
| Application, all ten views | implemented, tested, verified locally |
| Audit repairs F1 to F6 | implemented, tested, verified locally |
| Public deployment | NOT deployed (no URL exists) |
| Statistical sign-off | NOT approved (none recorded) |
| NASA listed-resource (Giovanni) | NOT demonstrated; fetch script implemented, not run with credentials |

## Branches and commits

- Start: `frostline-implementation` (= `main`) at `3feb9a81ada0e2e42544c2dde249ef15cbe245c2`.
- Audit branch: `frostline-global-audit` (local only, not pushed).
- `a61297d` road-finding caveats, demo scroll, atlas orientation, new regression tests, regenerated sample brief.
- `c19a36d` demo scroll helper on `st.html` (removes a deprecated API).
- `e04980b` Giovanni fetch script and eligibility note.
- Final commit: these documents and the demo-script wording (`git log -1` on the branch).

## Environment

macOS (arm64), Python 3.12.14 in `.venv312` (git-ignored), dependencies exactly as pinned in `UI/requirements.txt` (Streamlit 1.67.0, pandas 3.1.1, NumPy 2.5.4, SciPy 1.18.1, Plotly 7.1.0, PyDeck 0.9.3, openpyxl 3.1.5).

## Commands run and results

```bash
.venv312/bin/python -I -m unittest discover -s tests          # baseline: 155 tests OK; final: 164 tests OK
.venv312/bin/python -I scripts/regenerate_all.py --check      # baseline and final: "regeneration is a no-op", raw digest 029362aa0568d065
.venv312/bin/streamlit run UI/frostline_app.py --server.port 8601
```

Regeneration was run on an isolated copy of the working tree so the checkout itself was not rewritten.

## Data integrity

- `git diff 3feb9a8 -- UI/data_real data docs/RESULTS.md docs/APPROVED_FINDINGS.md docs/APP_DATA_SCHEMA.md` is empty: no approved data, raw data or generated document was changed.
- Raw checksums (`tests/raw_checksums.sha256`) pass; app data digest `7037c7be7383fe25` unchanged.
- `submission/sample_evidence_brief_dettah_opening_day.html` was regenerated with the app's own brief builder after F1.

## Running application (local)

Verified in the in-app browser at 1440x900 and 375x812: Observatory, all six demo stages forward and back (each opens at its top), Atlas with labels and marker selection, Questions, Trend Detective, Compare, Corridor, Evidence, Brief, Methods. Cold render under 1.1 s per view. No exceptions in the server log; one Streamlit session-state warning is logged once (audit F8).

## Independent scientific reproduction

See `docs/FINAL_GLOBAL_AWARD_AUDIT.md` section 4: Dettah and Aklavik road trends, NASA FDD trends and the NASA-versus-station bias reproduced from raw files with separately written code; all agree with the app.

## Commands to publish later (only with the Captain's authorization)

```bash
cd /Users/aneeshmahatekar/projects/frostline
git fetch origin
git log --oneline origin/frostline-implementation -1      # expect 3feb9a8; if it moved, merge it first and rerun the two checks
git push -u origin frostline-global-audit
gh pr create --base main --head frostline-global-audit --title "Frostline global audit: caveats, demo, atlas, Giovanni fetch script"
```

Then deploy per `submission/DEPLOYMENT.md` section 2 using branch `frostline-global-audit` (or `main` after merge), and record the URL only after opening it in a private window.

## Release candidate: map, Giovanni and live NASA POWER (2026-11-15)

Branch `frostline-map-giovanni-release` (local only; not pushed). Environment as above, plus folium 1.0.0, streamlit-folium 0.27.4 and, for verification only, h5py 3.16.0.

| Capability | Status |
|---|---|
| Giovanni files inspected, checksummed, NetCDF checked against CSV, ingested | implemented, tested |
| Giovanni record view (season and period selection, trend, uncertainty, POWER cross-check, provenance, brief/CSV/JSON export) | implemented, tested, verified locally |
| Leaflet map with Esri basemap and labels, curated markers, click-to-select exploratory points, coordinate fallback | implemented, tested, verified locally (1440x900 and 375x812) |
| Live NASA POWER retrieval, validation, caching and exploratory analysis | implemented, tested (fixtures from real cached POWER values), verified locally against the live API on 2026-11-15 |
| Public deployment | not done (needs authorization) |

Commands and results:

```bash
.venv312/bin/python -I -m unittest discover -s tests          # 198 tests OK (164 baseline + 34 new)
.venv312/bin/python -I scripts/regenerate_all.py --check      # "regeneration is a no-op", raw digest 2f4bc4f02926fbc2
.venv312/bin/python -I scripts/verify_giovanni_netcdf.py      # "NetCDF verification passed for 1 file(s)"
```

Browser check (in-app browser, http://localhost:8611): Map page clicked at an empty point, selected 62.59 N, 120.91 W; "Retrieve NASA POWER daily data" made a live request (POWER v2.10.3, 15,888 daily values, 0 missing) and showed Oct to Dec freezing degree-days -39.5 C-days per decade (95% interval -87.9 to 3.3, p = 0.061, 44 winters, exploratory) with chart, details and the three downloads. Giovanni record page rendered the 1980 to 2025 record. The approved data files in `UI/data_real/` other than the new `giovanni_*` files are unchanged.

## Final qualification (2026-11-15, branch `frostline-final-qualification`, local)

Start `fe04f73` (= `origin/frostline-map-giovanni-release`). Environment unchanged (Python 3.12.14, `.venv312`).

| Check | Result |
|---|---|
| Automated tests | 204 OK (198 baseline + 6 new in `tests/test_final_qualification.py`; no existing test modified) |
| Regeneration | `regenerate_all.py --check`: no-op; raw digest `2f4bc4f02926fbc2`; app data digest `a1f1cd6387875487` unchanged |
| NetCDF | `verify_giovanni_netcdf.py`: passed |
| Independent reproduction | `scripts/independent_verification.py` (no production imports): 7 Giovanni seasonal trends and BH q, Dettah opening day 1993-2024 (+9.00) and 2001-2024 (+10.33) all agree. JJA p differs at full precision (0.520) vs 4-decimal storage (0.526) because 2008 and 2013 tie; no verdict changes |
| Live NASA POWER, new points (app and independent curl + own code) | 66.93 N 125.31 W (map click): Oct-Dec FDD -68.1 per decade [-111.8, -19.6], p 0.002, 44 winters. 64.32 N 96.02 W (coordinate form): -51.5 [-100.8, -3.3], p 0.040. Identical in both |
| Browser (in-app, fresh server on :8612, 1440x900 and 375x812) | Landing; map click and coordinate form; live retrieval; Evidence Brief download inspected (HTTP 200, numbers match screen); Giovanni season and period changes recompute (SON 2000-2025: +0.75 [-0.12, 1.70], exploratory, matches independent code); six demo stages forward and back, no exceptions |
| Public deployment | NOT deployed |
| Statistical sign-off | NOT recorded |

Defects found and repaired: (1) a NASA POWER error for one point was shown after selecting a different point (stale session state; now point-scoped, regression test fails on old code); (2) the landing page never mentioned the map or the Giovanni record and repeated the hero chart in a card (card replaced by the full Giovanni seasonal family, workflow rows now lead with Map and Giovanni, second hero button opens the Map); (3) the phone tab bar had no Map; (4) the sidebar said "no live download" although map points download live. Guided-demo stage 4 now adds the 46-year Giovanni family (all seven tests, supported and unresolved). An attempt to silence the Streamlit session-state warning on the period slider broke slider identity in a test and was reverted; the warning is harmless.

Operational finding: a Streamlit server started at 11:17 kept serving `giovanni.py` as it was before an 11:18 edit and displayed "Exploratory window" for a full-record result. Restart the server after any code change before presenting.

### Competitiveness against the five judging criteria (honest assessment)

| Criterion | Demonstrable strength | Evidence | Strongest weakness | Fixable today? | Highest-leverage action |
|---|---|---|---|---|---|
| Impact | Compresses a multi-step NASA-data workflow into one reproducible investigation for any northern point | Live POWER journey, Evidence Brief | No users, no stakeholder contact; impact is argued, not shown | No | Say it plainly; describe the teacher/analyst use case concretely, never claim adoption |
| Creativity | Evidence-integrity layer (families, leakage audit, station disagreement, no overall score) beside real road records | Evidence page, Observatory cards | Trend tools exist (Giovanni, KNMI); the statistics are standard | Partly | Lead with "how sure, and what it can't tell you", not with "we fit a trend" |
| Validity | Unusually strong: byte-for-byte regeneration, 204 tests, independent reproduction, conservative families | This section | No external statistical sign-off; single grid cell for Giovanni | Partly (Yao) | Get even an informal sign-off from Yao before judging |
| Relevance | Matches the brief closely (choose variable/region, time series, rate, Mann-Kendall, CI) and uses Giovanni, a listed resource | Giovanni record view | Only T2M for live points; challenge imagines a variable picker | No | Show the variable selector on Trend Detective in Q&A; be explicit that only validated variables are offered |
| Presentation | Clear story; real data; honest uncertainty | `docs/FROSTLINE_JUDGE_PRESENTATION_STRATEGY.md` | Eleven pages and dense text; no public URL yet | Yes (URL), partly (rehearsal) | Deploy now; rehearse the 3-minute path twice |

Overall: strong for local judging. For Global Nomination it is credible on validity and relevance; a Global Award is a long shot unless the public URL works, the Giovanni use is accepted by organizers, and the presentation lands the "how sure" message in under a minute.
