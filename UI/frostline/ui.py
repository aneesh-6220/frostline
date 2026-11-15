"""Shared Streamlit layer: theme, the shared investigation state, and components used by every view.

One investigation state (location, variable, analysis window, guiding question) lives in st.session_state.
Every view reads it through current(), and every statistic on screen is derived from it through
analysis.trend(), so a change of selection re-derives every number, interval and sentence.
"""
from __future__ import annotations

import html as _html
from dataclasses import dataclass

import streamlit as st

from . import APP_NAME, TAGLINE, TEAM_NAME
from . import analysis as an
from . import brief as brief_mod
from . import evidence as ev
from . import fmt
from .registry import DEFAULT_LOCATION, DEFAULT_VARIABLE, QUESTIONS, SOURCES, VARIABLES, primary_locations, variables_for

PAGES: dict = {}   # view key -> st.Page, filled by the entrypoint on every run

STATE_TONE = {an.SUPPORTED: "good", an.UNRESOLVED: "neutral", an.EXPLORATORY: "warn", an.INSUFFICIENT: "muted", an.UNAVAILABLE: "muted"}

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
:root{--bg:#0B1220;--surface:#111B2E;--surface2:#16233A;--line:#22314D;--ink:#E8EEF7;--ink2:#A9B8CE;--ink3:#71829B;
--glacier:#7CCBF7;--blue:#3987E5;--amber:#FAB219;--good:#3FBF6B;--serious:#EC835A;}
html,body,[class*="css"],.stApp{font-family:'Inter','Segoe UI',system-ui,-apple-system,sans-serif}
.stApp{background:radial-gradient(1200px 520px at 78% -160px,rgba(57,135,229,.16),transparent 62%),var(--bg)}
.block-container{padding-top:3.4rem;padding-bottom:4rem;max-width:1280px}
h1,h2,h3{font-family:'Space Grotesk','Inter',system-ui,sans-serif;letter-spacing:-.01em;color:var(--ink)}
.fl-eyebrow{font-size:.74rem;letter-spacing:.18em;text-transform:uppercase;color:var(--glacier);font-weight:600;margin-bottom:.35rem}
.fl-title{font-family:'Space Grotesk','Inter',sans-serif;font-size:2.05rem;line-height:1.14;font-weight:700;color:var(--ink);margin:0 0 .45rem}
.fl-lede{color:var(--ink2);font-size:1.02rem;line-height:1.6;max-width:62rem;margin:0 0 1.1rem}
.fl-hero{padding:1.2rem 0 .4rem}
.fl-hero h1{font-family:'Space Grotesk','Inter',sans-serif;font-size:3.4rem;line-height:1.04;font-weight:700;margin:.3rem 0 1rem;max-width:15ch;padding:0}
.fl-hero p{font-size:1.16rem;line-height:1.6;color:var(--ink2);max-width:40rem;margin:0}
.fl-brand{font-family:'Space Grotesk',sans-serif;font-weight:700;letter-spacing:.3em;font-size:.86rem;color:var(--ink)}
.fl-brand span{display:block;color:var(--ink3);font-weight:500;letter-spacing:.06em;font-size:.78rem;margin-top:.2rem}
.fl-card{background:linear-gradient(180deg,rgba(22,35,58,.92),rgba(17,27,46,.92));border:1px solid var(--line);border-radius:14px;padding:1.05rem 1.2rem;height:100%}
.fl-card h4{font-family:'Space Grotesk',sans-serif;font-size:1rem;color:var(--ink);margin:0 0 .35rem;padding:0}
.fl-card p{color:var(--ink2);font-size:.9rem;line-height:1.55;margin:0}
.fl-card .k{font-size:.72rem;letter-spacing:.14em;text-transform:uppercase;color:var(--ink3);font-weight:600;margin-bottom:.4rem}
.fl-stat{font-family:'Space Grotesk',sans-serif;font-size:2.1rem;font-weight:700;color:var(--ink);line-height:1.1}
.fl-stat small{display:block;font-family:'Inter',sans-serif;font-size:.84rem;font-weight:500;color:var(--ink2);margin:.15rem 0 0;line-height:1.3}
.fl-sub{color:var(--ink2);font-size:.84rem;line-height:1.5;margin-top:.3rem}
.fl-src{color:var(--ink3);font-size:.76rem;margin-top:.45rem}
.fl-chip{display:inline-flex;align-items:center;gap:.4rem;padding:.2rem .7rem;border-radius:999px;font-size:.76rem;font-weight:600;border:1px solid var(--line);color:var(--ink);background:rgba(255,255,255,.04);white-space:nowrap}
.fl-chip i{width:.5rem;height:.5rem;border-radius:50%;display:inline-block;background:var(--ink3)}
.fl-chip.good i{background:var(--good)}.fl-chip.warn i{background:var(--amber)}.fl-chip.alert i{background:var(--serious)}.fl-chip.neutral i{background:var(--glacier)}
.fl-chip.good{border-color:rgba(63,191,107,.5)}.fl-chip.warn{border-color:rgba(250,178,25,.5)}.fl-chip.alert{border-color:rgba(236,131,90,.55)}.fl-chip.neutral{border-color:rgba(124,203,247,.45)}
.fl-finding{border:1px solid var(--line);border-left:3px solid var(--glacier);border-radius:12px;background:rgba(17,27,46,.9);padding:1rem 1.2rem;margin:.2rem 0 .8rem}
.fl-finding.good{border-left-color:var(--good)}.fl-finding.warn{border-left-color:var(--amber)}.fl-finding.muted{border-left-color:var(--ink3)}
.fl-finding .big{font-family:'Space Grotesk',sans-serif;font-size:1.9rem;font-weight:700;color:var(--ink);line-height:1.15;margin:.5rem 0 .15rem}
.fl-finding .big small{display:block;font-family:'Inter',sans-serif;font-size:.88rem;font-weight:500;color:var(--ink2);margin:.15rem 0 0;line-height:1.35}
.fl-finding p{color:var(--ink);font-size:.93rem;line-height:1.55;margin:.35rem 0 0}
.fl-finding p.dim{color:var(--ink2);font-size:.86rem}
.fl-caveat{border:1px solid rgba(250,178,25,.35);background:rgba(250,178,25,.07);border-radius:10px;padding:.6rem .9rem;color:var(--ink);font-size:.84rem;line-height:1.5;margin:.5rem 0}
.fl-caveat b{color:var(--amber)}
.fl-note{border:1px solid var(--line);background:rgba(124,203,247,.06);border-radius:10px;padding:.6rem .9rem;color:var(--ink2);font-size:.86rem;line-height:1.5;margin:.5rem 0}
.fl-kv{width:100%;border-collapse:collapse;font-size:.86rem}
.fl-kv td{padding:.42rem .2rem;border-bottom:1px solid rgba(34,49,77,.8);vertical-align:top;color:var(--ink)}
.fl-kv td:first-child{color:var(--ink2);width:44%;padding-right:.8rem}
.fl-dim{border:1px solid var(--line);border-radius:12px;background:rgba(17,27,46,.85);padding:.85rem 1rem;margin-bottom:.7rem}
.fl-dim .h{display:flex;justify-content:space-between;align-items:center;gap:.6rem;margin-bottom:.3rem}
.fl-dim .h b{font-family:'Space Grotesk',sans-serif;color:var(--ink);font-size:.96rem}
.fl-dim .s{color:var(--ink);font-size:.88rem;margin-bottom:.3rem}
.fl-dim ul{margin:.2rem 0 0;padding-left:1.05rem}.fl-dim li{color:var(--ink2);font-size:.83rem;line-height:1.5;margin-bottom:.15rem}
.fl-steps{display:flex;flex-wrap:wrap;gap:.45rem;align-items:center;margin:.9rem 0 .2rem}
.fl-steps span{border:1px solid var(--line);border-radius:999px;padding:.3rem .8rem;font-size:.82rem;color:var(--ink);background:rgba(255,255,255,.03)}
.fl-steps em{color:var(--ink3);font-style:normal}
.fl-steps span.on{border-color:var(--glacier);background:rgba(124,203,247,.12);font-weight:600}
.fl-steps span.done{color:var(--ink2)}
.fl-foot{color:var(--ink3);font-size:.78rem;line-height:1.6;border-top:1px solid var(--line);margin-top:2.4rem;padding-top:1rem}
.fl-layer{border-left:2px solid var(--line);padding:.1rem 0 .1rem .9rem;margin:.2rem 0 .9rem}
.fl-layer b{font-family:'Space Grotesk',sans-serif;color:var(--ink);font-size:.95rem}
.fl-layer .q{color:var(--ink3);font-size:.8rem;margin-bottom:.25rem}
.fl-layer li{color:var(--ink2);font-size:.86rem;line-height:1.55}
.fl-layer ul{margin:.1rem 0 0;padding-left:1.05rem}
section[data-testid="stSidebar"]{background:#0E1728;border-right:1px solid var(--line)}
section[data-testid="stSidebar"] .fl-eyebrow{margin-top:.2rem}
div[data-testid="stMetric"]{background:rgba(17,27,46,.85);border:1px solid var(--line);border-radius:12px;padding:.7rem .9rem}
.stTabs [data-baseweb="tab"]{font-weight:600}
@media (max-width:900px){.fl-hero h1{font-size:2.4rem}.fl-title{font-size:1.6rem}}
</style>
"""


def esc(s) -> str:
    return _html.escape(str(s), quote=False)


def html(body: str) -> None:
    st.markdown(body, unsafe_allow_html=True)


def inject_theme() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


# ------------------------------------------------------------------ state
@dataclass(frozen=True)
class Investigation:
    location_id: str
    variable_id: str
    first: int
    last: int
    question_id: str | None

    @property
    def variable(self):
        return VARIABLES[self.variable_id]


def init_state(ds) -> None:
    ss = st.session_state
    locs = an.locations(ds)
    if ss.get("loc") not in locs or not locs[ss["loc"]].is_primary_pair:
        ss["loc"] = DEFAULT_LOCATION
    if ss.get("var") not in VARIABLES:
        ss["var"] = DEFAULT_VARIABLE
    lo, hi = an.available_range(ds, ss["loc"], ss["var"])
    if not (isinstance(ss.get("first"), int) and isinstance(ss.get("last"), int) and lo <= ss["first"] <= ss["last"] <= hi):
        ss["first"], ss["last"] = lo, hi
    ss.setdefault("question", None)
    ss.setdefault("demo_step", 0)


def set_investigation(ds, location_id: str | None = None, variable_id: str | None = None, window: tuple | None = None, question_id: str | None = "__keep__") -> None:
    """Change the shared investigation. A new location or variable resets the window to that record's full range."""
    ss = st.session_state
    if location_id:
        ss["loc"] = location_id
    if variable_id:
        ss["var"] = variable_id
    lo, hi = an.available_range(ds, ss["loc"], ss["var"])
    if window:
        ss["first"], ss["last"] = max(lo, int(window[0])), min(hi, int(window[1]))
    elif location_id or variable_id:
        ss["first"], ss["last"] = lo, hi
    if question_id != "__keep__":
        ss["question"] = question_id


def current() -> Investigation:
    ss = st.session_state
    return Investigation(ss["loc"], ss["var"], int(ss["first"]), int(ss["last"]), ss.get("question"))


def goto(view: str) -> None:
    st.switch_page(PAGES[view])


# ---------------------------------------------------------------- console
def _var_label(vid: str) -> str:
    v = VARIABLES[vid]
    return v.short + (" (exploratory)" if v.tier == "exploratory" else "")


def _on_loc(ds):
    set_investigation(ds, location_id=st.session_state["w_loc"])


def _on_var(ds):
    set_investigation(ds, variable_id=st.session_state["w_var"])


def _on_period(ds):
    ss = st.session_state
    value = ss.get("w_period")
    if isinstance(value, (tuple, list)) and len(value) == 2:
        set_investigation(ds, window=(min(value), max(value)))
        ss["_w_period_canon"] = (ss["loc"], ss["var"], ss["first"], ss["last"])


def _on_preset(ds, window):
    set_investigation(ds, window=window)


def console(ds, where=None) -> Investigation:
    """The shared investigation controls. Rendered in the sidebar on every view."""
    box = where or st.sidebar
    ss = st.session_state
    locs = an.locations(ds)
    prim = [l.id for l in primary_locations(locs)]
    with box:
        html(f"<div class='fl-brand'>{APP_NAME.upper()}<span>by {TEAM_NAME}</span></div><div class='fl-src' style='margin:.25rem 0 1.1rem'>{TAGLINE}</div>")
        html("<div class='fl-eyebrow'>Current investigation</div>")
        ss["w_loc"] = ss["loc"]
        st.selectbox("Location", prim, format_func=lambda i: locs[i].road_name, key="w_loc", on_change=_on_loc, args=(ds,),
                     help="The two documented case studies. Statistics, charts and the Evidence Brief all follow this choice.")
        if VARIABLES[ss["var"]].tier == "exploratory":
            ss["show_exploratory"] = True
        ss.setdefault("show_exploratory", False)
        opts = [v.id for v in variables_for(locs[ss["loc"]]) if v.tier == "core" or ss["show_exploratory"]]
        ss["w_var"] = ss["var"]
        st.selectbox("Variable", opts, format_func=_var_label, key="w_var", on_change=_on_var, args=(ds,),
                     help="NASA environmental variables and the government road record. Exploratory variables have no station check.")
        st.toggle("Include exploratory NASA variables", key="show_exploratory", disabled=VARIABLES[ss["var"]].tier == "exploratory",
                  help="Skin temperature, precipitation, wind, humidity and surface radiation. They have no station check and are offered for exploration only.")
        lo, hi = an.available_range(ds, ss["loc"], ss["var"])
        years = list(range(lo, hi + 1))
        # the slider keeps one key (so it keeps keyboard focus); a change made elsewhere (a preset, a new variable) is pushed into it
        canon = (ss["loc"], ss["var"], ss["first"], ss["last"])
        if "w_period" in ss and ss.get("_w_period_canon") != canon:
            ss["w_period"] = (ss["first"], ss["last"])
        ss["_w_period_canon"] = canon
        st.select_slider("Analysis period (winters)", options=years, value=(ss["first"], ss["last"]), format_func=fmt.winter, key="w_period", on_change=_on_period, args=(ds,),
                         help="Winter y runs Oct 1 of y to Mar 31 of y+1. Changing the period recomputes every statistic.")
        var = VARIABLES[ss["var"]]
        if len(var.fixed_windows) > 1 or (ss["first"], ss["last"]) not in var.fixed_windows:
            for w in var.fixed_windows or ((lo, hi),):
                st.button("Approved window: " + fmt.period(*w), key=f"preset_{w[0]}_{w[1]}", on_click=_on_preset, args=(ds, w), width="stretch",
                          type="primary" if (ss["first"], ss["last"]) == w else "secondary", help="A fixed window whose result carries a multiplicity-adjusted q.")
        inv = current()
        f = an.trend(ds, inv.location_id, inv.variable_id, inv.first, inv.last)
        fixed = an.is_fixed_window(inv.variable_id, inv.first, inv.last)
        html(f"<div style='margin:.7rem 0 .3rem'>{chip(f.state_label, STATE_TONE[f.state])}</div>"
             f"<div class='fl-src'>{fmt.period(inv.first, inv.last)} · n = {f.n} winters · "
             f"{'approved fixed window' if fixed else 'user-selected window: exploratory, not adjusted for multiple testing'}</div>")
        html(f"<div class='fl-src' style='margin-top:1.2rem'>Data digest {ds.digest} · all values from the approved files in UI/data_real · no live download</div>")
    return inv


# -------------------------------------------------------------- components
def chip(label: str, tone: str = "neutral") -> str:
    return f"<span class='fl-chip {tone}'><i></i>{esc(label)}</span>"


def page_header(eyebrow: str, title: str, lede: str = "") -> None:
    html(f"<div class='fl-eyebrow'>{esc(eyebrow)}</div><div class='fl-title'>{esc(title)}</div>" + (f"<p class='fl-lede'>{esc(lede)}</p>" if lede else ""))


def caveat(text: str, label: str = "Caveat") -> None:
    html(f"<div class='fl-caveat'><b>{esc(label)}.</b> {esc(text)}</div>")


def note(text: str) -> None:
    html(f"<div class='fl-note'>{esc(text)}</div>")


def bias_caveat(ds) -> None:
    """The required caveat beside every NASA temperature figure (text from canonical_facts.json)."""
    caveat(ds.facts["bias_caveat"] + " Absolute NASA values are not local conditions.", "Reanalysis caveat")


def provenance_line(ds, var, loc) -> str:
    src = SOURCES[var.source_id]
    if var.kind == "road":
        return f"Source: {src.name} (government record of operations) · {loc.road_name}"
    return f"Source: {src.name}, parameter {var.power_parameter} · {src.kind}, {var.spatial_resolution}"


def kv_table(rows) -> str:
    return "<table class='fl-kv'>" + "".join(f"<tr><td>{esc(k)}</td><td>{esc(v)}</td></tr>" for k, v in rows) + "</table>"


def finding_card(ds, f: an.Finding, title: str | None = None, show_table: bool = True) -> None:
    """One result with everything the contract requires beside it: n, period, units, intervals, p, q, status and provenance."""
    var, loc = VARIABLES[f.variable_id], an.locations(ds)[f.location_id]
    tone = STATE_TONE[f.state]
    d = var.slope_decimals
    head = f"<div style='display:flex;justify-content:space-between;gap:.6rem;align-items:center;flex-wrap:wrap'><span class='fl-eyebrow' style='margin:0'>{esc(title or var.short + ' · ' + loc.short)}</span>{chip(f.state_label, tone)}</div>"
    if f.estimated:
        big = (f"<div class='big'>{fmt.num(f.slope, d, True)}<small>{esc(var.unit_per_decade)} · {esc(f.direction)}</small></div>"
               f"<p class='dim'>95% interval {fmt.interval(f.ci_low, f.ci_high, d)} · n = {f.n} winters · {fmt.period(f.first, f.last)}</p>")
    else:
        big = f"<div class='big'>Not estimated</div><p class='dim'>n = {f.n} winters · {fmt.period(f.first, f.last)}</p>"
    body = f"<p>{esc(f.sentence)}</p>" + "".join(f"<p class='dim'>{esc(s)}</p>" for s in f.extra_sentences)
    html(f"<div class='fl-finding {tone}'>{head}{big}{body}<div class='fl-src'>{esc(provenance_line(ds, var, loc))}</div></div>")
    if show_table:
        html(kv_table(brief_mod.stat_rows(ds, f)))
    if var.is_temperature:
        bias_caveat(ds)


def dimension_cards(report: ev.EvidenceReport, columns: int = 2) -> None:
    cols = st.columns(columns)
    for i, d in enumerate(report.dimensions):
        with cols[i % columns]:
            html(f"<div class='fl-dim'><div class='h'><b>{esc(d.title)}</b>{chip(d.state, d.tone)}</div><div class='s'>{esc(d.summary)}</div><ul>"
                 + "".join(f"<li>{esc(r)}</li>" for r in d.reasons) + "</ul>"
                 + (f"<div class='fl-src'>From: {esc(', '.join(d.sources))}</div>" if d.sources else "") + "</div>")


def layer_blocks(report: ev.EvidenceReport, keys=None) -> None:
    for layer in report.layers:
        if keys and layer.key not in keys:
            continue
        html(f"<div class='fl-layer'><b>{esc(layer.title)}</b><div class='q'>{esc(layer.question)}</div><ul>" + "".join(f"<li>{esc(i)}</li>" for i in layer.items) + "</ul></div>")


def steps(labels, active: int | None = None) -> None:
    parts = []
    for i, lab in enumerate(labels):
        cls = "on" if active == i else "done" if (active is not None and i < active) else ""
        parts.append(f"<span class='{cls}'>{esc(lab)}</span>")
    html("<div class='fl-steps'>" + "<em>→</em>".join(parts) + "</div>")


def card(kicker: str, title: str, text: str) -> str:
    return f"<div class='fl-card'><div class='k'>{esc(kicker)}</div><h4>{esc(title)}</h4><p>{esc(text)}</p></div>"


def stat_card(kicker: str, value: str, unit: str, sub: str, source: str) -> str:
    return (f"<div class='fl-card'><div class='k'>{esc(kicker)}</div><div class='fl-stat'>{esc(value)}<small>{esc(unit)}</small></div>"
            f"<div class='fl-sub'>{esc(sub)}</div><div class='fl-src'>{esc(source)}</div></div>")


def footer() -> None:
    html(f"<div class='fl-foot'>{APP_NAME} by {TEAM_NAME} · NASA Space Apps Challenge 2026, Be An Earth System Trend Detective! · "
         "An exploratory scientific investigation tool. It does not assess road safety, measure ice or predict opening dates, and it makes no statement of cause. "
         "Built with AI assistance; see Methods and sources for the disclosure. NASA does not endorse this project.</div>")


def plot(fig, key: str) -> None:
    from .charts import CONFIG

    st.plotly_chart(fig, key=key, config=CONFIG, theme=None)


def brief_downloads(ds, inv: Investigation, key: str = "brief") -> brief_mod.Brief:
    b = brief_mod.build(ds, inv.location_id, inv.variable_id, inv.first, inv.last, inv.question_id)
    c1, c2, c3 = st.columns(3)
    c1.download_button("Download Evidence Brief (HTML)", b.html, file_name=b.filename_stem + ".html", mime="text/html", type="primary", key=f"{key}_html", width="stretch", on_click="ignore")
    c2.download_button("Download data (CSV)", b.csv, file_name=b.filename_stem + ".csv", mime="text/csv", key=f"{key}_csv", width="stretch", on_click="ignore")
    c3.download_button("Download analysis record (JSON)", b.json, file_name=b.filename_stem + ".json", mime="application/json", key=f"{key}_json", width="stretch", on_click="ignore")
    return b
