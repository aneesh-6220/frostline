"""Regional trend comparison: one variable, matched winters, separate trends, and a test on the difference series."""
import pandas as pd
import streamlit as st

from .. import analysis as an
from .. import charts, fmt, ui
from ..registry import VARIABLES


def _set_var(ds):
    ui.set_investigation(ds, variable_id=st.session_state["cmp_var"])


def render(ds):
    inv = ui.current()
    locs = an.locations(ds)
    ui.page_header("Regional comparison", "Does the pattern differ somewhere else?",
                   "The same NASA variable at Dettah and Aklavik, on the winters present in both series. Slopes are said to differ only when a test on the difference supports it.")
    env = [v.id for v in VARIABLES.values() if v.kind == "environmental" and v.tier == "core" and v.id != "thaw_days_janmar"]
    vid = inv.variable_id if inv.variable_id in env else "fdd_octdec"
    c1, c2 = st.columns([1.2, 1])
    st.session_state["cmp_var"] = vid
    c1.selectbox("Environmental variable", env, format_func=lambda i: VARIABLES[i].label, key="cmp_var", on_change=_set_var, args=(ds,))
    var = VARIABLES[vid]
    lo, hi = an.available_range(ds, "dettah_bay", vid)
    first, last = (inv.first, inv.last) if (inv.variable_id == vid and lo <= inv.first <= inv.last <= hi) else (lo, hi)
    c2.markdown(f"<div class='fl-matched'><span class='fl-label'>Matched winters</span><b>{fmt.period(first, last)}</b><span class='fl-label'>set the period in the sidebar</span></div>", unsafe_allow_html=True)
    if inv.variable_id != vid:
        ui.note(f"The sidebar variable is not an environmental variable that can be compared between grid cells, so this view shows {var.phrase} instead.")
    cmp = an.compare(ds, vid, "dettah_bay", "aklavik_delta", first, last)
    a, b = locs[cmp.loc_a], locs[cmp.loc_b]

    left, right = st.columns([1.6, 1], gap="large")
    with left:
        with st.container(key="fl_frame_cmp"):
            ui.plot(charts.comparison_chart(ds, cmp), key="cmp_chart")
            ui.caption(f"{len(cmp.common_years)} winters present in both series. Dashed lines: each location's own Theil-Sen estimate. NASA grid-cell values, not station observations.", top=True)
    with right:
        d = var.slope_decimals
        tone = "neutral" if cmp.diff.state != an.EXPLORATORY else "warn"
        src = ("Approved comparison window (docs/SCIENTIFIC_METHODS.md section D); no multiplicity adjustment is defined for it." if cmp.formal
               else "User-selected window: descriptive comparison.")
        if cmp.diff.estimated:
            ui.result_panel(f"Difference in trend · {a.short} minus {b.short}", "", fmt.num(cmp.diff.slope, d, True), var.unit_per_decade,
                            f"95% interval {fmt.interval(cmp.diff.ci_low, cmp.diff.ci_high, d)} · block bootstrap {fmt.interval(cmp.diff.bb_low, cmp.diff.bb_high, d)} · "
                            f"p = {fmt.pval(cmp.diff.p)} (unadjusted) · n = {cmp.diff.n} matched winters", [cmp.sentence], source=src, tone=tone)
        else:
            ui.result_panel(f"Difference in trend · {a.short} minus {b.short}", "", "Not estimated", paragraphs=[cmp.sentence], source=src, tone=tone)
        ui.note("One location reaching a small p-value while the other does not would not show that their slopes differ. The valid question is whether the difference series has a trend.")

    ui.section("Each location on its own")
    c = st.columns(2)
    for col, f in zip(c, (cmp.a, cmp.b)):
        with col:
            ui.finding_card(ds, f, show_table=False)
    tbl = pd.DataFrame([{"Location": locs[f.location_id].short, "Slope per decade": fmt.num(f.slope, var.slope_decimals, True), "95% interval (Theil-Sen)": fmt.interval(f.ci_low, f.ci_high, var.slope_decimals),
                         "95% interval (block bootstrap)": fmt.interval(f.bb_low, f.bb_high, var.slope_decimals), "p (unadjusted)": fmt.pval(f.p),
                         "q": fmt.pval(f.q) if f.q is not None else "not reported", "n": f.n, "Evidence state": f.state_label} for f in (cmp.a, cmp.b)])
    st.dataframe(tbl, hide_index=True)
    ui.caption(f"Units: {var.unit_per_decade}. Period: {fmt.period(first, last)}. Source: NASA POWER daily (MERRA-2 reanalysis).")
    st.write("")

    t1, t2, t3 = st.tabs(["Difference series", "All nine corridors", "How the settings differ"])
    with t1:
        ui.plot(charts.difference_chart(ds, cmp), key="cmp_diff")
        ui.html("<div class='fl-src'>Each point is one winter's value at the first location minus the second. A trend in this series is what would indicate diverging conditions.</div>")
    with t2:
        ui.html("<p class='fl-sub'>Descriptive panel: the same variable at all nine corridors with NASA data, winters 2001/02 to 2024/25, with q across the 126-test family. "
                "Filled markers would indicate q below 0.05. No pooled test across corridors is made: they share weather, so pooling would overstate the evidence.</p>")
        ui.plot(charts.forest_chart(charts.corridor_rows(ds, vid), var.unit_per_decade, var.slope_decimals), key="cmp_forest")
    with t3:
        cc = st.columns(2, gap="large")
        for col, l in zip(cc, (a, b)):
            with col:
                ui.html(f"<div class='fl-panel'><div class='fl-place-name'>{ui.esc(l.short)}</div>" + ui.kv_table([
                    ("Setting", l.setting), ("Access", l.access), ("Sampling point", f"{l.lat:.2f} N, {abs(l.lon):.2f} W"), ("Station check", l.station)]) + "</div>")
        ui.caveat("This compares the climate series of two NASA grid cells about 1,100 km apart. The two roads are different objects (a 6.5 km lake crossing and a delta road of more than 100 km), "
                  "so it is a contrast between settings, not a repeat of one experiment, and it says nothing about road dates.", "Different settings")
