# Scientific methods and claim rules (authoritative specification)

This is the single authoritative specification. If another file disagrees with it, this file wins and the other file is a bug.
Implementation: `scripts/northlink_metrics.py`, `scripts/northlink_stats.py`, `scripts/run_*.py`. Numbers: `docs/RESULTS.md` (generated). Known-answer tests: `tests/`.
Status: **exploratory analysis, not signed off by a domain statistician.** Nothing was preregistered (see section F).

## A. Season definitions
- Winter y (`season_start_year = y`) is Oct 1 of y to Mar 31 of y+1. Early winter: Oct 1 to Dec 31 (92 days). Midwinter: Jan 1 to Mar 31 (90 days, 91 if y+1 is a leap year). Full season: 182 days (183 if y+1 is a leap year).
- Road dates: an opening or closing date in Oct to Dec belongs to the winter that started that year; Jan to Sep belongs to the winter that started the previous October.
- Day numbers (`open_day`, `close_day`) count days since Oct 1 of the season start year. In leap-year winters the same calendar date has a day number one larger after Feb 28. This is a known small artefact (at most 1 day) and is not corrected.
- NASA POWER dates are the calendar day as provided; the header states "in LST". ECCC dates are local standard days. A sub-day offset cannot be tested with daily data (see `TEMPERATURE_BIAS_DIAGNOSIS.md`, H1).

## B. Metrics (one value per winter per location; NaN if the season is incomplete)
1. **FDD (Oct to Dec)** = sum of max(0, -T_daily_mean) over Oct 1 to Dec 31. Degree-C days.
2. **Thaw days (Jan to Mar)** = days with T_daily_mean > 0 (exactly 0.0 is not a thaw day). In the NASA series this is zero in 23 of 24 winters at Dettah and in all 24 at Aklavik, so it carries almost no information, and NASA under-detects thaw relative to the station (0.05 versus 0.32 days per winter at Yellowknife A).
3. **Seasonal mean temperature** (Oct to Dec, Jan to Mar, full season).
4. **Pre-cutoff window metrics** (leakage-free predictors, section H): FDD and mean temperature from Oct 1 to the day before the earliest calendar opening in the full 1993-2024 road record (Dettah Nov 28, Aklavik Dec 2); mean temperature Mar 15 to the day before the earliest calendar closing (Dettah Apr 6, Aklavik Apr 15).
5. **Road metrics** (verified rows only): `open_day`, `close_day`, `open_to_close_days`. The interval is **not** usable days; temporary closures are not recorded, and "open" for Dettah means open to light vehicles first.
6. **380 degree-C day benchmark: not computed.** It is a James Bay (Ontario) result from Hori et al. (see `REFERENCES.md`), not an NWT, Dettah or safety threshold.

## C. Trend analysis
- Question: is there a monotonic change in the metric over the winters, and how large is it? H0: no monotonic trend (two-sided).
- Estimator: Theil-Sen slope against season_start_year, reported per decade, with the scipy 95% interval. Test: Mann-Kendall with tie correction (`mann_kendall`). Reported with tau, z, p.
- **Block-bootstrap interval** (`northlink_stats.block_bootstrap_slope`): moving blocks of length ceil(n^(1/3)), 2000 resamples, seed 20261114, percentile 95% interval. Reported next to the Theil-Sen interval because the Theil-Sen interval assumes independence.
- Serial correlation: lag-1 autocorrelation of Theil-Sen residuals; |r| > 0.3 sets `autocorr_flag`, which means the Mann-Kendall p-value may be optimistic. With 24 to 32 points the estimate is noisy; the flag is a warning, not a correction.
- Completeness: a season enters a trend only with complete coverage (`DATA_QUALITY.md`). At least 15 seasons are required; otherwise status `too_few`.
- Ties: constant series return status `constant_series` with no p-value. **Mostly tied series** (one value in at least 75% of seasons, `MOSTLY_TIED_FRACTION`) return status `mostly_tied` with no slope, CI or p, because a Theil-Sen slope of 0 with a degenerate interval would be reported as a finding. This applies to Dettah Jan-Mar thaw days.
- Sensitivity variants stored in `trend_results.csv` and `headline_trend_sensitivity.csv`: drop first 5 winters, drop last 5, drop the 2023 and 2024 winters (late 2023 opening), OLS slope as comparison only.
- Wording: "no trend detected in this record" is not "no change". "Evidence of a monotonic trend in this record" is not "caused by climate change".

## D. Comparison of the two NASA cells
Difference series d_y = metric(Dettah cell) - metric(Aklavik cell), complete winters in both; Theil-Sen and Mann-Kendall on d_y (`regional_comparison.csv`). One significant and one non-significant trend do not imply different slopes. This compares climate series of two grid cells; it is not a comparison of road conditions (the roads are different objects, `ROUTE_IDENTITY.md`).

## E. Associations between climate predictors and road dates (exploratory)
Spearman rank correlation with a moving-block bootstrap interval (`block_bootstrap_spearman`). Only leakage-free pairs are computed (section H). Invalid and not computed: Jan-Mar thaw days versus opening; any predicted opening date; any safety statement. Association is not causation; roads also depend on snow insulation, overflow, ice thickness, construction, equipment and administrative decisions.

## F. Hypotheses, preregistration and selection
- **Nothing was preregistered.** An earlier draft called H1 to H3 "pre-registered"; that was wrong. The Dettah road-date trend (later opening) was computed from the road records before the climate analysis and before Dettah was fixed as the primary route, so Dettah's road-date result is **selection-biased** and every Dettah finding is exploratory.
- Selection adjustment: the same trend tests are run for every NWT route with at least 15 verified winters (51 tests) and corrected across all of them (family F4). Dettah is reported with its q-value from that family.

## G. Multiplicity
Families are defined in `data/processed/hypothesis_families.csv` (F1 all 126 extended trend tests; F2 climate only; F3 road dates 2001-2024; F4 all-route road record; F5 leak-free associations). Benjamini-Hochberg q within the family named, Holm across F1 and F4. `p` is always labelled unadjusted. There is no pooled test across corridors: corridors share weather and operators, so pooled p-values would treat dependent winters as independent (pseudo-replication) and were removed.

## H. Leakage control
A predictor window must end before the earliest possible outcome. `analysis_windows.csv` fixes each window end at the day before the earliest calendar opening (closing) in the full verified 1993-2024 record, so it cannot overlap the outcome in any winter. `leakage_audit.csv` counts how often the older windows (Oct 1 to Dec 31 for opening; Mar 15 to Apr 15 for closing) reached the outcome date. Snow-on-ground on Dec 1 is leak-free only within the 2001-2024 sample (earliest opening in the full record is Nov 29) and is marked so.

## I. NASA temperature bias
NASA POWER T2M is MERRA-2 reanalysis for a 0.5 x 0.625 degree cell, not a station observation. At the Yellowknife cell it is colder than the station by about 3.4 to 7.3 C in Oct-Dec (monthly means). Consequences enforced here: absolute NASA FDD, mean temperature and thaw counts are never presented as local conditions, safety indicators or thresholds; trends and year-to-year variation are presented with intervals and the caveat (`TEMPERATURE_BIAS_DIAGNOSIS.md`). No bias correction is applied to any reported result.

## J. Claim rules (used by the website and the pitch)
Allowed: statements of the form "the Theil-Sen slope for X is S per decade (95% CI a to b; p unadjusted, q adjusted within family F); exploratory."
Required with every temperature figure: "NASA POWER T2M is MERRA-2 reanalysis for a 0.5 x 0.625 degree cell. At the Yellowknife cell it is on average 3.4 to 7.3 C colder than the airport station in Oct-Dec (2001-2025)."
Prohibited (and tested for in `tests/test_scientific_acceptance.py`):
- "preregistered" or "pre-registered" for any result; "causes", "caused by", "climate-caused", "because of warming" for any trend;
- "temperature cannot explain", "snow explains", "snow causes", or "no relationship" for a non-significant result;
- NASA temperature presented as ice thickness, road safety, road condition or a predictor of opening dates;
- usable days, predicted opening, safe or unsafe statements;
- any pooled significance test across corridors;
- the 380 C-day benchmark applied to NWT data or labelled as a result;
- synthetic data labelled or used as real.

## K. Reproducibility levels
1. **Cached-source reproducibility (verified):** `python3 -I scripts/regenerate_all.py` rebuilds every derived file from `data/raw/` without network access; `--check` fails if any committed output differs.
2. **Live verification (not done):** re-downloading POWER (versions can change), the NWT workbook, or the ECCC files and comparing byte for byte. POWER documents that its data may be replaced with improved versions, so a future download may differ. The Giovanni (MERRA-2) cross-extraction is UNVERIFIED (`CHALLENGE_ELIGIBILITY.md`).
3. The POWER record was **not** extended earlier than 2001-10-01. The extra winters (1993/94 to 2000/01) would raise n from 24 to 32, but the decision was not to add data without a verification step that this environment cannot perform (the shell cannot reach NASA) and because mixing a re-downloaded record with the cached one would break the cached-source guarantee.

## L. Units and rounding
Degree-C; FDD in degree-C days; slopes per decade in the metric's unit; p-values to 3 decimals ("<0.001" if smaller). Full precision in files; round only for display.
