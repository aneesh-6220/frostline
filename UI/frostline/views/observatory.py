"""Frostline Observatory: the landing view. Every indicator is computed from the approved data at render time."""
import datetime as dt

import streamlit as st

from .. import analysis as an
from .. import charts, fmt, ui
from .. import giovanni as gv
from ..registry import DEFAULT_LOCATION, DEFAULT_VARIABLE


def _begin(ds):
    ui.set_investigation(ds, DEFAULT_LOCATION, DEFAULT_VARIABLE, question_id=None)
    st.session_state["demo_step"] = 0


def _giovanni_metric(ds) -> tuple:
    """The longest NASA record in the app: how many of its pre-declared seasonal tests survive correction, led by the strongest one.

    Falls back to the 24-winter NASA POWER freezing-degree-day result when no Giovanni extraction is deployed."""
    if not gv.available(ds):
        env = an.trend(ds, "dettah_bay", "fdd_octdec", 2001, 2024)
        return ("NASA freezing accumulation · Dettah", fmt.num(env.slope, 0, True), "°C-days per decade",
                f"95% interval {fmt.interval(env.ci_low, env.ci_high, 0)} over {env.n} winters: not statistically distinguishable from no change. That is not proof of no change.",
                "NASA POWER daily T2M (MERRA-2 reanalysis)")
    loc = gv.locations(ds)[0]
    full = [gv.trend(ds, loc, s) for s in gv.SEASON_ORDER]
    fam = [t for t in full if t.q is not None]
    best = min(fam, key=lambda t: t.q)
    n_sup = sum(t.q < an.ALPHA for t in fam)
    octdec = next(t for t in full if t.season == "octdec_mean_c")
    return (f"NASA Giovanni · Dettah cell, {gv.SEASON_LABEL[best.season].split(' (')[0].lower()}", fmt.num(best.slope_per_decade, 2, True), "°C per decade",
            f"{best.first} to {best.last}, 95% interval {fmt.interval(best.ci_low, best.ci_high, 2)}, q = {fmt.pval(best.q)}. "
            f"{n_sup} of the {len(fam)} seasonal tests on this {best.last - best.first + 1}-year record {'survives' if n_sup == 1 else 'survive'} correction; early winter (Oct to Dec, {fmt.num(octdec.slope_per_decade, 2, True)} °C per decade) "
            f"does not (q = {fmt.pval(octdec.q)}). One reanalysis grid cell, not a station.",
            "MERRA-2 monthly T2M through NASA Giovanni")


def render(ds):
    left, right = st.columns([0.92, 1.08], gap="large", vertical_alignment="center")
    with left:
        ui.html("<div class='fl-hero'>" + ui.kicker("Frostline Observatory · NASA Earth science data, 1980 to 2025") +
                "<h1>How is winter changing across Canada's North?</h1>"
                "<p>Pick a place, pull NASA observations, measure how its winters have changed, see how certain that change is, and export a reproducible "
                "Evidence Brief. Two documented ice roads add 32 winters of government operating records.</p></div>")
        with st.container(horizontal=True, gap="small"):
            if st.button("Begin an Investigation", type="primary", key="home_begin", on_click=_begin, args=(ds,)):
                ui.goto("demo")
            if st.button("Explore the Data on the map", key="home_explore", icon=":material/map:"):
                ui.goto("atlas")
        ui.journey(["Choose a place", "Retrieve NASA data", "Measure the trend", "Weigh the evidence", "Export a brief"])
    with right:
        f = an.trend(ds, DEFAULT_LOCATION, DEFAULT_VARIABLE, 2001, 2024)
        with st.container(key="fl_frame_home"):
            ui.html("<div class='fl-panel-head'><div><div class='fl-label'>Live from the data · Dettah, Yellowknife Bay</div>"
                    "<div class='fl-panel-title'>Early-winter freezing degree-days, 24 winters of NASA data</div></div>"
                    f"{ui.chip(f.state_label, ui.STATE_TONE[f.state])}</div>")
            ui.plot(charts.trend_chart(ds, f, height=320), key="home_chart")
            ui.caption(f"NASA POWER daily T2M (MERRA-2 reanalysis, grid-cell value). Theil-Sen estimate "
                       f"{fmt.num(f.slope, 0, True)} °C-days per decade, 95% interval {fmt.interval(f.ci_low, f.ci_high, 0)}: "
                       f"{f.state_label.lower()}.", top=True)

    ui.section("What the evidence shows so far", "Computed from the approved data on every load")
    op = an.trend(ds, "dettah_bay", "open_day", 1993, 2024)
    op_n = an.trend(ds, "dettah_bay", "open_day", 2001, 2024)
    b, e = ds.facts["bias"], ds.facts["extended_126"]
    long_metric = _giovanni_metric(ds)
    ui.metrics([
        ("Road record · Dettah", fmt.num(op.slope, 1, True), "days per decade",
         f"The ice road opened later over {fmt.period(op.first, op.last)} (95% interval {fmt.interval(op.ci_low, op.ci_high, 1)}; q = {fmt.pval(op.q)} across {op.q_family_n} route tests). "
         f"Exploratory and selection-biased; not supported after correction in the NASA-era window {fmt.period(op_n.first, op_n.last)} (q = {fmt.pval(op_n.q)}).",
         "NWT Bureau of Statistics, Table 108"),
        long_metric,
        ("NASA against the ground station", fmt.num(b["overall_oct_dec"], 1, True), "°C in Oct to Dec",
         f"NASA reanalysis runs colder than the Yellowknife A station across {fmt.count(b['paired_days'])} paired days. Frostline shows this disagreement instead of hiding it.",
         "NASA POWER and ECCC Yellowknife A"),
        ("Trend tests, corrected", f"{e['bh_lt_05']} of {e['n']}", "survive correction",
         f"{e['nominal']} of {e['n']} trend tests have p below 0.05 (about {e['expected_by_chance']} expected by chance). None survives correction for multiple testing.",
         "126-test family, winters 2001/02 to 2024/25"),
    ])

    c = st.columns([1.1, 1], gap="large")
    with c[0]:
        ui.section("Why it matters")
        ui.html("<p class='fl-sub'>Seasonal roads built on frozen lakes and rivers connect northern communities and carry supplies each winter. "
                "Asking how winter conditions and road seasons have changed means finding NASA datasets, cleaning daily records, computing seasonal indicators, "
                "fitting trends, locating government records and working out what can honestly be concluded. Frostline compresses that workflow into one guided, reproducible investigation.</p>")
    with c[1]:
        ui.section("Scope and data in this release")
        s = ds.facts["status_counts"]
        p = ds.facts["periods"]
        days = (dt.date.fromisoformat(p["nasa_daily_last"]) - dt.date.fromisoformat(p["nasa_daily_first"])).days + 1
        ui.note("Frostline is a scientific investigation tool. It does not measure ice thickness, assess road safety, recommend routes or predict opening dates, "
                "and it does not show what produced any change in the road record.", "Scope")
        ui.caption(f"In this release: {fmt.count(days)} days of NASA daily data at each of two documented locations, "
                   f"{s['total_rows']} route-winters of government road records ({s['counts']['verified']} verified) across {s['routes']} NWT routes, "
                   f"and {fmt.count(b['paired_days'])} paired station days for validation.")
