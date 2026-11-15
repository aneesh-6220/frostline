"""Required application data files and columns.

Written from the approved files in UI/data_real at the fable-ready handoff commit (4fefedc) and kept in step with
the generated docs/APP_DATA_SCHEMA.md by tests/test_frostline_app.py. A file or column missing from the data
directory is a hard error in the app (docs/APP_IMPLEMENTATION_CONTRACT.md section 1): there is no fallback.
"""

REQUIRED_JSON = ('canonical_facts.json',)

REQUIRED_COLUMNS = {
    'bias_by_month.csv': ('month', 'n', 'mean_bias', 'median_bias', 'sd', 'bias_tmax', 'bias_tmin', 'station_mean_t'),
    'climate_annual.csv': ('corridor_id', 'season_year', 'metric', 'value', 'n_days', 'missing_days', 'synthetic'),
    'corridor_panel.csv': ('location_id', 'road_id', 'road_kind', 'mean_octdec_c_slope_per_dec', 'mean_octdec_c_p', 'fdd_octdec_slope_per_dec', 'fdd_octdec_p', 'open_day_slope_per_dec', 'open_day_p', 'close_day_slope_per_dec', 'close_day_p', 'open_to_close_days_slope_per_dec', 'open_to_close_days_p', 'n_road_seasons'),
    'corridors.csv': ('corridor_id', 'name', 'kind', 'lat', 'lon', 'has_road_records'),
    'extended_trends.csv': ('location_id', 'road_kind', 'metric', 'window', 'n', 'slope_per_decade', 'ci95_low', 'ci95_high', 'mk_p', 'lag1', 'status'),
    'headline_trend_sensitivity.csv': ('road_id', 'metric', 'variant', 'n', 'theil_sen_per_decade', 'ts_ci95_low', 'ts_ci95_high', 'mk_p_unadjusted', 'bb_ci95_low', 'bb_ci95_high', 'ols_per_decade', 'ols_p_unadjusted', 'lag1_resid', 'lag1_flag'),
    'hypothesis_families.csv': ('family_id', 'n_tests', 'definition', 'correction', 'role'),
    'leakage_audit.csv': ('location_id', 'road_id', 'predictor_window', 'outcome', 'n_winters', 'n_winters_window_reaches_outcome', 'fraction_leaky', 'verdict'),
    'multiple_testing_126.csv': ('location_id', 'road_kind', 'metric', 'family_type', 'window', 'n', 'slope_per_decade', 'ci95_low', 'ci95_high', 'bb_ci95_low', 'bb_ci95_high', 'bb_block_len', 'p_unadjusted', 'q_bh_all126', 'q_bh_within_family', 'holm_all126', 'lag1', 'autocorr_flag', 'ci_excludes_zero_theilsen', 'ci_excludes_zero_blockboot', 'modal_fraction', 'status', 'status_exploratory'),
    'road_climate_correlations.csv': ('location_id', 'climate_metric', 'road_metric', 'predictor_window', 'spearman_rho', 'ci95_low', 'ci95_high', 'ci_method', 'p_unadjusted', 'n', 'note', 'q_bh_family'),
    'road_operations_all_routes.csv': ('road_id', 'season_start_year', 'opening_date', 'closing_date', 'record_status', 'source_url', 'road_type', 'road_name', 'source_sheet', 'record_note'),
    'road_record_trends_all_routes.csv': ('road_id', 'road_name', 'road_type', 'metric', 'n_seasons', 'first_year', 'last_year', 'slope_per_decade', 'ci95_low', 'ci95_high', 'bb_ci95_low', 'bb_ci95_high', 'p_unadjusted', 'lag1', 'status', 'q_bh_all_routes', 'holm_all_routes', 'rank_by_p_within_metric', 'ci_excludes_zero_blockboot'),
    'road_seasons.csv': ('corridor_id', 'season_year', 'open_date', 'close_date', 'season_length_days', 'synthetic'),
    'season_metrics_extended.csv': ('location_id', 'road_id', 'road_kind', 'season_start_year', 'fdd_octdec', 'mean_octdec_c', 'mean_janmar_c', 'tmax_mean_mar15_apr15_c', 'skin_temp_mean_octdec_c', 'precip_octdec_mm', 'precip_oct_nov_mm', 'wind_mean_octdec_ms', 'rh_mean_octdec_pct', 'lw_down_mean_octdec', 'sw_down_mean_mar15_apr15', 'lw_down_mean_mar15_apr15', 'mean_mar15_apr15_c', 'open_day', 'close_day', 'open_to_close_days'),
    'snow_trends.csv': ('series', 'n', 'slope_per_decade', 'ci95_low', 'ci95_high', 'bb_ci95_low', 'bb_ci95_high', 'p_unadjusted', 'status'),
    'snow_vs_opening.csv': ('predictor', 'predictor_window', 'outcome', 'n', 'spearman_rho', 'ci95_low', 'ci95_high', 'ci_method', 'p_unadjusted', 'leak_free_vs_full_1993_2024_record', 'leak_free_in_2001_2024_sample', 'source', 'q_bh_family', 'bonferroni_5'),
    'station_fdd_by_season.csv': ('season_start_year', 'fdd_nasa', 'fdd_station'),
    'station_summary_aklavik_inuvik.csv': ('station_id', 'station', 'n_days', 'bias_all_c', 'mae_all_c', 'r_all', 'bias_octmar_c', 'mae_octmar_c', 'r_octmar'),
    'trends.csv': ('corridor_id', 'metric', 'slope_per_decade', 'ci_low', 'ci_high', 'n_seasons', 'kendall_tau', 'p_value', 'plain_takeaway', 'synthetic'),
    'yellowknife_snow_by_season.csv': ('season_start_year', 'snowfall_octdec_cm', 'snowfall_oct1_nov28_cm', 'sog_mean_nov1_28_cm', 'sog_nov28_cm', 'sog_dec1_cm', 'open_day', 'precip_octdec_mm', 'fdd_octdec'),
}

# Present only after a real Giovanni extraction has been ingested (scripts/ingest_giovanni_monthly.py).
OPTIONAL_FILES = ('giovanni_monthly_t2m_seasonal.csv', 'giovanni_monthly_t2m_trends.csv', 'giovanni_vs_power_check.csv')
