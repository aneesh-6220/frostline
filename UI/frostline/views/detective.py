"""Advanced Trend Detective: the historical series, the rate of change, its uncertainty and its evidence state."""
import pandas as pd
import streamlit as st

from .. import analysis as an
from .. import charts, fmt, ui
from ..registry import QUESTIONS, SOURCES, VARIABLES


def season_table(ds, f) -> pd.DataFrame:
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
    return pd.DataFrame(rows)


def render(ds):
    inv = ui.current()
    loc, var = an.locations(ds)[inv.location_id], inv.variable
    f = an.trend(ds, inv.location_id, inv.variable_id, inv.first, inv.last)
    q = QUESTIONS.get(inv.question_id) if inv.question_id else None
    ui.page_header("Trend Detective" + (f" · {q.text}" if q else ""), f"{var.label}", f"{loc.name}. {var.definition}")

    left, right = st.columns([1.7, 1], gap="large")
    with left:
        with st.container(key="fl_frame_detective"):
            ui.html(f"<div class='fl-panel-head'><div><div class='fl-label'>{ui.esc(loc.short)} · winters {fmt.period(inv.first, inv.last)}</div>"
                    f"<div class='fl-panel-title'>{ui.esc(var.short)} ({ui.esc(var.unit)})</div></div></div>")
            ui.plot(charts.trend_chart(ds, f), key="detective_chart")
            kind = "Recorded values from the government record" if var.kind == "road" else "NASA estimates for a grid cell, not station observations"
            ui.caption(f"Points: {kind}, one per winter. White line: Theil-Sen estimate for the selected period. "
                       "Grey band: 95% interval of the slope. Hollow points lie outside the selected period. Hover a point to inspect that winter.", top=True)
        ui.plain_language(ds, f)
    with right:
        ui.finding_card(ds, f)

    if not an.is_fixed_window(inv.variable_id, inv.first, inv.last) and f.estimated:
        ui.caveat("You selected your own period, which changes the statistical question. The p-value shown is exploratory and not adjusted for multiple testing, "
                  "and no adjusted q is reported. Use the buttons in the sidebar to return to an approved fixed window.", "Exploratory window")
    if var.id == "thaw_days_janmar":
        t = ds.facts["thaw"][inv.location_id]
        ui.note(f"NASA records an above-freezing midwinter day in {t['winters_with_any_thaw']} of {t['n']} winters here ({t['total_thaw_days']} such days in total). "
                "The reanalysis runs cold and under-detects thaw relative to the station, so zero NASA thaw days does not mean no thaw.")

    st.write("")
    t1, t2, t3, t4 = st.tabs(["Inspect the winters", "Why this variable", "Robustness", "Method and provenance"])
    with t1:
        st.dataframe(season_table(ds, f), hide_index=True, height=320)
        ui.caption("An empty value means no usable record for that winter. Missing values are never replaced with zero or interpolated.")
    with t2:
        src = SOURCES[var.source_id]
        ui.html(ui.kv_table([("What it measures", var.definition), ("Why it is relevant", var.why), ("Units", var.unit),
                             ("Source", f"{src.name} ({src.kind})" + (f", parameter {var.power_parameter}" if var.power_parameter else "")),
                             ("Temporal resolution", var.temporal_resolution), ("Spatial resolution", var.spatial_resolution),
                             ("Valid period", fmt.period(var.valid_first, var.valid_last)), ("Data-quality condition", var.quality),
                             ("Known limitations", " ".join(var.limitations))]))
    with t3:
        if var.kind == "road" and loc.is_primary_pair:
            sv = an.sensitivity(ds, inv.location_id, inv.variable_id)
            tbl = pd.DataFrame({"Variant": sv.variant, "n": sv.n, "Slope per decade": [fmt.num(v, 1, True) for v in sv.theil_sen_per_decade],
                                "95% interval (Theil-Sen)": [fmt.interval(a, b, 1) for a, b in zip(sv.ts_ci95_low, sv.ts_ci95_high)],
                                "95% interval (block bootstrap)": [fmt.interval(a, b, 1) for a, b in zip(sv.bb_ci95_low, sv.bb_ci95_high)],
                                "p (unadjusted)": [fmt.pval(p) for p in sv.mk_p_unadjusted], "Lag-1": [fmt.num(v, 2, True) for v in sv.lag1_resid]})
            st.dataframe(tbl, hide_index=True)
            ui.caption("Stored robustness variants (headline_trend_sensitivity.csv): different windows and dropping early or late winters. "
                       "They show how far the estimate depends on particular years. All are exploratory.")
        else:
            rows = charts.corridor_rows(ds, inv.variable_id) if var.fixed_windows else []
            if rows:
                ui.html("<p class='fl-sub'>The same variable at all nine corridors with NASA data, winters 2001/02 to 2024/25. This places the selected location in context; "
                        "supplementary corridors use approximate sampling points.</p>")
                ui.plot(charts.forest_chart(rows, var.unit_per_decade, var.slope_decimals), key="detective_forest")
            else:
                ui.note("No stored robustness variants exist for this variable.")
    with t4:
        ui.html(ui.kv_table([
            ("Estimator", "Theil-Sen slope against the winter start year, reported per decade with its 95% interval"),
            ("Significance test", "Mann-Kendall with tie correction, two-sided; the p-value is unadjusted"),
            ("Dependence-aware interval", "Moving-block bootstrap of residuals (blocks of ceil(n^(1/3)), 2000 resamples, fixed seed)"),
            ("Serial correlation", "Lag-1 autocorrelation of residuals; above 0.3 in size raises a flag that p may be optimistic"),
            ("Minimum record", f"{an.MIN_SEASONS} complete winters; no estimate when one value fills at least 75% of winters"),
            ("Multiple testing", "Benjamini-Hochberg q only for approved fixed windows within their declared family"),
            ("This result", (f"Precomputed in {f.stored_source} and cross-checked against a live recomputation" if f.cross_checked else "Recomputed for this window from the per-winter values with the approved period_trend function")),
            ("Series file", an.get_series(ds, inv.location_id, inv.variable_id).source_file), ("App data digest", ds.digest)]))

    ui.section("Continue the investigation")
    c = st.columns(4)
    if c[0].button("Compare with another region", width="stretch", key="det_compare"):
        ui.goto("compare")
    if c[1].button("Investigate the corridor", width="stretch", key="det_corridor"):
        ui.goto("corridor")
    if c[2].button("Audit the evidence", width="stretch", key="det_evidence"):
        ui.goto("evidence")
    if c[3].button("Export the Evidence Brief", type="primary", width="stretch", key="det_brief"):
        ui.goto("brief")
