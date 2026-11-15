"""Interactive Northern Atlas: verified study locations, their NASA grid cells and transportation context.

The map background is optional. Markers, grid cells and the location selector work without map tiles,
and nothing is drawn that is not in the approved data: no road geometry, no heatmap, no ice surface.
"""
import pydeck as pdk
import streamlit as st

from .. import analysis as an
from .. import fmt, ui
from ..registry import ROAD_KIND_LABEL, primary_locations

COLORS = {"dettah_bay": [76, 155, 232], "aklavik_delta": [224, 119, 63]}   # charts.LOCATION_COLOR


def build_deck(ds, selected: str) -> pdk.Deck:
    locs = primary_locations(an.locations(ds))
    points, cells, labels = [], [], []
    for l in locs:
        c, col = l.cell, COLORS[l.id]
        points.append(dict(location_id=l.id, name=l.name, lon=l.lon, lat=l.lat, color=col + [255], radius=9 if l.id == selected else 7,
                           line=[231, 236, 242, 255] if l.id == selected else [11, 14, 19, 255],
                           tip=f"{l.lat:.2f} N, {abs(l.lon):.2f} W · sampling point (calculated)"))
        cells.append(dict(location_id=l.id, name=f"NASA grid cell for {l.short}", color=col + [46], line=col + [200],
                          polygon=[[c["west"], c["south"]], [c["east"], c["south"]], [c["east"], c["north"]], [c["west"], c["north"]]],
                          tip="MERRA-2 0.5 x 0.625 degree cell containing the sampling point (calculated from the grid definition)"))
        labels.append(dict(text=l.short, lon=l.lon, lat=l.lat))
    layers = [
        pdk.Layer("PolygonLayer", id="cells", data=cells, get_polygon="polygon", get_fill_color="color", get_line_color="line", line_width_min_pixels=1.5, stroked=True, filled=True, pickable=True),
        pdk.Layer("ScatterplotLayer", id="locations", data=points, get_position="[lon, lat]", get_fill_color="color", get_line_color="line", get_radius="radius",
                  radius_units="'pixels'", stroked=True, line_width_units="'pixels'", get_line_width=2, pickable=True, auto_highlight=True),
        pdk.Layer("TextLayer", id="labels", data=labels, get_position="[lon, lat]", get_text="text", get_size=13, get_color=[231, 236, 242, 255], font_family="'Inter, -apple-system, sans-serif'", font_weight=600,
                  get_text_anchor="'middle'", get_alignment_baseline="'bottom'", get_pixel_offset=[0, -16]),
    ]
    sel = next(l for l in locs if l.id == selected)
    view = pdk.ViewState(latitude=65.5, longitude=-122.6, zoom=3.6, pitch=0) if not st.session_state.get("atlas_zoom") else pdk.ViewState(latitude=sel.lat, longitude=sel.lon, zoom=7.2, pitch=0)
    return pdk.Deck(layers=layers, initial_view_state=view, map_provider="carto", map_style="dark", tooltip={"html": "<b>{name}</b><br/>{tip}", "style": {"backgroundColor": "#1B212B", "color": "#E7ECF2", "fontSize": "12px", "border": "1px solid #2E3644", "borderRadius": "6px", "padding": "8px 10px"}})


def _pick(ds, lid):
    ui.set_investigation(ds, location_id=lid)


def render(ds):
    inv = ui.current()
    locs = an.locations(ds)
    loc = locs[inv.location_id]
    ui.page_header("Northern Atlas", "Where the evidence comes from",
                   "Two documented case studies in the Northwest Territories. Select a marker or use the list; every chart, statistic and export follows the selection.")
    left, right = st.columns([1.5, 1], gap="large")
    with left:
        st.toggle("Zoom to the selected NASA grid cell", key="atlas_zoom", help="The shaded rectangle is the reanalysis grid cell whose average the NASA values describe.")
        event = st.pydeck_chart(build_deck(ds, inv.location_id), on_select="rerun", selection_mode="single-object", key="atlas_map", height=470)
        picked = None
        try:
            for objs in (event.selection.objects or {}).values():
                for o in objs:
                    picked = o.get("location_id") or picked
        except Exception:
            picked = None
        if picked and picked != st.session_state.get("atlas_last_pick"):
            st.session_state["atlas_last_pick"] = picked
            if picked in locs and picked != inv.location_id:
                ui.set_investigation(ds, location_id=picked)
                st.rerun()
        ui.html("<div class='fl-src'>Markers are calculated sampling points, not measurement sites. Shaded rectangles are the MERRA-2 grid cells (calculated from the grid definition). "
                "No road line is drawn: the app holds no verified route geometry. Background map by CARTO with OpenStreetMap data, loaded only if a connection is available; "
                "the list on the right works without it.</div>")
    with right:
        for l in primary_locations(locs):
            on = l.id == inv.location_id
            st.button(f"{l.name}", key=f"atlas_pick_{l.id}", type="primary" if on else "secondary", width="stretch", on_click=_pick, args=(ds, l.id))
        c = loc.cell
        ui.html(f"<div class='fl-panel fl-place'><div class='fl-label'>{ui.esc(loc.role)} case study · {ui.esc(ROAD_KIND_LABEL[loc.road_kind])}</div>"
                f"<div class='fl-place-name'>{ui.esc(loc.name)}</div><div class='fl-place-region'>{ui.esc(loc.region)}</div>"
                + ui.kv_table([
            ("Setting", loc.setting), ("Access context", loc.access),
            ("Sampling point", f"{loc.lat:.2f} N, {abs(loc.lon):.2f} W. {loc.sampling_point}"),
            ("NASA grid cell (calculated)", f"Centre {c['center_lat']:.3f} N, {abs(c['center_lon']):.3f} W; {c['south']:.2f} to {c['north']:.2f} N, {abs(c['east']):.4f} to {abs(c['west']):.4f} W; "
                                            f"cell-average elevation {loc.cell_elevation_m} m (POWER file header)"),
            ("Nearest station check", loc.station),
            ("Records held", f"NASA daily data for winters {fmt.period(*an.available_range(ds, loc.id, 'fdd_octdec'))}; road dates for {fmt.period(*an.available_range(ds, loc.id, 'open_day'))}")])
                + "</div>")
        ui.caveat(loc.caution, "Read this first")

    ui.section("Continue with this location")
    b = st.columns(3)
    if b[0].button(f"Open the {loc.short} trend investigation", type="primary", width="stretch", key="atlas_det"):
        ui.goto("detective")
    if b[1].button(f"Open the {loc.short} corridor investigation", width="stretch", key="atlas_cor"):
        ui.goto("corridor")
    if b[2].button("Compare the two regions", width="stretch", key="atlas_cmp"):
        ui.goto("compare")
    st.write("")

    with st.expander("What is verified about this location, and what is not"):
        ui.html(ui.kv_table([(f"{f.label} [{f.status}]", f.text) for f in loc.facts]))
        ui.html("<div class='fl-src'>Status labels follow docs/ROUTE_IDENTITY.md: VERIFIED against a named source, SECONDARY from press or reference pages, CALCULATED by the team, UNVERIFIED or UNRESOLVED.</div>")
    with st.expander("Supplementary corridors (not mapped)"):
        sup = [l for l in locs.values() if not l.is_primary_pair]
        ui.html(ui.kv_table([(l.name, f"{ROAD_KIND_LABEL.get(l.road_kind, l.road_kind)}. Approximate location; precomputed results for winters 2001/02 to 2024/25 only.") for l in sup]))
        ui.html("<div class='fl-src'>Seven further corridors have NASA data at approximate, team-chosen points. Their coordinates are not part of the approved app data, so they are not drawn. "
                "They appear in the nine-corridor comparison and in the all-route road table. An arbitrary custom point is not supported: no data exist for it.</div>")
