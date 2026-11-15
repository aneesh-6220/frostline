"""Corridor investigation: one documented road, its NASA environmental record and its government operating record.

Environmental results and road-operations results are separate objects in separate sections. They appear
side by side only under the label "association, not cause".
"""
import pandas as pd
import streamlit as st

from .. import analysis as an
from .. import charts, evidence as ev, fmt, ui
from ..registry import ROAD_KIND_LABEL, VARIABLES

ROAD_VARS = ("open_day", "close_day", "open_to_close_days")
ENV_VARS = ("fdd_octdec", "mean_octdec_c", "mean_janmar_c", "tmax_mean_mar15_apr15_c")


def season_record(ds, location_id: str, year: int) -> list:
    """Everything recorded for one winter at one location, each value with its source and date convention."""
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
    return rows


def render(ds):
    inv = ui.current()
    locs = an.locations(ds)
    loc = locs[inv.location_id]
    ui.page_header(f"Corridor investigation · {ROAD_KIND_LABEL[loc.road_kind]}", loc.name, loc.setting)
    c = st.columns([1.2, 1], gap="large")
    with c[0]:
        ui.html("<div class='fl-panel'>" + ui.kv_table([("Community connection", loc.access), ("Sampling point", loc.sampling_point), ("Station check", loc.station)]) + "</div>")
    with c[1]:
        ui.caveat(loc.caution, "Read this first")
        ui.caveat(an.T_ROAD, "About the road record")

    st.write("")
    tabs = st.tabs(["Road history", "Environmental record", "Timeline", "Associations", "All NWT routes", "Evidence conclusion"])

    with tabs[0]:
        ui.html(ui.kicker("Road-operations results · government record"))
        rv = st.segmented_control("Road measure", list(ROAD_VARS), default=inv.variable_id if inv.variable_id in ROAD_VARS else "open_day",
                                  format_func=lambda i: VARIABLES[i].short, key="cor_road_var", required=True) or "open_day"
        full, nasa = an.trend(ds, loc.id, rv, 1993, 2024), an.trend(ds, loc.id, rv, 2001, 2024)
        with st.container(key="fl_frame_cor_road"):
            ui.plot(charts.trend_chart(ds, full, height=380), key="cor_road_chart")
        cc = st.columns(2)
        with cc[0]:
            ui.finding_card(ds, full, title=f"{VARIABLES[rv].short} · full record")
        with cc[1]:
            ui.finding_card(ds, nasa, title=f"{VARIABLES[rv].short} · NASA-era window")
        ui.note("The two windows answer different questions and belong to different multiplicity families. A result that holds in one window and not the other is fragile and is reported as such.")
        st.dataframe(pd.DataFrame([{"Winter": fmt.winter(r.season_start_year), "Opened": r.opening_date if r.record_status == "verified" else "",
                                    "Closed": r.closing_date if r.record_status == "verified" else "",
                                    "Interval (days)": None if pd.isna(r.open_to_close_days) else int(r.open_to_close_days), "Record status": r.record_status.replace("_", " ")}
                                   for r in an.road_record(ds, loc.id).itertuples()]), hide_index=True, height=260)

    with tabs[1]:
        ui.html(ui.kicker("Environmental results · NASA reanalysis"))
        evv = st.segmented_control("Environmental variable", list(ENV_VARS), default=inv.variable_id if inv.variable_id in ENV_VARS else "fdd_octdec",
                                   format_func=lambda i: VARIABLES[i].short, key="cor_env_var", required=True) or "fdd_octdec"
        fe = an.trend(ds, loc.id, evv, 2001, 2024)
        cc = st.columns([1.6, 1], gap="large")
        with cc[0]:
            with st.container(key="fl_frame_cor_env"):
                ui.plot(charts.trend_chart(ds, fe, height=380), key="cor_env_chart")
        with cc[1]:
            ui.finding_card(ds, fe, show_table=False)
        t = ds.facts["thaw"][loc.id]
        ui.note(f"Midwinter above-freezing days: not estimated. NASA records such a day in {t['winters_with_any_thaw']} of {t['n']} winters here; "
                "the reanalysis runs cold, so zero NASA thaw days does not mean no thaw.")

    with tabs[2]:
        ui.html(ui.kicker("Environmental and operational timeline") +
                "<p class='fl-sub'>Two panels on one winter axis, each with its own units. The upper panel is NASA data; the lower panel is the government record.</p>")
        cc = st.columns([1, 1])
        tv = cc[0].selectbox("Environmental variable", list(ENV_VARS), format_func=lambda i: VARIABLES[i].label, key="cor_tl_var")
        rec = an.road_record(ds, loc.id)
        years = [int(y) for y in rec.season_start_year]
        yr = cc[1].select_slider("Inspect a winter", options=years, value=years[-1], format_func=fmt.winter, key="cor_tl_year")
        with st.container(key="fl_frame_cor_timeline"):
            ui.plot(charts.timeline_chart(ds, loc.id, tv, highlight=yr), key="cor_timeline")
        ov = an.window_overlap(ds, loc.id)
        cc = st.columns([1, 1], gap="large")
        with cc[0]:
            ui.html(f"<div class='fl-panel'><div class='fl-place-name'>Winter {fmt.winter(yr)}</div>" + ui.kv_table(season_record(ds, loc.id, yr)) + "</div>")
        with cc[1]:
            if ov:
                ui.caveat(f"In {ov['n_overlap']} of {ov['n_winters']} winters the road opened on or before Dec 31 (bars that start below the dotted line). In those winters the Oct to Dec "
                          "environmental value includes days after the opening. It describes the season in retrospect and is not information that was available before the road opened.", "Retrospective information")
            ui.note("The timeline is descriptive. It does not forecast road dates, and visual similarity between the panels is not evidence of a relationship. "
                    "Each bar runs from the recorded opening to the recorded closing; temporary closures are not recorded.")

    with tabs[3]:
        ui.html(ui.kicker("Exploratory associations · association, not cause") +
                "<p class='fl-sub'>Spearman rank correlations between NASA climate predictors and road dates. Each predictor window ends the day before the earliest opening "
                "(or closing) ever recorded for the road, so it never includes information from after the outcome.</p><div class='fl-gap'></div>")
        a = an.associations(ds, loc.id)
        st.dataframe(pd.DataFrame({"Predictor": a.climate_metric, "Window": a.predictor_window, "Road outcome": a.road_metric,
                                   "Spearman rho": [fmt.num(v, 2, True) for v in a.spearman_rho], "95% interval (block bootstrap)": [fmt.interval(x, y, 2) for x, y in zip(a.ci95_low, a.ci95_high)],
                                   "n": a.n, "p (unadjusted)": [fmt.pval(p) for p in a.p_unadjusted], "q (family of 11)": [fmt.pval(q) for q in a.q_bh_family]}), hide_index=True)
        ui.note(("Every interval includes zero: none of these associations is distinguishable from zero. " if an.all_ci_include_zero(a) else "") +
                "A non-significant association is not evidence that the variables are unrelated; 24 winters is a short record.")
        if ov:
            ui.html(f"<div class='fl-src'>Why the windows are short: the full Oct 1 to Dec 31 window reached or passed the {ui.esc(loc.short)} opening date in {ov['n_overlap']} of {ov['n_winters']} winters (leakage_audit.csv), so pairs using it were removed.</div>")
        if loc.id == "dettah_bay":
            s = ds.facts["snow"]
            ui.section("Snow hypothesis · hypothesis, not a cause")
            cc = st.columns([1.5, 1], gap="large")
            with cc[0]:
                with st.container(key="fl_frame_cor_snow"):
                    ui.plot(charts.snow_chart(ds), key="cor_snow")
            with cc[1]:
                ui.result_panel("Snow on the ground, Nov 28 · Dettah opening day", ui.chip("Hypothesis", "warn"), fmt.num(s['sog_nov28_rho'], 2, True), "Spearman rho",
                                f"95% interval {fmt.interval(s['lo'], s['hi'], 2)} · n = {s['n']} winters · q = {fmt.pval(s['q'])} in a family of 5 snow predictors",
                                [f"Winters with more snow on the ground at the airport on Nov 28 tended to have later openings. The snow series itself has no detectable trend "
                                 f"({fmt.num(s['trend_cm_per_decade'], 1, True)} cm per decade, 95% interval {fmt.interval(s['trend_lo'], s['trend_hi'], 1)}), so the record does not show that snow cover changed. "
                                 "This is a hypothesis for further study, not a mechanism."], source="ECCC Yellowknife A station and NWT Table 108", tone="warn")

    with tabs[4]:
        ui.html(ui.kicker("Selection-adjusted view · all NWT routes") +
                "<p class='fl-sub'>Dettah was chosen after its trend had been seen. To adjust for that, the same test is run for every NWT route with at least 15 verified winters "
                "(17 routes, 3 measures, 51 tests) and corrected across all of them.</p><div class='fl-gap'></div>")
        st.session_state.setdefault("cor_all_metric", "open_day")
        metric = st.segmented_control("Road measure", list(ROAD_VARS), format_func=lambda i: VARIABLES[i].short, key="cor_all_metric", required=True) or "open_day"
        window = st.radio("Window", ["1993/94 to 2024/25 (all-route family of 51 tests)", "2001/02 to 2024/25 (nine corridors with NASA data)"], key="cor_all_window", horizontal=True)
        fam = ds.facts["all_routes_family"]
        if window.startswith("1993"):
            ui.plot(charts.forest_chart(charts.routes_rows(ds, metric), "days per decade", 1), key="cor_routes")
            t = ds["road_record_trends_all_routes"]
            t = t[t.metric == metric].sort_values("p_unadjusted")
            st.dataframe(pd.DataFrame({"Route": t.road_name, "n": t.n_seasons, "Slope per decade (days)": [fmt.num(v, 1, True) for v in t.slope_per_decade],
                                       "95% interval": [fmt.interval(a, b, 1) for a, b in zip(t.ci95_low, t.ci95_high)], "p (unadjusted)": [fmt.pval(p) for p in t.p_unadjusted],
                                       "q (all-route family, 51 tests)": [fmt.pval(q) for q in t.q_bh_all_routes]}), hide_index=True, height=300)
            ui.note(f"Family F4, all-route road record: {fam['n_tests']} tests, {fam['nominal']} with p below 0.05, {fam['bh_lt_05']} with q below 0.05 (Holm: {fam['holm_lt_05']}). "
                    "Signs are mixed across routes, so there is no single regional signal. Tests across routes are not independent, so q is indicative.")
        else:
            ui.plot(charts.forest_chart(charts.corridor_rows(ds, metric), "days per decade", 1), key="cor_routes_2001")
            t = ds["multiple_testing_126"]
            t = t[t.metric == metric].sort_values("p_unadjusted")
            st.dataframe(pd.DataFrame({"Corridor": t.location_id, "n": t.n, "Slope per decade (days)": [fmt.num(v, 1, True) for v in t.slope_per_decade],
                                       "95% interval": [fmt.interval(a, b, 1) for a, b in zip(t.ci95_low, t.ci95_high)], "p (unadjusted)": [fmt.pval(p) for p in t.p_unadjusted]}), hide_index=True, height=300)
            ui.note("This window belongs to a different family, so the all-route q is not shown here. The adjusted value for this window is the q across the 126 extended tests, "
                    "shown on each corridor's own result card and under Evidence Engine, Multiple testing.")

    with tabs[5]:
        ui.result_panel(f"Evidence conclusion · {loc.short}", "", paragraphs=ev.corridor_conclusion(ds, loc.id), lead=True,
                        source="Each sentence is generated from the computed results above; none is typed for a particular case.")
        with st.container(horizontal=True, gap="small"):
            if st.button("Audit this evidence", key="cor_ev"):
                ui.goto("evidence")
            if st.button("Export the Evidence Brief", type="primary", key="cor_brief"):
                ui.goto("brief")
