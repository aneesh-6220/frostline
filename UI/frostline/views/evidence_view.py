"""Evidence Engine view: the evidence assessment, the source disagreement explorer and the multiple-testing audit."""
import pandas as pd
import streamlit as st

from .. import analysis as an
from .. import charts, evidence as ev, fmt, ui
from ..registry import VARIABLES


def render(ds):
    inv = ui.current()
    loc, var = an.locations(ds)[inv.location_id], inv.variable
    rep = ev.assess(ds, inv.location_id, inv.variable_id, inv.first, inv.last)
    f = an.trend(ds, inv.location_id, inv.variable_id, inv.first, inv.last)
    ui.page_header("Frostline Evidence Engine", "How far can this evidence be trusted?",
                   f"{var.label} · {loc.name} · winters {fmt.period(inv.first, inv.last)}. A trend estimate is only as good as the data behind it. "
                   "The engine separates what was observed, what was derived and what was inferred, and judges seven aspects of evidence quality one by one.")
    ui.html(f"<div class='fl-finding {ui.STATE_TONE[f.state]}'><div style='display:flex;justify-content:space-between;gap:.6rem;flex-wrap:wrap;align-items:center'>"
            f"<span class='fl-eyebrow' style='margin:0'>Assessment for the current investigation</span>{ui.chip(f.state_label, ui.STATE_TONE[f.state])}</div>"
            f"<p style='font-size:1.05rem'>{ui.esc(rep.headline)}</p><p class='dim'>{ui.esc(rep.suitability)}</p></div>")

    tabs = st.tabs(["Evidence quality", "Evidence layers", "Source disagreement", "Multiple testing"])
    with tabs[0]:
        ui.html("<div class='fl-sub' style='margin-bottom:.7rem'>Seven dimensions, each with a plain state and the specific reasons for it, read from the data. "
                "There is deliberately no overall score: one number would hide which part of the evidence is weak.</div>")
        ui.dimension_cards(rep)
    with tabs[1]:
        c = st.columns(2, gap="large")
        with c[0]:
            ui.layer_blocks(rep, ("observations", "derived", "inference"))
        with c[1]:
            ui.layer_blocks(rep, ("corroboration", "limitations", "questions"))
        ui.html("<div class='fl-src'>Data files behind this assessment: " + ui.esc(", ".join(rep.files)) + "</div>")
    with tabs[2]:
        _disagreement(ds)
    with tabs[3]:
        _multiple_testing(ds)

    st.write("")
    if st.button("Export this investigation as an Evidence Brief", type="primary", icon=":material/description:", key="ev_brief"):
        ui.goto("brief")


def _disagreement(ds):
    b = ds.facts["bias"]
    s = an.station_fdd(ds)
    ui.html("<div class='fl-eyebrow'>Source disagreement explorer · NASA reanalysis against a ground station</div>"
            "<div class='fl-sub'>NASA POWER temperature is a MERRA-2 reanalysis value for a grid cell roughly 55 km north to south and 25 to 32 km east to west. Yellowknife A is a single weather station inside that cell, "
            "about 6 km from the Dettah sampling point. They are different kinds of measurement, and they disagree.</div>")
    c = st.columns(4)
    c[0].markdown(ui.stat_card("Oct to Dec", fmt.num(b["overall_oct_dec"], 2, True), "°C", "Mean NASA minus station, early winter", "bias_by_month.csv"), unsafe_allow_html=True)
    c[1].markdown(ui.stat_card("Jan to Mar", fmt.num(b["overall_jan_mar"], 2, True), "°C", "Mean NASA minus station, midwinter", "canonical_facts.json"), unsafe_allow_html=True)
    c[2].markdown(ui.stat_card("Freezing degree-days", fmt.num(s.pct_over, 1, True), "%", f"NASA {fmt.num(s.nasa_mean, 0)} against station {fmt.num(s.station_mean, 0)} °C-days on {s.n_complete} matched winters", "station_fdd_by_season.csv"), unsafe_allow_html=True)
    c[3].markdown(ui.stat_card("Year-to-year correlation", fmt.num(s.pearson_r, 2), "r", "NASA tracks the station's ups and downs while disagreeing on the level", "station_fdd_by_season.csv"), unsafe_allow_html=True)
    ui.bias_caveat(ds)
    c = st.columns(2, gap="large")
    with c[0]:
        ui.html("<div class='fl-eyebrow' style='margin-top:.6rem'>Seasonal difference</div>")
        ui.plot(charts.bias_month_chart(ds), key="ev_bias")
        ui.html(f"<div class='fl-src' style='margin-top:-.5rem'>{fmt.count(b['paired_days'])} paired days, 2001 to 2025; {fmt.num(b['overall_all_days'], 2, True)} °C over all days. "
                "The difference is largest in the freeze-up months and close to zero in summer, so it is not a constant offset.</div>")
    with c[1]:
        ui.html("<div class='fl-eyebrow' style='margin-top:.6rem'>Freezing accumulation, winter by winter</div>")
        ui.plot(charts.station_fdd_chart(ds), key="ev_fdd")
        ui.html(f"<div class='fl-src' style='margin-top:-.5rem'>{s.n_complete} of {len(s.years_all)} winters have a complete Oct to Dec station record; incomplete station winters are left as gaps, not filled.</div>")
    ui.html("<div class='fl-eyebrow' style='margin-top:.8rem'>Trend sensitivity on the matched winters</div>")
    st.dataframe(pd.DataFrame([{"Series": f.location_id, "Slope (°C-days per decade)": fmt.num(f.slope, 1, True), "95% interval (Theil-Sen)": fmt.interval(f.ci_low, f.ci_high, 0),
                                "p (unadjusted)": fmt.pval(f.p), "n": f.n, "Period": fmt.period(f.first, f.last)} for f in (s.nasa, s.station, s.diff)]), hide_index=True)
    ui.note("Neither trend is distinguishable from zero, and the trend of the difference is not distinguishable from zero either. That does not make the two series equivalent: "
            "with intervals this wide the comparison is weak, and a high year-to-year correlation says nothing about absolute accuracy.")
    c = st.columns(2, gap="large")
    with c[0]:
        st2 = ds["station_summary_aklavik_inuvik"]
        ui.html("<div class='fl-eyebrow'>Aklavik and Inuvik stations</div>")
        st.dataframe(pd.DataFrame({"Station": st2.station, "Paired days": st2.n_days, "Difference, all days (°C)": [fmt.num(v, 2, True) for v in st2.bias_all_c],
                                   "Difference, Oct to Mar (°C)": [fmt.num(v, 2, True) for v in st2.bias_octmar_c], "Mean absolute difference, Oct to Mar (°C)": [fmt.num(v, 2) for v in st2.mae_octmar_c]}), hide_index=True)
        ui.html("<div class='fl-src'>NASA minus station for the Aklavik cell. The stations sit at the two ends of the road, not at the sampling point.</div>")
    with c[1]:
        t = ds.facts["thaw"]["dettah_bay"]
        ui.html("<div class='fl-eyebrow'>What this means for the investigation</div>")
        ui.html("<div class='fl-layer'><ul>"
                "<li>Use NASA series for year-to-year variation and for trends read with their intervals.</li>"
                "<li>Do not read absolute NASA temperature, freezing degree-days or thaw counts as local conditions.</li>"
                f"<li>NASA records a midwinter thaw day in {t['winters_with_any_thaw']} of {t['n']} winters at Dettah; the station records more, so NASA under-detects thaw.</li>"
                "<li>Frostline applies no bias correction. An offset fitted to this one station would not be a validated correction.</li>"
                "<li>The cause of the difference is not established. A date shift, a different daily-mean definition, an elevation mismatch and a drift were tested and ruled out.</li>"
                "</ul></div>")


def _multiple_testing(ds):
    e = ds.facts["extended_126"]
    ui.html("<div class='fl-eyebrow'>Multiple testing · why small p-values are not all findings</div>"
            f"<div class='fl-sub'>The extended analysis runs {e['n']} trend tests (14 measures at 9 corridors, winters 2001/02 to 2024/25). When many tests are run, some small p-values appear by chance alone.</div>")
    c = st.columns(4)
    c[0].markdown(ui.stat_card("Tests run", str(e["n"]), "trend tests", "14 measures at 9 corridors", "multiple_testing_126.csv"), unsafe_allow_html=True)
    c[1].markdown(ui.stat_card("Nominal", str(e["nominal"]), "with p below 0.05", f"About {e['expected_by_chance']} would be expected by chance if nothing were changing", "multiple_testing_126.csv"), unsafe_allow_html=True)
    c[2].markdown(ui.stat_card("After correction", str(e["bh_lt_05"]), "with q below 0.05", f"Benjamini-Hochberg across all {e['n']}; Holm also leaves {e['holm_lt_05']}", "multiple_testing_126.csv"), unsafe_allow_html=True)
    c[3].markdown(ui.stat_card("NASA climate tests", str(e["climate_family_bh_lt_05"]), "of 99 survive", "No NASA climate trend survives correction at any corridor", "hypothesis_families.csv"), unsafe_allow_html=True)
    ui.plot(charts.multiple_testing_chart(ds), key="ev_mt")
    ui.html("<div class='fl-src' style='margin-top:-.5rem'>Each point is one test. A test is supported only if it falls on or below the amber line. Points between the amber line and the dotted line "
            "look significant on their own and are not, once the number of tests is taken into account.</div>")
    fam = ds["hypothesis_families"]
    st.dataframe(pd.DataFrame({"Family": fam.family_id, "Tests": fam.n_tests, "Definition": fam.definition, "Correction": fam.correction, "Role": fam.role}), hide_index=True)
    t = ds["multiple_testing_126"]
    with st.expander("All 126 tests"):
        st.dataframe(pd.DataFrame({"Corridor": t.location_id, "Measure": t.metric, "Family": t.family_type, "n": t.n, "Slope per decade": t.slope_per_decade,
                                   "95% low": t.ci95_low, "95% high": t.ci95_high, "p (unadjusted)": t.p_unadjusted, "q (126 tests)": t.q_bh_all126, "Holm": t.holm_all126,
                                   "Lag-1 flag": t.autocorr_flag}).sort_values("p (unadjusted)"), hide_index=True, height=360)
        st.download_button("Download the 126-test table (CSV)", t.to_csv(index=False), file_name="frostline_multiple_testing_126.csv", mime="text/csv", key="ev_mt_csv", on_click="ignore")
    ui.note("Adjusted q values belong to these declared families and fixed windows only. When you choose your own period, Frostline shows the unadjusted p and labels it exploratory.")
