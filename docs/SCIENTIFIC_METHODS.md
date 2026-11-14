# Scientific methods (what must be calculated)

Reference implementation: `scripts/northlink_metrics.py`. Known-answer tests: `tests/test_metrics.py` (see VALIDATION_CASES.md).
Status: specification written by the data team. Yao must still review and sign off before results are presented.

## A. Season definitions
- Winter y (`season_start_year = y`) is Oct 1 of y to Mar 31 of y+1.
- Early winter: Oct 1 to Dec 31 of y (always 92 days).
- Midwinter: Jan 1 to Mar 31 of y+1 (90 days, or 91 if y+1 is a leap year).
- Full season: 182 days, or 183 if y+1 is a leap year. Dates are calendar dates as provided by the product (see DATA_SOURCES.md for the time-standard note).
- Road dates: an opening or closing date in Oct to Dec belongs to the winter that started that year; Jan to Sep belongs to the winter that started the previous October (`season_start_year_from_date`).

## B. Metrics (one value per winter per location; NaN if the season is incomplete)
1. **FDD (Oct to Dec)** = sum over days of max(0, -T_daily_mean_C). Units degree-C days.
2. **Thaw days (Jan to Mar)** = count of days with T_daily_mean_C > 0 (0.0 exactly is NOT a thaw day). Units days. Secondary: longest run of consecutive thaw days.
3. **Seasonal mean temperature** for Oct to Dec, Jan to Mar and the full season. Units degree-C.
4. **Road metrics** (verified dates only): opening day = days since Oct 1 of the season start; closing day likewise; open-to-close interval = closing date minus opening date in days. The interval is **not** usable days.
5. **380 degree-C day benchmark: do not compute.** It is a published James Bay (Ontario) result. It is not a general NWT or Dettah threshold, not a safety threshold, and not an ice thickness measure.

## C. Trend analysis (applied to every metric above)
- Null hypothesis H0: there is no monotonic trend in the metric over the winters. Alternative H1 (two-sided): there is a monotonic trend.
- Estimator: **Theil-Sen** slope against season_start_year. Report per decade (slope x 10) with a 95% confidence interval (scipy `theilslopes`, alpha 0.95 on the slope; multiply the bounds by 10).
- Test: **Mann-Kendall** with tie correction and continuity correction (formula in `mann_kendall`). Report tau, z and the two-sided p-value.
- Serial correlation: report the lag-1 autocorrelation of the Theil-Sen residuals. If its magnitude exceeds 0.3, flag the p-value as "possibly optimistic; autocorrelation present" on the website. (With 24 to 32 points the estimate is noisy; the flag is a warning, not a correction. A prewhitening or block-bootstrap sensitivity run is an optional extra.)
- Completeness: a season enters a trend only if its coverage is complete (see DATA_QUALITY.md). At least **15** complete seasons are required; otherwise report "too few seasons".
- Ties: handled by the tie correction in the variance. A constant series gives slope 0, and the test is reported as **undefined**, never as p = 1.
- Sensitivity (report all three alongside the main result): (a) drop the first 5 winters; (b) drop the last 5 winters; (c) a second estimator, ordinary least squares slope, shown only as a comparison. If the sign or significance changes, say so.
- Multiple testing: we compute several metrics for 2 locations. Show raw p-values and state plainly that they are unadjusted; mark as "headline" only the pre-registered pair in section E.
- Wording rule: a nonsignificant result means "no trend detected in this record", never "no change". A significant result means "evidence of a monotonic trend in this record", never "caused by climate change".

## D. Regional comparison (Dettah vs Aklavik)
- Use only the winters that are complete at both locations.
- Compare slopes using the **difference series** d_y = metric_Dettah(y) - metric_Aklavik(y): compute Theil-Sen and Mann-Kendall on d_y (`difference_series_trend`). A non-zero slope in d_y means the locations are diverging.
- One significant trend and one non-significant trend do NOT mean the slopes differ. Say "different" only if the difference-series trend itself is significant, and give its confidence interval.
- Do not compare road-date trends of two roads as if they were one experiment: different road types, different built-up processes.

## E. Road-operation relationships (exploratory)
Valid comparisons (pre-defined; run nothing else and report all of these even if not significant):
1. Dettah: FDD (Oct to Dec, same winter) vs opening day. Use only as a retrospective association. October to December FDD includes days after a December opening, so it must NOT be presented as a prospective predictor of opening. A preferable robust variant is FDD accumulated from Oct 1 up to a fixed date before the earliest opening in the record (Dettah's earliest opening in the record is 1995-11-29, so use Oct 1 to Nov 28; Aklavik's is 2014-12-03, so use Oct 1 to Dec 2). Report both.
2. Dettah: seasonal mean temperature Mar to May vs closing day needs daily data from April and May, which are NOT in the Oct to Mar requirement. If April data are obtained, compute mean temperature for Mar 15 to Apr 15 vs closing day. Otherwise report "not computed".
3. Aklavik: the same two comparisons, using its own fixed cut-off date.
Method: Spearman rank correlation (n, rho, p) and, if useful, a simple Theil-Sen regression of the date on the metric. Report n and the 95% CI of the slope.
Invalid comparisons (must not be shown): Jan to Mar thaw days vs opening date (the thaw occurs after the opening, so it cannot influence it); any "predicted opening date" or any safety statement; any claim that a temperature trend caused a road-date trend.
Always show: association is not causation; roads also depend on snowfall (insulation), overflow, ice thickness, construction, equipment, maintenance and administrative decisions.

## F. Pre-registered headline results (decide now, before looking at NASA data)
H1: Dettah Oct to Dec mean temperature trend. H2: Dettah Oct to Dec FDD trend. H3: Dettah opening day trend (already computed from the road records alone: +9.0 days per decade). All other results are labelled exploratory.

## G. Monthly fallback (only if daily data cannot be obtained)
The team brief earlier asked for monthly data. The handoff requires daily. If only monthly means (for example Giovanni MERRA-2 monthly T2M) are available, compute only these and label them "monthly-mean based, approximate":
- Oct to Dec mean temperature, Jan to Mar mean temperature, Mar to May mean temperature (using monthly values).
- Approximate FDD = sum over months of max(0, -monthly mean) x days in month. This underestimates true FDD because it ignores within-month variation (a month with mean +0.5 degrees can still have freezing days). Never mix it with true daily FDD in one series.
- Thaw-day counts and benchmark timing cannot be computed from monthly data.

## H. Output units and rounding
Temperatures degree-C; FDD degree-C days; slopes "per decade" in the metric's own unit (degree-C per decade, degree-C days per decade, days per decade); p-values to 3 decimals ("< 0.001" if smaller). Keep full precision in files; round only for display.
