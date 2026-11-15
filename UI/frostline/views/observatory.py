"""Frostline Observatory: the landing view. Every indicator is computed from the approved data at render time."""
import datetime as dt

import streamlit as st

from .. import analysis as an
from .. import charts, fmt, ui
from ..registry import DEFAULT_LOCATION, DEFAULT_VARIABLE


def _begin(ds):
    ui.set_investigation(ds, DEFAULT_LOCATION, DEFAULT_VARIABLE, question_id=None)
    st.session_state["demo_step"] = 0


def render(ds):
    left, right = st.columns([0.92, 1.08], gap="large", vertical_alignment="center")
    with left:
        ui.html("<div class='fl-hero'>" + ui.kicker("Frostline Observatory · NASA Earth science data, 2001 to 2025") +
                "<h1>How is winter changing across Canada's North?</h1>"
                "<p>Follow NASA Earth science data from measurement to discovery, and investigate what the evidence reveals about seasonal transportation.</p></div>")
        with st.container(horizontal=True, gap="small"):
            if st.button("Begin an Investigation", type="primary", key="home_begin", on_click=_begin, args=(ds,)):
                ui.goto("demo")
            if st.button("Explore the Data", key="home_explore"):
                ui.goto("detective")
        ui.html("<div class='fl-label' style='margin-top:var(--s5)'>The guided investigation</div>")
        ui.steps(["Location", "Environmental Evidence", "Trend", "Comparison", "Road History", "Evidence Brief"])
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
    env = an.trend(ds, "dettah_bay", "fdd_octdec", 2001, 2024)
    b, e = ds.facts["bias"], ds.facts["extended_126"]
    ui.metrics([
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
    ])

    c = st.columns([1.1, 1], gap="large")
    with c[0]:
        ui.section("What you can do here")
        ui.html("<div class='fl-rows'>"
                "<div><span class='n'>01</span><div><div class='k'>Guided discovery</div><h4>Start from a question</h4>"
                "<p>Pick a plain question about northern winters. Frostline recommends the NASA variables that can answer it and tells you why each one is relevant.</p></div></div>"
                "<div><span class='n'>02</span><div><div class='k'>Research explorer</div><h4>Quantify the change</h4>"
                "<p>Choose a location, a variable and a period. See the real series, the rate of change per decade, its uncertainty and a significance test that always matches your selection.</p></div></div>"
                "<div><span class='n'>03</span><div><div class='k'>Evidence workspace</div><h4>Judge the evidence, then export it</h4>"
                "<p>The Evidence Engine separates observations, inference and limitations, exposes where sources disagree, and produces a reproducible Evidence Brief.</p></div></div>"
                "</div>")
        with st.container(horizontal=True, gap="small"):
            st.page_link(ui.PAGES["questions"], label="Questions", icon=":material/arrow_forward:")
            st.page_link(ui.PAGES["detective"], label="Trend Detective", icon=":material/arrow_forward:")
            st.page_link(ui.PAGES["evidence"], label="Evidence Engine", icon=":material/arrow_forward:")
    with c[1]:
        ui.section("Why it matters")
        ui.html("<p class='fl-sub'>Seasonal roads built on frozen lakes and rivers connect northern communities and carry supplies each winter. "
                "Asking how winter conditions and road seasons have changed means finding NASA datasets, cleaning daily records, computing seasonal indicators, "
                "fitting trends, locating government records and working out what can honestly be concluded. Frostline compresses that workflow into one guided, reproducible investigation.</p>")
        s = ds.facts["status_counts"]
        p = ds.facts["periods"]
        days = (dt.date.fromisoformat(p["nasa_daily_last"]) - dt.date.fromisoformat(p["nasa_daily_first"])).days + 1
        ui.caption(f"In this release: {fmt.count(days)} days of NASA daily data at each of two documented locations, "
                   f"{s['total_rows']} route-winters of government road records ({s['counts']['verified']} verified) across {s['routes']} NWT routes, "
                   f"and {fmt.count(b['paired_days'])} paired station days for validation.")
        ui.note("Frostline is a scientific investigation tool. It does not measure ice thickness, assess road safety, recommend routes or predict opening dates, "
                "and it does not show what produced any change in the road record.", "Scope")
