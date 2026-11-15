import { useCallback, useMemo } from "react";
import type { Location } from "../lib/types";
import { Plot } from "./Plot";

/*
 * Northern Atlas map (frostline/views/atlas.py build_deck): the calculated sampling points and their MERRA-2 grid cells.
 * Nothing else is drawn: no road geometry, no heatmap, no ice surface. The basemap (CARTO Positron, OpenStreetMap data)
 * is optional; the location list beside the map works without it.
 */
const COLOR: Record<string, [number, number, number]> = { dettah_bay: [37, 99, 235], aklavik_delta: [234, 88, 12] };
const MAP_CONFIG = { scrollZoom: true, displayModeBar: false };
const rgba = (c: [number, number, number], a: number) => `rgba(${c[0]},${c[1]},${c[2]},${a})`;

export function MapView({ locations, selected, zoomed, onSelect, height = 470 }: {
  locations: Location[]; selected: string; zoomed: boolean; onSelect: (id: string) => void; height?: number;
}) {
  const figure = useMemo(() => {
    const data: any[] = [];
    for (const l of locations) {
      const c = l.cell!;
      const col = COLOR[l.id] ?? [37, 99, 235];
      data.push({
        type: "scattermap", mode: "lines", fill: "toself", fillcolor: rgba(col, l.id === selected ? 0.16 : 0.1), line: { color: rgba(col, 0.85), width: 1.5 },
        lon: [c.west, c.east, c.east, c.west, c.west], lat: [c.south, c.south, c.north, c.north, c.south],
        name: `NASA grid cell for ${l.short}`, hoverinfo: "text", customdata: Array(5).fill(l.id),
        text: Array(5).fill(`<b>NASA grid cell for ${l.short}</b><br>MERRA-2 0.5 x 0.625 degree cell containing the sampling point<br>(calculated from the grid definition)`),
        showlegend: false,
      });
    }
    data.push({
      type: "scattermap", mode: "markers+text", lon: locations.map((l) => l.lon), lat: locations.map((l) => l.lat), customdata: locations.map((l) => l.id),
      text: locations.map((l) => l.short), textposition: "top center", textfont: { size: 13, color: "#0B1736", family: "'Geist Variable', sans-serif" },
      marker: { size: locations.map((l) => (l.id === selected ? 17 : 13)), color: locations.map((l) => rgba(COLOR[l.id] ?? [37, 99, 235], 1)), opacity: 1 },
      hovertext: locations.map((l) => `<b>${l.name}</b><br>${l.lat!.toFixed(2)} N, ${Math.abs(l.lon!).toFixed(2)} W · sampling point (calculated)`),
      hoverinfo: "text", showlegend: false,
    });
    const sel = locations.find((l) => l.id === selected)!;
    const center = zoomed ? { lat: sel.lat!, lon: sel.lon! } : { lat: 65.5, lon: -122.6 };
    return {
      data,
      layout: {
        height, margin: { l: 0, r: 0, t: 0, b: 0 }, paper_bgcolor: "rgba(0,0,0,0)",
        map: { style: "carto-positron", center, zoom: zoomed ? 7.2 : 3.4 },
        hoverlabel: { bgcolor: "#FFFFFF", bordercolor: "#E2E8F0", font: { family: "'Geist Variable', sans-serif", size: 12.5, color: "#0B1736" }, align: "left" },
        showlegend: false,
      },
    };
  }, [locations, selected, zoomed, height]);

  /* without network the CARTO basemap cannot load: draw the same cells and markers on a plain background */
  const fallback = useMemo(() => ({
    data: figure.data.map((t: any) => (t.mode === "markers+text" ? { ...t, mode: "markers" } : t)),
    layout: { ...figure.layout, map: { ...(figure.layout as any).map, style: "white-bg" } },
  }), [figure]);

  const click = useCallback((p: any) => {
    const id = Array.isArray(p?.customdata) ? p.customdata[0] : p?.customdata;
    if (typeof id === "string" && id !== selected) onSelect(id);
  }, [onSelect, selected]);

  return (
    <div className="overflow-hidden rounded-lg border border-line bg-[#eef3f8]">
      <Plot figure={figure} label="Map of the two documented case-study locations and their NASA grid cells" onPointClick={click} config={MAP_CONFIG} fallback={fallback} />
    </div>
  );
}
