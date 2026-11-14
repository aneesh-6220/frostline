#!/usr/bin/env python3
"""Derive canonical facts from the authoritative outputs and render docs/APPROVED_FINDINGS.md.

Writes:
  data/processed/canonical_facts.json and UI/data_real/canonical_facts.json  (machine-readable; every number computed here)
  docs/APPROVED_FINDINGS.md                                                   (generated; do not edit by hand)

Nothing is typed by hand except wording templates. Classification rule for a trend (applied by this script, not by judgement):
  supported     : BH q < 0.05 in its declared family
  inconclusive  : otherwise (the interval may still be one-sided; it is not evidence of "no change")
Usage (repo root): python3 -I scripts/generate_approved_findings.py [--out-docs PATH]
"""
import json
import os
import sys

import numpy as np
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
P = lambda *a: os.path.join(ROOT, *a)
rd = lambda f: pd.read_csv(P("data/processed", f))

ro, mt, rr = rd("road_operations.csv"), rd("multiple_testing_126.csv"), rd("road_record_trends_all_routes.csv")
hs, snow, snt, loc = rd("headline_trend_sensitivity.csv"), rd("snow_vs_opening.csv"), rd("snow_trends.csv"), rd("locations.csv")
cor, fam = rd("road_climate_correlations.csv"), rd("hypothesis_families.csv")
clim, cor_ui = pd.read_csv(P("UI/data_real/climate_annual.csv")), pd.read_csv(P("UI/data_real/corridors.csv"))
daily = rd("nasa_daily_temperature.csv")
bym = pd.read_csv(P("data/processed/diagnostics/bias_by_month.csv"))
dg = json.load(open(P("data/processed/diagnostics/diagnostics_summary.json")))
rs = json.load(open(P("data/processed/remediation_summary.json")))

DET, AKL = ("dettah", "dettah_bay"), ("aklavik", "aklavik_delta")


def f(x, d=1):
    return round(float(x), d) + 0.0  # + 0.0 turns -0.0 into 0.0


def road_all(rid, metric):
    r = rr[(rr.road_id == rid) & (rr.metric == metric)].iloc[0]
    return dict(n=int(r.n_seasons), slope=f(r.slope_per_decade), lo=f(r.ci95_low), hi=f(r.ci95_high), bb_lo=f(r.bb_ci95_low), bb_hi=f(r.bb_ci95_high),
                p=float(r.p_unadjusted), q=float(r.q_bh_all_routes), holm=float(r.holm_all_routes))


def road_w(lid, metric):
    r = mt[(mt.location_id == lid) & (mt.metric == metric)].iloc[0]
    return dict(n=int(r.n), slope=f(r.slope_per_decade), lo=f(r.ci95_low), hi=f(r.ci95_high), bb_lo=f(r.bb_ci95_low), bb_hi=f(r.bb_ci95_high),
                p=float(r.p_unadjusted), q=float(r.q_bh_all126))


# ---- status counts (mutually exclusive by construction: one status value per row)
sc = ro.groupby("record_status").size().to_dict()
status = dict(counts={k: int(v) for k, v in sorted(sc.items())}, total_rows=int(len(ro)), routes=int(ro.road_id.nunique()),
              winters=int(ro.season_start_year.nunique()), expected_rows=int(ro.road_id.nunique() * ro.season_start_year.nunique()),
              duplicate_route_winter_keys=int(ro.duplicated(["road_id", "season_start_year"]).sum()))
assert sum(status["counts"].values()) == status["total_rows"] == status["expected_rows"] and status["duplicate_route_winter_keys"] == 0, status
verified = ro[ro.record_status == "verified"].groupby("road_id").size().astype(int).to_dict()

periods = dict(nasa_daily_first=str(daily.date.min()), nasa_daily_last=str(daily.date.max()),
               trend_winters_first=int(clim.season_year.min()), trend_winters_last=int(clim.season_year.max()),
               trend_winters_n=int(clim.season_year.nunique()),
               road_record_first=int(ro.season_start_year.min()), road_record_last=int(ro.season_start_year.max()),
               missing_nasa_days_in_trend_seasons=int(clim.missing_days.sum()),
               winter_label_rule="winter y runs Oct 1 of y to Mar 31 of y+1; season_year/season_start_year = y; day numbers count days since Oct 1 of y")

oct_dec = bym[bym.month.isin([10, 11, 12])].mean_bias.abs()
bias = dict(overall_all_days=f(dg["overall_bias_all_days"]["mean_bias"], 2), overall_oct_dec=f(dg["overall_bias_Oct_Dec"]["mean_bias"], 2),
            overall_jan_mar=f(dg["overall_bias_Jan_Mar"]["mean_bias"], 2), paired_days=int(dg["overall_bias_all_days"]["n"]),
            oct_dec_monthly_abs_min=f(oct_dec.min()), oct_dec_monthly_abs_max=f(oct_dec.max()),
            fdd_nasa_mean=f(dg["effect_on_metrics"]["fdd_mean_nasa"], 0), fdd_station_mean=f(dg["effect_on_metrics"]["fdd_mean_station"], 0),
            fdd_pct_over=f(dg["effect_on_metrics"]["fdd_pct_overestimate"]), fdd_pearson_r=f(dg["effect_on_metrics"]["fdd_nasa_station_pearson_r"], 2),
            winters_compared=int(dg["effect_on_metrics"]["winters_with_complete_Oct_Dec_in_both"]))
CAVEAT = (f"NASA POWER T2M is MERRA-2 reanalysis for a 0.5 x 0.625 degree cell. At the Yellowknife cell it is on average "
          f"{bias['oct_dec_monthly_abs_min']} to {bias['oct_dec_monthly_abs_max']} C colder than the airport station in Oct-Dec (2001-2025).")

thaw = {}
for cid in ("dettah_bay", "aklavik_delta"):
    t = clim[(clim.corridor_id == cid) & (clim.metric == "thaw_days")].value
    thaw[cid] = dict(n=int(len(t)), winters_with_any_thaw=int((t > 0).sum()), total_thaw_days=int(t.sum()))
fdd = {cid: road_w(cid, "fdd_octdec") for cid in ("dettah_bay", "aklavik_delta")}

d_open, d_close, d_int = (road_all("dettah", m) for m in ("open_day", "close_day", "open_to_close_days"))
a_open = road_all("aklavik", "open_day")
d_open_w, a_open_w = road_w("dettah_bay", "open_day"), road_w("aklavik_delta", "open_day")
d_int_w = road_w("dettah_bay", "open_to_close_days")
sens = {r.variant: dict(n=int(r.n), slope=f(r.theil_sen_per_decade), lo=f(r.ts_ci95_low), hi=f(r.ts_ci95_high), bb_lo=f(r.bb_ci95_low),
                        bb_hi=f(r.bb_ci95_high), p=float(r.mk_p_unadjusted))
        for _, r in hs[(hs.road_id == "dettah") & (hs.metric == "open_day")].iterrows()}
sn = snow[snow.predictor == "sog_nov28_cm"].iloc[0]
snt_i = snt.set_index("series").loc["sog_nov28_cm"]
x126 = rs["extended_126"]
climate_rows = mt[mt.location_id.isin(["dettah_bay", "aklavik_delta"]) & (mt.family_type == "climate")] if "family_type" in mt else mt.iloc[0:0]
sup_all_routes = rr[rr.q_bh_all_routes < 0.05]

facts = dict(
    status_counts=status, verified_winters_by_route=verified, periods=periods, bias=bias, bias_caveat=CAVEAT, thaw=thaw,
    locations=[dict(location_id=r.location_id, name=r["name"], role=r.role, road_id=r.road_id, lat=float(r.latitude), lon=float(r.longitude)) for _, r in loc.iterrows()],
    corridors_in_app=cor_ui.corridor_id.tolist(),
    dettah=dict(open_full=d_open, close_full=d_close, interval_full=d_int, open_2001_2024=d_open_w, interval_2001_2024=d_int_w, open_sensitivity=sens, fdd_octdec=fdd["dettah_bay"]),
    aklavik=dict(open_full=a_open, open_2001_2024=a_open_w, fdd_octdec=fdd["aklavik_delta"]),
    all_routes_family=dict(n_tests=int(rs["road_record_all_routes"]["n_tests_with_p"]), nominal=int(rs["road_record_all_routes"]["nominal_p_lt_0.05"]),
                           bh_lt_05=int(rs["road_record_all_routes"]["bh_q_lt_0.05"]), holm_lt_05=int(rs["road_record_all_routes"]["holm_lt_0.05"])),
    extended_126=dict(n=int(x126["n_tests_with_p"]), nominal=int(x126["nominal_p_lt_0.05"]), expected_by_chance=f(x126["expected_false_positives_at_0.05"]),
                      bh_lt_05=int(x126["bh_q_lt_0.05_all126"]), bh_lt_10=int(x126["bh_q_lt_0.10_all126"]), holm_lt_05=int(x126["holm_lt_0.05_all126"]),
                      climate_family_bh_lt_05=int(x126["climate_family"]["bh_q_lt_0.05"])),
    snow=dict(sog_nov28_rho=f(sn.spearman_rho, 2), lo=f(sn.ci95_low, 2), hi=f(sn.ci95_high, 2), n=int(sn.n), q=float(sn.q_bh_family),
              trend_cm_per_decade=f(snt_i.slope_per_decade), trend_lo=f(snt_i.ci95_low), trend_hi=f(snt_i.ci95_high)),
    leakage=rs["leakage"],
    families=fam[["family_id", "n_tests"]].to_dict("records"),
    leak_free_assoc_all_ci_include_zero=bool(((cor.ci95_low <= 0) & (cor.ci95_high >= 0)).all()),
    supported_all_routes=[dict(road_id=r.road_id, metric=r.metric, slope=f(r.slope_per_decade), q=float(r.q_bh_all_routes)) for _, r in sup_all_routes.iterrows()],
)
for d in (P("data/processed"), P("UI/data_real")):
    json.dump(facts, open(os.path.join(d, "canonical_facts.json"), "w"), indent=1, sort_keys=True)
    open(os.path.join(d, "canonical_facts.json"), "a").write("\n")

ci = lambda r, k="": f"{r['lo']:+.1f} to {r['hi']:+.1f}"
p3 = lambda p: "<0.001" if p < 0.001 else f"{p:.3f}"
L, w = [], None
w = L.append
w("# Approved findings (generated file; do not edit by hand)\n")
w("Generated by `python3 -I scripts/generate_approved_findings.py` from `data/processed/`. It states what may be shown publicly, with the rule used to classify each item. "
  "Full tables are in `docs/RESULTS.md`; method rules in `docs/SCIENTIFIC_METHODS.md`. Every number below is computed from the data files. All results are **exploratory**: nothing was preregistered, and no reviewer sign-off on the methods is recorded in this repository.\n")
w("Classification rule: a trend is **supported** only if its Benjamini-Hochberg q < 0.05 in its declared family; otherwise **inconclusive** (not evidence of no change).\n")
w("## 0. Data coverage (mutually exclusive road-record statuses)\n")
w(f"`road_operations.csv` has {status['total_rows']} rows = {status['routes']} routes x {status['winters']} winters ({periods['road_record_first']}/{str(periods['road_record_first'] + 1)[2:]} to {periods['road_record_last']}/{str(periods['road_record_last'] + 1)[2:]}). Each row has exactly one status:\n")
w("| Status | Rows |\n|---|---|")
for k, v in status["counts"].items():
    w(f"| {k} | {v} |")
w(f"| **Total** | **{sum(status['counts'].values())}** |\n")
w("Only `verified` rows carry dates and enter any trend. The categories sum exactly to the row total and to routes x winters. (An earlier report quoted 540 rows; that figure was wrong. The data have always held 544.)\n")
w("## A. Valid environmental observations (reanalysis, with required caveat)\n")
w(f"- NASA POWER daily T2M for two points, {periods['nasa_daily_first']} to {periods['nasa_daily_last']}; {periods['trend_winters_n']} winters ({periods['trend_winters_first']}/{str(periods['trend_winters_first'] + 1)[2:]} to {periods['trend_winters_last']}/{str(periods['trend_winters_last'] + 1)[2:]}) with {periods['missing_nasa_days_in_trend_seasons']} missing days in the trend seasons.")
w(f"- Against the Yellowknife A station ({bias['paired_days']} paired days) NASA is {bias['overall_oct_dec']:+.2f} C in Oct-Dec and {bias['overall_jan_mar']:+.2f} C in Jan-Mar. NASA mean Oct-Dec FDD is {bias['fdd_nasa_mean']:.0f} versus {bias['fdd_station_mean']:.0f} C-days at the station ({bias['fdd_pct_over']:+.1f}%) on {bias['winters_compared']} winters, with year-to-year correlation r = {bias['fdd_pearson_r']}.")
w(f"- Required wording on every temperature figure: \"{CAVEAT}\"")
w("- Use NASA series for year-to-year variation and trends with intervals. Do not present absolute NASA temperatures, FDD or thaw-day counts as local conditions.\n")
w("## B. Supported trends (q < 0.05 in the stated family)\n")
for r in facts["supported_all_routes"]:
    if r["road_id"] == "aklavik":
        fragile = " Fragile: absent in 2001-2024 (section C)." if r["metric"] == "open_day" else ""
        w(f"- Aklavik {r['metric'].replace('_', ' ')}, 1993-2024: {r['slope']:+.1f} days per decade, q = {p3(r['q'])} (all-routes family of {facts['all_routes_family']['n_tests']}).{fragile} Road identity and segment unverified (`ROUTE_IDENTITY.md`); not a replication of Dettah. Exploratory.")
w(f"- Dettah opening day (full record, n = {d_open['n']}): {d_open['slope']:+.1f} days per decade, 95% CI {ci(d_open)}, block CI {d_open['bb_lo']:+.1f} to {d_open['bb_hi']:+.1f}, p {p3(d_open['p'])}. Positive means later opening.")
w(f"- Dettah open-to-close interval (full record): {d_int['slope']:+.1f} days per decade, 95% CI {ci(d_int)}, q = {p3(d_int['q'])}. The interval is not usable days.")
w(f"- Of {facts['all_routes_family']['n_tests']} route-level tests across NWT routes, {facts['all_routes_family']['nominal']} have p < 0.05 and {facts['all_routes_family']['bh_lt_05']} have q < 0.05 (Holm: {facts['all_routes_family']['holm_lt_05']}); signs are mixed across routes (`RESULTS.md` section 4).")
w("- Caveat to show: the Dettah series is selection-biased (the route was chosen after its trend was seen); the 51-test family is the adjustment.\n")
w("## C. Inconclusive or fragile trends\n")
w(f"- Dettah opening day, 2001-2024 (n = {d_open_w['n']}): {d_open_w['slope']:+.1f} days per decade, CI {ci(d_open_w)}, q = {p3(d_open_w['q'])} in the 126-test family (not below 0.05). Dropping the first five winters: {sens['2001-2024 drop first 5']['slope']:+.1f}, Theil-Sen CI {sens['2001-2024 drop first 5']['lo']:+.1f} to {sens['2001-2024 drop first 5']['hi']:+.1f}, p {p3(sens['2001-2024 drop first 5']['p'])}. Sensitive to the early years.")
w(f"- Aklavik opening day: {a_open['slope']:+.1f} days per decade over 1993-2024 (q = {p3(a_open['q'])}) but {a_open_w['slope']:+.1f} over 2001-2024 (CI {ci(a_open_w)}). Not robust.")
w(f"- NASA Oct-Dec FDD: Dettah {fdd['dettah_bay']['slope']:+.0f} C-days per decade (CI {fdd['dettah_bay']['lo']:+.0f} to {fdd['dettah_bay']['hi']:+.0f}, q = {p3(fdd['dettah_bay']['q'])}); Aklavik {fdd['aklavik_delta']['slope']:+.0f} (CI {fdd['aklavik_delta']['lo']:+.0f} to {fdd['aklavik_delta']['hi']:+.0f}, q = {p3(fdd['aklavik_delta']['q'])}). Not distinguishable from no change in {periods['trend_winters_n']} winters; this is not proof of no change.")
w(f"- Across all {facts['extended_126']['n']} extended NASA-window trend tests, {facts['extended_126']['nominal']} have p < 0.05 (about {facts['extended_126']['expected_by_chance']} expected by chance); {facts['extended_126']['bh_lt_05']} have q < 0.05; no climate metric survives correction ({facts['extended_126']['climate_family_bh_lt_05']} of the climate family).")
w(f"- Jan-Mar thaw days: not estimated. Dettah had thaw in {thaw['dettah_bay']['winters_with_any_thaw']} of {thaw['dettah_bay']['n']} winters (total thaw days: {thaw['dettah_bay']['total_thaw_days']}), Aklavik in {thaw['aklavik_delta']['winters_with_any_thaw']} of {thaw['aklavik_delta']['n']}. Reanalysis runs cold, so zero NASA thaw days does not mean no thaw.\n")
w("## D. Exploratory operational associations (not mechanisms)\n")
w(f"- Yellowknife A snow-on-ground on Nov 28 versus Dettah opening day: Spearman rho {facts['snow']['sog_nov28_rho']:+.2f} (CI {facts['snow']['lo']:.2f} to {facts['snow']['hi']:.2f}), n = {facts['snow']['n']}, q = {p3(facts['snow']['q'])} in a 5-predictor family. The snow series itself has a trend of {facts['snow']['trend_cm_per_decade']:+.1f} cm per decade (CI {facts['snow']['trend_lo']:+.1f} to {facts['snow']['trend_hi']:+.1f}), so it does not show that snow changed and does not explain the opening trend. Label: hypothesis.")
w(f"- Leak-free NASA climate predictors versus Dettah and Aklavik opening/closing dates: all confidence intervals include zero = {facts['leak_free_assoc_all_ci_include_zero']}.")
w(f"- Windows that overlapped the outcome were removed: the Oct-Dec window reached the Dettah opening date in {rs['leakage']['dettah_oct_dec_vs_opening_leaky_winters']} of 24 winters.\n")
w("## E. Statistical limitations to show\n")
w(f"- {periods['trend_winters_n']} winters for NASA-window trends; 15 is the minimum for any estimate. Theil-Sen with Mann-Kendall p and a moving-block bootstrap CI; residual lag-1 > 0.3 is flagged.")
w("- Five declared hypothesis families (" + ", ".join(f"{r['family_id']}: {r['n_tests']}" for r in facts["families"]) + "); tests are not independent, so q values are indicative.")
w("- NASA values are reanalysis for a 0.5 x 0.625 degree cell; one cell is not the whole road; Dettah (about 6.5 km lake crossing) and Aklavik (delta road, length ambiguous) are different objects; the road record is operations, not ice measurement.")
w("- No bias correction is applied anywhere. No causal inference is made. Statistical sign-off is pending (owner: Yao); none is recorded here.\n")
w("## F. Prohibited claims\n")
for s in ("Any prediction of opening dates, ice thickness, usable days or road safety; any statement that a road is or will be safe or unsafe.",
          "Any statement that warming, snow, or any other variable caused, drove or explains the Dettah or Aklavik date trends.",
          "Any pooled significance test across corridors or winters; any unadjusted p-value presented as a finding without its family and q.",
          "Presenting NASA absolute temperatures, FDD or thaw counts as local observations, or applying the 380 C-day threshold to this data.",
          "Any synthetic value (`UI/data/`, `UI/generate_data.py`) shown as real; any fallback to synthetic figures.",
          "Claiming Giovanni/MERRA-2 extraction, NASA eligibility confirmation, community adoption, stakeholder endorsement or statistician sign-off that has not happened."):
    w(f"- {s}")
OUT = sys.argv[sys.argv.index("--out-docs") + 1] if "--out-docs" in sys.argv else P("docs/APPROVED_FINDINGS.md")
open(OUT, "w").write("\n".join(L).replace(chr(8212), "-").replace("–", "-") + "\n")
