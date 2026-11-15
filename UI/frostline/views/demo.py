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
    c = st.columns([1, 1, 2.2])
    c[0].button("Back", icon=":material/arrow_back:", key=f"demo_back_{step}", disabled=step == 0, width="stretch", on_click=_go, args=(ds, step - 1))
    if step < len(STAGES) - 1:
        c[1].button(f"Next: {STAGES[step + 1]}", icon=":material/arrow_forward:", type="primary", key=f"demo_next_{step}", width="stretch", on_click=_go, args=(ds, step + 1))
    else:
        if c[1].button("Explore freely", icon=":material/explore:", type="primary", key="demo_free", width="stretch"):
            ui.goto("detective")


def render(ds):
    step = int(st.session_state.get("demo_step", 0))
    inv = ui.current()
    locs = an.locations(ds)
    loc = locs[inv.location_id]
    ui.html(f"<div class='fl-eyebrow'>Guided demo · stage {step + 1} of {len(STAGES)}</div>")
    ui.steps(STAGES, active=step)
    st.write("")

    if step == 0:
        ui.html("<div class='fl-title'>Winter is the road</div>"
                "<p class='fl-lede'>Across northern Canada, seasonal roads are built each winter on frozen lakes and rivers. They connect communities and carry supplies, and they exist only "
                "while the cold holds. People say winters are changing. Checking that claim properly is hard: it takes NASA climate data, daily records, seasonal indicators, trend statistics, "
                "government road records and a clear sense of what can and cannot be concluded.</p>")
        s, p = ds.facts["status_counts"], ds.facts["periods"]
        c = st.columns(3)
        c[0].markdown(ui.stat_card("NASA record", str(p["trend_winters_n"]), "winters", f"Daily NASA data for {fmt.period(p['trend_winters_first'], p['trend_winters_last'])}, with {p['missing_nasa_days_in_trend_seasons']} missing days", "NASA POWER daily (MERRA-2)"), unsafe_allow_html=True)
        c[1].markdown(ui.stat_card("Government record", str(s["winters"]), "winters", f"Opening and closing dates for {s['routes']} NWT routes, {s['counts']['verified']} of {s['total_rows']} route-winters verified", "NWT Bureau of Statistics, Table 108"), unsafe_allow_html=True)
        c[2].markdown(ui.stat_card("Ground truth", fmt.count(ds.facts["bias"]["paired_days"]), "paired days", "Station observations used to check the NASA values, including where they disagree", "ECCC Yellowknife A"), unsafe_allow_html=True)
        ui.note("Frostline turns that workflow into one investigation. It reports what the evidence supports and what it does not. It is not a road-safety tool and it predicts nothing.")

    elif step == 1:
        ui.html("<div class='fl-title'>Choose a real northern case study</div>"
                "<p class='fl-lede'>Two documented ice roads in the Northwest Territories, about 1,100 km apart and very different in kind. Pick one; the rest of the demo follows your choice.</p>")
        c = st.columns([1.35, 1], gap="large")
        with c[0]:
            st.pydeck_chart(atlas.build_deck(ds, inv.location_id), key="demo_map", height=400)
            ui.html("<div class='fl-src'>Markers: calculated sampling points. Rectangles: NASA grid cells. No road geometry is drawn.</div>")
        with c[1]:
            for l in primary_locations(locs):
                st.button(l.name, key=f"demo_pick_{l.id}", type="primary" if l.id == inv.location_id else "secondary", width="stretch", icon=":material/location_on:", on_click=_pick, args=(ds, l.id))
            ui.html(f"<div class='fl-card' style='margin-top:.6rem'><div class='k'>{ui.esc(loc.role)} case study</div><h4>{ui.esc(loc.name)}</h4><p>{ui.esc(loc.setting)}</p>"
                    f"<p style='margin-top:.5rem'>{ui.esc(loc.access)}</p></div>")

    elif step == 2:
        f = an.trend(ds, inv.location_id, inv.variable_id, inv.first, inv.last)
        var = inv.variable
        ui.html(f"<div class='fl-title'>NASA data: {ui.esc(var.phrase)} at {ui.esc(loc.short)}</div>"
                f"<p class='fl-lede'>{ui.esc(var.why)} {ui.esc(var.definition)} Each point is one winter of NASA POWER daily data, a MERRA-2 reanalysis value for the grid cell containing the road.</p>")
        ui.plot(charts.trend_chart(ds, f, height=400), key="demo_chart_data")
        ui.html("<div class='fl-src' style='margin-top:-.5rem'>Hover any winter to read its value. Change the variable or period in the sidebar and the chart follows.</div>")
        if var.is_temperature:
            ui.bias_caveat(ds)

    elif step == 3:
        f = an.trend(ds, inv.location_id, inv.variable_id, inv.first, inv.last)
        ui.html("<div class='fl-title'>Has it changed, and how sure are we?</div>"
                "<p class='fl-lede'>A rate of change per decade, a 95% interval, a significance test and a correction for the number of tests run. "
                "A result that is not statistically resolved is still a scientific result.</p>")
        c = st.columns([1.5, 1], gap="large")
        with c[0]:
            ui.plot(charts.trend_chart(ds, f, height=390), key="demo_chart_trend")
            ui.html(f"<div class='fl-note'><b style='color:#E8EEF7'>In plain language.</b> {ui.esc(an.plain_language(ds, f))} {ui.esc(f.sentence)}</div>")
        with c[1]:
            ui.finding_card(ds, f)

    elif step == 4:
        f = an.trend(ds, inv.location_id, "open_day", 1993, 2024)
        ui.html(f"<div class='fl-title'>What the road record shows at {ui.esc(loc.short)}</div>"
                "<p class='fl-lede'>The territorial government publishes the date each road opened and closed, every winter since 1993/94. This is a record of operations, shown beside the NASA data, never merged with it.</p>")
        c = st.columns([1.5, 1], gap="large")
        with c[0]:
            ui.plot(charts.timeline_chart(ds, inv.location_id, "fdd_octdec", height=500), key="demo_timeline")
        with c[1]:
            ui.finding_card(ds, f, show_table=False)
            ui.html("<div class='fl-finding'><div class='fl-eyebrow' style='margin:0'>Evidence conclusion</div>" + "".join(f"<p class='dim'>{ui.esc(s)}</p>" for s in ev.corridor_conclusion(ds, inv.location_id)[2:]) + "</div>")

    else:
        rep = ev.assess(ds, inv.location_id, inv.variable_id, inv.first, inv.last)
        ui.html("<div class='fl-title'>Audit the evidence, then take it with you</div>"
                f"<p class='fl-lede'>{ui.esc(rep.headline)} {ui.esc(rep.suitability)}</p>")
        ui.dimension_cards(rep, columns=3)
        ui.html("<div class='fl-eyebrow' style='margin-top:.6rem'>Reusable finding</div>")
        ui.brief_downloads(ds, inv, key="demo_brief")
        ui.html("<div class='fl-src'>The brief contains the question, location, data, trend, uncertainty, evidence assessment, limitations, sources and file hashes for this exact investigation.</div>")

    _nav(ds, step)
