"""NASA Giovanni monthly record: MERRA-2 monthly 2 m temperature for the Dettah / Yellowknife grid cell, 1980 to 2025.

All values come from the ingested Giovanni export (UI/data_real/giovanni_*.csv). This view never mixes monthly means into the
daily freezing-degree-day analysis and never attaches road records to them.
"""
import datetime as dt

import plotly.graph_objects as go
import streamlit as st

from .. import charts as ch
from .. import fmt, ui
from .. import giovanni as gv
from ..data import code_version

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def series_chart(t: gv.GTrend, height: int = 400) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=list(t.years), y=list(t.values), mode="markers+lines", name="Seasonal mean (Giovanni)",
                             line=dict(color=ch._rgba(ch.C_PRIMARY, 0.35), width=1), marker=dict(color=ch.C_PRIMARY, size=6),
                             hovertemplate="<b>%{x}</b><br>%{y:.2f} °C<extra></extra>"))
    if t.estimated:
        fig.add_trace(go.Scatter(x=list(t.years), y=gv.fitted(t), mode="lines", name="Theil-Sen trend", line=dict(color=ch.TREND, width=2),
                                 hovertemplate="Trend %{y:.2f} °C<extra></extra>"))
    fig.update_yaxes(title_text="°C")
    fig.update_xaxes(title_text="Year" + (f" ({gv.YEAR_NOTE[t.season]})" if t.season in gv.YEAR_NOTE else ""))
    return ch._layout(fig, height=height)


def climatology_chart(clim, height: int = 300) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=MONTHS, y=clim["max"], mode="lines", line=dict(width=0), showlegend=False, hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=MONTHS, y=clim["min"], mode="lines", line=dict(width=0), fill="tonexty", fillcolor=ch.BAND, name="Range of monthly means",
                             hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=MONTHS, y=clim["mean"], mode="lines+markers", name=f"Mean {gv.NORMAL[0]} to {gv.NORMAL[1]}", line=dict(color=ch.C_PRIMARY, width=2),
                             hovertemplate="%{x}: %{y:.1f} °C<extra></extra>"))
    fig.add_hline(y=0, line=dict(color=ch.AXIS, width=1, dash="dot"))
    fig.update_yaxes(title_text="°C")
    return ch._layout(fig, height=height)


def anomaly_chart(an_df, height: int = 280) -> go.Figure:
    a = an_df.dropna(subset=["anomaly_c"])
    roll = a.set_index("date").anomaly_c.rolling(60, min_periods=48, center=True).mean()
    fig = go.Figure()
    fig.add_trace(go.Bar(x=a.date, y=a.anomaly_c, name="Monthly anomaly", marker_color=[ch.WARM if v > 0 else ch.COLD for v in a.anomaly_c],
                         hovertemplate="%{x|%b %Y}: %{y:+.1f} °C<extra></extra>"))
    fig.add_trace(go.Scatter(x=roll.index, y=roll.values, mode="lines", name="5-year running mean", line=dict(color=ch.TREND, width=2),
                             hovertemplate="%{x|%b %Y}: %{y:+.2f} °C<extra></extra>"))
    fig.update_yaxes(title_text=f"°C vs {gv.NORMAL[0]} to {gv.NORMAL[1]}")
    return ch._layout(fig, height=height)


def render(ds):
    ui.page_header("NASA Giovanni record", "46 years of monthly temperature at the Dettah grid cell",
                   "Monthly 2 m air temperature from NASA's MERRA-2 reanalysis, extracted through NASA Giovanni for 1980 to 2025. "
                   "Choose a season and a period; the trend, its uncertainty and the export all follow your choice.")
    if not gv.available(ds):
        ui.caveat("No Giovanni extraction is present in this deployment, so nothing is shown here. No other data are substituted.")
        return
    loc = gv.locations(ds)[0]
    p = gv.provenance(ds, loc)
    ui.html("<div class='fl-src'>Source: " + ui.esc(gv.DATASET_NAME) + ". Grid point " + ui.esc(p.get("data_grid_point_wsen", "")) +
            " (west, south, east, north), resolved by Giovanni from the requested box " + ui.esc(p.get("user_bounding_box_wsen", "")) + ".</div>")
    ui.caveat(gv.WHAT_IT_IS_NOT, "What this record is")

    c1, c2 = st.columns([1, 1.4], gap="large")
    season = c1.selectbox("Season", gv.SEASON_ORDER, format_func=lambda s: gv.SEASON_LABEL[s], key="gv_season")
    lo, hi = gv.year_range(ds, loc, season)
    first, last = c2.slider("Period", min_value=lo, max_value=hi, value=(lo, hi), key=f"gv_period_{season}",
                            help=f"At least {gv.MIN_YEARS} complete years are needed for a trend. The full record is the pre-specified analysis; a shorter window is exploratory.")
    t = gv.trend(ds, loc, season, first, last)

    state = gv.evidence_state(t)
    ui.result_panel("Trend in the " + gv._lc(gv.SEASON_LABEL[season]) + " mean", ui.chip(ui.an.STATE_LABEL[state], ui.STATE_TONE[state]),
                    fmt.num(t.slope_per_decade, 2, True) if t.estimated else "not estimated", "°C per decade" if t.estimated else "",
                    meta=(f"95% interval {fmt.interval(t.ci_low, t.ci_high, 2)} · p = {fmt.pval(t.p)} (unadjusted)"
                          + (f" · q = {fmt.pval(t.q)} across {t.family_size} seasonal tests" if t.q is not None else " · exploratory window") + f" · {t.n} years")
                    if t.estimated else "", paragraphs=(gv.plain_language(t),), source="Computed live from giovanni_t2m_calendar_seasons.csv / giovanni_monthly_t2m_seasonal.csv", tone=ui.STATE_TONE[state], lead=True)
    ui.plot(series_chart(t), key="gv_series")
    if t.excluded_incomplete:
        ui.caption(f"{t.excluded_incomplete} year(s) in this window lack a complete set of months and are excluded, not filled.")

    with st.expander("How sure is this? Statistical details"):
        ui.html(ui.kv_table([
            ("Estimator", "Theil-Sen slope against year, with its 95% interval (the same trend function as every Frostline result)"),
            ("Test", "Mann-Kendall with tie correction, two-sided; p-value unadjusted"),
            ("Multiple testing", "Full record only: Benjamini-Hochberg across the seven seasonal aggregates tested on this record"),
            ("Residual lag-1 autocorrelation", fmt.num(t.lag1, 2) + (" (above 0.3: the p-value may be too small)" if t.estimated and t.lag1 > 0.3 else "")),
            ("Missing values", f"{p.get('n_missing', '?')} of {p.get('n_months', '?')} months are missing or fill values; incomplete seasons are excluded"),
            ("Unit conversion", "Giovanni publishes kelvin; °C = K - 273.15"),
        ]))
        tr = gv.stored_trends(ds, loc)
        st.dataframe({"Aggregate": [gv.SEASON_LABEL.get(m, m) for m in tr.metric], "Years": [f"{a} to {b}" for a, b in zip(tr.first_year, tr.last_year)], "n": tr.n,
                      "°C per decade": [fmt.num(v, 2, True) for v in tr.slope_per_decade], "95% interval": [fmt.interval(a, b, 2) for a, b in zip(tr.ci95_low, tr.ci95_high)],
                      "p (unadjusted)": [fmt.pval(v) for v in tr.mk_p], "q (BH)": [fmt.pval(v) for v in tr.q_bh_within_location]}, hide_index=True)

    ui.section("The seasonal cycle and how each month departs from it")
    a, b = st.columns(2, gap="large")
    with a:
        ui.plot(climatology_chart(gv.climatology(ds, loc)), key="gv_clim")
        ui.caption(f"Mean of the monthly values {gv.NORMAL[0]} to {gv.NORMAL[1]}; shading spans the coldest to warmest value of each calendar month in that period.")
    with b:
        ui.plot(anomaly_chart(gv.anomalies(ds, loc)), key="gv_anom")
        ui.caption("Each bar is one month minus its 1991 to 2020 mean. The line is a centred 60-month running mean, shown only where at least 48 months are available.")
    pc = gv.period_contrast(ds, loc, season, (lo, lo + 9), (hi - 9, hi))
    if fmt.is_num(pc["diff"]):
        ui.note(f"{gv.SEASON_LABEL[season]}: the mean of {hi - 9} to {hi} is {fmt.num(pc['diff'], 2, True)} °C relative to {lo} to {lo + 9} "
                f"(95% interval {fmt.interval(pc['lo'], pc['hi'], 2)}, Welch; years treated as independent).", "First decade vs last decade")

    ui.section("Is the extraction consistent with Frostline's daily NASA data?")
    chk = gv.power_check(ds, loc)
    ui.html(ui.kv_table([
        ("Months compared", f"{chk.get('n_months')} ({chk.get('first')} to {chk.get('last')}), complete POWER months only"),
        ("Mean difference, Giovanni minus POWER", f"{fmt.num(chk.get('mean_diff_giovanni_minus_power_c'), 3, True)} °C"),
        ("Largest monthly difference", f"{fmt.num(chk.get('max_abs_diff_c'), 3)} °C"),
        ("Correlation", fmt.num(chk.get("pearson_r"), 4)),
        ("Interpretation", "Both routes deliver the same MERRA-2 grid cell, so close agreement checks the access route and processing; it is not independent validation. "
                           "Small monthly differences are expected because POWER days are local solar time while MERRA-2 months are UTC."),
    ]))

    with st.expander("Provenance: exactly which files these numbers come from"):
        ui.html(ui.kv_table([(k.replace("_", " ").capitalize(), v) for k, v in p.items()]))
        ui.html("<div class='fl-src'>Citation: " + ui.esc(gv.CITATION) + " The companion NetCDF file was checked value by value against the CSV export "
                "(scripts/verify_giovanni_netcdf.py; result in data/processed/giovanni_netcdf_verification.json).</div>")

    ui.section("Export these findings")
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    stem = f"frostline_giovanni_{season.lower()}_{t.first}_{t.last}"
    d1, d2, d3 = st.columns(3)
    d1.download_button("Download Evidence Brief (HTML)", gv.brief_html(ds, t, now, code_version()), file_name=stem + ".html", mime="text/html", type="primary",
                       key="gv_brief", width="stretch", on_click="ignore")
    d2.download_button("Download data (CSV)", gv.export_csv(ds, t), file_name=stem + ".csv", mime="text/csv", key="gv_csv", width="stretch", on_click="ignore")
    d3.download_button("Download analysis record (JSON)", gv.record_json(ds, t, now), file_name=stem + ".json", mime="application/json", key="gv_json",
                       width="stretch", on_click="ignore")
