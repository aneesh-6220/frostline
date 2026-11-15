"""Frostline Observatory: the landing view. Every indicator is computed from the approved data at render time."""
import datetime as dt

import streamlit as st

from .. import analysis as an
from .. import charts, fmt, ui
from .. import giovanni as gv
from ..registry import DEFAULT_LOCATION, DEFAULT_VARIABLE, GLOBAL_CONTEXT


def _begin(ds):
    ui.set_investigation(ds, DEFAULT_LOCATION, DEFAULT_VARIABLE, question_id=None)
    st.session_state["demo_step"] = 0


def _giovanni_metric(ds) -> tuple:
    """The longest NASA record in the app: how many of its pre-declared seasonal tests survive correction, led by the strongest one.

    Falls back to the 24-winter NASA POWER freezing-degree-day result when no Giovanni extraction is deployed."""
    if not gv.available(ds):
        env = an.trend(ds, "dettah_bay", "fdd_octdec", 2001, 2024)
        return ("NASA freezing accumulation · Dettah", fmt.num(env.slope, 0, True), "°C-days per decade",
                f"95% interval {fmt.interval(env.ci_low, env.ci_high, 0)} over {env.n} winters: not statistically distinguishable from no change. That is not proof of no change.",
                "NASA POWER daily T2M (MERRA-2 reanalysis)")
    loc = gv.locations(ds)[0]
    full = [gv.trend(ds, loc, s) for s in gv.SEASON_ORDER]
    fam = [t for t in full if t.q is not None]
    best = min(fam, key=lambda t: t.q)
    n_sup = sum(t.q < an.ALPHA for t in fam)
    octdec = next(t for t in full if t.season == "octdec_mean_c")
    return (f"NASA Giovanni · Dettah cell, {gv.SEASON_LABEL[best.season].split(' (')[0].lower()}", fmt.num(best.slope_per_decade, 2, True), "°C per decade",
            f"{best.first} to {best.last}, 95% interval {fmt.interval(best.ci_low, best.ci_high, 2)}, q = {fmt.pval(best.q)}. "
            f"{n_sup} of the {len(fam)} seasonal tests on this {best.last - best.first + 1}-year record {'survives' if n_sup == 1 else 'survive'} correction; early winter (Oct to Dec, {fmt.num(octdec.slope_per_decade, 2, True)} °C per decade) "
            f"does not (q = {fmt.pval(octdec.q)}). One reanalysis grid cell, not a station.",
            "MERRA-2 monthly T2M through NASA Giovanni")


def _story(ds, op, op_n, env) -> None:
    """The investigation in three plain steps, each with its live number and its verdict. No step claims a cause."""
    s = ds.facts["snow"]
    fragile = op_n.q is not None and (op_n.q < an.ALPHA) != (op.q is not None and op.q < an.ALPHA)
    rows = [
        ("Road record · Dettah", f"The ice road opens {op.direction}: {fmt.num(op.slope, 1, True)} days per decade",
         f"Over {fmt.period(op.first, op.last)}, the recorded opening date moved {op.direction} ({ui.PLAIN_VERDICT[op.state].lower()}, q = {fmt.pval(op.q)}). "
         "Dettah was picked after this trend was seen"
         + (f", and the result does not hold in the shorter {fmt.period(op_n.first, op_n.last)} window (q = {fmt.pval(op_n.q)})" if fragile else "")
         + ", so treat it as a lead, not a settled fact."),
        ("NASA data · Dettah", f"But early-winter cold shows {ui.PLAIN_VERDICT[env.state].lower()}",
         f"Freezing degree-days moved {fmt.num(env.slope, 0, True)} °C-days per decade, with a 95% interval of {fmt.interval(env.ci_low, env.ci_high, 0)}. "
         "Year-to-year swings are much larger than any long-term shift, so this record alone does not show a matching shift in early-winter cold."),
        ("Station data · Yellowknife A", "So other conditions may matter: snow is one open lead",
         f"Winters with more snow on the ground on Nov 28 tended to open later (Spearman rho {fmt.num(s['sog_nov28_rho'], 2, True)}, n = {s['n']}, q = {fmt.pval(s['q'])}). "
         "This is a hypothesis for further study, not a mechanism."),
    ]
    ui.section("The story in three steps", "Roads, cold and snow")
    ui.html("<div class='fl-rows'>" + "".join(
        f"<div><div class='n'>{i + 1}</div><div><div class='k'>{ui.esc(k)}</div><h4>{ui.esc(h)}</h4><p>{ui.esc(p)}</p></div></div>"
        for i, (k, h, p) in enumerate(rows)) + "</div>")
    with st.expander("How we tested this", expanded=False):
        ui.html(ui.kv_table([
            ("The trend line", "Theil-Sen slope: the median of the slopes between every pair of winters, so one extreme winter cannot drag it."),
            ("Is it real or noise?", "Mann-Kendall test: do values rise or fall more often than chance would give?"),
            ("The grey band", "The 95% range of plausible slopes. If it allows both up and down, the record cannot tell the direction."),
            ("Many tests at once", "Running many tests produces some small p-values by luck, so results are corrected (Benjamini-Hochberg q). "
                                   "Only q below 0.05 counts as a clear change."),
        ]))


def _global_context(ds) -> None:
    """Published global and Arctic warming rates beside the local estimates. Context only: nothing is tested against them."""
    ui.section("How this compares with global warming", "Context, not cause")
    cells = [c for c in GLOBAL_CONTEXT]
    if gv.available(ds):
        loc = gv.locations(ds)[0]
        for season, label in (("ANN", "This grid cell, whole year"), ("SON", "This grid cell, autumn (Sep to Nov)")):
            t = gv.trend(ds, loc, season)
            verdict = "clear change" if t.q is not None and t.q < an.ALPHA else "no clear change"
            cells.append((label, fmt.num(t.slope_per_decade, 2, True), "°C per decade",
                          f"{t.first} to {t.last}, 95% interval {fmt.interval(t.ci_low, t.ci_high, 2)}, q = {fmt.pval(t.q)}: {verdict}.",
                          "MERRA-2 monthly T2M through NASA Giovanni"))
    ui.metrics(cells)
    ui.note("The global and Arctic figures are published averages over very large areas, shown for scale. One grid cell is far noisier than a global average, "
            "so its intervals are much wider. Frostline does not test whether these winters match global warming and makes no statement of cause.", "How to read this")


def render(ds):
    left, right = st.columns([0.92, 1.08], gap="large", vertical_alignment="center")
    with left:
        ui.html("<div class='fl-hero'>" + ui.kicker("Frostline Observatory · NASA Earth science data, 1980 to 2025") +
                "<h1>How is winter changing across Canada's North?</h1>"
                "<p>Pick a place, pull NASA observations, measure how its winters have changed, see how certain that change is, and export a reproducible "
                "Evidence Brief. Two documented ice roads add 32 winters of government operating records.</p></div>")
        with st.container(horizontal=True, gap="small"):
            if st.button("Begin an Investigation", type="primary", key="home_begin", on_click=_begin, args=(ds,)):
                ui.goto("demo")
            if st.button("Explore the Data on the map", key="home_explore", icon=":material/map:"):
                ui.goto("atlas")
        ui.journey(["Choose a place", "Retrieve NASA data", "Measure the trend", "Weigh the evidence", "Export a brief"])
    with right:
        f = an.trend(ds, DEFAULT_LOCATION, DEFAULT_VARIABLE, 2001, 2024)
        with st.container(key="fl_frame_home"):
            ui.html("<div class='fl-panel-head'><div><div class='fl-label'>Live from the data · Dettah, Yellowknife Bay</div>"
                    "<div class='fl-panel-title'>How cold an average early-winter day was (Oct to Dec), 24 winters of NASA data</div></div>"
                    f"{ui.verdict_chip(f)}</div>")
            ui.answer(ds, f, subject="Early-winter cold at Dettah")
            ui.plot(charts.trend_chart(ds, f, height=320), key="home_chart")
            k = charts.PER_DAY[DEFAULT_VARIABLE]
            ui.caption(f"Each dot is one winter: on average, how many degrees below 0 °C each day from Oct 1 to Dec 31 was "
                       f"(the freezing degree-day total divided by its {k} days). NASA POWER daily T2M (MERRA-2 reanalysis, grid-cell value). "
                       f"Theil-Sen estimate {fmt.num(f.slope / k, 2, True)} °C per day per decade, 95% interval {fmt.interval(f.ci_low / k, f.ci_high / k, 2)} "
                       f"(as a total: {fmt.num(f.slope, 0, True)} °C-days per decade, {fmt.interval(f.ci_low, f.ci_high, 0)}): "
                       f"{f.state_label.lower()}.", top=True)

    op = an.trend(ds, "dettah_bay", "open_day", 1993, 2024)
    op_n = an.trend(ds, "dettah_bay", "open_day", 2001, 2024)
    _story(ds, op, op_n, f)

    ui.section("What the evidence shows so far", "Computed from the approved data on every load")
    b, e = ds.facts["bias"], ds.facts["extended_126"]
    long_metric = _giovanni_metric(ds)
    ui.metrics([
        ("Road record · Dettah", fmt.num(op.slope, 1, True), "days per decade",
         f"The ice road opened later over {fmt.period(op.first, op.last)} (95% interval {fmt.interval(op.ci_low, op.ci_high, 1)}; q = {fmt.pval(op.q)} across {op.q_family_n} route tests). "
         f"Exploratory and selection-biased; not supported after correction in the NASA-era window {fmt.period(op_n.first, op_n.last)} (q = {fmt.pval(op_n.q)}).",
         "NWT Bureau of Statistics, Table 108"),
        long_metric,
        ("NASA against the ground station", fmt.num(b["overall_oct_dec"], 1, True), "°C in Oct to Dec",
         f"NASA reanalysis runs colder than the Yellowknife A station across {fmt.count(b['paired_days'])} paired days. Frostline shows this disagreement instead of hiding it.",
         "NASA POWER and ECCC Yellowknife A"),
        ("Trend tests, corrected", f"{e['bh_lt_05']} of {e['n']}", "survive correction",
         f"{e['nominal']} of {e['n']} trend tests have p below 0.05 (about {e['expected_by_chance']} expected by chance). None survives correction for multiple testing.",
         "126-test family, winters 2001/02 to 2024/25"),
    ])
    _global_context(ds)

    c = st.columns([1.1, 1], gap="large")
    with c[0]:
        ui.section("Why it matters")
        ui.html("<p class='fl-sub'>Seasonal roads built on frozen lakes and rivers connect northern communities and carry supplies each winter. "
                "Asking how winter conditions and road seasons have changed means finding NASA datasets, cleaning daily records, computing seasonal indicators, "
                "fitting trends, locating government records and working out what can honestly be concluded. Frostline compresses that workflow into one guided, reproducible investigation.</p>")
    with c[1]:
        ui.section("Scope and data in this release")
        s = ds.facts["status_counts"]
        p = ds.facts["periods"]
        days = (dt.date.fromisoformat(p["nasa_daily_last"]) - dt.date.fromisoformat(p["nasa_daily_first"])).days + 1
        ui.note("Frostline is a scientific investigation tool. It does not measure ice thickness, assess road safety, recommend routes or predict opening dates, "
                "and it does not show what produced any change in the road record.", "Scope")
        ui.caption(f"In this release: {fmt.count(days)} days of NASA daily data at each of two documented locations, "
                   f"{s['total_rows']} route-winters of government road records ({s['counts']['verified']} verified) across {s['routes']} NWT routes, "
                   f"and {fmt.count(b['paired_days'])} paired station days for validation.")
