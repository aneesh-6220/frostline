# Brief for Fable 5.2 (implementation)

Read `docs/HANDOFF_README.md` and `docs/RESULTS.md` first. Do not invent scientific choices; everything is specified in `docs/SCIENTIFIC_METHODS.md`.

## Goal
Turn the existing Streamlit prototype in `UI/` into the final NorthLink app using REAL data. The prototype currently runs on synthetic data (`UI/data/`, banner "Provisional synthetic data").

## Data to use
`UI/data_real/` has the four CSVs in the prototype's locked schema, filled from real results: corridors (Dettah, Aklavik, custom), `climate_annual.csv` (fdd, thaw_days per winter 2001-2024, synthetic = false), `road_seasons.csv` (open_date, close_date, season_length_days, 1993-2024; note the added `close_date` column), `trends.csv` (Theil-Sen slope per decade, CI, Kendall tau, p; thaw_days has no p-value because the series is almost always zero). Richer data in `data/processed/` (season_metrics, trend_results, regional_comparison, road_climate_correlations, station_summary, station_validation).

## Required changes to the prototype
1. Point `load` at `data_real/` (or replace `UI/data/`); remove the synthetic banner and the synthetic wording in the Evidence Audit.
2. Corridors are now Dettah and Aklavik. Remove the James Bay 380 C-day threshold metric from the user journey (not valid for NWT; methods section B.5). If kept at all, label it a James Bay literature benchmark with no data.
3. Trend line and CI: use Theil-Sen with 95% CI and Mann-Kendall (the prototype uses OLS); show the sensitivity variants from `trend_results.csv` (drop first/last 5 winters).
4. Handle `thaw_days`: show "almost always zero; no trend can be estimated"; never show p = 0 or 1 for it. Handle empty p_value.
5. Plain-language cards must say "not statistically distinguishable from no change" for non-significant trends, never "no change", and must never say temperature caused a road-date trend.
6. Add the road-date view: opening day, closing day, open-to-close days trends (`trend_results.csv`, variants "road record 1993-2024"), and the exploratory Spearman table with the association-not-causation notice. Never call open-to-close "usable days".
7. Regional comparison: use `regional_comparison.csv` (difference series). Currently no difference is supported; say so.
8. Evidence audit: show coverage (24/24 winters complete, 0 missing days), the station check (NASA about 4.5 C colder than Yellowknife A in Oct-Mar, r 0.96, same trend sign), the NASA POWER source and the limitations list in HANDOFF_README.
9. Do not show absolute FDD as a local or threshold value without the cold-bias note.
10. Add tests that load `UI/data_real` and check schema, units and that no `synthetic == true` rows exist.

## Do not
Claim the tool predicts openings or ice safety; claim community validation; call POWER and MERRA-2 independent; present Aklavik's earlier-opening trend as robust (it vanishes in 2001-2024).
