"""Plotly figures. Every figure is built from analysis objects; nothing is computed here except display geometry.

Conventions: one y-axis per panel (measures with different units get separate panels, never a second axis);
observations are markers, the Theil-Sen estimate is a line, its 95% slope interval is a neutral band;
categorical colours follow the entity in a fixed order; text is never drawn in a series colour.
"""
from __future__ import annotations

import math

import plotly.graph_objects as go
from plotly.subplots import make_subplots

from . import analysis as an
from . import fmt
from .registry import ROAD_KIND_LABEL, VARIABLES

# surfaces and ink
BG = "#0B1220"
SURFACE = "#111B2E"
INK = "#E8EEF7"
INK_2 = "#A9B8CE"
INK_3 = "#71829B"
GRID = "rgba(169,184,206,0.13)"
AXIS = "rgba(169,184,206,0.35)"
# categorical slots (fixed order; the entity keeps its colour everywhere)
C_PRIMARY = "#3987E5"     # slot 1: Dettah / NASA
C_SECOND = "#D95926"      # slot 2: Aklavik / station
C_THIRD = "#199E70"       # slot 3
TREND = "#F3F6FB"
BAND = "rgba(169,184,206,0.16)"
NEUTRAL = "#7C8BA1"
WARN = "#FAB219"
COLD, WARM = "#3987E5", "#E66767"

LOCATION_COLOR = {"dettah_bay": C_PRIMARY, "aklavik_delta": C_SECOND}
FONT = "Inter, 'Segoe UI', system-ui, -apple-system, sans-serif"
CONFIG = {"displaylogo": False, "modeBarButtonsToRemove": ["lasso2d", "select2d", "autoScale2d", "zoomIn2d", "zoomOut2d"], "responsive": True}


def _layout(fig: go.Figure, height: int = 420, title: str | None = None, legend: bool = True) -> go.Figure:
    fig.update_layout(
        height=height, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT, size=13, color=INK_2), margin=dict(l=64, r=28, t=56 if title else 28, b=52),
        title=dict(text=title, font=dict(size=15, color=INK), x=0, xanchor="left", y=0.98) if title else None,
        showlegend=legend, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color=INK_2, size=12), bgcolor="rgba(0,0,0,0)"),
        hoverlabel=dict(bgcolor="#17233B", bordercolor="#2B3B59", font=dict(family=FONT, size=13, color=INK)), hovermode="closest",
    )
    fig.update_xaxes(showgrid=False, linecolor=AXIS, tickcolor=AXIS, ticks="outside", ticklen=4, tickfont=dict(color=INK_2), title_font=dict(color=INK_2, size=12), zeroline=False)
    fig.update_yaxes(gridcolor=GRID, linecolor="rgba(0,0,0,0)", tickfont=dict(color=INK_2), title_font=dict(color=INK_2, size=12), zeroline=False)
    return fig


def _winter_ticks(years) -> dict:
    years = sorted(int(y) for y in years)
    step = 4 if len(years) > 20 else 2 if len(years) > 10 else 1
    vals = [y for y in years if (y - years[0]) % step == 0]
    return dict(tickmode="array", tickvals=vals, ticktext=[fmt.winter(y) for y in vals])


def _value_hover(var, name: str) -> str:
    if var.id in ("open_day", "close_day"):
        return f"<b>Winter %{{customdata[0]}}</b><br>{name}: day %{{y:.0f}} (%{{customdata[1]}})<extra></extra>"
    return f"<b>Winter %{{customdata[0]}}</b><br>{name}: %{{y:,.{var.decimals}f}} {var.unit}<extra></extra>"


def _custom(var, years, values):
    out = []
    for y, v in zip(years, values):
        date = fmt.day_to_date_label(v, int(y)) if var.id in ("open_day", "close_day") and fmt.is_num(v) else ""
        out.append([fmt.winter(y), date])
    return out


def _add_series(fig, var, years, values, color, name, row=None, col=None, showlegend=True):
    kw = dict(row=row, col=col) if row else {}
    fig.add_trace(go.Scatter(x=list(years), y=list(values), mode="lines+markers", name=name, showlegend=showlegend, connectgaps=False,
                             line=dict(color=color, width=1.2), marker=dict(color=color, size=8, line=dict(color=BG, width=2)),
                             customdata=_custom(var, years, values), hovertemplate=_value_hover(var, name)), **kw)


def _add_trend(fig, finding, years, color=TREND, name="Theil-Sen trend", band=True, row=None, col=None, showlegend=True):
    if not finding.estimated or not len(years):
        return
    kw = dict(row=row, col=col) if row else {}
    xs = [min(years), max(years)]
    if band:
        bx = sorted(set(float(y) for y in years) | {float(finding.pivot_year)})
        lo, hi = an.slope_band(finding, bx)
        fig.add_trace(go.Scatter(x=bx + bx[::-1], y=hi + lo[::-1], fill="toself", fillcolor=BAND, line=dict(width=0), hoverinfo="skip",
                                 name="95% interval of the slope", showlegend=showlegend), **kw)
    fig.add_trace(go.Scatter(x=xs, y=an.fitted_line(finding, xs), mode="lines", name=name, showlegend=showlegend,
                             line=dict(color=color, width=2.5), hoverinfo="skip"), **kw)


def trend_chart(ds, finding, height: int = 430) -> go.Figure:
    """Observed per-winter values with the Theil-Sen estimate for the selected window. Winters outside the window are dimmed."""
    var, loc = VARIABLES[finding.variable_id], an.locations(ds)[finding.location_id]
    s = an.get_series(ds, finding.location_id, finding.variable_id)
    color = LOCATION_COLOR.get(loc.id, C_PRIMARY)
    fig = go.Figure()
    inside = [(y, v) for y, v in zip(s.years, s.values) if finding.first <= y <= finding.last]
    outside = [(y, v) for y, v in zip(s.years, s.values) if not (finding.first <= y <= finding.last)]
    obs_name = "Recorded value" if var.kind == "road" else "NASA value (reanalysis)" if var.source_id == "power" else "NASA value (satellite-derived)"
    if outside:
        fig.add_trace(go.Scatter(x=[y for y, _ in outside], y=[v for _, v in outside], mode="markers", name="Outside the selected period",
                                 marker=dict(color="rgba(0,0,0,0)", size=8, line=dict(color=NEUTRAL, width=1.5)),
                                 customdata=_custom(var, [y for y, _ in outside], [v for _, v in outside]), hovertemplate=_value_hover(var, "Not in this analysis")))
    _add_trend(fig, finding, [y for y, _ in inside])
    _add_series(fig, var, [y for y, _ in inside], [v for _, v in inside], color, obs_name)
    _layout(fig, height)
    fig.update_xaxes(title_text="Winter (Oct 1 of the first year to Mar 31 of the next)", **_winter_ticks(s.years))
    fig.update_yaxes(title_text=f"{var.short} ({var.unit})")
    if var.id in ("open_day", "close_day"):
        _date_ticks(fig, [v for v in s.values if fmt.is_num(v)])
    return fig


def _date_ticks(fig, values, row=None, col=None):
    if not values:
        return
    lo, hi = int(min(values)) // 15 * 15, (int(max(values)) // 15 + 1) * 15
    vals = list(range(lo, hi + 1, 15 if hi - lo <= 120 else 30))
    kw = dict(row=row, col=col) if row else {}
    fig.update_yaxes(tickmode="array", tickvals=vals, ticktext=[f"{fmt.day_to_date_label(v)} · day {v}" for v in vals], title_text="", **kw)
    fig.update_layout(margin=dict(l=112))


def comparison_chart(ds, cmp: an.Comparison, height: int = 430) -> go.Figure:
    """Two locations, one variable, matched winters, each with its own Theil-Sen line."""
    var, locs = VARIABLES[cmp.variable_id], an.locations(ds)
    fig = go.Figure()
    for lid, f, color in ((cmp.loc_a, cmp.a, C_PRIMARY), (cmp.loc_b, cmp.b, C_SECOND)):
        s = an.get_series(ds, lid, cmp.variable_id).window(cmp.first, cmp.last)
        s = s[s.season_start_year.isin(cmp.common_years)]
        years, vals = list(s.season_start_year), list(s.value)
        name = locs[lid].short
        _add_series(fig, var, years, vals, color, name)
        if f.estimated:
            xs = [min(years), max(years)]
            fig.add_trace(go.Scatter(x=xs, y=an.fitted_line(f, xs), mode="lines", line=dict(color=color, width=2.5, dash="dash"), name=f"{name} trend", hoverinfo="skip"))
        if years:
            fig.add_annotation(x=years[-1], y=vals[-1], text=name, showarrow=False, xanchor="left", xshift=10, font=dict(color=INK, size=12))
    _layout(fig, height)
    fig.update_layout(margin=dict(r=84))
    fig.update_xaxes(title_text="Winter (matched in both series)", **_winter_ticks(cmp.common_years or [cmp.first, cmp.last]))
    fig.update_yaxes(title_text=f"{var.short} ({var.unit})")
    return fig


def difference_chart(ds, cmp: an.Comparison, height: int = 300) -> go.Figure:
    """The difference series (first location minus second) with its own trend: the approved way to ask whether slopes differ."""
    var, locs = VARIABLES[cmp.variable_id], an.locations(ds)
    a = an.get_series(ds, cmp.loc_a, cmp.variable_id).frame().set_index("season_start_year").value
    b = an.get_series(ds, cmp.loc_b, cmp.variable_id).frame().set_index("season_start_year").value
    years = list(cmp.common_years)
    diff = [float(a[y] - b[y]) for y in years]
    fig = go.Figure()
    _add_trend(fig, cmp.diff, years, name="Trend of the difference")
    name = f"{locs[cmp.loc_a].short} minus {locs[cmp.loc_b].short}"
    fig.add_trace(go.Scatter(x=years, y=diff, mode="lines+markers", name=name, line=dict(color=NEUTRAL, width=1.2),
                             marker=dict(color=INK_2, size=8, line=dict(color=BG, width=2)), customdata=[[fmt.winter(y)] for y in years],
                             hovertemplate=f"<b>Winter %{{customdata[0]}}</b><br>{name}: %{{y:,.{var.decimals}f}} {var.unit}<extra></extra>"))
    _layout(fig, height)
    fig.update_xaxes(**_winter_ticks(years or [cmp.first, cmp.last]))
    fig.update_yaxes(title_text=f"Difference ({var.unit})")
    return fig


def forest_chart(rows: list, unit: str, decimals: int = 1, height: int | None = None, zero_label: str = "no change") -> go.Figure:
    """Slopes with 95% intervals. rows: dicts with label, slope, lo, hi, emphasis (bool), note (str)."""
    rows = [r for r in rows if fmt.is_num(r.get("slope"))]
    rows = sorted(rows, key=lambda r: r["slope"])
    fig = go.Figure()
    for emphasis, name in ((True, "q below 0.05 in the stated family"), (False, "Not supported after correction")):
        sub = [r for r in rows if bool(r.get("emphasis")) == emphasis]
        if not sub:
            continue
        fig.add_trace(go.Scatter(
            x=[r["slope"] for r in sub], y=[r["label"] for r in sub], mode="markers", name=name,
            marker=dict(size=11, color=C_PRIMARY if emphasis else BG, line=dict(color=C_PRIMARY if emphasis else NEUTRAL, width=2), symbol="circle"),
            error_x=dict(type="data", symmetric=False, array=[r["hi"] - r["slope"] for r in sub], arrayminus=[r["slope"] - r["lo"] for r in sub],
                         color=C_PRIMARY if emphasis else NEUTRAL, thickness=2, width=0),
            customdata=[[fmt.num(r["slope"], decimals, True), fmt.interval(r["lo"], r["hi"], decimals), r.get("note", "")] for r in sub],
            hovertemplate=f"<b>%{{y}}</b><br>%{{customdata[0]}} {unit}<br>95% interval %{{customdata[1]}}<br>%{{customdata[2]}}<extra></extra>"))
    fig.add_vline(x=0, line=dict(color=AXIS, width=1, dash="dot"))
    _layout(fig, height or max(260, 34 * len(rows) + 110))
    fig.update_layout(margin=dict(l=200))
    fig.update_yaxes(categoryorder="array", categoryarray=[r["label"] for r in rows], showgrid=False, tickfont=dict(color=INK, size=12))
    fig.update_xaxes(title_text=f"Theil-Sen slope ({unit}); the dotted line marks {zero_label}", showgrid=True, gridcolor=GRID)
    return fig


def timeline_chart(ds, location_id: str, env_variable_id: str = "fdd_octdec", highlight: int | None = None, height: int = 560) -> go.Figure:
    """Environmental values and the recorded operating window on a shared winter axis, in separate panels with separate units."""
    loc, var = an.locations(ds)[location_id], VARIABLES[env_variable_id]
    rec = an.road_record(ds, location_id)
    ok = rec[rec.record_status == "verified"]
    env = an.get_series(ds, location_id, env_variable_id)
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.09, row_heights=[0.4, 0.6],
                        subplot_titles=(f"{var.short} ({var.unit}): NASA, available from {fmt.winter(min(env.years))}",
                                        f"{loc.road_name}: recorded opening to closing (NWT Table 108)"))
    _add_series(fig, var, env.years, env.values, LOCATION_COLOR.get(location_id, C_PRIMARY), var.short, row=1, col=1, showlegend=False)
    years = [int(y) for y in ok.season_start_year]
    custom = [[fmt.winter(y), fmt.iso_to_label(o), fmt.iso_to_label(c), int(n)] for y, o, c, n in zip(years, ok.opening_date, ok.closing_date, ok.open_to_close_days)]
    fig.add_trace(go.Bar(x=years, y=list(ok.open_to_close_days), base=list(ok.open_day), name="Recorded operating window", showlegend=False, width=0.62,
                         marker=dict(color="rgba(57,135,229,0.55)", line=dict(color=C_PRIMARY, width=1), cornerradius=3), customdata=custom,
                         hovertemplate="<b>Winter %{customdata[0]}</b><br>Opened %{customdata[1]}<br>Closed %{customdata[2]}<br>Interval %{customdata[3]} days (not usable days)<extra></extra>"),
                  row=2, col=1)
    fig.add_trace(go.Scatter(x=years, y=list(ok.open_day), mode="markers", name="Opening date", showlegend=False, hoverinfo="skip",
                             marker=dict(color=INK, size=7, symbol="line-ew", line=dict(color=INK, width=2))), row=2, col=1)
    fig.add_hline(y=91.5, line=dict(color=WARN, width=1, dash="dot"), row=2, col=1,
                  annotation_text="Dec 31: end of the Oct to Dec environmental window", annotation_position="top left", annotation_font=dict(color=INK_2, size=11))
    if highlight is not None:
        for r in (1, 2):
            fig.add_vrect(x0=highlight - 0.5, x1=highlight + 0.5, fillcolor="rgba(250,178,25,0.10)", line=dict(color=WARN, width=1), row=r, col=1)
    _layout(fig, height, legend=False)
    fig.update_annotations(font=dict(color=INK, size=13))
    all_years = sorted(set(years) | set(env.years))
    fig.update_xaxes(range=[min(all_years) - 0.7, max(all_years) + 0.7], **_winter_ticks(all_years))
    fig.update_xaxes(title_text="Winter", row=2, col=1)
    fig.update_yaxes(title_text=var.unit, row=1, col=1)
    vals = list(ok.open_day) + list(ok.close_day)
    _date_ticks(fig, vals, row=2, col=1)
    fig.update_yaxes(range=[min(vals) - 12, max(vals) + 10], row=2, col=1)
    return fig


def bias_month_chart(ds, height: int = 340) -> go.Figure:
    """Mean NASA minus station temperature by calendar month at the Yellowknife cell."""
    b = ds["bias_by_month"].sort_values("month")
    names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    order = [10, 11, 12, 1, 2, 3, 4, 5, 6, 7, 8, 9]  # winter first
    b = b.set_index("month").loc[order].reset_index()
    fig = go.Figure(go.Bar(
        x=[names[m - 1] for m in b.month], y=list(b.mean_bias), width=0.62,
        marker=dict(color=[COLD if v < 0 else WARM for v in b.mean_bias], cornerradius=4),
        text=[fmt.num(v, 1, True) for v in b.mean_bias], textposition="outside", textfont=dict(color=INK_2, size=11), cliponaxis=False,
        customdata=[[int(n), fmt.num(sd, 1)] for n, sd in zip(b.n, b.sd)],
        hovertemplate="<b>%{x}</b><br>NASA minus station: %{y:+.2f} °C<br>%{customdata[0]} paired days, daily spread (SD) %{customdata[1]} °C<extra></extra>"))
    fig.add_hline(y=0, line=dict(color=AXIS, width=1))
    _layout(fig, height, legend=False)
    fig.update_yaxes(title_text="Mean difference, NASA minus station (°C)")
    fig.update_xaxes(title_text="Calendar month (cold season first)")
    return fig


def station_fdd_chart(ds, height: int = 380) -> go.Figure:
    """Oct-Dec freezing degree-days per winter: NASA reanalysis against the ECCC station. Incomplete station winters are gaps."""
    s = an.station_fdd(ds)
    var = VARIABLES["fdd_octdec"]
    fig = go.Figure()
    _add_series(fig, var, s.years_all, s.nasa_all, C_PRIMARY, "NASA POWER (reanalysis, grid cell)")
    _add_series(fig, var, s.years_all, s.station_all, C_SECOND, "ECCC Yellowknife A (station)")
    fig.add_annotation(x=s.years_all[-1], y=s.nasa_all[-1], text="NASA", showarrow=False, xanchor="left", xshift=10, font=dict(color=INK, size=12))
    last_ok = [(y, v) for y, v in zip(s.years_all, s.station_all) if fmt.is_num(v)][-1]
    fig.add_annotation(x=last_ok[0], y=last_ok[1], text="Station", showarrow=False, xanchor="left", xshift=10, font=dict(color=INK, size=12))
    _layout(fig, height)
    fig.update_layout(margin=dict(r=84))
    fig.update_xaxes(title_text="Winter (gaps: station winter incomplete, not filled)", **_winter_ticks(s.years_all))
    fig.update_yaxes(title_text="Oct-Dec freezing degree-days (°C-days)")
    return fig


def snow_chart(ds, height: int = 380) -> go.Figure:
    """Snow on the ground at Yellowknife A on Nov 28 against the Dettah opening day. A hypothesis, not a cause."""
    d = ds["yellowknife_snow_by_season"].dropna(subset=["sog_nov28_cm", "open_day"])
    fig = go.Figure(go.Scatter(
        x=list(d.sog_nov28_cm), y=list(d.open_day), mode="markers", marker=dict(color=C_PRIMARY, size=10, line=dict(color=BG, width=2)),
        customdata=[[fmt.winter(y), fmt.day_to_date_label(o, int(y))] for y, o in zip(d.season_start_year, d.open_day)],
        hovertemplate="<b>Winter %{customdata[0]}</b><br>Snow on ground, Nov 28: %{x:.0f} cm<br>Opened: %{customdata[1]} (day %{y:.0f})<extra></extra>"))
    _layout(fig, height, legend=False)
    fig.update_xaxes(title_text="Snow on the ground at Yellowknife A on Nov 28 (cm, ECCC station)", showgrid=True, gridcolor=GRID)
    fig.update_yaxes(title_text="Dettah opening day")
    _date_ticks(fig, list(d.open_day))
    return fig


def multiple_testing_chart(ds, height: int = 380) -> go.Figure:
    """All 126 unadjusted p-values in rank order against the Benjamini-Hochberg line: why 20 small p-values are not 20 findings."""
    t = ds["multiple_testing_126"].sort_values("p_unadjusted").reset_index(drop=True)
    m = len(t)
    rank = list(range(1, m + 1))
    is_road = t.family_type.astype(str).str.startswith("road")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=rank, y=[0.05 * k / m for k in rank], mode="lines", name="Benjamini-Hochberg line (5% false discovery rate)", line=dict(color=WARN, width=2), hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=rank, y=[0.05] * m, mode="lines", name="p = 0.05, no correction", line=dict(color=AXIS, width=1, dash="dot"), hoverinfo="skip"))
    for mask, name, color, symbol in ((~is_road, "NASA climate tests (99)", C_PRIMARY, "circle"), (is_road, "Road-date tests (27)", C_SECOND, "diamond")):
        sub = t[mask]
        fig.add_trace(go.Scatter(x=[r + 1 for r in sub.index], y=list(sub.p_unadjusted), mode="markers", name=name,
                                 marker=dict(color=color, size=8, symbol=symbol, line=dict(color=BG, width=1.5)),
                                 customdata=[[a, b, fmt.pval(p), fmt.pval(q)] for a, b, p, q in zip(sub.location_id, sub.metric, sub.p_unadjusted, sub.q_bh_all126)],
                                 hovertemplate="<b>%{customdata[0]}</b> · %{customdata[1]}<br>p = %{customdata[2]} (unadjusted)<br>q = %{customdata[3]} across 126 tests<extra></extra>"))
    _layout(fig, height)
    fig.update_xaxes(title_text="Tests ranked from smallest to largest p-value (126 in all)", showgrid=False)
    fig.update_yaxes(title_text="Unadjusted Mann-Kendall p-value", type="log", range=[math.log10(2e-4), 0.02])
    return fig


def routes_rows(ds, metric: str) -> list:
    """Rows for the all-route forest chart of one road-date metric (family of 51 tests, winters 1993/94 to 2024/25)."""
    t = ds["road_record_trends_all_routes"]
    rows = []
    for _, r in t[t.metric == metric].iterrows():
        rows.append(dict(label=str(r.road_name).replace(" Winter Road", "").replace(" Ice Crossing", " crossing").replace(" Ice Road", " ice road"),
                         slope=float(r.slope_per_decade), lo=float(r.ci95_low), hi=float(r.ci95_high), emphasis=bool(r.q_bh_all_routes < 0.05),
                         note=f"q = {fmt.pval(r.q_bh_all_routes)} across 51 tests; n = {int(r.n_seasons)} winters; {ROAD_KIND_LABEL.get(str(r.road_type), str(r.road_type)).lower()}"))
    return rows


def corridor_rows(ds, variable_id: str) -> list:
    """Rows for the nine-corridor panel of one variable (family of 126 tests, winters 2001/02 to 2024/25)."""
    t = ds["multiple_testing_126"]
    locs = an.locations(ds)
    rows = []
    for _, r in t[t.metric == VARIABLES[variable_id].column].iterrows():
        loc = locs.get(str(r.location_id))
        label = (loc.short if loc else str(r.location_id)) + ("" if loc and loc.is_primary_pair else " (approx.)")
        rows.append(dict(label=label, slope=float(r.slope_per_decade), lo=float(r.ci95_low), hi=float(r.ci95_high), emphasis=bool(r.q_bh_all126 < 0.05),
                         note=f"p = {fmt.pval(r.p_unadjusted)} (unadjusted); q = {fmt.pval(r.q_bh_all126)} across 126 tests; n = {int(r.n)} winters"))
    return rows
