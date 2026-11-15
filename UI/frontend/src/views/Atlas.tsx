import clsx from "clsx";
import { Switch } from "radix-ui";
import { useState } from "react";
import { MapView } from "../components/MapView";
import { Icon } from "../components/icons";
import { Button, Callout, Caption, Disclosure, KV, PageHeader, Section } from "../components/ui";
import { period, useInv } from "../lib/investigation";
import type { Location } from "../lib/types";

export function LocationPicker({ locations, selected, onSelect }: { locations: Location[]; selected: string; onSelect: (id: string) => void }) {
  return (
    <div className="flex flex-col gap-2" role="radiogroup" aria-label="Case study">
      {locations.map((l) => {
        const on = l.id === selected;
        return (
          <button key={l.id} role="radio" aria-checked={on} onClick={() => onSelect(l.id)}
            className={clsx("flex items-center gap-3 rounded-lg border px-4 py-3 text-left transition-[border-color,background-color,box-shadow] duration-150",
              on ? "border-brand bg-brand-soft shadow-[0_0_0_3px_rgb(37_99_235/0.12)]" : "border-line-strong bg-surface hover:border-[#b8c4d6] hover:bg-subtle")}>
            <span className={clsx("size-3 shrink-0 rounded-full ring-2 ring-white", l.id === "aklavik_delta" ? "bg-akl" : "bg-brand")} />
            <span className="min-w-0 flex-1">
              <span className="block text-[14.5px] font-semibold tracking-[-0.01em] text-ink">{l.name}</span>
              <span className="block truncate text-[12.5px] text-ink-3">{l.road_kind_label} · {l.region}</span>
            </span>
            <span className={clsx("grid size-5 shrink-0 place-items-center rounded-full border", on ? "border-brand bg-brand text-white" : "border-line-strong")}>
              {on && <Icon.Check size={12} strokeWidth={2.2} />}
            </span>
          </button>
        );
      })}
    </div>
  );
}

export default function Atlas() {
  const { boot, sel, set, go } = useInv();
  const [zoomed, setZoomed] = useState(false);
  const prim = boot.primary.map((id) => boot.locations[id]);
  const loc = boot.locations[sel.loc];
  const c = loc.cell!;
  const sup = Object.values(boot.locations).filter((l) => !l.is_primary_pair);

  return (
    <div>
      <PageHeader eyebrow="Northern Atlas" title="Where the evidence comes from"
        lede="Two documented case studies in the Northwest Territories. Select a marker or use the list; every chart, statistic and export follows the selection." />
      <div className="grid items-start gap-6 lg:grid-cols-[minmax(0,1.5fr)_minmax(0,1fr)]">
        <div>
          <label className="mb-3 flex w-fit items-center gap-2.5 text-[13px] text-ink-2 select-none" title="The shaded rectangle is the reanalysis grid cell whose average the NASA values describe.">
            <Switch.Root checked={zoomed} onCheckedChange={setZoomed} className="relative h-[22px] w-[38px] rounded-full bg-[#cfd8e5] transition-colors data-[state=checked]:bg-brand">
              <Switch.Thumb className="block size-[18px] translate-x-[2px] rounded-full bg-white shadow transition-transform data-[state=checked]:translate-x-[18px]" />
            </Switch.Root>
            Zoom to the selected NASA grid cell
          </label>
          <MapView locations={prim} selected={sel.loc} zoomed={zoomed} onSelect={(id) => set({ loc: id })} />
          <Caption>
            Markers are calculated sampling points, not measurement sites. Shaded rectangles are the MERRA-2 grid cells (calculated from the grid definition). No road line is
            drawn: the app holds no verified route geometry. Background map by CARTO with OpenStreetMap data, loaded only if a connection is available; the list works without it.
          </Caption>
        </div>
        <div className="flex flex-col gap-4">
          <LocationPicker locations={prim} selected={sel.loc} onSelect={(id) => set({ loc: id })} />
          <div className="card p-5 sm:p-6">
            <div className="text-[12.5px] font-medium text-ink-3 capitalize">{loc.role} case study · {loc.road_kind_label}</div>
            <h2 className="mt-1 text-[19px] font-semibold tracking-[-0.02em]">{loc.name}</h2>
            <div className="mb-4 text-[13px] text-ink-2">{loc.region}</div>
            <KV keyWidth="36%" rows={[
              ["Setting", loc.setting], ["Access context", loc.access],
              ["Sampling point", `${loc.lat!.toFixed(2)} N, ${Math.abs(loc.lon!).toFixed(2)} W. ${loc.sampling_point}`],
              ["NASA grid cell (calculated)", `Centre ${c.center_lat.toFixed(3)} N, ${Math.abs(c.center_lon).toFixed(3)} W; ${c.south.toFixed(2)} to ${c.north.toFixed(2)} N, ${Math.abs(c.east).toFixed(4)} to ${Math.abs(c.west).toFixed(4)} W; cell-average elevation ${loc.cell_elevation_m} m (POWER file header)`],
              ["Nearest station check", loc.station],
              ["Records held", `NASA daily data for winters ${period(...loc.ranges!.nasa)}; road dates for ${period(...loc.ranges!.road)}`],
            ]} />
          </div>
          <Callout kind="caveat" label="Read this first">{loc.caution}</Callout>
        </div>
      </div>

      <Section title="Continue with this location">
        <div className="grid gap-3 md:grid-cols-3">
          <Button variant="primary" onClick={() => go("/trends")} iconRight={<Icon.ArrowRight size={16} />}>Open the {loc.short} trend investigation</Button>
          <Button onClick={() => go("/corridor")} iconRight={<Icon.ArrowRight size={16} />}>Open the {loc.short} corridor investigation</Button>
          <Button onClick={() => go("/compare")} iconRight={<Icon.ArrowRight size={16} />}>Compare the two regions</Button>
        </div>
      </Section>

      <div className="mt-10 flex flex-col gap-3">
        <Disclosure title="What is verified about this location, and what is not">
          <KV keyWidth="34%" rows={loc.facts.map((f) => [`${f.label} [${f.status}]`, f.text])} />
          <Caption>Status labels follow docs/ROUTE_IDENTITY.md: VERIFIED against a named source, SECONDARY from press or reference pages, CALCULATED by the team, UNVERIFIED or UNRESOLVED.</Caption>
        </Disclosure>
        <Disclosure title="Supplementary corridors (not mapped)">
          <KV keyWidth="34%" rows={sup.map((l) => [l.name, `${l.road_kind_label}. Approximate location; precomputed results for winters 2001/02 to 2024/25 only.`])} />
          <Caption>
            Seven further corridors have NASA data at approximate, team-chosen points. Their coordinates are not part of the approved app data, so they are not drawn. They appear
            in the nine-corridor comparison and in the all-route road table. An arbitrary custom point is not supported: no data exist for it.
          </Caption>
        </Disclosure>
      </div>
    </div>
  );
}
