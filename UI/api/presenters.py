"""View models for the web frontend.

Each function returns what one Streamlit view (UI/frostline/views/*.py) put on screen: the same analysis calls,
the same frostline.fmt formatting and the same sentences, as JSON. The text is copied from the views so that
the redesigned interface says exactly what the audited Streamlit interface said. No statistic is computed here.
"""
from __future__ import annotations

import datetime as dt

import pandas as pd

from frostline import APP_NAME, APP_VERSION, METHOD_ID, TAGLINE, TEAM_NAME
from frostline import analysis as an
from frostline import brief as brief_mod
from frostline import charts
from frostline import evidence as ev
from frostline import fmt
from frostline.data import code_version
from frostline.registry import (DEFAULT_LOCATION, DEFAULT_VARIABLE, LITERATURE, POWER_ACK, QUESTIONS, ROAD_KIND_LABEL, SOFTWARE, SOURCES, VARIABLES,
                                primary_locations, variables_for)

from .chart_theme import themed
from .serialize import clean, table

STATE_TONE = {an.SUPPORTED: "good", an.UNRESOLVED: "neutral", an.EXPLORATORY: "warn", an.INSUFFICIENT: "muted", an.UNAVAILABLE: "muted"}
ROAD_VARS = ("open_day", "close_day", "open_to_close_days")
ENV_VARS = ("fdd_octdec", "mean_octdec_c", "mean_janmar_c", "tmax_mean_mar15_apr15_c")


# ------------------------------------------------------------------ shared pieces
def location_json(ds, loc) -> dict:
    d = clean(loc)
    d["is_primary_pair"] = loc.is_primary_pair
    d["cell"] = clean(loc.cell)
    d["road_kind_label"] = ROAD_KIND_LABEL.get(loc.road_kind, loc.road_kind)
    d["facts"] = [clean(f) for f in loc.facts]
    if loc.is_primary_pair:
        d["ranges"] = {"nasa": list(an.available_range(ds, loc.id, "fdd_octdec")), "road": list(an.available_range(ds, loc.id, "open_day"))}
        d["variables"] = [v.id for v in variables_for(loc)]
    return d


def variable_json(v) -> dict:
    d = clean(v)
    d["phrase"] = v.phrase
    d["unit_per_decade"] = v.unit_per_decade
    d["fixed_windows"] = [list(w) for w in v.fixed_windows]
    return d


def provenance_line(var, loc) -> str:
    src = SOURCES[var.source_id]
    if var.kind == "road":
        return f"Source: {src.name} (government record of operations) · {loc.road_name}"
    return f"Source: {src.name}, parameter {var.power_parameter} · {src.kind}, {var.spatial_resolution}"


def finding_json(ds, f: an.Finding, with_rows: bool = True) -> dict:
    """A finding plus every display string the finding card showed (ui.finding_card)."""
    var, loc = VARIABLES[f.variable_id], an.locations(ds).get(f.location_id)
    d = f.as_dict()
    d = clean(d)
    dec = var.slope_decimals
    d.update(
        estimated=f.estimated, tone=STATE_TONE[f.state],
        display={
            "slope": fmt.num(f.slope, dec, True) if f.estimated else None,
            "unit": var.unit_per_decade,
            "direction": f.direction,
            "interval": fmt.interval(f.ci_low, f.ci_high, dec) if f.estimated else None,
            "bb_interval": fmt.interval(f.bb_low, f.bb_high, dec) if f.estimated else None,
            "p": fmt.pval(f.p) if f.estimated else None,
            "q": fmt.pval(f.q) if f.q is not None else None,
            "period": fmt.period(f.first, f.last),
            "meta": (f"95% interval {fmt.interval(f.ci_low, f.ci_high, dec)} · n = {f.n} winters · {fmt.period(f.first, f.last)}" if f.estimated
                     else f"n = {f.n} winters · {fmt.period(f.first, f.last)}"),
            "title": var.short + " · " + (loc.short if loc else f.location_id),
            "provenance": provenance_line(var, loc) if loc else "",
        },
        is_temperature=var.is_temperature,
    )
    if with_rows:
        d["stat_rows"] = [list(r) for r in brief_mod.stat_rows(ds, f)]
    return d


def plain_language(ds, f) -> str:
    return f"{an.plain_language(ds, f)} {f.sentence}"


def bias_caveat(ds) -> str:
    return ds.facts["bias_caveat"] + " Absolute NASA values are not local conditions."


def report_json(rep: ev.EvidenceReport) -> dict:
    d = clean(rep)
    d["dimensions"] = [dict(clean(x), tone=x.tone) for x in rep.dimensions]
    return d


def chart(fig) -> dict:
    return themed(fig)


# ------------------------------------------------------------------ bootstrap
def catalogue(ds) -> dict:
    rows = []
    for v in VARIABLES.values():
        src = SOURCES[v.source_id]
        rows.append({"Variable": v.label, "Identifier": v.id, "Units": v.unit, "Group": ("Road record" if v.kind == "road" else "NASA core" if v.tier == "core" else "NASA exploratory"),
                     "Definition": v.definition, "Source": src.name, "Temporal resolution": v.temporal_resolution, "Spatial resolution": v.spatial_resolution,
                     "Valid period": fmt.period(v.valid_first, v.valid_last),
                     "Locations": "Dettah, Aklavik" if v.locations == "primary" else "Dettah, Aklavik and 7 supplementary corridors",
                     "Trend methods": "; ".join(v.methods) if v.id != "thaw_days_janmar" else "counts only; trend not estimated",
                     "Quality condition": v.quality, "Limitations": " ".join(v.limitations)})
    return table(list(rows[0]), rows)


def bootstrap(ds) -> dict:
    locs = an.locations(ds)
    return clean({
        "app": {"name": APP_NAME, "team": TEAM_NAME, "tagline": TAGLINE, "version": APP_VERSION, "method_id": METHOD_ID, "code_version": code_version(), "digest": ds.digest},
        "defaults": {"location": DEFAULT_LOCATION, "variable": DEFAULT_VARIABLE},
        "min_seasons": an.MIN_SEASONS,
        "locations": {k: location_json(ds, l) for k, l in locs.items()},
        "primary": [l.id for l in primary_locations(locs)],
        "variables": {k: variable_json(v) for k, v in VARIABLES.items()},
        "questions": {k: clean(q) for k, q in QUESTIONS.items()},
        "sources": {k: clean(s) for k, s in SOURCES.items()},
        "state_labels": an.STATE_LABEL, "state_tone": STATE_TONE,
        "road_note": an.T_ROAD,
        "bias_caveat": bias_caveat(ds),
        "facts": ds.facts,
        "giovanni": bool(ds.giovanni),
    })


def ranges(ds, location_id: str) -> dict:
    """Available winter range of every variable at a primary location (the period control needs it)."""
    out = {}
    for v in variables_for(an.locations(ds)[location_id]):
        out[v.id] = list(an.available_range(ds, location_id, v.id))
    return out


# ------------------------------------------------------------------ observatory
def observatory(ds) -> dict:
    f = an.trend(ds, DEFAULT_LOCATION, DEFAULT_VARIABLE, 2001, 2024)
    op = an.trend(ds, "dettah_bay", "open_day", 1993, 2024)
    env = an.trend(ds, "dettah_bay", "fdd_octdec", 2001, 2024)
    b, e = ds.facts["bias"], ds.facts["extended_126"]
    s, p = ds.facts["status_counts"], ds.facts["periods"]
    days = (dt.date.fromisoformat(p["nasa_daily_last"]) - dt.date.fromisoformat(p["nasa_daily_first"])).days + 1
    metrics = [
        ("Road record · Dettah", fmt.num(op.slope, 1, True), "days per decade",
         f"The ice road opened later over {fmt.period(op.first, op.last)} (95% interval {fmt.interval(op.ci_low, op.ci_high, 1)}; q = {fmt.pval(op.q)} across {op.q_family_n} route tests). Exploratory.",
         "NWT Bureau of Statistics, Table 108"),
        ("NASA freezing accumulation · Dettah", fmt.num(env.slope, 0, True), "°C-days per decade",
         f"95% interval {fmt.interval(env.ci_low, env.ci_high, 0)} over {env.n} winters: not statistically distinguishable from no change. That is not proof of no change.",
         "NASA POWER daily T2M (MERRA-2 reanalysis)"),
        ("NASA against the ground station", fmt.num(b["overall_oct_dec"], 1, True), "°C in Oct to Dec",
         f"NASA reanalysis runs colder than the Yellowknife A station across {fmt.count(b['paired_days'])} paired days. Frostline shows this disagreement instead of hiding it.",
         "NASA POWER and ECCC Yellowknife A"),
        ("Trend tests, corrected", f"{e['bh_lt_05']} of {e['n']}", "survive correction",
         f"{e['nominal']} of {e['n']} trend tests have p below 0.05 (about {e['expected_by_chance']} expected by chance). None survives correction for multiple testing.",
         "126-test family, winters 2001/02 to 2024/25"),
    ]
    return clean({
        "hero_finding": finding_json(ds, f, with_rows=False),
        "hero_chart": chart(charts.trend_chart(ds, f, height=340)),
        "hero_caption": (f"NASA POWER daily T2M (MERRA-2 reanalysis, grid-cell value). Theil-Sen estimate {fmt.num(f.slope, 0, True)} °C-days per decade, "
                         f"95% interval {fmt.interval(f.ci_low, f.ci_high, 0)}: {f.state_label.lower()}."),
        "metrics": [dict(zip(("kicker", "value", "unit", "description", "source"), m)) for m in metrics],
        "release": (f"In this release: {fmt.count(days)} days of NASA daily data at each of two documented locations, "
                    f"{s['total_rows']} route-winters of government road records ({s['counts']['verified']} verified) across {s['routes']} NWT routes, "
                    f"and {fmt.count(b['paired_days'])} paired station days for validation."),
        "intro_metrics": [
            dict(kicker="NASA record", value=str(p["trend_winters_n"]), unit="winters",
                 description=f"Daily NASA data for {fmt.period(p['trend_winters_first'], p['trend_winters_last'])}, with {p['missing_nasa_days_in_trend_seasons']} missing days", source="NASA POWER daily (MERRA-2)"),
            dict(kicker="Government record", value=str(s["winters"]), unit="winters",
                 description=f"Opening and closing dates for {s['routes']} NWT routes, {s['counts']['verified']} of {s['total_rows']} route-winters verified", source="NWT Bureau of Statistics, Table 108"),
            dict(kicker="Ground truth", value=fmt.count(b["paired_days"]), unit="paired days",
                 description="Station observations used to check the NASA values, including where they disagree", source="ECCC Yellowknife A"),
        ],
    })


# ------------------------------------------------------------------ trend detective
def season_table(ds, f) -> dict:
    var = VARIABLES[f.variable_id]
    s = an.get_series(ds, f.location_id, f.variable_id)
    rows = []
    for y, v in zip(s.years, s.values):
        row = {"Winter": fmt.winter(y), f"{var.short} ({var.unit})": None if not fmt.is_num(v) else round(float(v), var.decimals),
               "In analysis period": "yes" if f.first <= y <= f.last else "no"}
        if var.id in ("open_day", "close_day"):
            row["Calendar date"] = fmt.day_to_date_label(v, y) if fmt.is_num(v) else "no verified record"
        if f.estimated and f.first <= y <= f.last:
            row["Theil-Sen fit"] = round(an.fitted_line(f, [y])[0], max(var.decimals, 1))
        rows.append(row)
    cols = []
    for r in rows:
        for k in r:
            if k not in cols:
                cols.append(k)
    return table(cols, rows)


def investigation(ds, loc_id: str, var_id: str, first: int, last: int, height: int = 430) -> dict:
    """Everything the Trend Detective (and the sidebar status, and demo stages 2 and 3) showed for one selection."""
    loc, var = an.locations(ds)[loc_id], VARIABLES[var_id]
    f = an.trend(ds, loc_id, var_id, first, last)
    fixed = an.is_fixed_window(var_id, first, last)
    out = {
        "finding": finding_json(ds, f),
        "plain": plain_language(ds, f),
        "chart": chart(charts.trend_chart(ds, f, height=height)),
        "fixed": fixed,
        "status_meta": f"{fmt.period(first, last)} · n = {f.n} winters · " + ("approved fixed window" if fixed else "user-selected window: exploratory, not adjusted for multiple testing"),
        "chart_caption": ("Points: " + ("Recorded values from the government record" if var.kind == "road" else "NASA estimates for a grid cell, not station observations") +
                          ", one per winter. Dark line: Theil-Sen estimate for the selected period. Blue band: 95% interval of the slope. "
                          "Hollow points lie outside the selected period. Hover a point to inspect that winter."),
        "exploratory_caveat": (not fixed and f.estimated),
        "season_table": season_table(ds, f),
    }
    if var.id == "thaw_days_janmar":
        t = ds.facts["thaw"][loc_id]
        out["thaw_note"] = (f"NASA records an above-freezing midwinter day in {t['winters_with_any_thaw']} of {t['n']} winters here ({t['total_thaw_days']} such days in total). "
                            "The reanalysis runs cold and under-detects thaw relative to the station, so zero NASA thaw days does not mean no thaw.")
    src = SOURCES[var.source_id]
    out["why_rows"] = [["What it measures", var.definition], ["Why it is relevant", var.why], ["Units", var.unit],
                       ["Source", f"{src.name} ({src.kind})" + (f", parameter {var.power_parameter}" if var.power_parameter else "")],
                       ["Temporal resolution", var.temporal_resolution], ["Spatial resolution", var.spatial_resolution],
                       ["Valid period", fmt.period(var.valid_first, var.valid_last)], ["Data-quality condition", var.quality],
                       ["Known limitations", " ".join(var.limitations)]]
    if var.kind == "road" and loc.is_primary_pair:
        sv = an.sensitivity(ds, loc_id, var_id)
        rows = [{"Variant": a, "n": n, "Slope per decade": fmt.num(s_, 1, True), "95% interval (Theil-Sen)": fmt.interval(lo, hi, 1),
                 "95% interval (block bootstrap)": fmt.interval(blo, bhi, 1), "p (unadjusted)": fmt.pval(p), "Lag-1": fmt.num(l1, 2, True)}
                for a, n, s_, lo, hi, blo, bhi, p, l1 in zip(sv.variant, sv.n, sv.theil_sen_per_decade, sv.ts_ci95_low, sv.ts_ci95_high, sv.bb_ci95_low, sv.bb_ci95_high,
                                                             sv.mk_p_unadjusted, sv.lag1_resid)]
        out["robustness"] = {"kind": "table", "table": table(["Variant", "n", "Slope per decade", "95% interval (Theil-Sen)", "95% interval (block bootstrap)", "p (unadjusted)", "Lag-1"], rows),
                             "caption": "Stored robustness variants (headline_trend_sensitivity.csv): different windows and dropping early or late winters. "
                                        "They show how far the estimate depends on particular years. All are exploratory."}
    else:
        rows = charts.corridor_rows(ds, var_id) if var.fixed_windows else []
        if rows:
            out["robustness"] = {"kind": "forest", "chart": chart(charts.forest_chart(rows, var.unit_per_decade, var.slope_decimals)),
                                 "caption": "The same variable at all nine corridors with NASA data, winters 2001/02 to 2024/25. This places the selected location in context; "
                                            "supplementary corridors use approximate sampling points."}
        else:
            out["robustness"] = {"kind": "none", "caption": "No stored robustness variants exist for this variable."}
    out["method_rows"] = [
        ["Estimator", "Theil-Sen slope against the winter start year, reported per decade with its 95% interval"],
        ["Significance test", "Mann-Kendall with tie correction, two-sided; the p-value is unadjusted"],
        ["Dependence-aware interval", "Moving-block bootstrap of residuals (blocks of ceil(n^(1/3)), 2000 resamples, fixed seed)"],
        ["Serial correlation", "Lag-1 autocorrelation of residuals; above 0.3 in size raises a flag that p may be optimistic"],
        ["Minimum record", f"{an.MIN_SEASONS} complete winters; no estimate when one value fills at least 75% of winters"],
        ["Multiple testing", "Benjamini-Hochberg q only for approved fixed windows within their declared family"],
        ["This result", (f"Precomputed in {f.stored_source} and cross-checked against a live recomputation" if f.cross_checked
                         else "Recomputed for this window from the per-winter values with the approved period_trend function")],
        ["Series file", an.get_series(ds, loc_id, var_id).source_file], ["App data digest", ds.digest]]
    return clean(out)


# ------------------------------------------------------------------ questions
def question(ds, qid: str, loc_id: str) -> dict:
    q = QUESTIONS[qid]
    loc = an.locations(ds)[loc_id]
    available = {v.id for v in variables_for(loc)}
    recs = []
    for v in (VARIABLES[x] for x in q.variables if x in available):
        lo, hi = an.available_range(ds, loc.id, v.id)
        f = an.trend(ds, loc.id, v.id, lo, hi)
        src = SOURCES[v.source_id]
        recs.append({"variable": v.id, "kicker": f"{'Road record' if v.kind == 'road' else 'NASA variable'} · {v.unit}", "label": v.label,
                     "fit": q.reasons.get(v.id, v.why), "why": v.why, "phrase": v.phrase,
                     "source": f"{src.name} · winters {fmt.period(lo, hi)} · n = {f.n} · {f.state_label.lower()}", "state": f.state, "tone": STATE_TONE[f.state],
                     "state_label": f.state_label, "range": [lo, hi]})
    return clean({"id": qid, "text": q.text, "blurb": q.blurb, "next_view": q.next_view, "next_label": q.next_label, "recommendations": recs,
                  "footnote": f"Each recommendation opens {q.next_label.lower().replace('open ', '')} with this question, location and variable selected.",
                  "thaw_note": ("Above-freezing midwinter days are almost absent from the NASA series at both locations, so their trend cannot be estimated. Frostline reports that plainly "
                                "and offers the midwinter mean temperature as the analysable alternative.") if qid == "thaw" else None})


# ------------------------------------------------------------------ compare
def compare(ds, var_id: str, first: int, last: int) -> dict:
    locs = an.locations(ds)
    env = [v.id for v in VARIABLES.values() if v.kind == "environmental" and v.tier == "core" and v.id != "thaw_days_janmar"]
    vid = var_id if var_id in env else "fdd_octdec"
    var = VARIABLES[vid]
    lo, hi = an.available_range(ds, "dettah_bay", vid)
    if not (var_id == vid and lo <= first <= last <= hi):
        first, last = lo, hi
    cmp = an.compare(ds, vid, "dettah_bay", "aklavik_delta", first, last)
    a, b = locs[cmp.loc_a], locs[cmp.loc_b]
    d = var.slope_decimals
    src = ("Approved comparison window (docs/SCIENTIFIC_METHODS.md section D); no multiplicity adjustment is defined for it." if cmp.formal
           else "User-selected window: descriptive comparison.")
    diff = {"label": f"Difference in trend · {a.short} minus {b.short}", "tone": "neutral" if cmp.diff.state != an.EXPLORATORY else "warn", "source": src,
            "sentence": cmp.sentence, "estimated": cmp.diff.estimated}
    if cmp.diff.estimated:
        diff.update(value=fmt.num(cmp.diff.slope, d, True), unit=var.unit_per_decade,
                    meta=f"95% interval {fmt.interval(cmp.diff.ci_low, cmp.diff.ci_high, d)} · block bootstrap {fmt.interval(cmp.diff.bb_low, cmp.diff.bb_high, d)} · "
                         f"p = {fmt.pval(cmp.diff.p)} (unadjusted) · n = {cmp.diff.n} matched winters")
    else:
        diff.update(value="Not estimated")
    rows = [{"Location": locs[f.location_id].short, "Slope per decade": fmt.num(f.slope, d, True), "95% interval (Theil-Sen)": fmt.interval(f.ci_low, f.ci_high, d),
             "95% interval (block bootstrap)": fmt.interval(f.bb_low, f.bb_high, d), "p (unadjusted)": fmt.pval(f.p),
             "q": fmt.pval(f.q) if f.q is not None else "not reported", "n": f.n, "Evidence state": f.state_label} for f in (cmp.a, cmp.b)]
    return clean({
        "variable": vid, "env_variables": env, "first": first, "last": last, "period": fmt.period(first, last),
        "substituted": var_id != vid,
        "substitute_note": f"The selected variable is not an environmental variable that can be compared between grid cells, so this view shows {var.phrase} instead.",
        "chart": chart(charts.comparison_chart(ds, cmp)),
        "chart_caption": f"{len(cmp.common_years)} winters present in both series. Dashed lines: each location's own Theil-Sen estimate. NASA grid-cell values, not station observations.",
        "diff": diff,
        "a": finding_json(ds, cmp.a, with_rows=False), "b": finding_json(ds, cmp.b, with_rows=False),
        "table": table(list(rows[0]), rows),
        "table_caption": f"Units: {var.unit_per_decade}. Period: {fmt.period(first, last)}. Source: NASA POWER daily (MERRA-2 reanalysis).",
        "diff_chart": chart(charts.difference_chart(ds, cmp)),
        "forest_chart": chart(charts.forest_chart(charts.corridor_rows(ds, vid), var.unit_per_decade, var.slope_decimals)),
        "settings": [{"name": l.short, "rows": [["Setting", l.setting], ["Access", l.access], ["Sampling point", f"{l.lat:.2f} N, {abs(l.lon):.2f} W"], ["Station check", l.station]]} for l in (a, b)],
        "is_temperature": var.is_temperature,
    })


# ------------------------------------------------------------------ corridor
def corridor_overview(ds, loc_id: str) -> dict:
    loc = an.locations(ds)[loc_id]
    return clean({"kicker": f"Corridor investigation · {ROAD_KIND_LABEL[loc.road_kind]}", "name": loc.name, "setting": loc.setting,
                  "rows": [["Community connection", loc.access], ["Sampling point", loc.sampling_point], ["Station check", loc.station]],
                  "caution": loc.caution, "road_note": an.T_ROAD})


def corridor_road(ds, loc_id: str, measure: str) -> dict:
    loc = an.locations(ds)[loc_id]
    measure = measure if measure in ROAD_VARS else "open_day"
    full, nasa = an.trend(ds, loc.id, measure, 1993, 2024), an.trend(ds, loc.id, measure, 2001, 2024)
    rec = an.road_record(ds, loc.id)
    rows = [{"Winter": fmt.winter(r.season_start_year), "Opened": r.opening_date if r.record_status == "verified" else "",
             "Closed": r.closing_date if r.record_status == "verified" else "",
             "Interval (days)": None if pd.isna(r.open_to_close_days) else int(r.open_to_close_days), "Record status": r.record_status.replace("_", " ")}
            for r in rec.itertuples()]
    fa, fb = finding_json(ds, full), finding_json(ds, nasa)
    fa["display"]["title"] = f"{VARIABLES[measure].short} · full record"
    fb["display"]["title"] = f"{VARIABLES[measure].short} · NASA-era window"
    return clean({"measure": measure, "chart": chart(charts.trend_chart(ds, full, height=380)), "full": fa, "nasa": fb,
                  "note": "The two windows answer different questions and belong to different multiplicity families. A result that holds in one window and not the other is fragile and is reported as such.",
                  "table": table(["Winter", "Opened", "Closed", "Interval (days)", "Record status"], rows)})


def corridor_env(ds, loc_id: str, var_id: str) -> dict:
    var_id = var_id if var_id in ENV_VARS else "fdd_octdec"
    fe = an.trend(ds, loc_id, var_id, 2001, 2024)
    t = ds.facts["thaw"][loc_id]
    return clean({"variable": var_id, "chart": chart(charts.trend_chart(ds, fe, height=380)), "finding": finding_json(ds, fe, with_rows=False),
                  "thaw_note": f"Midwinter above-freezing days: not estimated. NASA records such a day in {t['winters_with_any_thaw']} of {t['n']} winters here; "
                               "the reanalysis runs cold, so zero NASA thaw days does not mean no thaw."})


def season_record(ds, location_id: str, year: int) -> list:
    """Everything recorded for one winter at one location (views/corridor.py season_record)."""
    rec = an.road_record(ds, location_id)
    r = rec[rec.season_start_year == year]
    rows = [("Winter", f"{fmt.winter(year)} (Oct 1, {year} to Mar 31, {year + 1})")]
    if len(r) and r.iloc[0].record_status == "verified":
        r = r.iloc[0]
        rows += [("Recorded opening", f"{fmt.iso_to_label(r.opening_date)} (day {int(r.open_day)} since Oct 1) · NWT Table 108"),
                 ("Recorded closing", f"{fmt.iso_to_label(r.closing_date)} (day {int(r.close_day)}) · NWT Table 108"),
                 ("Opening-to-closing interval", f"{int(r.open_to_close_days)} days (not usable days)")]
        opened_in_window = int(r.open_day) <= 91
    else:
        rows.append(("Road record", "No verified record for this winter"))
        opened_in_window = None
    for vid in ENV_VARS + ("thaw_days_janmar",):
        s = an.get_series(ds, location_id, vid)
        v = dict(zip(s.years, s.values)).get(year)
        var = VARIABLES[vid]
        rows.append((var.short, f"{fmt.num(v, var.decimals)} {var.unit} · NASA POWER (reanalysis)" if fmt.is_num(v) else "No NASA value: the NASA record starts with winter 2001/02"))
    if opened_in_window is not None and year >= 2001:
        rows.append(("Timing of the Oct to Dec values", "The road opened on or before Dec 31, so the Oct to Dec values include days after the opening: retrospective for this winter."
                     if opened_in_window else "The road opened after Dec 31, so the Oct to Dec window had ended before the opening in this winter."))
    if location_id == "dettah_bay":
        sn = ds["yellowknife_snow_by_season"]
        srow = sn[sn.season_start_year == year]
        if len(srow) and fmt.is_num(float(srow.iloc[0].sog_nov28_cm)):
            rows.append(("Snow on the ground, Nov 28", f"{fmt.num(float(srow.iloc[0].sog_nov28_cm), 0)} cm · ECCC Yellowknife A station"))
    return [list(x) for x in rows]


def corridor_timeline(ds, loc_id: str, var_id: str, year: int | None, height: int = 560) -> dict:
    var_id = var_id if var_id in ENV_VARS else "fdd_octdec"
    rec = an.road_record(ds, loc_id)
    years = [int(y) for y in rec.season_start_year]
    year = year if year in years else years[-1]
    ov = an.window_overlap(ds, loc_id)
    return clean({"variable": var_id, "years": years, "year": year, "winter": fmt.winter(year),
                  "chart": chart(charts.timeline_chart(ds, loc_id, var_id, highlight=year, height=height)),
                  "record": season_record(ds, loc_id, year),
                  "overlap": (f"In {ov['n_overlap']} of {ov['n_winters']} winters the road opened on or before Dec 31 (bars that start below the dotted line). In those winters the Oct to Dec "
                              "environmental value includes days after the opening. It describes the season in retrospect and is not information that was available before the road opened.") if ov else None,
                  "note": "The timeline is descriptive. It does not forecast road dates, and visual similarity between the panels is not evidence of a relationship. "
                          "Each bar runs from the recorded opening to the recorded closing; temporary closures are not recorded."})


def corridor_associations(ds, loc_id: str) -> dict:
    loc = an.locations(ds)[loc_id]
    a = an.associations(ds, loc_id)
    rows = [{"Predictor": pm, "Window": w, "Road outcome": rm, "Spearman rho": fmt.num(rho, 2, True), "95% interval (block bootstrap)": fmt.interval(lo, hi, 2),
             "n": n, "p (unadjusted)": fmt.pval(p), "q (family of 11)": fmt.pval(q)}
            for pm, w, rm, rho, lo, hi, n, p, q in zip(a.climate_metric, a.predictor_window, a.road_metric, a.spearman_rho, a.ci95_low, a.ci95_high, a.n, a.p_unadjusted, a.q_bh_family)]
    ov = an.window_overlap(ds, loc_id)
    out = {"table": table(["Predictor", "Window", "Road outcome", "Spearman rho", "95% interval (block bootstrap)", "n", "p (unadjusted)", "q (family of 11)"], rows),
           "note": ("Every interval includes zero: none of these associations is distinguishable from zero. " if an.all_ci_include_zero(a) else "") +
                   "A non-significant association is not evidence that the variables are unrelated; 24 winters is a short record.",
           "overlap": (f"Why the windows are short: the full Oct 1 to Dec 31 window reached or passed the {loc.short} opening date in {ov['n_overlap']} of {ov['n_winters']} winters "
                       "(leakage_audit.csv), so pairs using it were removed.") if ov else None,
           "snow": None}
    if loc_id == "dettah_bay":
        s = ds.facts["snow"]
        out["snow"] = {"chart": chart(charts.snow_chart(ds)), "value": fmt.num(s["sog_nov28_rho"], 2, True), "unit": "Spearman rho",
                       "meta": f"95% interval {fmt.interval(s['lo'], s['hi'], 2)} · n = {s['n']} winters · q = {fmt.pval(s['q'])} in a family of 5 snow predictors",
                       "text": (f"Winters with more snow on the ground at the airport on Nov 28 tended to have later openings. The snow series itself has no detectable trend "
                                f"({fmt.num(s['trend_cm_per_decade'], 1, True)} cm per decade, 95% interval {fmt.interval(s['trend_lo'], s['trend_hi'], 1)}), so the record does not show that snow cover changed. "
                                "This is a hypothesis for further study, not a mechanism."),
                       "source": "ECCC Yellowknife A station and NWT Table 108"}
    return clean(out)


def corridor_routes(ds, metric: str, window: str) -> dict:
    metric = metric if metric in ROAD_VARS else "open_day"
    fam = ds.facts["all_routes_family"]
    if window != "2001":
        t = ds["road_record_trends_all_routes"]
        t = t[t.metric == metric].sort_values("p_unadjusted")
        rows = [{"Route": r, "n": n, "Slope per decade (days)": fmt.num(s, 1, True), "95% interval": fmt.interval(a, b, 1), "p (unadjusted)": fmt.pval(p),
                 "q (all-route family, 51 tests)": fmt.pval(q)} for r, n, s, a, b, p, q in zip(t.road_name, t.n_seasons, t.slope_per_decade, t.ci95_low, t.ci95_high, t.p_unadjusted, t.q_bh_all_routes)]
        return clean({"metric": metric, "window": "1993", "chart": chart(charts.forest_chart(charts.routes_rows(ds, metric), "days per decade", 1)),
                      "table": table(list(rows[0]) if rows else [], rows),
                      "note": f"Family F4, all-route road record: {fam['n_tests']} tests, {fam['nominal']} with p below 0.05, {fam['bh_lt_05']} with q below 0.05 (Holm: {fam['holm_lt_05']}). "
                              "Signs are mixed across routes, so there is no single regional signal. Tests across routes are not independent, so q is indicative."})
    t = ds["multiple_testing_126"]
    t = t[t.metric == metric].sort_values("p_unadjusted")
    rows = [{"Corridor": c, "n": n, "Slope per decade (days)": fmt.num(s, 1, True), "95% interval": fmt.interval(a, b, 1), "p (unadjusted)": fmt.pval(p)}
            for c, n, s, a, b, p in zip(t.location_id, t.n, t.slope_per_decade, t.ci95_low, t.ci95_high, t.p_unadjusted)]
    return clean({"metric": metric, "window": "2001", "chart": chart(charts.forest_chart(charts.corridor_rows(ds, metric), "days per decade", 1)),
                  "table": table(list(rows[0]) if rows else [], rows),
                  "note": "This window belongs to a different family, so the all-route q is not shown here. The adjusted value for this window is the q across the 126 extended tests, "
                          "shown on each corridor's own result card and under Evidence Engine, Multiple testing."})


def corridor_conclusion(ds, loc_id: str) -> dict:
    loc = an.locations(ds)[loc_id]
    return clean({"label": f"Evidence conclusion · {loc.short}", "paragraphs": ev.corridor_conclusion(ds, loc_id),
                  "source": "Each sentence is generated from the computed results above; none is typed for a particular case."})


# ------------------------------------------------------------------ evidence
def evidence(ds, loc_id: str, var_id: str, first: int, last: int) -> dict:
    loc, var = an.locations(ds)[loc_id], VARIABLES[var_id]
    rep = ev.assess(ds, loc_id, var_id, first, last)
    f = an.trend(ds, loc_id, var_id, first, last)
    return clean({"lede": f"{var.label} · {loc.name} · winters {fmt.period(first, last)}. A trend estimate is only as good as the data behind it. "
                          "The engine separates what was observed, what was derived and what was inferred, and judges seven aspects of evidence quality one by one.",
                  "report": report_json(rep), "state": f.state, "state_label": f.state_label, "tone": STATE_TONE[f.state]})


def disagreement(ds) -> dict:
    b = ds.facts["bias"]
    s = an.station_fdd(ds)
    st2 = ds["station_summary_aklavik_inuvik"]
    t = ds.facts["thaw"]["dettah_bay"]
    trows = [{"Series": f.location_id, "Slope (°C-days per decade)": fmt.num(f.slope, 1, True), "95% interval (Theil-Sen)": fmt.interval(f.ci_low, f.ci_high, 0),
              "p (unadjusted)": fmt.pval(f.p), "n": f.n, "Period": fmt.period(f.first, f.last)} for f in (s.nasa, s.station, s.diff)]
    arows = [{"Station": st_, "Paired days": n, "Difference, all days (°C)": fmt.num(a, 2, True), "Difference, Oct to Mar (°C)": fmt.num(o, 2, True),
              "Mean absolute difference, Oct to Mar (°C)": fmt.num(m, 2)} for st_, n, a, o, m in zip(st2.station, st2.n_days, st2.bias_all_c, st2.bias_octmar_c, st2.mae_octmar_c)]
    return clean({
        "metrics": [
            dict(kicker="Oct to Dec", value=fmt.num(b["overall_oct_dec"], 2, True), unit="°C", description="Mean NASA minus station, early winter", source="bias_by_month.csv"),
            dict(kicker="Jan to Mar", value=fmt.num(b["overall_jan_mar"], 2, True), unit="°C", description="Mean NASA minus station, midwinter", source="canonical_facts.json"),
            dict(kicker="Freezing degree-days", value=fmt.num(s.pct_over, 1, True), unit="%", description=f"NASA {fmt.num(s.nasa_mean, 0)} against station {fmt.num(s.station_mean, 0)} °C-days on {s.n_complete} matched winters", source="station_fdd_by_season.csv"),
            dict(kicker="Year-to-year correlation", value=fmt.num(s.pearson_r, 2), unit="r", description="NASA tracks the station's ups and downs while disagreeing on the level", source="station_fdd_by_season.csv")],
        "bias_chart": chart(charts.bias_month_chart(ds)),
        "bias_caption": (f"{fmt.count(b['paired_days'])} paired days, 2001 to 2025; {fmt.num(b['overall_all_days'], 2, True)} °C over all days. "
                         "The difference is largest in the freeze-up months and close to zero in summer, so it is not a constant offset."),
        "fdd_chart": chart(charts.station_fdd_chart(ds)),
        "fdd_caption": f"{s.n_complete} of {len(s.years_all)} winters have a complete Oct to Dec station record; incomplete station winters are left as gaps, not filled.",
        "trend_table": table(list(trows[0]), trows),
        "trend_note": "Neither trend is distinguishable from zero, and the trend of the difference is not distinguishable from zero either. That does not make the two series equivalent: "
                      "with intervals this wide the comparison is weak, and a high year-to-year correlation says nothing about absolute accuracy.",
        "aklavik_table": table(list(arows[0]), arows),
        "aklavik_caption": "NASA minus station for the Aklavik cell. The stations sit at the two ends of the road, not at the sampling point.",
        "meaning": ["Use NASA series for year-to-year variation and for trends read with their intervals.",
                    "Do not read absolute NASA temperature, freezing degree-days or thaw counts as local conditions.",
                    f"NASA records a midwinter thaw day in {t['winters_with_any_thaw']} of {t['n']} winters at Dettah; the station records more, so NASA under-detects thaw.",
                    "Frostline applies no bias correction. An offset fitted to this one station would not be a validated correction.",
                    "The cause of the difference is not established. A date shift, a different daily-mean definition, an elevation mismatch and a drift were tested and ruled out."],
    })


def multiple_testing(ds) -> dict:
    e = ds.facts["extended_126"]
    fam = ds["hypothesis_families"]
    t = ds["multiple_testing_126"]
    all_rows = pd.DataFrame({"Corridor": t.location_id, "Measure": t.metric, "Family": t.family_type, "n": t.n, "Slope per decade": t.slope_per_decade,
                             "95% low": t.ci95_low, "95% high": t.ci95_high, "p (unadjusted)": t.p_unadjusted, "q (126 tests)": t.q_bh_all126, "Holm": t.holm_all126,
                             "Lag-1 flag": t.autocorr_flag}).sort_values("p (unadjusted)")
    return clean({
        "intro": f"The extended analysis runs {e['n']} trend tests (14 measures at 9 corridors, winters 2001/02 to 2024/25). When many tests are run, some small p-values appear by chance alone.",
        "metrics": [
            dict(kicker="Tests run", value=str(e["n"]), unit="trend tests", description="14 measures at 9 corridors", source="multiple_testing_126.csv"),
            dict(kicker="Nominal", value=str(e["nominal"]), unit="with p below 0.05", description=f"About {e['expected_by_chance']} would be expected by chance if nothing were changing", source="multiple_testing_126.csv"),
            dict(kicker="After correction", value=str(e["bh_lt_05"]), unit="with q below 0.05", description=f"Benjamini-Hochberg across all {e['n']}; Holm also leaves {e['holm_lt_05']}", source="multiple_testing_126.csv"),
            dict(kicker="NASA climate tests", value=str(e["climate_family_bh_lt_05"]), unit="of 99 survive", description="No NASA climate trend survives correction at any corridor", source="hypothesis_families.csv")],
        "chart": chart(charts.multiple_testing_chart(ds)),
        "chart_caption": "Each point is one test. A test is supported only if it falls on or below the amber line. Points between the amber line and the dotted line "
                         "look significant on their own and are not, once the number of tests is taken into account.",
        "families": table(["Family", "Tests", "Definition", "Correction", "Role"],
                          [{"Family": a, "Tests": b, "Definition": c, "Correction": d, "Role": e_} for a, b, c, d, e_ in zip(fam.family_id, fam.n_tests, fam.definition, fam.correction, fam.role)]),
        "all": table(list(all_rows.columns), all_rows.to_dict(orient="records")),
        "note": "Adjusted q values belong to these declared families and fixed windows only. When you choose your own period, Frostline shows the unadjusted p and labels it exploratory.",
    })


# ------------------------------------------------------------------ demo stage 4
def demo_road(ds, loc_id: str) -> dict:
    f = an.trend(ds, loc_id, "open_day", 1993, 2024)
    return clean({"chart": chart(charts.timeline_chart(ds, loc_id, "fdd_octdec", height=500)), "finding": finding_json(ds, f, with_rows=False),
                  "conclusion": ev.corridor_conclusion(ds, loc_id)[2:]})


# ------------------------------------------------------------------ methods
def methods(ds) -> dict:
    p, s = ds.facts["periods"], ds.facts["status_counts"]
    locs = an.locations(ds)
    out = {
        "method_rows": [
            ["Winter definition", p["winter_label_rule"]],
            ["Trend estimator", "Theil-Sen slope against the winter start year, reported per decade, with its 95% interval"],
            ["Significance test", "Mann-Kendall with tie correction, two-sided. The p-value is always labelled unadjusted"],
            ["Dependence-aware interval", "Moving-block bootstrap of residuals: blocks of ceil(n^(1/3)) winters, 2000 resamples, fixed seed 20261114"],
            ["Serial correlation", "Lag-1 autocorrelation of the residuals; above 0.3 in size raises a flag (a warning, not a correction)"],
            ["Completeness", "A winter enters a trend only with complete daily coverage. At least 15 winters are required. Missing days are never filled"],
            ["Degenerate series", "No slope or p-value when one value fills at least 75% of winters (midwinter above-freezing days)"],
            ["Multiple testing", "Benjamini-Hochberg q within five declared families, Holm across the two main families. q is shown only for the fixed windows of those families"],
            ["Regional comparison", "Trend of the difference series on matched winters; one small and one large p-value do not imply different slopes"],
            ["Associations", "Spearman rank correlation with a block-bootstrap interval, only for predictor windows that end before the earliest recorded outcome"],
            ["Bias handling", "No bias correction is applied to any reported result"],
            ["Method identifier", METHOD_ID]],
        "data_rows": [
            ["NASA daily data", f"{p['nasa_daily_first']} to {p['nasa_daily_last']}; {p['trend_winters_n']} winters ({fmt.period(p['trend_winters_first'], p['trend_winters_last'])}); "
                                f"{p['missing_nasa_days_in_trend_seasons']} missing days in the trend seasons"],
            ["Road record", f"Winters {fmt.period(p['road_record_first'], p['road_record_last'])}; {s['total_rows']} route-winter rows across {s['routes']} routes: "
                            + ", ".join(f"{v} {k.replace('_', ' ')}" for k, v in sorted(s['counts'].items()))],
            ["Station validation", f"{fmt.count(ds.facts['bias']['paired_days'])} paired days against ECCC Yellowknife A; Aklavik and Inuvik stations for the delta cell"],
            ["App data", f"{len(ds.file_hashes)} approved files in UI/data_real, digest {ds.digest}. The app reads nothing else and downloads nothing"]],
        "sources": [clean(x) for x in SOURCES.values()],
        "power_ack": POWER_ACK, "literature": LITERATURE, "software": SOFTWARE + ["FastAPI", "React", "Tailwind CSS", "Motion", "Plotly.js", "MapLibre GL"],
        "file_hashes": table(["File", "sha256"], [{"File": k, "sha256": v} for k, v in ds.file_hashes.items()]),
        "giovanni": None,
        "giovanni_rows": [
            ["What is used", "NASA POWER daily data: T2M, T2M_MAX, TS, PRECTOTCORR, WS10M, RH2M (MERRA-2) and surface irradiance (CERES SYN1deg)"],
            ["What the challenge names", "MERRA-2 is named in the challenge background as a suitable model; POWER distributes MERRA-2 variables"],
            ["What is ready", "A strict ingest path for a Giovanni MERRA-2 monthly T2M extraction (collection M2TMNXSLV). A panel appears here automatically once real files are ingested"],
            ["What it would add", "A consistency check that POWER equals the MERRA-2 product at the same cell, and seasonal mean-temperature trends from a listed resource. Not an independent observation"],
            ["What it would never do", "Monthly means are never used to compute freezing degree-days or thaw counts"]],
        "review_rows": [["Statistical sign-off", "Pending. No independent reviewer has signed off on the methods"],
                        ["NASA listed-resource requirement", "Not demonstrated" if not ds.giovanni else "Giovanni extraction ingested; confirmation pending"],
                        ["Stakeholder validation", "None. No community adoption, interviews or endorsements are claimed"],
                        ["Automated checks", "Scientific and application test suites; deterministic regeneration of every derived file"]],
        "locations_table": table(["Location", "Identifier", "Role", "Road record", "On the map"],
                                 [{"Location": l.name, "Identifier": l.id, "Role": l.role, "Road record": l.road_id, "On the map": "yes" if l.mapped else "no (approximate point)"} for l in locs.values()]),
        "extend_rows": [
            ["To add a location", "Add its verified coordinates and per-winter values through scripts/regenerate_all.py, then add its context to the location registry"],
            ["To add a variable", "Add its per-winter column to the data files and one entry to the variable registry with definition, units, source and limitations"],
            ["Quality gates", "Complete daily coverage, documented provenance, validated units and at least 15 winters before any trend is shown"],
            ["Live NASA downloads", "Not offered. The app makes no network request for data, so results cannot change under a presenter and remain reproducible"],
            ["Guide", "docs/EXTENDING_FROSTLINE.md"]],
        "version_line": f"Frostline {APP_VERSION} · code {code_version()} · app data digest {ds.digest}",
        "catalogue": catalogue(ds),
    }
    if ds.giovanni:
        tr, chk = ds.giovanni["giovanni_monthly_t2m_trends.csv"], ds.giovanni["giovanni_vs_power_check.csv"]
        trows = [{"Location": l, "Seasonal mean": {"octdec_mean_c": "Oct to Dec", "janmar_mean_c": "Jan to Mar"}.get(m, m), "n": n, "Slope (°C per decade)": fmt.num(sl, 2, True),
                  "95% interval": fmt.interval(a, b, 2), "p (unadjusted)": fmt.pval(p_), "Status": st_}
                 for l, m, n, sl, a, b, p_, st_ in zip(tr.location_id, tr.metric, tr.n, tr.slope_per_decade, tr.ci95_low, tr.ci95_high, tr.mk_p, tr.status)]
        crows = [{"Location": l, "Months compared": n, "Mean difference, Giovanni minus POWER (°C)": md, "Largest absolute difference (°C)": mx, "Correlation": r}
                 for l, n, md, mx, r in zip(chk.location_id, chk.n_months, chk.mean_diff_giovanni_minus_power_c, chk.max_abs_diff_c, chk.pearson_r)]
        out["giovanni"] = {"trends": table(list(trows[0]), trows), "check": table(list(crows[0]), crows)}
    return clean(out)
