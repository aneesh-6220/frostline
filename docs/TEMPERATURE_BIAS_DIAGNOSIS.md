# NASA POWER T2M vs ECCC Yellowknife A: bias diagnosis

Reproduce: `python3 -I scripts/diagnose_temperature_bias.py` (writes `data/processed/diagnostics/`, read-only on raw data).
Compared series: POWER daily `T2M` at the Dettah/Yellowknife grid cell (62.43 N, -114.34 W) vs ECCC Yellowknife A daily mean (station IDs 1706 to 2012 and 51058 from 2013; 9,066 station rows, no duplicate dates), 8,574 paired days with a station mean, 2001-10-01 to 2025-06-30. Bias = NASA minus station.

## Result

| Hypothesis | Test | Outcome |
|---|---|---|
| H1 date or time-of-day shift | NASA shifted by -2..+2 days | Rejected. Lag 0 has the lowest RMSE (4.20 C vs 5.35 at +1, 5.65 at -1) and the highest correlation (0.987). The mean bias does not change with lag. |
| H2 different daily-mean definition | station mean vs (Tmax+Tmin)/2; NASA T2M vs (T2M_MAX+T2M_MIN)/2 | Not the cause. ECCC mean equals (Tmax+Tmin)/2 to within 0.035 C. NASA T2M is only +0.25 C warmer than its own midrange. Both versions are about 2.3 to 2.5 C colder than the station. |
| H3 one-sided (Tmax only or Tmin only) | bias of each | Both are cold. Tmax -3.2 C, Tmin -1.8 C overall. In Nov: Tmax -7.8, Tmin -7.2. In summer Tmax is still cold (about -1.2) and Tmin is warm (about +1.4). |
| H4 dependence on how cold the day is | bias vs station temperature | In Oct to Mar the relation is weak (slope 0.024 C per C, R2 0.006, n=4,340); the winter bias is roughly -4 to -5.5 C across the range from -35 C to 0 C. The all-year slope (0.12) is a seasonal effect, not a cold-day effect. |
| H5 era / drift | station 1706 vs 51058 eras; slope of winter-mean bias | No drift detected. Nov bias is -7.37 (2001-12) vs -7.15 (2013-25). Theil-Sen drift per decade: Oct-Dec +0.06 (95% CI -0.38 to 0.58), Jan-Mar -0.30 (-0.66 to 0.09). |
| H6 unit or sign error | | Rejected by H1 to H5: not a constant offset, not a sign flip, seasonal. |
| H7 duplicated or padded station rows | de-duplicated by date | No duplicate dates among IDs 1706 and 51058. |
| H8 elevation mismatch | POWER cell-average elevation (204.71 m, from the POWER file header) vs station elevation (205.7 m, ECCC record) | Rejected as a cause. The difference is about 1 m, which at a lapse rate of order 6.5 C per km is about 0.01 C, far below a 3 to 7 C bias. Surface-height handling inside the reanalysis is not testable here. |
| H9 sub-day time offset (POWER "LST" vs ECCC local standard day) | not testable with daily means | Not tested. Lags of +-1 and +-2 days (H1) are worse than lag 0; a shift of a few hours cannot produce a seasonal bias that is zero in summer. |

### The bias is strongly seasonal

| Month | Jan | Feb | Mar | Apr | May | Jun | Jul | Aug | Sep | Oct | Nov | Dec |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Mean bias (C) | -5.08 | -3.95 | -1.71 | -0.61 | +0.65 | +0.62 | +0.42 | +0.13 | -0.68 | -3.42 | -7.26 | -5.89 |

Oct, Nov and Dec reproduce the earlier audit figures (-3.4, -7.3, -5.9). Overall -2.26 C; Oct-Dec -5.50 C; Jan-Mar -3.57 C. 5th to 95th percentile of the daily bias is -9.1 to +2.4 C. The 25 largest daily differences (up to -18.6 C) are all Nov-Dec days; see `data/processed/diagnostics/worst_days.csv`.

## Cause

**Not established.** The data exclude a time shift, a mean-definition difference, a unit error, and a drift or station-change artefact. They do not identify the physical cause. Candidate explanations that this repository cannot test: a 0.5 x 0.625 degree reanalysis cell that is largely Great Slave Lake and the surrounding Shield versus a single land point station; elevation or surface-height handling in POWER; how MERRA-2 represents lake ice and snow during freeze-up; near-surface inversions. None of these may be stated as a finding.

## Effect on the analysis metrics (winters complete in both series)

| Quantity | NASA | Station | Note |
|---|---|---|---|
| Mean Oct-Dec FDD, 17 winters | 1,551 C-days | 1,059 C-days | NASA is +492 C-days (+46.5%) |
| Interannual correlation of Oct-Dec FDD | Pearson 0.918, Spearman 0.909 | | year-to-year variation is tracked well |
| Oct-Dec FDD Theil-Sen slope, same 17 winters | +14.0 C-d/decade (95% CI -134 to +148) | +1.5 (-157 to +167) | neither distinguishable from zero |
| Slope of (NASA - station) FDD | +12.4 C-d/decade (-43 to +86) | | difference in trend not distinguishable from zero |
| Jan-Mar thaw days (T>0), mean | 0.05 | 0.32 | NASA under-counts; Spearman 0.36 over 19 winters |
| Winters with any thaw day | 1 of 24 (NASA) | 5 of 19 complete station winters | |

Sensitivity (in-sample, monthly offsets estimated from this same station, not a publishable correction): after removing monthly mean offsets the NASA mean FDD is 1,088 vs 1,059 and the number of NASA winters with a thaw day goes from 1 to 8 of 24. The FDD slope on all 24 winters is +14.6 (raw) vs +16.5 (adjusted) C-days/decade, both with 95% CIs spanning zero.

Station completeness limits the check: only 17 winters have a complete Oct-Dec station record and 19 a complete Jan-Mar record (no gap filling).

## Allowed and prohibited use

Allowed:
- Interannual variation and relative change of NASA-derived FDD (the series tracks the station at r about 0.92). Trend estimates are exploratory and interpreted with their CIs.
- Stating that T2M is MERRA-2 reanalysis, not an observation.

Not allowed:
- Treating NASA FDD, mean temperature, or thaw-day counts as absolute local conditions or as ice-thickness or road-safety indicators.
- Using the NASA thaw-day count as a proxy for real thaw events (it misses most of them because of the cold bias; zero NASA thaw days does not mean zero thaw days).
- Claiming a physical cause for the bias.
- Quoting an offset-corrected NASA series as an observation.

Any figure or UI text that shows NASA temperature must carry the statement: "NASA POWER T2M is MERRA-2 reanalysis for a 0.5 x 0.625 degree cell. At the Yellowknife cell it is on average 3.4 to 7.3 C colder than the airport station in Oct-Dec (2001-2025)."
