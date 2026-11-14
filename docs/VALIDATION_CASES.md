# Validation cases

Run: `python3 -I -m unittest discover -s tests -v` from the repository root. The current pass count is recorded in `docs/FABLE_HANDOFF_FINAL.md` from the run at delivery; the acceptance tests in `tests/test_scientific_acceptance.py` are described at the end of this file.

| # | Required check | Test | Expected |
|---|---|---|---|
| 1 | 10 days at -10 C give 100 C-days FDD | `test_ten_days_minus10_is_100` | 100.0 |
| 2 | 10 days at +5 C give 0 | `test_ten_days_plus5_is_0` | 0.0 |
| 3 | Missing dates trigger exclusion | `test_missing_day_gives_nan_not_zero`, `test_nan_value_not_valid`, `test_sentinel_invalid`, `test_duplicate_date_flagged` | NaN, coverage flagged, 91 of 92 valid |
| 4 | Leap years | `test_expected_days_and_leap`, `test_leap_year_midwinter` | Jan to Mar 90 or 91; full 182 or 183 |
| 5 | December opening and April closing in the correct winter | `test_season_assignment`, `test_dec_open_april_close` | 2023-12-24 and 2024-04-09 are winter 2023; open day 84, close day 191, interval 107 |
| 6 | Constant series gives zero slope, test undefined | `test_constant_series` | slope 0, p NaN, status constant_series |
| 7 | Known positive/negative trends | `test_positive_linear`, `test_negative_linear` | +20 and -5 per decade, tau +1 and -1 |
| 8 | Units | Kelvin test; slopes are per decade by construction | 263.15 K = -10 C |
| 9 | Only complete seasons used | `test_nan_dropped_before_fit` | n reduced by 1, slope unchanged |
| 10 | Tie handling in Mann-Kendall | `test_mann_kendall_ties` | z = 3/sqrt(120/18) |
| 11 | Mann-Kendall hand check | `test_mann_kendall_hand_check` | S = 45, Var = 125, z = 44/sqrt(125) |
| 12 | Regional comparison uses difference series | `test_diff_series_zero_when_identical` | constant series |

## Hand-checked example using real observations (road records)
Dettah 2024/25 (NWT workbook): opened 2024-12-21, closed 2025-04-08. Hand count: Dec 21 to Dec 31 = 10 days, plus Jan 31, Feb 28, Mar 31, plus 8 days to Apr 8 = 10 + 31 + 28 + 31 + 8 = 108 days. The workbook "Days" value is 108. Test: `test_dettah_2024_hand_check`. Open day relative to Oct 1 = 31 + 30 + 20 = 81.

## Cross-check of the trend code against independent code
For Dettah (n = 32, road record 1993-2024) our Theil-Sen slope for opening day is +9.00 days per decade, 95% CI 3.57 to 12.35. The Mann-Kendall p-value uses the tie-corrected variance (the earlier spreadsheet values used scipy's `kendalltau` p, which differs by up to about 0.004). Current values for every trend are in `docs/RESULTS.md`; they are regenerated, not typed.

## Real-data checks (done)
- Hand-checked FDD: Dettah Oct 1-10 2001 daily T2M = 4.85, 4.75, -1.13, -1.78, 0.5, 3.31, 4.45, 1.08, 1.4, 1.57; only -1.13 and -1.78 are below zero, so FDD = 1.13 + 1.78 = 2.91 C-days (`tests/test_real_data.py`).
- All 24 winters at both locations have 92 + 90/91 records and no duplicates (same test file; also `season_audit.csv`).
- Monthly POWER file equals the mean of the daily file (max difference 0.005 C, 138 months).
- Station comparison: `docs/RESULTS.md` section 1 and `docs/TEMPERATURE_BIAS_DIAGNOSIS.md` (seasonal cold bias, monthly means -3.4 to -7.3 C in Oct-Dec).

## Acceptance and regression tests (`tests/test_scientific_acceptance.py`)
Raw data checksums stay fixed; `validate_dates` rejects the Tibbitt 2023 and 2024 rows; Benjamini-Hochberg and Holm known values; the `mostly_tied` guard; leakage-free windows end before the outcome in every winter; the 126-test family reproduces (126 tests, 0 at q < 0.05); no pooled tests exist; `docs/RESULTS.md` equals the generator output; prohibited phrases are absent from docs and UI data; legacy synthetic UI data is flagged and `UI/data_real` is not synthetic and contains no 380 C-day metric.
