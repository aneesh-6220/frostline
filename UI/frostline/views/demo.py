"""Guided demo: a six-stage path through the production application.

Every stage renders the same components, data and analysis functions as the free-exploration views.
The stage only fixes the starting selection; the sidebar controls stay live throughout.
"""
import streamlit as st

from .. import analysis as an
from .. import charts, evidence as ev, fmt, ui
from ..registry import primary_locations
from . import atlas

STAGES = ["The problem", "The geography", "The NASA data", "The scientific finding", "The transportation evidence", "The Evidence Brief"]


def _go(ds, step):
    step = max(0, min(len(STAGES) - 1, step))
    st.session_state["demo_step"] = step
    if step in (2, 3):
        ui.set_investigation(ds, variable_id="fdd_octdec", question_id="freezing")
    elif step == 4:
        ui.set_investigation(ds, variable_id="open_day", question_id="roads")


def _pick(ds, lid):
    ui.set_investigation(ds, location_id=lid)


def _nav(ds, step):
    st.write("")
    with st.container(horizontal=True, gap="small", key="fl_demo_nav"):
        st.button("Back", icon=":material/arrow_back:", key=f"demo_back_{step}", disabled=step == 0, on_click=_go, args=(ds, step - 1))
        if step < len(STAGES) - 1:
            st.button(f"Next: {STAGES[step + 1]}", icon=":material/arrow_forward:", icon_position="right", type="primary", key=f"demo_next_{step}", on_click=_go, args=(ds, step + 1))
        else:
            if st.button("Explore freely", icon=":material/arrow_forward:", icon_position="right", type="primary", key="demo_free"):
                ui.goto("detective")


def render(ds):
    step = int(st.session_state.get("demo_step", 0))
    inv = ui.current()
    locs = an.locations(ds)
    loc = locs[inv.location_id]
    ui.html(ui.kicker(f"Guided demo · stage {step + 1} of {len(STAGES)}"))
    ui.steps(STAGES, active=step)
    ui.html("<div class='fl-gap'></div>")

    if step == 0:
        ui.html("<header class='fl-page'><div class='fl-title' role='heading' aria-level='1'>Winter is the road</div>"
                "<p class='fl-lede'>Across northern Canada, seasonal roads are built each winter on frozen lakes and rivers. They connect communities and carry supplies, and they exist only "
                "while the cold holds. People say winters are changing. Checking that claim properly is hard: it takes NASA climate data, daily records, seasonal indicators, trend statistics, "
                "government road records and a clear sense of what can and cannot be concluded.</p></header>")
        s, p = ds.facts["status_counts"], ds.facts["periods"]
        ui.metrics([
            ("NASA record", str(p["trend_winters_n"]), "winters", f"Daily NASA data for {fmt.period(p['trend_winters_first'], p['trend_winters_last'])}, with {p['missing_nasa_days_in_trend_seasons']} missing days", "NASA POWER daily (MERRA-2)"),
            ("Government record", str(s["winters"]), "winters", f"Opening and closing dates for {s['routes']} NWT routes, {s['counts']['verified']} of {s['total_rows']} route-winters verified", "NWT Bureau of Statistics, Table 108"),
            ("Ground truth", fmt.count(ds.facts["bias"]["paired_days"]), "paired days", "Station observations used to check the NASA values, including where they disagree", "ECCC Yellowknife A")])
        ui.note("Frostline turns that workflow into one investigation. It reports what the evidence supports and what it does not. It is not a road-safety tool and it predicts nothing.")

    elif step == 1:
        ui.page_header("", "Choose a real northern case study",
                       "Two documented ice roads in the Northwest Territories, about 1,100 km apart and very different in kind. Pick one; the rest of the demo follows your choice.")
        c = st.columns([1.35, 1], gap="large")
        with c[0]:
            st.pydeck_chart(atlas.build_deck(ds, inv.location_id), key="demo_map", height=400)
            ui.caption("Markers: calculated sampling points. Rectangles: NASA grid cells. No road geometry is drawn.")
        with c[1]:
            for l in primary_locations(locs):
                st.button(l.name, key=f"demo_pick_{l.id}", type="primary" if l.id == inv.location_id else "secondary", width="stretch", on_click=_pick, args=(ds, l.id))
            ui.html(f"<div class='fl-card' style='margin-top:var(--s2)'><div class='k'>{ui.esc(loc.role)} case study</div><h4>{ui.esc(loc.name)}</h4><p>{ui.esc(loc.setting)}</p>"
                    f"<p>{ui.esc(loc.access)}</p></div>")

    elif step == 2:
        f = an.trend(ds, inv.location_id, inv.variable_id, inv.first, inv.last)
        var = inv.variable
        ui.page_header("", f"NASA data: {var.phrase} at {loc.short}",
                       f"{var.why} {var.definition} Each point is one winter of NASA POWER daily data, a MERRA-2 reanalysis value for the grid cell containing the road.")
        with st.container(key="fl_frame_demo_data"):
            ui.plot(charts.trend_chart(ds, f, height=400), key="demo_chart_data")
            ui.caption("Hover any winter to read its value. Change the variable or period in the sidebar and the chart follows.", top=True)
        if var.is_temperature:
            ui.bias_caveat(ds)

    elif step == 3:
        f = an.trend(ds, inv.location_id, inv.variable_id, inv.first, inv.last)
        ui.page_header("", "Has it changed, and how sure are we?",
                       "A rate of change per decade, a 95% interval, a significance test and a correction for the number of tests run. "
                       "A result that is not statistically resolved is still a scientific result.")
        c = st.columns([1.5, 1], gap="large")
        with c[0]:
            with st.container(key="fl_frame_demo_trend"):
                ui.plot(charts.trend_chart(ds, f, height=390), key="demo_chart_trend")
            ui.plain_language(ds, f)
        with c[1]:
            ui.finding_card(ds, f)

    elif step == 4:
        f = an.trend(ds, inv.location_id, "open_day", 1993, 2024)
        ui.page_header("", f"What the road record shows at {loc.short}",
                       "The territorial government publishes the date each road opened and closed, every winter since 1993/94. This is a record of operations, shown beside the NASA data, never merged with it.")
        c = st.columns([1.5, 1], gap="large")
        with c[0]:
            with st.container(key="fl_frame_demo_timeline"):
                ui.plot(charts.timeline_chart(ds, inv.location_id, "fdd_octdec", height=500), key="demo_timeline")
        with c[1]:
            ui.finding_card(ds, f, show_table=False)
            ui.result_panel("Evidence conclusion", "", dim=ev.corridor_conclusion(ds, inv.location_id)[2:])

    else:
        rep = ev.assess(ds, inv.location_id, inv.variable_id, inv.first, inv.last)
        ui.page_header("", "Audit the evidence, then take it with you", f"{rep.headline} {rep.suitability}")
        ui.dimension_cards(rep, columns=3)
        ui.section("Reusable finding")
        ui.brief_downloads(ds, inv, key="demo_brief")
        ui.caption("The brief contains the question, location, data, trend, uncertainty, evidence assessment, limitations, sources and file hashes for this exact investigation.")

    _nav(ds, step)
