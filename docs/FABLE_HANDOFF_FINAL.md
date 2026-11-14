# NorthLink: final implementation handoff for Fable 5.2

This is the single authoritative implementation specification. Anything in another file that contradicts it is outdated (`docs/FABLE_BRIEF.md` and `docs/HANDOFF_README.md` are marked SUPERSEDED).
Branch with all remediation work: `remediation-final` (see delivery notes at the end). Event: NASA Space Apps 2026 Halifax, local judging Sun 2026-11-15, 3 PM.

## 0. Prohibited (read first)
You must NOT:
1. **Invent scientific results**: every number shown must come from a file in `data/processed/` or `UI/data_real/` or from `docs/RESULTS.md` (generated). No hand-typed figures, no placeholder figures, no "typical" values.
2. **Make unapproved statistical choices**: no OLS trend lines as the main estimate, no new tests, windows, transformations, detrending, smoothing, bias corrections or different significance thresholds. Use Theil-Sen, Mann-Kendall, the stored block-bootstrap CI and the stored q-values. New analysis needs a named human approver and a rerun of `scripts/regenerate_all.py` plus the tests.
3. **Treat synthetic UI data as real**: `UI/data/` and `UI/generate_data.py` are synthetic (every row `synthetic=true`). The public app must read only `UI/data_real/` and must fail loudly (not fall back) if a file is missing or any `synthetic` value is true.
4. **Present road-safety or opening-date predictions**, "safe/unsafe", "usable days", ice thickness, or a threshold test. Delete the "Date of 380 C-day threshold (James Bay benchmark)" metric and its text in `UI/northlink_app.py` (lines near 377 to 398 and 817); it is a James Bay literature result, not an NWT threshold, and the prototype's wording calls it a safety criterion.
5. **Reintroduce invalid pooled significance tests** across corridors or winters (`pooled_anomaly_correlations.csv` was removed because shared weather makes p-values optimistic).
6. **Claim causality** from observational associations: never "caused by", "due to warming", "climate-caused", "snow explains", "temperature cannot explain". Use the wording in section 13.
7. **Reintroduce outdated or contradicted documentation**: do not copy text from superseded files, earlier chat summaries or the pre-remediation `RESULTS.md` (it contained a Bonferroni statement of 14 tests, pooled p-values and leaky windows).
Also: do not edit anything under `data/raw/`; do not re-run the Planetary Computer script without approval; do not name individual people in the app.

## 1. Repository structure (actual)
```
README.md
data/raw/        nasa/ (POWER daily T2M+PRECTOTCORR for 2 sites; 9 corridor extended files; monthly file), roads/ (NWT Table 108 xlsx), weather_stations/ (ECCC)
data/processed/  derived CSVs (section 3) and diagnostics/
docs/            SCIENTIFIC_METHODS.md (rules), RESULTS.md (generated numbers), TEMPERATURE_BIAS_DIAGNOSIS.md, ROUTE_IDENTITY.md,
                 CHALLENGE_ELIGIBILITY.md, DATA_*.md, GEOGRAPHIC_SCOPE.md, REFERENCES.md, RESEARCH_EVIDENCE.md, VALIDATION_CASES.md, this file
scripts/         build_*.py, run_analysis.py, run_extended_analysis.py, run_remediation_analysis.py, diagnose_temperature_bias.py,
                 build_ui_data_real.py, generate_results_md.py, regenerate_all.py, northlink_metrics.py, northlink_stats.py
tests/           test_metrics.py, test_pipeline.py, test_real_data.py, test_scientific_acceptance.py, raw_checksums.sha256
UI/              northlink_app.py (legacy prototype), data/ (SYNTHETIC), data_real/ (real, regenerated), generate_data.py, requirements.txt
```

## 2. Approved raw data (never modify; checksums in `tests/raw_checksums.sha256`)
NASA POWER daily files downloaded 2026-11-14; NWT Table 108 workbook; ECCC bulk daily CSVs. Provenance and required acknowledgement: `docs/REFERENCES.md`, `docs/DATA_SOURCES.md`.

## 3. Processed data and schemas
Data dictionary: `docs/DATA_DICTIONARY.md`. The files the app needs are in `UI/data_real/`: `corridors.csv`, `climate_annual.csv` (fdd, thaw_days per winter), `road_seasons.csv` (open_date, close_date, `season_length_days` = interval, not usable days), `trends.csv` (with caveat text), `extended_trends.csv`, `multiple_testing_126.csv`, `road_record_trends_all_routes.csv`, `hypothesis_families.csv`, `corridor_panel.csv`, `snow_vs_opening.csv`, `snow_trends.csv`, `yellowknife_snow_by_season.csv`, `station_summary_aklavik_inuvik.csv`. All are produced by `scripts/build_ui_data_real.py`; do not edit them by hand. `trends.csv` has empty `p_value`, `slope`, `ci` cells for thaw days (status mostly_tied or constant): render "not estimated", never 0 or 1.

## 4. Route and location definitions
Primary: Dettah Ice Road, road_id `dettah`, point `dettah_bay` (62.43 N, -114.34 W). Comparison: Aklavik Ice Road, `aklavik_delta` (68.29 N, -134.37 W). Seven further corridors are supplementary with approximate coordinates (label "approximate"). Route identity, length ambiguity (Aklavik), the point-versus-road limitation and press-source status: `docs/ROUTE_IDENTITY.md`. The two roads are different objects (6.5 km lake crossing vs a delta road of about 112 to 117 km); present them as a "different settings" contrast, not replication.

## 5. Periods and seasons
NASA daily: 2001-10-01 to 2025-06-30; trend winters 2001/02 to 2024/25 (n = 24). Road record: 1993/94 to 2024/25 (n up to 32). Winter y = Oct 1 y to Mar 31 y+1. Extension of POWER before 2001 was not done (`SCIENTIFIC_METHODS.md` K).

## 6. Metrics and formulas
`docs/SCIENTIFIC_METHODS.md` sections A and B (FDD, thaw days, means, leakage-free window metrics, road day numbers, interval).

## 7. Statistical methods and limitations
Theil-Sen per decade, Mann-Kendall (tie-corrected), moving-block-bootstrap CI, lag-1 flag, BH and Holm in defined families, leakage-free predictors, `mostly_tied` guard: `SCIENTIFIC_METHODS.md` C to H. Limits: 24 winters, large grid cell, cold bias, dependent tests, exploratory.

## 8. Approved findings that may appear publicly (numbers from `docs/RESULTS.md`)
Show each with its interval, p unadjusted, q and the word "exploratory".
1. **Dettah ice road opened later.** Opening day trend +9.0 days per decade (95% CI 3.6 to 12.4), 1993-2024, n = 32; all-route family q = 0.002. Open-to-close interval -10.2 days per decade (CI -15.8 to -5.3), q = 0.004. These survive correction across 17 routes. In 2001-2024 (n = 24) the opening trend is +10.3 (CI 3.3 to 17.2) with q = 0.085 in the 126-test family, and it is fragile to dropping the first five winters (the Theil-Sen interval then touches zero; the block-bootstrap interval does not). Closing-day trend is not distinguishable from no change.
2. **No NASA climate trend survives correction.** Of 126 trend tests, 20 have p < 0.05 (about 6 expected by chance), none has q < 0.05; none of the 99 climate tests does. Dettah Oct-Dec mean temperature -0.25 C per decade (CI -1.26 to 1.23), FDD +15 (CI -108 to 111): not distinguishable from no change in this 24-winter record, which is not proof of no change.
3. **Road dates change in many NWT routes with mixed signs** (`RESULTS.md` section 4), so no single regional signal.
4. **NASA POWER is colder than the Yellowknife A station**, by month (`RESULTS.md` section 1; -3.4 to -7.3 C in Oct-Dec means). Year-to-year FDD tracks the station (r about 0.92). Absolute NASA values must not be used as local conditions.
5. **Leakage matters**: older Oct-Dec windows overlapped Dettah opening dates in 16 of 24 winters; leak-free climate predictors show no association with opening or closing day (all CIs include zero).
6. **Snow (exploratory hypothesis only)**: Yellowknife snow-on-ground on Nov 28 is positively associated with Dettah opening day (Spearman +0.64, CI 0.39 to 0.85, n = 23, q = 0.005 in a 5-test family), but the snow series has no detectable trend (+4.0 cm per decade, CI -1.7 to 8.7), so this is not an explanation of the opening trend and not evidence of a cause.

## 9. Exploratory, invalid or unsupported
- Exploratory (label so): everything above; Dettah results are selection-biased because Dettah was chosen after its road trend was seen; the 9-corridor panel; the extended variables.
- Invalid (must not appear): pooled corridor correlations; Jan-Mar thaw-day trends (not estimable); leaky-window correlations (including the old Dettah closing rho -0.34 and the old "FDD vs opening" pairs); Bonferroni "0.05/14"; the 380 C-day threshold on NASA data; any prediction.
- Unsupported: any cause of the road-date trends; warming as explanation of Dettah; Aklavik's 1993-2024 earlier-opening trend as robust (absent in 2001-2024); Aklavik/Dettah as one experiment; usable days.

## 10. Provenance and citations
`docs/REFERENCES.md`. The POWER acknowledgement text and the MERRA-2 reference (Gelaro et al. 2017) must appear in the app's evidence page. Cite only what that file lists.

## 11. Known data limitations
NASA values are MERRA-2 reanalysis for a 0.5 x 0.625 degree cell (not observations; seasonal cold bias, cause unproven); one cell is not the whole road; POWER and MERRA-2 not independent; Aklavik representativeness unverified; two Tibbitt rows and two other rows flagged and excluded; opening for Dettah is for light vehicles first; temporary closures unrecorded; Dettah has an all-season alternative road; POWER not extended before 2001; MODIS and Giovanni not obtained.

## 12. Required application pages
1. Overview map with Dettah and Aklavik highlighted (CARTO keyless basemap is fine) and supplementary corridors marked approximate.
2. Variable selector limited to: Oct-Dec mean temperature, Oct-Dec FDD, Jan-Mar mean temperature, road opening day, closing day, open-to-close interval (and the extended variables only on an "exploratory" tab). No threshold metric.
3. Time-series chart with the Theil-Sen line and 95% interval (not OLS), per-winter points, and a legend note that NASA values are reanalysis.
4. Trend cards: slope per decade, CI (Theil-Sen and block-bootstrap), Mann-Kendall p unadjusted, q with its family, lag-1 flag, status text from section 13.
5. Road-date view for Dettah and Aklavik (1993-2024 and 2001-2024), plus the "all 17 routes" selection-adjusted table.
6. Multiple-testing page: 126 tests, 20 nominal, 0 at q < 0.05; link to the CSV.
7. Exploratory associations page: leak-free table and the snow chart labelled "hypothesis, not a cause".
8. Evidence audit: coverage (24 of 24 winters complete, 0 missing days), station bias table and chart, provenance, limitations, NASA eligibility status, **AI-use disclosure** (see 17).

## 13. User-facing interpretation rules
Use these templates; do not paraphrase into stronger claims.
- Non-significant: "Not statistically distinguishable from no change in this record. That is not proof of no change."
- Supported-in-family: "Evidence of a monotonic change in this record (q = X within the stated family). Exploratory; this does not show what caused it."
- Every temperature: "NASA POWER T2M is MERRA-2 reanalysis for a 0.5 x 0.625 degree cell. At the Yellowknife cell it is on average 3.4 to 7.3 C colder than the airport station in Oct-Dec (2001-2025)."
- Road dates: "Opening and closing dates are government records of operations, not measurements of ice thickness. The interval is not usable days."
- Never: predict, rank safety, or say "because".

## 14. Scientific acceptance tests
`python3 -I -m unittest discover -s tests -v`. `tests/test_scientific_acceptance.py` checks raw checksums, the road-date validator, BH and Holm known values, the `mostly_tied` guard, leakage-free windows, the 126 and 51-test families, absence of pooled tests, bias figures, `RESULTS.md` equal to its generator, prohibited phrases, legacy UI containment. Add a UI test that loads `UI/data_real`, checks schema and that no `synthetic` value is true, and that no 380 metric exists in the app.

## 15. Commands
```
python3 -I scripts/regenerate_all.py            # rebuild all derived files from cached raw data, no network
python3 -I scripts/regenerate_all.py --check    # fail if committed outputs differ
python3 -I -m unittest discover -s tests -v
cd UI && pip install -r requirements.txt && streamlit run northlink_app.py   # after repointing the loader to data_real/
```

## 16. Deployment and integration
`UI/northlink_app.py` was deliberately **not edited** (possible concurrent work by Fable or Shaurya). Integration: work on a branch from `remediation-final` (or merge it into main first). If `UI/data_real/*` conflicts, take either side and rerun `scripts/build_ui_data_real.py`. If `docs/RESULTS.md` conflicts, rerun `scripts/generate_results_md.py`. The loader currently reads relative `data/*.csv`; change it to `data_real/` and the schema additions above, then remove the synthetic banner (only then). Keep the app free of network calls for data.

## 17. NASA eligibility status
`docs/CHALLENGE_ELIGIBILITY.md`. No required dataset found; POWER is not on the Resources list but T2M is a MERRA-2 model variable; plausible, not confirmed by an organizer. Giovanni extraction UNVERIFIED (needs an Earthdata login). Fit risk: the brief describes a general variable-and-region tool; NorthLink is a case study. AI use is allowed and must be described in the submission: this repository's code and documents were produced with AI assistance.

## 18. Unresolved issues requiring human approval
1. Statistical sign-off by a named reviewer (none has reviewed the methods).
2. Confirm the two flagged Tibbitt rows and the Fort Good Hope 1994 and Peel River 2006 rows with GNWT, or keep excluded.
3. Decide whether to extend POWER to 1993/94 (needs a live re-download and a verification step).
4. Giovanni cross-check, if a team member has an Earthdata login.
5. Confirm organizer acceptance of POWER (ask at the local event) and read the Project Submission Guide.
6. Cause of the NASA cold bias (not established); verification of the Aklavik alignment.
7. Repoint and test the UI; remove the 380 C-day metric.
