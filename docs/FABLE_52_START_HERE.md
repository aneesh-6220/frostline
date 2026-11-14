# Frostline by Strongest Soldiers: Fable 5.2 start here

*Trace the evidence behind changing winters.*

## 0. Who and what (read first)
- The public product is **Frostline**. The team is **Strongest Soldiers**. Public branding is "Frostline - by Strongest Soldiers". [legacy-name note] The earlier names (NorthLink for the product, Asterfen for the team) must never appear in anything a user or judge sees. Technical file names that still contain `northlink` (`UI/northlink_app.py`, `scripts/northlink_metrics.py`, `scripts/northlink_stats.py`, `scripts/northlink_recompute.py`) are preserved on purpose so imports, tests and the regeneration pipeline keep working; renaming them is optional and only safe if every import, test and doc is updated together.
- **`docs/FROSTLINE_NORTH_STAR.md` is the authoritative product specification** and your primary execution instruction. Build the **complete Frostline application**, not a demo. The Guided Demo must be a path through the real production components and real `UI/data_real/` data, never a separate mockup.
- **Scientific methods and generated results remain the source of numerical truth** (`docs/SCIENTIFIC_METHODS.md`, `docs/APPROVED_FINDINGS.md`, `docs/RESULTS.md`, `UI/data_real/`). The North Star does not authorize inventing or changing any scientific finding. Preserve all validated scientific outputs.
- Ownership: **Fable (with Shaurya) owns the application**; **Cason owns Giovanni acquisition**; **Yao owns scientific sign-off**. Fable must implement the outstanding app-level acceptance tests (`docs/APP_IMPLEMENTATION_CONTRACT.md` section 6: AC-1, AC-3, AC-4, AC-5, AC-8 data side and AC-13 already exist as repo tests; the rows marked "app" - AC-2, AC-6, AC-7, AC-9 to AC-12, AC-14 and the display side of AC-8 - still have to be written).
- Do not assume NASA-resource eligibility, deployment or human scientific validation is complete. As of this commit none of the three is: the Giovanni extraction has not been done, no app URL exists, and no statistician sign-off is recorded.

Read this file first. It points to the authoritative files; it does not restate or change the science. Where a detail lives elsewhere, follow the link and do not copy it from memory. Event: NASA Space Apps Halifax, Nov 14-15 2026. **Official NASA deadline:** project page submission closes Nov 15 2026, 11:59 PM local time. **Locally provided (Halifax organizer, not an official NASA deadline):** local judging Sun Nov 15 at 3 PM Atlantic, presentation intent due 2 PM.

## 1. Objective and challenge
Frostline is an **Earth-system trend detective** for winter-road conditions in northern Canada, not an ice-road safety predictor. Challenge: "Be An Earth System Trend Detective!" (https://www.spaceappschallenge.org/2026/challenges/earth-system-trend-detective/). The challenge asks for a tool where a user picks variables, a region and a period, sees the time series, and gets a rate of change with a significance test (Mann-Kendall, confidence intervals) and an honest statement of what is and is not supported. Details and eligibility: `docs/CHALLENGE_ELIGIBILITY.md`.

## 2. Verified repository state
- Scientific base: branch `remediation-final`, commit `a8675ec2e9a0965d98dbdee3c96aa219f75b6416` (all of it is contained in this branch's history).
- This branch (`fable-ready`) adds the final handoff layer, the Frostline North Star and the rebrand. Its head is the commit you checked out: run `git rev-parse HEAD` and quote that when reporting. Create `frostline-implementation` from it; do not commit to `fable-ready` directly.
- `main` is unchanged (0520097) and no implementation branch existed when this branch was cut.
- Verify before starting: `python3 -I -m unittest discover -s tests` must pass and `python3 -I scripts/regenerate_all.py --check` must say "regeneration is a no-op".

## 3. Authoritative data (read-only for the app)
Everything the app reads is in `UI/data_real/` (20 CSV files plus `canonical_facts.json`; the North Star's "twenty files" counts the CSVs only); the file list, columns and dtypes are in `docs/APP_DATA_SCHEMA.md` (generated). Raw sources are in `data/raw/` and are never modified (`tests/raw_checksums.sha256`). Machine-readable headline numbers and the required bias caveat are in `UI/data_real/canonical_facts.json`.

## 4. Source-of-truth files (precedence)
1. `docs/SCIENTIFIC_METHODS.md`: methods, seasons, metrics, claim rules (the science).
2. `docs/FABLE_HANDOFF_FINAL.md`: scope, pages, prohibitions, interpretation wording.
3. `docs/APP_IMPLEMENTATION_CONTRACT.md`: data rules, period recomputation, acceptance tests.
4. `docs/APPROVED_FINDINGS.md` (generated) and `docs/RESULTS.md` (generated): the numbers. Never type a number by hand.
5. `docs/ROUTE_IDENTITY.md`, `docs/TEMPERATURE_BIAS_DIAGNOSIS.md`, `docs/REFERENCES.md`, `docs/DATA_DICTIONARY.md`, `docs/CHALLENGE_ELIGIBILITY.md`.
`docs/FABLE_BRIEF.md` and `docs/HANDOFF_README.md` are SUPERSEDED stubs. Do not use older chat summaries.

## 5. Approved metrics and locations
Locations: `dettah_bay` (primary, Dettah Ice Road, 6.5 km lake crossing) and `aklavik_delta` (comparison, Aklavik Ice Road, delta road, ambiguous length); seven supplementary corridors marked approximate; `custom` is unsupported. Winter y = Oct 1 y to Mar 31 y+1. NASA daily data 2001-10-01 to 2025-06-30 (24 winters 2001/02 to 2024/25); road record 1993/94 to 2024/25 (544 route-winter rows: 512 verified, 24 missing, 4 not applicable, 4 flagged; see `APPROVED_FINDINGS.md` section 0). Metrics: Oct-Dec FDD and mean temperature, Jan-Mar mean temperature, thaw days (no trend), opening day, closing day, open-to-close interval. Formulas: `SCIENTIFIC_METHODS.md`.

## 6. Required app behaviour and pages
The 8 pages in `FABLE_HANDOFF_FINAL.md` section 12, built to `APP_IMPLEMENTATION_CONTRACT.md`. Essentials: location, metric and period selectors; statistics that always match the selection (fixed-window results only for their own window, otherwise recomputed with `scripts/northlink_recompute.py`); n, period, units, intervals and provenance on every result; the bias caveat beside every temperature figure; environmental and road trends kept separate; visible failure when data are missing.

## 7. Approved user-facing claims
Use `docs/APPROVED_FINDINGS.md` sections A to E and the wording templates in `FABLE_HANDOFF_FINAL.md` section 13. In short: Dettah's opening date has moved later over 1993-2024 in the government record (exploratory, selection-adjusted, fragile in the 2001-2024 window); NASA climate trends are not distinguishable from no change in 24 winters; NASA POWER runs colder than the Yellowknife station; a snow association is a hypothesis. Every statement carries its interval, window and exploratory label.

## 8. Prohibited
Section F of `APPROVED_FINDINGS.md` and section 0 of `FABLE_HANDOFF_FINAL.md`. Never: road-safety statements or predictions; causal claims; pooled significance tests; invented or changed statistics; synthetic values shown as real (`UI/data/` and `UI/generate_data.py` are a synthetic prototype); fallback to synthetic data; the 380 C-day metric; claims of Giovanni extraction, eligibility confirmation, endorsements, adoption or statistician sign-off that have not happened.

## 9. Preserve
`scripts/` (pipeline, `northlink_metrics.py`, `northlink_stats.py`, `northlink_recompute.py`), `tests/` (all must stay green), `data/raw/` (unchanged), generated docs and data (change only by running the generators). Do not edit generated files by hand.

## 10. Commands
```
python3 -I scripts/regenerate_all.py            # rebuild every derived file from cached raw data; no network
python3 -I scripts/regenerate_all.py --check    # after a commit: fails if committed outputs differ
python3 -I -m unittest discover -s tests -v     # scientific, data and contract tests
pip install -r UI/requirements.txt
streamlit run UI/northlink_app.py   # LEGACY synthetic prototype; the real Frostline entrypoint does not exist yet
```
The legacy entrypoint `UI/northlink_app.py` reads synthetic `UI/data/` and must not be shown as real. The production Frostline entrypoint is yours to create and then record here and in the submission draft (do not invent a path in advance). `UI/requirements.txt` currently lists only streamlit, pandas, altair and numpy; the North Star needs Plotly, PyDeck and SciPy (SciPy is already used by `scripts/`), so add and pin them when you build.
Reproducibility proven here is from **cached** sources, not a live re-download.

## 11. Suggested order
1. Run the two verification commands above. 2. Build a data layer that loads `UI/data_real/` with the failure rules of the contract (AC-1, AC-2). 3. Add `northlink_recompute` calls and the selection-matches-statistics logic (AC-3 to AC-6). 4. Build the pages in `FABLE_HANDOFF_FINAL.md` section 12 in this order: trend explorer (Dettah, Aklavik), road dates, evidence and bias, multiple testing, exploratory associations, overview map. 5. Delete the 380 C-day metric and any import of `UI/data/`; remove the synthetic banner only then. 6. Add the app-level acceptance tests (contract section 6). 7. Add the AI-use disclosure and citations from `docs/REFERENCES.md`. 8. Deploy and fill the links in `submission/SUBMISSION_DRAFT.md`.

## 12. Deployment
A public URL that works without credentials, loads only `UI/data_real/`, and fails visibly if data are absent. Streamlit Community Cloud, Render or Vercel are acceptable. Set the main file to the Frostline entrypoint you create and point the dependency file at `UI/requirements.txt` (pinned). The GitHub repository stays **private**; on Streamlit Community Cloud a private repo can be deployed, but the app itself must then be set to publicly viewable so judges can open it without logging in. No deployment URL exists yet; record one in the submission draft only after you have opened it from a clean private browser window. The default investigation must not need a live NASA API call.

## 13. Acceptance
All items AC-1 to AC-14 in the contract pass; the full test suite passes; the app displays no prohibited claim; every number on screen can be traced to a file in `UI/data_real/`.

## 14. Known blockers and owners
| Blocker | Owner |
|---|---|
| Giovanni MERRA-2 extraction (Earthdata login); NASA-resource requirement NOT demonstrated until done | Cason (steps in `CHALLENGE_ELIGIBILITY.md`) |
| Statistical sign-off on methods and corrections (none recorded) | Yao |
| Ask an organizer whether POWER counts; read the Project Submission Guide | Ethan (with Captain) |
| Confirm 4 flagged road rows with GNWT, or keep them excluded | Cason |
| Aklavik alignment, segment and representativeness unverified; Dettah Jan 28/29 2024 date discrepancy | Cason |
| Cause of the NASA cold bias unknown | open (report as unknown) |
| Repoint/rebuild app, delete 380 metric, app-level tests, deploy, fill links | Shaurya with Fable |
| UI quality pass, presentation checks | Louie |

## 15. Avoiding conflicts
Work on your own branch from `fable-ready`; never force-push or rewrite `main`, `remediation-final` or `fable-ready`; do not edit `data/raw/`, `docs/RESULTS.md`, `docs/APPROVED_FINDINGS.md`, `docs/APP_DATA_SCHEMA.md` or `UI/data_real/` by hand (regenerate them). Claim files before editing shared ones (`UI/northlink_app.py` is yours; the science and data files are not). If a conflict arises in a generated file, take either side and rerun `python3 -I scripts/regenerate_all.py`. Open a pull request to `main` only after the Captain approves.
