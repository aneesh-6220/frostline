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
