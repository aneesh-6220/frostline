"""Question-to-variable discovery: a deterministic mapping from plain questions to catalogued, available variables."""
import pandas as pd
import streamlit as st

from .. import analysis as an
from .. import fmt, ui
from ..registry import QUESTIONS, SOURCES, VARIABLES, primary_locations, variables_for


def _choose(ds, qid, vid, loc_id):
    ui.set_investigation(ds, location_id=loc_id, variable_id=vid, question_id=qid)


def catalogue(ds) -> pd.DataFrame:
    rows = []
    for v in VARIABLES.values():
        src = SOURCES[v.source_id]
        rows.append({"Variable": v.label, "Identifier": v.id, "Units": v.unit, "Group": ("Road record" if v.kind == "road" else "NASA core" if v.tier == "core" else "NASA exploratory"),
                     "Definition": v.definition, "Source": src.name, "Temporal resolution": v.temporal_resolution, "Spatial resolution": v.spatial_resolution,
                     "Valid period": fmt.period(v.valid_first, v.valid_last),
                     "Locations": "Dettah, Aklavik" if v.locations == "primary" else "Dettah, Aklavik and 7 supplementary corridors",
                     "Trend methods": "; ".join(v.methods) if v.id != "thaw_days_janmar" else "counts only; trend not estimated",
                     "Quality condition": v.quality, "Limitations": " ".join(v.limitations)})
    return pd.DataFrame(rows)


def render(ds):
    inv = ui.current()
    locs = an.locations(ds)
    ui.page_header("Guided discovery", "What would you like to investigate?",
                   "Choose a question. Frostline recommends variables that are actually available for your location and says why each one fits. "
                   "The mapping is a fixed, documented catalogue, not a language model.")
    qids = list(QUESTIONS)
    default = inv.question_id if inv.question_id in QUESTIONS else qids[0]
    qid = st.radio("Question", qids, index=qids.index(default), format_func=lambda k: QUESTIONS[k].text, key="q_pick", label_visibility="collapsed")
    q = QUESTIONS[qid]
    prim = primary_locations(locs)
    loc_id = st.segmented_control("Location", [l.id for l in prim], default=inv.location_id, format_func=lambda i: locs[i].short, key="q_loc", required=True)
    loc = locs[loc_id or inv.location_id]
    ui.html(f"<div class='fl-eyebrow' style='margin-top:1rem'>Recommended for: {ui.esc(q.text)}</div><div class='fl-sub' style='margin-bottom:.6rem'>{ui.esc(q.blurb)}</div>")
    available = {v.id for v in variables_for(loc)}
    recs = [VARIABLES[v] for v in q.variables if v in available]
    cols = st.columns(len(recs))
    for col, v in zip(cols, recs):
        with col:
            lo, hi = an.available_range(ds, loc.id, v.id)
            f = an.trend(ds, loc.id, v.id, lo, hi)
            src = SOURCES[v.source_id]
            ui.html(f"<div class='fl-card'><div class='k'>{'Road record' if v.kind == 'road' else 'NASA variable'} · {ui.esc(v.unit)}</div><h4>{ui.esc(v.label)}</h4>"
                    f"<p>{ui.esc(q.reasons.get(v.id, v.why))}</p><p style='margin-top:.5rem'>{ui.esc(v.why)}</p>"
                    f"<div class='fl-src'>{ui.esc(src.name)} · winters {fmt.period(lo, hi)} · n = {f.n} · {ui.esc(f.state_label.lower())}</div></div>")
            if st.button(f"Investigate {v.phrase}", key=f"q_go_{qid}_{v.id}", type="primary" if v is recs[0] else "secondary", width="stretch",
                         on_click=_choose, args=(ds, qid, v.id, loc.id)):
                ui.goto(q.next_view)
    ui.html(f"<div class='fl-src' style='margin-top:.6rem'>Each recommendation opens {ui.esc(q.next_label.lower().replace('open ', ''))} with this question, location and variable selected.</div>")
    if qid == "thaw":
        ui.note("Above-freezing midwinter days are almost absent from the NASA series at both locations, so their trend cannot be estimated. Frostline reports that plainly "
                "and offers the midwinter mean temperature as the analysable alternative.")

    st.write("")
    with st.expander("Variable catalogue: every variable Frostline can analyse", expanded=False):
        st.dataframe(catalogue(ds), hide_index=True, height=420)
        ui.html("<div class='fl-src'>Only variables with real data and a documented method are offered. Not offered and never to be added: ice thickness, "
                "safety or usability scores, any prediction, any threshold test, and freezing degree-days from monthly means.</div>")
