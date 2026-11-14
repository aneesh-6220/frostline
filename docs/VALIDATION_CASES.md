# Validation cases

Run: `python3 -I -m unittest discover -s tests -v` from the repository root. Current result: **26 tests, all passing** (run 2026-11-14).

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
For Dettah (n = 32): our Theil-Sen slope for opening day is +9.00 days per decade, 95% CI 3.57 to 12.35, Mann-Kendall p = 0.0003; scipy's `kendalltau` gives p = 0.0003. Open-to-close interval: -10.24 days per decade (CI -15.83 to -5.29), p = 0.0007 for both. Closing day: -1.43 per decade (CI -4.00 to 0.00), p = 0.125 (not significant). Aklavik opening day: -6.67 per decade (CI -14.17 to 0.00), p = 0.024; interval +8.30 per decade (CI 1.67 to 15.00), p = 0.007.
(Earlier spreadsheet values used scipy's `kendalltau` p-value, which differs from the tie-corrected Mann-Kendall p by up to about 0.004. Use the tie-corrected value everywhere from now on.)

## Still required once NASA data exist
- A hand-checked FDD for one real Dettah winter: pick Oct 1 to Oct 10 daily values from the CSV, sum max(0, -T) by hand and compare with the code.
- Confirm the CSV has 92 + 90/91 records per season per location.
- Compare POWER T2M with the ECCC station on matched days (mean bias, mean absolute error) if the station file is obtained.
