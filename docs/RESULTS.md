# Results (first full run, 2026-11-14)

Produced by `python3 -I scripts/run_analysis.py` from real NASA POWER daily data (24 complete winters, 2001/02 to 2024/25, both locations, zero missing days) and the NWT road records. Yao has NOT yet signed these off. All p-values are unadjusted (about 14 temperature tests were run; with a Bonferroni threshold of 0.05/14 = 0.004, nothing below passes except road-date trends). Full tables: `data/processed/trend_results.csv`, `regional_comparison.csv`, `road_climate_correlations.csv`, `station_summary.csv`.

## 1. NASA temperature trends (per decade, Theil-Sen, 95% CI, Mann-Kendall p, n = 24)
| Metric | Dettah (Yellowknife Bay) | Aklavik (Mackenzie Delta) |
|---|---|---|
| Oct-Dec mean temperature (C) | -0.25 (-1.26 to +1.23), p 0.64 | +0.78 (-0.07 to +1.81), p 0.078 |
| Jan-Mar mean temperature (C) | +0.24 (-1.45 to +1.36), p 0.67 | +1.19 (-0.28 to +3.08), p 0.12 |
| Full-season mean (C) | +0.03 (-0.99 to +0.99), p 0.94 | +0.91 (-0.01 to +1.84), p 0.056 |
| Oct-Dec FDD (C-days) | +15 (-108 to +111), p 0.79 | -74 (-150 to +6), p 0.087 |
| FDD to a fixed date before the earliest opening* | -16 (-82 to +56), p 0.64 | -108 (-158 to -23), p 0.008 (exploratory; not significant after multiple-test adjustment) |
| Jan-Mar thaw days | 1 thaw day in 24 winters (undefined trend) | 0 in 24 winters (constant series) |
*Dettah Oct 1 to Nov 28; Aklavik Oct 1 to Dec 2.
Sensitivity (drop first 5 or last 5 winters, OLS) is in `trend_results.csv`; for Dettah Oct-Dec mean the sign flips between variants, which means there is no robust trend.

## 2. Regional comparison (Dettah minus Aklavik, difference-series trend)
No difference is statistically supported: Oct-Dec FDD +82 C-days per decade (CI -26 to +191, p 0.14); Oct-Dec mean -0.78 C per decade (CI -2.07 to +0.36, p 0.19). We cannot say the two locations are trending differently.

## 3. Road-date trends
| Road | Window | Opening day | Closing day | Open-to-close days |
|---|---|---|---|---|
| Dettah | 1993-2024 (n 32) | +9.0 d/decade (3.6 to 12.4), p < 0.001 | -1.4 (-4.0 to 0.0), p 0.125 | -10.2 (-15.8 to -5.3), p 0.001 |
| Dettah | 2001-2024 (n 24) | +10.3 (3.3 to 17.2), p 0.002 | -2.5 (-7.1 to +0.8), p 0.095 | -15.0 (-23.6 to -6.0), p 0.001 |
| Aklavik | 1993-2024 (n 32) | -6.7 (-14.2 to 0.0), p 0.024 | +0.8 (-1.3 to +3.3), p 0.48 | +8.3 (1.7 to 15.0), p 0.007 |
| Aklavik | 2001-2024 (n 24) | -0.5 (-10.8 to +3.8), p 0.69 | -1.1 (-5.0 to +2.3), p 0.44 | +1.6 (-4.4 to +10.0), p 0.43 |
Dettah's later openings are robust to the window. Aklavik's earlier openings are not (they vanish in 2001-2024), so call that result fragile.

## 4. Climate vs road dates (Spearman, exploratory, n = 24, association only)
All weak and not significant: Dettah Oct-Dec FDD vs opening day rho -0.13 (p 0.55); FDD to Nov 28 rho -0.18 (p 0.40); Mar 15 to Apr 15 mean temperature vs closing day rho -0.34 (p 0.10, warmer springs trend toward earlier closing, not significant). Aklavik: rho -0.29 (p 0.17), -0.19 (p 0.38), closing 0.03 (p 0.90).

## 5. Station check (Yellowknife A, ECCC, 8,574 matched days)
- NASA POWER daily T2M is **colder than the station**: mean bias -2.3 C over all days and **-4.5 C in Oct-Mar**; MAE 3.0 C (all) and 4.7 C (Oct-Mar); correlation 0.987 (all) and 0.958 (Oct-Mar). Same bias before and after the station ID change in 2013 (-2.25 vs -2.26 C).
- Oct-Dec FDD: NASA is about 1,600 C-days, the station about 1,050 (bias about +492 C-days; 17 winters with complete station data).
- Trends agree in sign and are both flat: Oct-Dec FDD trend +14 (NASA) vs +1.5 (station) C-days per decade on the same 17 winters (station p 0.97).
- Station Jan-Mar thaw days: 7 in about 24 winters, so the thaw-day metric carries almost no information at this location.
**What to say on the website:** NASA absolute temperatures here are biased cold, so absolute FDD values must not be compared with thresholds or described as local station temperatures. Trends and year-to-year variation track the station closely. Never apply the 380 C-day James Bay benchmark to NASA FDD.

## 6. Plain-language summary
1. Over 2001 to 2024 the NASA temperature metrics show no statistically supported trend at Dettah, and only weak, uncertain warming signals at Aklavik.
2. Dettah's ice road nevertheless opened later (about 9 to 10 days per decade) and its open-to-close interval shortened. The temperature metrics we computed do not explain this, so the honest statement is: the cause is untested; snow cover, ice thickness, overflow, construction and decisions are candidates (reported by news sources).
3. The data are a short record from large grid cells with a cold bias; non-significant is not proof of no change.
