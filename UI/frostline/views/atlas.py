"""Explore map: a real interactive Leaflet map (folium + streamlit-folium) at the centre of the investigation workflow.

Select a place -> choose a question -> retrieve NASA observations -> analyse the trend -> understand the evidence -> export.

* Curated case studies (Dettah, Aklavik) select the shared investigation and open the precomputed, reproducible analyses.
* Any other click inside the supported area becomes an exploratory point: live NASA POWER daily data are retrieved on request
  and run through the same metric and trend engine. No road records are attached to exploratory points.
* Basemap tiles are Esri ArcGIS Online basemaps (dark canvas plus a place-label layer, or topographic) with an OpenStreetMap alternative, all attributed on the map. Nothing on the map is
  invented: no road geometry, no risk overlay, no raster surface. Rectangles are calculated grid cells or the supported area.
* Without tiles (offline) the markers still draw, and the coordinate form and case-study buttons below the map work without the map.
"""
from __future__ import annotations

import datetime as dt

import folium
import plotly.graph_objects as go
import streamlit as st
from streamlit_folium import st_folium

from .. import analysis as an
from .. import charts as ch
from .. import explore as ex
from .. import fmt, ui
from .. import giovanni as gv
from .. import power_api as pa
from ..data import code_version
from ..registry import ROAD_KIND_LABEL, primary_locations

COLORS = {"dettah_bay": ch.C_PRIMARY, "aklavik_delta": ch.C_SECOND}
EXPLORE_COLOR = "#E7ECF2"
ESRI = "https://server.arcgisonline.com/ArcGIS/rest/services/{}/MapServer/tile/{{z}}/{{y}}/{{x}}"
ESRI_ATTR = 'Basemap &copy; <a href="https://www.esri.com/">Esri</a>, HERE, Garmin, FAO, NOAA, USGS, &copy; OpenStreetMap contributors, and the GIS User Community'
OSM_ATTR = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
# (name, url, attribution, is_overlay, shown). CARTO basemaps were dropped: since 2026 they return an "API key required" tile without a key.
TILES = (("Dark (Esri Dark Gray Canvas)", ESRI.format("Canvas/World_Dark_Gray_Base"), ESRI_ATTR, False, True),
         ("Topographic (Esri World Topo)", ESRI.format("World_Topo_Map"), ESRI_ATTR, False, False),
         ("OpenStreetMap", "https://tile.openstreetmap.org/{z}/{x}/{y}.png", OSM_ATTR, False, False),
         ("Place labels (Esri)", ESRI.format("Canvas/World_Dark_Gray_Reference"), ESRI_ATTR, True, True))
STEPS = ["Select a place", "Choose a question", "Retrieve observations", "Analyze the trend", "Understand the evidence", "Export"]
MATCH_TOL = 1e-4


def _rect(cell: dict) -> list:
    return [[cell["south"], cell["west"]], [cell["north"], cell["east"]]]


def build_map(ds, selected: str | None, point: tuple | None = None) -> folium.Map:
    """The static part of the map: tiles, supported area, curated case studies and their grid cells."""
    m = folium.Map(location=[64.5, -122.0], zoom_start=4, min_zoom=2, max_zoom=12, tiles=None, control_scale=True, prefer_canvas=False,
                   max_bounds=False)
    for name, url, attr, overlay, show in TILES:
        folium.TileLayer(tiles=url, attr=attr, name=name, max_zoom=16, max_native_zoom=16, show=show, overlay=overlay, control=True).add_to(m)
    cov = pa.COVERAGE
    folium.Rectangle([[cov["south"], cov["west"]], [cov["north"], cov["east"]]], color="#8CCBF0", weight=1, dash_array="6 6", fill=False,
                     tooltip="Supported area for exploratory points (click anywhere inside)", interactive=False).add_to(m)
    for loc in primary_locations(an.locations(ds)):
        on = loc.id == selected
        folium.Rectangle(_rect(loc.cell), color=COLORS[loc.id], weight=1.5, fill=True, fill_opacity=0.12,
                         tooltip=f"NASA MERRA-2 grid cell for {loc.short} (calculated)" + (" · Giovanni monthly record 1980 to 2025" if loc.id in gv.locations(ds) else "")).add_to(m)
        folium.CircleMarker([loc.lat, loc.lon], radius=11 if on else 8, color="#E7ECF2" if on else "#0B0E13", weight=3 if on else 2, fill=True,
                            fill_color=COLORS[loc.id], fill_opacity=1.0,
                            tooltip=folium.Tooltip(f"<b>{loc.name}</b><br>Curated case study · NASA data + road records" + ("<br><i>selected</i>" if on else ""), sticky=True)).add_to(m)
    folium.LayerControl(position="topright", collapsed=True).add_to(m)
    return m


def selection_layer(point: tuple | None) -> folium.FeatureGroup:
    fg = folium.FeatureGroup(name="Exploratory selection")
    if point:
        cell = pa.merra2_cell(*point)
        folium.Rectangle(_rect(cell), color=EXPLORE_COLOR, weight=1.5, dash_array="4 4", fill=True, fill_opacity=0.06,
                         tooltip="NASA MERRA-2 grid cell that POWER values describe (calculated)").add_to(fg)
        folium.CircleMarker(list(point), radius=9, color=EXPLORE_COLOR, weight=3, fill=True, fill_color="#0B0E13", fill_opacity=0.9,
                            tooltip=f"Exploratory point {point[0]:.2f} N, {abs(point[1]):.2f} W (selected)").add_to(fg)
    return fg


def resolve_click(ds, lat: float, lon: float) -> tuple:
    """Map a click to ('curated', location_id), ('explore', (lat, lon)) or ('outside', (lat, lon))."""
    for loc in primary_locations(an.locations(ds)):
        if abs(loc.lat - lat) < MATCH_TOL and abs(loc.lon - lon) < MATCH_TOL:
            return "curated", loc.id
    p = pa.canonical_point(lat, lon)
    return ("explore", p) if pa.in_coverage(*p) else ("outside", p)


def new_click(out) -> dict | None:
    """The click to act on from st_folium's return value, or None. A marker click (last_object_clicked) wins over the map click
    it also produces; a value seen on a previous run is ignored, so a rerun never re-applies an old click."""
    if not isinstance(out, dict):
        return None
    ss = st.session_state
    oc, mc = out.get("last_object_clicked"), out.get("last_clicked")
    new = None
    if oc and oc != ss.get("xp_prev_obj"):
        new = oc
    elif mc and mc != ss.get("xp_prev_map"):
        new = mc
    ss["xp_prev_obj"], ss["xp_prev_map"] = oc, mc
    return new if new and new.get("lat") is not None and new.get("lng") is not None else None


def apply_selection(ds, kind: str, value) -> None:
    ss = st.session_state
    if kind == "curated":
        ss["xp_point"] = None
        ui.set_investigation(ds, location_id=value)
    elif kind == "explore":
        if ss.get("xp_point") != tuple(value):
            ss["xp_point"] = tuple(value)
        ss.pop("xp_outside", None)
    else:
        ss["xp_outside"] = tuple(value)


def _pick(ds, lid):
    apply_selection(ds, "curated", lid)


def _use_coords(ds):
    kind, val = resolve_click(ds, float(st.session_state["xp_lat"]), float(st.session_state["xp_lon"]))
    apply_selection(ds, kind if kind != "curated" else "explore", val if kind != "curated" else pa.canonical_point(st.session_state["xp_lat"], st.session_state["xp_lon"]))


def result_chart(r: ex.ExploreResult, height: int = 380) -> go.Figure:
    t = r.table
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=t.season_start_year, y=t[r.question_id], mode="markers+lines", name="NASA POWER, this point",
                             line=dict(color=ch._rgba(EXPLORE_COLOR, 0.25), width=1), marker=dict(color=EXPLORE_COLOR, size=7),
                             customdata=t.winter, hovertemplate="<b>Winter %{customdata}</b><br>%{y:.1f} " + r.q["unit"] + "<extra></extra>"))
    if r.estimated:
        fig.add_trace(go.Scatter(x=t.season_start_year, y=ex.fitted(r), mode="lines", name="Theil-Sen trend", line=dict(color=ch.C_PRIMARY, width=2.5),
                                 hoverinfo="skip"))
    fig.update_yaxes(title_text=r.q["unit"])
    fig.update_xaxes(**ch._winter_ticks(t.season_start_year.tolist()), title_text="Winter")
    return ch._layout(fig, height=height)


def _curated_panel(ds, loc):
    c = loc.cell
    ui.html(f"<div class='fl-panel fl-place'><div class='fl-label'>Curated case study · {ui.esc(loc.role)} · {ui.esc(ROAD_KIND_LABEL[loc.road_kind])}</div>"
            f"<div class='fl-place-name'>{ui.esc(loc.name)}</div><div class='fl-place-region'>{ui.esc(loc.region)}</div>"
            + ui.kv_table([
                ("Setting", loc.setting), ("Access context", loc.access),
                ("Sampling point", f"{loc.lat:.2f} N, {abs(loc.lon):.2f} W. {loc.sampling_point}"),
                ("NASA grid cell (calculated)", f"Centre {c['center_lat']:.3f} N, {abs(c['center_lon']):.3f} W; {c['south']:.2f} to {c['north']:.2f} N, {abs(c['east']):.4f} to {abs(c['west']):.4f} W; "
                                                f"cell-average elevation {loc.cell_elevation_m} m (POWER file header)"),
                ("Nearest station check", loc.station),
                ("Records held", f"NASA daily data for winters {fmt.period(*an.available_range(ds, loc.id, 'fdd_octdec'))}; road dates for {fmt.period(*an.available_range(ds, loc.id, 'open_day'))}"
                 + ("; NASA Giovanni monthly temperature 1980 to 2025" if loc.id in gv.locations(ds) else ""))])
            + "</div>")
    ui.caveat(loc.caution, "Read this first")


def _explore_panel(point):
    cell = pa.merra2_cell(*point)
    ui.html(f"<div class='fl-panel fl-place'><div class='fl-label'>Exploratory point · climate analysis only</div>"
            f"<div class='fl-place-name'>{point[0]:.2f} N, {abs(point[1]):.2f} W</div>"
            + ui.kv_table([("NASA grid cell (calculated)", f"MERRA-2 cell centred at {cell['center_lat']:.3f} N, {abs(cell['center_lon']):.3f} W (about 55 km north to south)"),
                           ("What you can ask", "How early-winter cold, Oct to Dec and Jan to Mar temperature, and midwinter thaws have changed, from live NASA POWER daily data"),
                           ("What is not available", "Road-operation dates, ice measurements and station checks. Nothing here describes a specific road or community.")])
            + "</div>")


def error_for(stored, point) -> str | None:
    """The retrieval error recorded for this point, or None. An error raised for another point is never shown here."""
    if isinstance(stored, tuple) and len(stored) == 2 and stored[0] == point:
        return stored[1]
    return None


def _run_explorer(ds, point):
    ss = st.session_state
    ui.section("2 · Choose a question")
    q1, q2, q3 = st.columns([1.6, 1, 1.2], gap="medium")
    qid = q1.selectbox("Scientific question", list(ex.QUESTIONS), format_func=lambda k: ex.QUESTIONS[k]["question"], key="xp_question")
    q2.selectbox("NASA variable", list(pa.PARAMETERS), format_func=lambda k: f"{k}: {pa.PARAMETERS[k]['label']}", key="xp_param",
                 help="Only daily mean 2 m air temperature is offered: it is the variable Frostline's metrics were validated on.")
    first, last = q3.slider("Winters", min_value=pa.FIRST_WINTER, max_value=pa.LAST_WINTER, value=(pa.FIRST_WINTER, pa.LAST_WINTER), key="xp_period",
                            help=f"Winter 1981/82 is the first complete winter in NASA POWER daily data. At least {ex.MIN_WINTERS} complete winters are needed for a trend.")
    st.caption(ex.QUESTIONS[qid]["meaning"])

    ui.section("3 · Retrieve NASA observations")
    store = ss.setdefault("xp_power", {})
    have = store.get(point)
    label = "Retrieve NASA POWER daily data for this point" if not have else "Data retrieved for this point · retrieve again (served from cache)"
    if st.button(label, type="primary" if not have else "secondary", key="xp_fetch", width="stretch", icon=":material/cloud_download:"):
        with st.spinner("Requesting daily T2M from NASA POWER..."):
            try:
                store[point] = pa.fetch_daily(point[0], point[1], pa.FIRST_WINTER, pa.LAST_WINTER)
                ss.pop("xp_error", None)
            except pa.PowerError as exc:
                ss["xp_error"] = (point, str(exc))   # an error belongs to the point it was raised for
        have = store.get(point)
    err = error_for(ss.get("xp_error"), point)
    if err and not have:
        st.error(f"No data retrieved: {err}", icon=":material/cloud_off:")
        return
    if not have:
        ui.note("Nothing is shown until real NASA observations are retrieved for this point. One request covers every winter from 1981/82 to 2024/25; "
                "changing the question or period afterwards reuses it.", "Next")
        return
    m = have.meta
    ui.html(f"<div class='fl-src'>Retrieved {ui.esc(m.get('retrieved_utc'))} from {ui.esc(m.get('served_from'))}: {m.get('n_days_returned')} daily values, "
            f"{m.get('n_fill_or_missing')} missing or fill values, NASA POWER {ui.esc(m.get('api_version'))}, source {ui.esc(m.get('sources'))}.</div>")

    r = ex.analyze(have, point[0], point[1], qid, first, last)
    ui.section("4 · Analyze the trend")
    state = an.EXPLORATORY if r.estimated else an.INSUFFICIENT
    ui.result_panel(r.q["short"] + f" · {point[0]:.2f} N, {abs(point[1]):.2f} W", ui.chip(an.STATE_LABEL[state], ui.STATE_TONE[state]),
                    fmt.num(r.slope_per_decade, r.q["decimals"] + 1, True) if r.estimated else "not estimated", (r.q["unit"] + " per decade") if r.estimated else "",
                    meta=(f"95% interval {fmt.interval(r.ci_low, r.ci_high, r.q['decimals'] + 1)} · p = {fmt.pval(r.p)} (unadjusted) · {r.n} winters" if r.estimated else ""),
                    paragraphs=(ex.headline(r),), source="Computed now from the retrieved NASA POWER series with scripts/northlink_metrics.py", tone=ui.STATE_TONE[state], lead=True)
    ui.plot(result_chart(r), key="xp_chart")

    ui.section("5 · Understand the evidence")
    ui.caveat(ex.EXPLORATORY_CAVEAT, "Exploratory")
    with st.expander("Statistical details, missing data and source metadata"):
        ui.html(ui.kv_table(ex.evidence_rows(r)))
    with st.expander("Winter-by-winter values"):
        st.dataframe(r.table[["winter", r.question_id, "valid_days_octdec", "expected_days_octdec", "valid_days_janmar", "expected_days_janmar"]]
                     .rename(columns={r.question_id: f"{r.q['short']} ({r.q['unit']})"}), hide_index=True)

    ui.section("6 · Export findings")
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    stem = f"frostline_explore_{point[0]:.2f}N_{abs(point[1]):.2f}W_{qid}_{first}_{last}".replace(".", "p")
    d1, d2, d3 = st.columns(3)
    d1.download_button("Download Evidence Brief (HTML)", ex.brief_html(r, now, code_version()), file_name=stem + ".html", mime="text/html", type="primary",
                       key="xp_brief", width="stretch", on_click="ignore")
    d2.download_button("Download data (CSV)", ex.export_csv(r), file_name=stem + ".csv", mime="text/csv", key="xp_csv", width="stretch", on_click="ignore")
    d3.download_button("Download analysis record (JSON)", ex.record_json(r, now), file_name=stem + ".json", mime="application/json", key="xp_json",
                       width="stretch", on_click="ignore")


def render(ds):
    ss = st.session_state
    inv = ui.current()
    locs = an.locations(ds)
    point = ss.get("xp_point")
    ui.page_header("Explore the map", "Pick a place in the North and ask what NASA data say about its winters",
                   "Click a curated case study for the fully documented investigations, or click anywhere else in the dashed area to retrieve live NASA POWER "
                   "observations for that point and test how its winters have changed.")
    ui.steps(STEPS, active=0 if not point else (2 if point not in ss.get("xp_power", {}) else 3))
    left, right = st.columns([1.55, 1], gap="large")
    with left:
        ui.section("1 · Select a place")
        out = st_folium(build_map(ds, None if point else inv.location_id), feature_group_to_add=selection_layer(point), key="xp_map", height=480,
                        use_container_width=True, returned_objects=["last_clicked", "last_object_clicked"])
        click = new_click(out)
        if click:
            kind, val = resolve_click(ds, click["lat"], click["lng"])
            apply_selection(ds, kind, val)
            st.rerun()
        ui.html("<div class='fl-src'>Coloured dots: curated case studies (NASA daily data plus government road records). White ring: your exploratory point. "
                "Shaded rectangles: calculated NASA MERRA-2 grid cells. Dashed outline: area supported for exploration. No road line, risk layer or raster is drawn. "
                "Basemap and labels &copy; Esri and contributors, including &copy; OpenStreetMap contributors (other basemaps in the layer menu, top right). If tiles do not load, markers still work, and the case-study buttons and coordinate form beside the map (below it on a phone) need no map.</div>")
        if ss.get("xp_outside"):
            o = ss["xp_outside"]
            st.warning(f"{o[0]:.2f}, {o[1]:.2f} is outside the supported area ({pa.COVERAGE['south']:.0f} to {pa.COVERAGE['north']:.0f} N, "
                       f"{abs(pa.COVERAGE['west']):.0f} to {abs(pa.COVERAGE['east']):.0f} W). Choose a point inside the dashed outline.", icon=":material/location_off:")
    with right:
        ui.section("Selected")
        if point:
            _explore_panel(point)
            if st.button("Back to the curated case studies", key="xp_clear", width="stretch"):
                ss["xp_point"] = None
                st.rerun()
        else:
            _curated_panel(ds, locs[inv.location_id])
        with st.expander("Case studies and coordinates (works without the map)", expanded=False):
            for l in primary_locations(locs):
                on = (not point) and l.id == inv.location_id
                st.button(f"{l.name}", key=f"atlas_pick_{l.id}", type="primary" if on else "secondary", width="stretch", on_click=_pick, args=(ds, l.id))
            c1, c2 = st.columns(2)
            c1.number_input("Latitude (N)", min_value=pa.COVERAGE["south"], max_value=pa.COVERAGE["north"], value=float(point[0]) if point else 66.0, step=0.25, key="xp_lat", format="%.2f")
            c2.number_input("Longitude (E, negative = W)", min_value=pa.COVERAGE["west"], max_value=pa.COVERAGE["east"], value=float(point[1]) if point else -128.0, step=0.25,
                            key="xp_lon", format="%.2f")
            st.button("Explore these coordinates", key="xp_use", on_click=_use_coords, args=(ds,), width="stretch")

    if point:
        _run_explorer(ds, point)
        return

    loc = locs[inv.location_id]
    ui.section("Continue with this case study")
    b = st.columns(4 if loc.id in gv.locations(ds) else 3)
    if b[0].button(f"Open the {loc.short} trend investigation", type="primary", width="stretch", key="atlas_det"):
        ui.goto("detective")
    if b[1].button(f"Open the {loc.short} corridor investigation", width="stretch", key="atlas_cor"):
        ui.goto("corridor")
    if b[2].button("Compare the two regions", width="stretch", key="atlas_cmp"):
        ui.goto("compare")
    if len(b) > 3 and b[3].button("Open the NASA Giovanni record", width="stretch", key="atlas_gv"):
        ui.goto("giovanni")
    with st.expander("What is verified about this location, and what is not"):
        ui.html(ui.kv_table([(f"{f.label} [{f.status}]", f.text) for f in loc.facts]))
        ui.html("<div class='fl-src'>Status labels follow docs/ROUTE_IDENTITY.md: VERIFIED against a named source, SECONDARY from press or reference pages, CALCULATED by the team, UNVERIFIED or UNRESOLVED.</div>")
    with st.expander("Supplementary corridors (not mapped)"):
        sup = [l for l in locs.values() if not l.is_primary_pair]
        ui.html(ui.kv_table([(l.name, f"{ROAD_KIND_LABEL.get(l.road_kind, l.road_kind)}. Approximate location; precomputed results for winters 2001/02 to 2024/25 only.") for l in sup]))
        ui.html("<div class='fl-src'>Seven further corridors have NASA data at approximate, team-chosen points. Their coordinates are not part of the approved app data, so they are not drawn. "
                "They appear in the nine-corridor comparison and in the all-route road table. Any other point can be explored with live NASA POWER data, as climate analysis only.</div>")
