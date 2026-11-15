import clsx from "clsx";
import { Dialog, Popover, Slider, Switch } from "radix-ui";
import { useEffect, useMemo, useState } from "react";
import { useStatus } from "../lib/api";
import { period, useInv, winter } from "../lib/investigation";
import { Icon } from "./icons";
import { Badge, Button, Select } from "./ui";

/* The shared investigation controls (frostline/ui.py console): location, variable, analysis period, approved windows, status. */

function useVariableOptions() {
  const { boot, sel, showExploratory } = useInv();
  const loc = boot.locations[sel.loc];
  return (loc.variables ?? [])
    .map((id) => boot.variables[id])
    .filter((v) => v.tier === "core" || showExploratory)
    .map((v) => ({ value: v.id, label: v.short + (v.tier === "exploratory" ? " (exploratory)" : ""),
                   group: v.kind === "road" ? "Road record" : v.tier === "core" ? "NASA core" : "NASA exploratory" }));
}

function LocationSelect({ className, hideLabel }: { className?: string; hideLabel?: boolean }) {
  const { boot, sel, set } = useInv();
  return (
    <Select label="Location" hideLabel={hideLabel} value={sel.loc} onChange={(v) => set({ loc: v })} className={className}
      options={boot.primary.map((id) => ({ value: id, label: boot.locations[id].road_name, hint: boot.locations[id].region }))} />
  );
}

function VariableSelect({ className, hideLabel }: { className?: string; hideLabel?: boolean }) {
  const { sel, set } = useInv();
  const options = useVariableOptions();
  return <Select label="Variable" hideLabel={hideLabel} value={sel.var} onChange={(v) => set({ variable: v })} options={options} className={className} />;
}

function ExploratorySwitch({ compact }: { compact?: boolean }) {
  const { boot, sel, showExploratory, setShowExploratory } = useInv();
  const locked = boot.variables[sel.var].tier === "exploratory";
  return (
    <label className={clsx("flex items-center gap-2.5 text-[13px] whitespace-nowrap text-ink-2 select-none", locked && "opacity-60")}
      title="Skin temperature, precipitation, wind, humidity and surface radiation. They have no station check and are offered for exploration only.">
      <Switch.Root checked={showExploratory} disabled={locked} onCheckedChange={setShowExploratory}
        className="relative h-[22px] w-[38px] shrink-0 rounded-full bg-[#cfd8e5] transition-colors data-[state=checked]:bg-brand">
        <Switch.Thumb className="block size-[18px] translate-x-[2px] rounded-full bg-white shadow-[0_1px_2px_rgb(11_23_54/0.25)] transition-transform data-[state=checked]:translate-x-[18px]" />
      </Switch.Root>
      {compact ? "Exploratory variables" : "Include exploratory NASA variables"}
    </label>
  );
}

function PeriodControl({ onDone }: { onDone?: () => void }) {
  const { boot, sel, range, set } = useInv();
  const [lo, hi] = range;
  const [draft, setDraft] = useState<[number, number]>([sel.first, sel.last]);
  useEffect(() => setDraft([sel.first, sel.last]), [sel.first, sel.last]);
  const v = boot.variables[sel.var];
  const windows = v.fixed_windows.length ? v.fixed_windows : [[lo, hi] as [number, number]];
  const isFixed = (w: [number, number]) => sel.first === w[0] && sel.last === w[1];
  const showPresets = v.fixed_windows.length > 1 || !v.fixed_windows.some(isFixed);
  return (
    <div className="flex flex-col gap-5">
      <div>
        <div className="flex items-baseline justify-between">
          <span className="text-[12px] font-medium text-ink-3">Analysis period (winters)</span>
          <span className="tnum text-[13px] font-medium text-ink">{period(draft[0], draft[1])}</span>
        </div>
        <Slider.Root className="relative mt-4 flex h-6 touch-none items-center select-none" min={lo} max={hi} step={1} minStepsBetweenThumbs={0}
          value={draft} onValueChange={(x) => setDraft([x[0], x[1]])} onValueCommit={(x) => set({ window: [x[0], x[1]] })} aria-label="Analysis period">
          <Slider.Track className="relative h-1.5 grow rounded-full bg-[#e3e9f2]">
            <Slider.Range className="absolute h-full rounded-full bg-brand" />
          </Slider.Track>
          {[0, 1].map((i) => (
            <Slider.Thumb key={i} aria-label={i ? "Last winter" : "First winter"} aria-valuetext={winter(draft[i])}
              className="block size-5 rounded-full border-2 border-brand bg-white shadow-[0_1px_3px_rgb(11_23_54/0.25)] transition-shadow hover:shadow-[0_0_0_6px_rgb(37_99_235/0.12)] focus-visible:shadow-[0_0_0_6px_rgb(37_99_235/0.2)] focus-visible:outline-none max-sm:size-6" />
          ))}
        </Slider.Root>
        <div className="tnum mt-2 flex justify-between text-[11.5px] text-ink-3"><span>{winter(lo)}</span><span>{winter(hi)}</span></div>
        <p className="mt-3 text-[12.5px] leading-[1.55] text-ink-3">Winter y runs Oct 1 of y to Mar 31 of y+1. Changing the period recomputes every statistic.</p>
      </div>
      {showPresets && (
        <div className="flex flex-col gap-2">
          {windows.map((w) => (
            <Button key={w.join("-")} variant={isFixed(w as [number, number]) ? "primary" : "secondary"} className="w-full justify-start"
              title="A fixed window whose result carries a multiplicity-adjusted q." onClick={() => { set({ window: w as [number, number] }); onDone?.(); }}>
              <Icon.Check size={15} className={isFixed(w as [number, number]) ? "opacity-100" : "opacity-0"} />Approved window: {period(w[0], w[1])}
            </Button>
          ))}
        </div>
      )}
    </div>
  );
}

function StatusBadge({ withMeta }: { withMeta?: boolean }) {
  const { sel } = useInv();
  const { data } = useStatus(sel);
  if (!data) return <span className="skeleton inline-block h-6 w-40 rounded-full" />;
  return (
    <div className="flex min-w-0 flex-col gap-1.5">
      <Badge tone={data.tone}>{data.state_label}</Badge>
      {withMeta && <span className="text-[12.5px] leading-[1.5] text-ink-3">{data.meta}</span>}
    </div>
  );
}

/* Desktop: a slim bar above the content. */
export function InvestigationBar() {
  const { sel } = useInv();
  const { data } = useStatus(sel);
  const [open, setOpen] = useState(false);
  return (
    <div className="hidden items-end gap-3 lg:flex">
      <LocationSelect className="w-[220px] xl:w-[250px]" />
      <VariableSelect className="w-[240px] xl:w-[290px]" />
      <div className="flex flex-col gap-1.5">
        <span className="text-[12px] font-medium text-ink-3">Analysis period</span>
        <Popover.Root open={open} onOpenChange={setOpen}>
          <Popover.Trigger asChild>
            <button className="tnum inline-flex h-10 items-center gap-2 rounded-md whitespace-nowrap border border-line-strong bg-surface px-3 text-[14px] text-ink shadow-[0_1px_2px_rgb(11_23_54/0.04)] hover:border-[#b8c4d6] data-[state=open]:border-brand">
              <Icon.Calendar size={16} className="text-ink-3" />{period(sel.first, sel.last)}<Icon.ChevronDown size={15} className="text-ink-3" />
            </button>
          </Popover.Trigger>
          <Popover.Portal>
            <Popover.Content align="start" sideOffset={8} collisionPadding={16} className="z-[70] w-[380px] rounded-lg border border-line bg-surface p-5 shadow-[var(--shadow-pop)]">
              <PeriodControl onDone={() => setOpen(false)} />
            </Popover.Content>
          </Popover.Portal>
        </Popover.Root>
      </div>
      <div className="ml-auto flex items-center gap-4 pb-2">
        <ExploratorySwitch compact />
        <div className="h-6 w-px bg-line" />
        <div title={data?.meta}><StatusBadge /></div>
      </div>
    </div>
  );
}

/* Tablet and phone: a summary button that opens the controls as a sheet. */
export function InvestigationSheetTrigger() {
  const { boot, sel } = useInv();
  const [open, setOpen] = useState(false);
  const { data } = useStatus(sel);
  const summary = useMemo(() => `${boot.locations[sel.loc].short} · ${boot.variables[sel.var].short} · ${period(sel.first, sel.last)}`, [boot, sel]);
  return (
    <Dialog.Root open={open} onOpenChange={setOpen}>
      <Dialog.Trigger asChild>
        <button className="flex w-full items-center gap-3 rounded-lg border border-line-strong bg-surface px-3.5 py-2.5 text-left shadow-[0_1px_2px_rgb(11_23_54/0.04)] lg:hidden" aria-label="Change the investigation">
          <Icon.Sliders size={18} className="shrink-0 text-brand" />
          <span className="min-w-0 flex-1">
            <span className="block text-[11px] font-medium text-ink-3">Current investigation</span>
            <span className="tnum block truncate text-[13.5px] font-medium text-ink">{summary}</span>
          </span>
          {data && <span className={clsx("size-2 shrink-0 rounded-full", { good: "bg-good", warn: "bg-[#d98a06]", alert: "bg-alert", neutral: "bg-ink-3", muted: "bg-[#a6b2c4]" }[data.tone])} />}
        </button>
      </Dialog.Trigger>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-[60] bg-navy/30 backdrop-blur-[2px] data-[state=open]:animate-[fadein_160ms_ease-out]" />
        <Dialog.Content className="fixed inset-x-0 bottom-0 z-[61] max-h-[88dvh] overflow-y-auto rounded-t-2xl bg-surface px-5 pt-3 pb-[calc(20px+env(safe-area-inset-bottom))] shadow-[var(--shadow-pop)] data-[state=open]:animate-[sheetup_240ms_cubic-bezier(.2,.7,.2,1)] sm:inset-x-auto sm:right-4 sm:bottom-4 sm:w-[420px] sm:rounded-2xl">
          <div className="mx-auto mb-4 h-1 w-10 rounded-full bg-line-strong sm:hidden" />
          <div className="mb-5 flex items-center justify-between">
            <Dialog.Title className="text-[17px] font-semibold">Current investigation</Dialog.Title>
            <Dialog.Close asChild><Button variant="ghost" className="size-10 px-0!" aria-label="Close"><Icon.Close size={18} /></Button></Dialog.Close>
          </div>
          <Dialog.Description className="sr-only">Choose the location, variable and analysis period. Every view follows this selection.</Dialog.Description>
          <div className="flex flex-col gap-5">
            <LocationSelect />
            <VariableSelect />
            <ExploratorySwitch />
            <div className="h-px bg-line" />
            <PeriodControl />
            <div className="rounded-lg border border-line bg-subtle p-4"><StatusBadge withMeta /></div>
            <Button variant="primary" onClick={() => setOpen(false)}>Done</Button>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
