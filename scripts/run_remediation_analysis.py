#!/usr/bin/env python3
"""Authoritative statistical layer for Frostline (run AFTER run_analysis.py and run_extended_analysis.py).

Usage (repo root): python3 -I scripts/run_remediation_analysis.py
Writes data/processed/: hypothesis_families.csv, multiple_testing_126.csv, road_record_trends_all_routes.csv,
leakage_audit.csv, snow_vs_opening.csv, snow_trends.csv, headline_trend_sensitivity.csv, remediation_summary.json

Everything here is EXPLORATORY. No hypothesis was pre-specified before the data were examined; Dettah was chosen after
its road-date trends were seen (selection bias). Adjusted values answer "how surprising is this given how many things
were looked at", not "is this causal".
"""
import datetime as dt
import json
import os
import sys

import numpy as np
import pandas as pd
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)
import northlink_metrics as m  # noqa: E402
import northlink_stats as ns  # noqa: E402

P = lambda *a: os.path.join(ROOT, *a)
SEED = 20261114
ROAD_METRICS = ["open_day", "close_day", "open_to_close_days"]
summary = {}

et = pd.read_csv(P("data/processed/extended_trends.csv"))
em = pd.read_csv(P("data/processed/extended_season_metrics.csv"))
roads = pd.read_csv(P("data/processed/road_operations.csv"))

# ------------------------------------------------------------------ 1. hypothesis families + multiplicity (126 tests)
et = et.rename(columns={"mk_p": "p_unadjusted"})
et["family_type"] = np.where(et.metric.isin(ROAD_METRICS), "road_dates_2001_2024", "climate_2001_2024")
ci_bb = []
for _, r in et.iterrows():
    g = em[em.location_id == r.location_id].sort_values("season_start_year")
    slope, lo, hi, L = ns.block_bootstrap_slope(g.season_start_year, g[r.metric], seed=SEED)
    ci_bb.append((lo, hi, L, ns.modal_fraction(g[r.metric])))
et["bb_ci95_low"], et["bb_ci95_high"], et["bb_block_len"], et["modal_fraction"] = zip(*ci_bb)
et["q_bh_all126"] = ns.bh_adjust(et.p_unadjusted.to_numpy())
et["holm_all126"] = ns.holm_adjust(et.p_unadjusted.to_numpy())
for ft, g in et.groupby("family_type"):
    et.loc[g.index, "q_bh_within_family"] = ns.bh_adjust(g.p_unadjusted.to_numpy())
et["autocorr_flag"] = et.lag1.abs() > 0.3
et["ci_excludes_zero_theilsen"] = (et.ci95_low > 0) | (et.ci95_high < 0)
et["ci_excludes_zero_blockboot"] = (et.bb_ci95_low > 0) | (et.bb_ci95_high < 0)
et["status_exploratory"] = "exploratory"
cols = ["location_id", "road_kind", "metric", "family_type", "window", "n", "slope_per_decade", "ci95_low", "ci95_high",
        "bb_ci95_low", "bb_ci95_high", "bb_block_len", "p_unadjusted", "q_bh_all126", "q_bh_within_family", "holm_all126",
        "lag1", "autocorr_flag", "ci_excludes_zero_theilsen", "ci_excludes_zero_blockboot", "modal_fraction", "status", "status_exploratory"]
et[cols].to_csv(P("data/processed/multiple_testing_126.csv"), index=False, float_format="%.5g")
d = et.dropna(subset=["p_unadjusted"])
summary["extended_126"] = {
    "n_tests_with_p": int(len(d)), "nominal_p_lt_0.05": int((d.p_unadjusted < 0.05).sum()),
    "expected_false_positives_at_0.05": round(0.05 * len(d), 1),
    "bh_q_lt_0.05_all126": int((d.q_bh_all126 < 0.05).sum()), "bh_q_lt_0.10_all126": int((d.q_bh_all126 < 0.10).sum()),
    "holm_lt_0.05_all126": int((d.holm_all126 < 0.05).sum()),
    "survivors_q_lt_0.10": d[d.q_bh_all126 < 0.10][["location_id", "metric", "p_unadjusted", "q_bh_all126"]].round(4).to_dict("records"),
    "climate_family": {"n": int((d.family_type == "climate_2001_2024").sum()),
                       "nominal": int(((d.family_type == "climate_2001_2024") & (d.p_unadjusted < 0.05)).sum()),
                       "bh_q_lt_0.05": int(((d.family_type == "climate_2001_2024") & (d.q_bh_within_family < 0.05)).sum()),
                       "bh_q_lt_0.10": int(((d.family_type == "climate_2001_2024") & (d.q_bh_within_family < 0.10)).sum())},
    "road_family": {"n": int((d.family_type == "road_dates_2001_2024").sum()),
                    "nominal": int(((d.family_type == "road_dates_2001_2024") & (d.p_unadjusted < 0.05)).sum()),
                    "bh_q_lt_0.05": int(((d.family_type == "road_dates_2001_2024") & (d.q_bh_within_family < 0.05)).sum()),
                    "bh_q_lt_0.10": int(((d.family_type == "road_dates_2001_2024") & (d.q_bh_within_family < 0.10)).sum())},
    "autocorr_flagged": int(d.autocorr_flag.sum()),
}

fam = pd.DataFrame([
    dict(family_id="F1_all_extended", n_tests=int(len(d)), definition="every Theil-Sen/Mann-Kendall trend in extended_trends.csv (14 metrics x 9 corridors, 2001-2024)",
         correction="Benjamini-Hochberg (q) and Holm across all tests", role="primary multiplicity family for the NASA-window analysis"),
    dict(family_id="F2_climate", n_tests=summary["extended_126"]["climate_family"]["n"], definition="climate metrics only (11 per corridor x 9)",
         correction="Benjamini-Hochberg within family", role="sensitivity: does any NASA climate trend survive on its own?"),
    dict(family_id="F3_road_2001_2024", n_tests=summary["extended_126"]["road_family"]["n"], definition="road-date metrics (open day, close day, open-to-close interval) x 9 corridors, 2001-2024",
         correction="Benjamini-Hochberg within family", role="sensitivity for the NASA-aligned road window"),
    dict(family_id="F4_road_record_all_routes", n_tests=0, definition="road-date trends for EVERY NWT route with >=15 verified winters, full 1993-2024 record",
         correction="Benjamini-Hochberg across routes x 3 metrics", role="selection-adjusted view of the Dettah result (Dettah was chosen after seeing its trend)"),
    dict(family_id="F5_road_climate_associations", n_tests=0, definition="leak-free Spearman associations (Dettah and Aklavik predictors, plus Yellowknife snow predictors)",
         correction="Benjamini-Hochberg within family", role="association (not trend) tests"),
])

# ------------------------------------------------------------------ 2. road record, ALL routes (selection correction)
rows = []
for rid, g in roads[roads.record_status == "verified"].groupby("road_id"):
    g = g.sort_values("season_start_year").copy()
    g["od"] = [(dt.date.fromisoformat(a) - dt.date(y, 10, 1)).days for a, y in zip(g.opening_date, g.season_start_year)]
    g["cd"] = [(dt.date.fromisoformat(a) - dt.date(y, 10, 1)).days for a, y in zip(g.closing_date, g.season_start_year)]
    g["span"] = (pd.to_datetime(g.closing_date) - pd.to_datetime(g.opening_date)).dt.days
    # Opening/closing day counts differ by 1 in leap years (calendar date vs days since Oct 1); kept as in the main analysis.
    for met, col in zip(ROAD_METRICS, ["od", "cd", "span"]):
        t = m.trend(g.season_start_year, g[col])
        slope, lo, hi, L = ns.block_bootstrap_slope(g.season_start_year, g[col], seed=SEED)
        rows.append(dict(road_id=rid, road_name=g.road_name.iloc[0], road_type=g.road_type.iloc[0], metric=met, n_seasons=t.n,
                         first_year=int(g.season_start_year.min()), last_year=int(g.season_start_year.max()),
                         slope_per_decade=t.slope_per_decade, ci95_low=t.ci_low_per_decade, ci95_high=t.ci_high_per_decade,
                         bb_ci95_low=lo, bb_ci95_high=hi, p_unadjusted=t.mk_p, lag1=t.lag1_autocorr_resid, status=t.status))
rr = pd.DataFrame(rows)
rr["q_bh_all_routes"] = ns.bh_adjust(rr.p_unadjusted.to_numpy())
rr["holm_all_routes"] = ns.holm_adjust(rr.p_unadjusted.to_numpy())
rr["rank_by_p_within_metric"] = rr.groupby("metric").p_unadjusted.rank(method="min")
rr["ci_excludes_zero_blockboot"] = (rr.bb_ci95_low > 0) | (rr.bb_ci95_high < 0)
rr.to_csv(P("data/processed/road_record_trends_all_routes.csv"), index=False, float_format="%.5g")
dd = rr.dropna(subset=["p_unadjusted"])
fam.loc[fam.family_id == "F4_road_record_all_routes", "n_tests"] = int(len(dd))
summary["road_record_all_routes"] = {
    "n_routes": int(rr.road_id.nunique()), "n_tests_with_p": int(len(dd)), "nominal_p_lt_0.05": int((dd.p_unadjusted < 0.05).sum()),
    "bh_q_lt_0.05": int((dd.q_bh_all_routes < 0.05).sum()), "bh_q_lt_0.10": int((dd.q_bh_all_routes < 0.10).sum()),
    "holm_lt_0.05": int((dd.holm_all_routes < 0.05).sum()),
    "dettah": dd[dd.road_id == "dettah"][["metric", "n_seasons", "slope_per_decade", "ci95_low", "ci95_high", "bb_ci95_low", "bb_ci95_high",
                                           "p_unadjusted", "q_bh_all_routes", "holm_all_routes", "rank_by_p_within_metric"]].round(4).to_dict("records"),
    "aklavik": dd[dd.road_id == "aklavik"][["metric", "n_seasons", "slope_per_decade", "ci95_low", "ci95_high", "p_unadjusted", "q_bh_all_routes"]].round(4).to_dict("records"),
    "survivors_q_lt_0.10": dd[dd.q_bh_all_routes < 0.10][["road_id", "metric", "slope_per_decade", "p_unadjusted", "q_bh_all_routes"]].round(4).to_dict("records"),
}

# ------------------------------------------------------------------ 3. leakage audit (every predictor window vs outcome date)
verified = roads[roads.road_status == "verified"] if "road_status" in roads else roads[roads.record_status == "verified"]
ROAD = {"dettah_bay": "dettah", "aklavik_delta": "aklavik", "wrigley_tulita": "wrigley_tulita", "norman_wells_fgh": "norman_wells_fort_good_hope",
        "deline": "deline", "liard_fort_simpson": "liard_fort_simpson", "tibbitt_contwoyto": "tibbitt_contwoyto",
        "sambaa_ke": "sambaa_ke", "nahanni_butte": "nahanni_butte"}
# (label, window start (month, day, year offset), window end (month, day, year offset), outcome)
WINS = [
    ("Oct 1 - Dec 31 (FDD/mean/precip/wind/RH/LW windows)", (10, 1, 0), (12, 31, 0), "opening"),
    ("Oct 1 - Nov 28 (leak-free opening window)", (10, 1, 0), (11, 28, 0), "opening"),
    ("Nov 28 snow on ground", (11, 28, 0), (11, 28, 0), "opening"),
    ("Dec 1 snow on ground", (12, 1, 0), (12, 1, 0), "opening"),
    ("Mar 15 - Apr 15 (T/Tmax/SW/LW windows)", (3, 15, 1), (4, 15, 1), "closing"),
    ("Mar 15 - day before earliest closing (leak-free closing window; Dettah Apr 6, Aklavik Apr 15)", (3, 15, 1), (4, 6, 1), "closing"),
]
leak = []
for loc, rid in ROAD.items():
    g = verified[(verified.road_id == rid) & (verified.season_start_year.between(2001, 2024))]
    for label, (m0, d0, o0), (m1, d1, o1), outcome in WINS:
        if "leak-free closing window" in label:
            md = (4, 6) if rid == "dettah" else (4, 15)
            m1, d1 = md
        n_leaky = 0
        for _, r in g.iterrows():
            end = dt.date(int(r.season_start_year) + o1, m1, d1)
            out = dt.date.fromisoformat(r.opening_date if outcome == "opening" else r.closing_date)
            n_leaky += int(end >= out)
        leak.append(dict(location_id=loc, road_id=rid, predictor_window=label, outcome=outcome + "_date", n_winters=len(g), n_winters_window_reaches_outcome=n_leaky,
                         fraction_leaky=round(n_leaky / len(g), 3) if len(g) else np.nan,
                         verdict="LEAKY (uses information from on/after the outcome)" if n_leaky else "no leakage in the 2001-2024 sample"))
lk = pd.DataFrame(leak)
lk.to_csv(P("data/processed/leakage_audit.csv"), index=False)
summary["leakage"] = {
    "dettah_oct_dec_vs_opening_leaky_winters": lk[(lk.location_id == "dettah_bay") & lk.predictor_window.str.startswith("Oct 1 - Dec 31")].n_winters_window_reaches_outcome.iloc[0],
    "dettah_mar15_apr15_vs_closing_leaky_winters": lk[(lk.location_id == "dettah_bay") & lk.predictor_window.str.startswith("Mar 15 - Apr 15")].n_winters_window_reaches_outcome.iloc[0],
    "aklavik_oct_dec_vs_opening_leaky_winters": lk[(lk.location_id == "aklavik_delta") & lk.predictor_window.str.startswith("Oct 1 - Dec 31")].n_winters_window_reaches_outcome.iloc[0],
    "aklavik_mar15_apr15_vs_closing_leaky_winters": lk[(lk.location_id == "aklavik_delta") & lk.predictor_window.str.startswith("Mar 15 - Apr 15")].n_winters_window_reaches_outcome.iloc[0],
    "dettah_dec1_sog_vs_opening_leaky_winters": lk[(lk.location_id == "dettah_bay") & lk.predictor_window.str.startswith("Dec 1")].n_winters_window_reaches_outcome.iloc[0],
}

# ------------------------------------------------------------------ 4. snow: association, leakage status, snow trend
sn = pd.read_csv(P("data/processed/yellowknife_snow_by_season.csv"))
rows = []
SN = [("sog_nov28_cm", "Nov 28 (last day before earliest-ever Dettah opening, Nov 29)", True, True),
      ("sog_mean_nov1_28_cm", "Nov 1 to Nov 28 mean", True, True),
      ("snowfall_oct1_nov28_cm", "Oct 1 to Nov 28 total snowfall", True, True),
      ("sog_dec1_cm", "Dec 1 (after the earliest-ever opening, Nov 29, but before every opening in 2001-2024; earliest Dec 6)", False, True),
      ("snowfall_octdec_cm", "Oct 1 to Dec 31 total snowfall (extends past every opening in some winters)", False, False)]
for col, label, free_full, free_sample in SN:
    r_, p_, n_ = m.spearman(sn[col], sn.open_day)
    _, lo, hi, _, L = ns.block_bootstrap_spearman(sn[col], sn.open_day, seed=SEED)
    rows.append(dict(predictor=col, predictor_window=label, outcome="Dettah open_day", n=n_, spearman_rho=r_, ci95_low=lo, ci95_high=hi,
                     ci_method=f"moving-block bootstrap (block {L})", p_unadjusted=p_,
                     leak_free_vs_full_1993_2024_record=free_full, leak_free_in_2001_2024_sample=free_sample, source="ECCC Yellowknife A (ids 1706, 51058)"))
sa = pd.DataFrame(rows)
sa["q_bh_family"] = ns.bh_adjust(sa.p_unadjusted.to_numpy())
sa["bonferroni_5"] = np.minimum(sa.p_unadjusted * len(sa), 1.0)
sa.to_csv(P("data/processed/snow_vs_opening.csv"), index=False, float_format="%.5g")
tr = []
for col in ["sog_nov28_cm", "sog_mean_nov1_28_cm", "sog_dec1_cm", "snowfall_oct1_nov28_cm", "snowfall_octdec_cm"]:
    t = m.trend(sn.season_start_year, sn[col])
    slope, lo, hi, L = ns.block_bootstrap_slope(sn.season_start_year, sn[col], seed=SEED)
    tr.append(dict(series=col, n=t.n, slope_per_decade=t.slope_per_decade, ci95_low=t.ci_low_per_decade, ci95_high=t.ci_high_per_decade,
                   bb_ci95_low=lo, bb_ci95_high=hi, p_unadjusted=t.mk_p, status=t.status))
st_tr = pd.DataFrame(tr)
st_tr.to_csv(P("data/processed/snow_trends.csv"), index=False, float_format="%.5g")
summary["snow"] = {"associations": sa[["predictor", "n", "spearman_rho", "ci95_low", "ci95_high", "p_unadjusted", "q_bh_family", "bonferroni_5",
                                       "leak_free_vs_full_1993_2024_record", "leak_free_in_2001_2024_sample"]].round(4).to_dict("records"),
                   "trends": st_tr.round(4).to_dict("records")}
fam.loc[fam.family_id == "F5_road_climate_associations", "n_tests"] = int(len(sa) + 6)

# ------------------------------------------------------------------ 5. headline sensitivity (Dettah, Aklavik road dates)
hs = []
for rid in ["dettah", "aklavik"]:
    g = roads[(roads.road_id == rid) & (roads.record_status == "verified")].sort_values("season_start_year").copy()
    g["od"] = [(dt.date.fromisoformat(a) - dt.date(y, 10, 1)).days for a, y in zip(g.opening_date, g.season_start_year)]
    g["cd"] = [(dt.date.fromisoformat(a) - dt.date(y, 10, 1)).days for a, y in zip(g.closing_date, g.season_start_year)]
    g["span"] = (pd.to_datetime(g.closing_date) - pd.to_datetime(g.opening_date)).dt.days
    for met, col in zip(ROAD_METRICS, ["od", "cd", "span"]):
        for variant, sub in [("2001-2024", g[g.season_start_year >= 2001]), ("1993-2024", g),
                             ("2001-2024 drop first 5", g[g.season_start_year >= 2006]), ("2001-2024 drop last 5", g[(g.season_start_year >= 2001) & (g.season_start_year <= 2019)]),
                             ("2001-2024 drop 2023 and 2024 (late 2023 opening)", g[(g.season_start_year >= 2001) & (g.season_start_year <= 2022)])]:
            t = m.trend(sub.season_start_year, sub[col])
            slope, lo, hi, L = ns.block_bootstrap_slope(sub.season_start_year, sub[col], seed=SEED)
            ols = stats.linregress(sub.season_start_year, sub[col])
            hs.append(dict(road_id=rid, metric=met, variant=variant, n=t.n, theil_sen_per_decade=t.slope_per_decade, ts_ci95_low=t.ci_low_per_decade,
                           ts_ci95_high=t.ci_high_per_decade, mk_p_unadjusted=t.mk_p, bb_ci95_low=lo, bb_ci95_high=hi, ols_per_decade=ols.slope * 10,
                           ols_p_unadjusted=ols.pvalue, lag1_resid=t.lag1_autocorr_resid,
                           lag1_flag=bool(abs(t.lag1_autocorr_resid) > 0.3)))
hs = pd.DataFrame(hs)
hs.to_csv(P("data/processed/headline_trend_sensitivity.csv"), index=False, float_format="%.5g")
summary["headline_dettah_lag1"] = hs[(hs.road_id == "dettah") & (hs.variant == "2001-2024")][["metric", "theil_sen_per_decade", "ts_ci95_low", "ts_ci95_high", "mk_p_unadjusted", "bb_ci95_low", "bb_ci95_high", "lag1_resid", "lag1_flag"]].round(3).to_dict("records")

fam.to_csv(P("data/processed/hypothesis_families.csv"), index=False)
with open(P("data/processed/remediation_summary.json"), "w") as f:
    json.dump(summary, f, indent=2, default=lambda o: o.item() if hasattr(o, "item") else str(o))
print(json.dumps(summary, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o)))
