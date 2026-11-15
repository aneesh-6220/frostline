import clsx from "clsx";
import { AnimatePresence, motion } from "motion/react";
import { Collapsible, Select as RSelect, Tabs as RTabs, ToggleGroup } from "radix-ui";
import { forwardRef, useId, useState, type ButtonHTMLAttributes, type ReactNode } from "react";
import { Link, type LinkProps } from "react-router";
import type { Metric, Row, Table, Tone } from "../lib/types";
import { Icon } from "./icons";

/* ------------------------------------------------------------------ buttons */
type Variant = "primary" | "secondary" | "ghost" | "quiet";
const BTN: Record<Variant, string> = {
  primary: "bg-brand text-white shadow-[0_1px_0_rgb(255_255_255/0.18)_inset,0_1px_2px_rgb(11_23_54/0.16)] hover:bg-brand-hover active:bg-brand-press",
  secondary: "bg-surface text-ink border border-line-strong hover:border-[#b8c4d6] hover:bg-subtle shadow-[0_1px_2px_rgb(11_23_54/0.05)]",
  ghost: "text-ink-2 hover:text-ink hover:bg-[#eef3fa]",
  quiet: "text-brand hover:text-brand-hover underline-offset-4 hover:underline px-0! h-auto!",
};
const BTN_BASE = "inline-flex items-center justify-center gap-2 h-10 px-4 rounded-md text-[14px] font-medium tracking-[-0.005em] whitespace-nowrap transition-[background-color,border-color,color,transform,box-shadow] duration-150 active:translate-y-px disabled:opacity-45 disabled:active:translate-y-0 max-sm:h-11";

export const Button = forwardRef<HTMLButtonElement, ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant; icon?: ReactNode; iconRight?: ReactNode }>(
  function Button({ variant = "secondary", className, icon, iconRight, children, ...rest }, ref) {
    return (
      <button ref={ref} className={clsx(BTN_BASE, BTN[variant], className)} {...rest}>
        {icon}{children}{iconRight}
      </button>
    );
  });

export function ButtonLink({ variant = "secondary", className, icon, iconRight, children, ...rest }: LinkProps & { variant?: Variant; icon?: ReactNode; iconRight?: ReactNode }) {
  return <Link className={clsx(BTN_BASE, BTN[variant], className)} {...rest}>{icon}{children}{iconRight}</Link>;
}

export function DownloadLink({ href, children, variant = "secondary", className }: { href: string; children: ReactNode; variant?: Variant; className?: string }) {
  return <a href={href} download className={clsx(BTN_BASE, BTN[variant], className)}><Icon.Download size={16} />{children}</a>;
}

/* ------------------------------------------------------------------ evidence state badge */
const TONE_DOT: Record<Tone, string> = { good: "bg-good", neutral: "bg-ink-3", warn: "bg-[#d98a06]", alert: "bg-alert", muted: "bg-[#a6b2c4]" };
const TONE_CHIP: Record<Tone, string> = {
  good: "bg-good-soft text-good border-good-line",
  neutral: "bg-[#f1f5fa] text-ink-body border-line-strong",
  warn: "bg-warn-soft text-warn border-warn-line",
  alert: "bg-alert-soft text-alert border-alert-line",
  muted: "bg-[#f4f6f9] text-ink-3 border-line",
};
export function Badge({ tone = "neutral", children, className }: { tone?: Tone; children: ReactNode; className?: string }) {
  return (
    <span className={clsx("inline-flex h-6 w-fit items-center gap-1.5 rounded-full border px-2.5 text-[12px] font-medium leading-none whitespace-nowrap", TONE_CHIP[tone], className)}>
      <i className={clsx("size-1.5 rounded-full", TONE_DOT[tone])} aria-hidden="true" />{children}
    </span>
  );
}

/* ------------------------------------------------------------------ type */
export function Kicker({ children, className }: { children: ReactNode; className?: string }) {
  return <div className={clsx("kicker", className)}>{children}</div>;
}

export function PageHeader({ eyebrow, title, lede, aside }: { eyebrow?: ReactNode; title: ReactNode; lede?: ReactNode; aside?: ReactNode }) {
  return (
    <header className="mb-8 flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
      <div className="max-w-[760px]">
        {eyebrow && <Kicker className="mb-3">{eyebrow}</Kicker>}
        <h1 className="text-[28px] leading-[1.12] font-semibold tracking-[-0.03em] text-balance sm:text-[34px]">{title}</h1>
        {lede && <p className="prose-frost mt-3 max-w-[68ch] text-pretty">{lede}</p>}
      </div>
      {aside && <div className="shrink-0">{aside}</div>}
    </header>
  );
}

export function Section({ title, aside, children, className, id }: { title: ReactNode; aside?: ReactNode; children?: ReactNode; className?: string; id?: string }) {
  return (
    <section className={clsx("mt-12", className)} aria-labelledby={id}>
      <div className="mb-4 flex flex-col gap-1 sm:flex-row sm:items-baseline sm:justify-between">
        <h2 id={id} className="text-[17px] font-semibold tracking-[-0.015em]">{title}</h2>
        {aside && <span className="text-[13px] text-ink-3">{aside}</span>}
      </div>
      {children}
    </section>
  );
}

export function Caption({ children, className }: { children: ReactNode; className?: string }) {
  return <p className={clsx("mt-3 text-[12.5px] leading-[1.6] text-ink-3", className)}>{children}</p>;
}

/* ------------------------------------------------------------------ callouts */
export function Callout({ kind = "note", label, children, className }: { kind?: "note" | "caveat" | "brand"; label?: string; children: ReactNode; className?: string }) {
  const styles = {
    note: "bg-surface border-line text-ink-2 [&_b]:text-ink",
    caveat: "bg-warn-soft border-warn-line text-[#4a3410] [&_b]:text-warn",
    brand: "bg-brand-soft border-brand-tint text-[#1e3a6e] [&_b]:text-brand-press",
  }[kind];
  const icon = kind === "caveat" ? <Icon.Alert size={16} className="mt-[3px] shrink-0 text-warn" /> : <Icon.Info size={16} className={clsx("mt-[3px] shrink-0", kind === "brand" ? "text-brand" : "text-ink-3")} />;
  return (
    <div role="note" className={clsx("flex gap-3 rounded-md border px-4 py-3 text-[13.5px] leading-[1.6]", styles, className)}>
      {icon}<div>{label && <b className="font-semibold">{label}. </b>}{children}</div>
    </div>
  );
}

/* ------------------------------------------------------------------ surfaces */
export function Panel({ children, className, pad = true }: { children: ReactNode; className?: string; pad?: boolean }) {
  return <div className={clsx("card", pad && "p-5 sm:p-6", className)}>{children}</div>;
}

export function KV({ rows, className, keyWidth = "38%" }: { rows: Row[]; className?: string; keyWidth?: string }) {
  return (
    <dl className={clsx("divide-y divide-line-soft text-[13.5px]", className)}>
      {rows.map(([k, v], i) => (
        <div key={i} className="grid gap-1 py-3 first:pt-0 last:pb-0 sm:grid-cols-[var(--kw)_1fr] sm:gap-4" style={{ ["--kw" as string]: keyWidth }}>
          <dt className="font-medium text-ink-3">{k}</dt>
          <dd className="leading-[1.6] text-ink-body">{v}</dd>
        </div>
      ))}
    </dl>
  );
}

export function MetricStrip({ items, className, cols }: { items: Metric[]; className?: string; cols?: number }) {
  const n = cols ?? items.length;
  return (
    <div className={clsx("ruled", n >= 4 ? "sm:grid-cols-2 xl:grid-cols-4" : n === 3 ? "md:grid-cols-3" : "sm:grid-cols-2", className)}>
      {items.map((m, i) => (
        <motion.div key={i} className="flex flex-col p-5 sm:p-6" initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35, delay: i * 0.05, ease: [0.2, 0.7, 0.2, 1] }}>
          <div className="text-[12.5px] font-medium text-ink-3">{m.kicker}</div>
          <div className="tnum mt-3 text-[34px] leading-none font-semibold tracking-[-0.04em] text-navy">{m.value}</div>
          <div className="mt-1.5 text-[13px] font-medium text-ink-2">{m.unit}</div>
          <p className="mt-3 text-[13px] leading-[1.6] text-ink-2">{m.description}</p>
          <div className="mt-auto pt-4 font-mono text-[11px] text-ink-3">{m.source}</div>
        </motion.div>
      ))}
    </div>
  );
}

/* ------------------------------------------------------------------ data table */
const isNum = (v: unknown) => typeof v === "number" || (typeof v === "string" && /^[+\-−]?\d[\d,.]*$/.test(v));

export function DataTable({ table, maxHeight = 420, className, caption }: { table: Table; maxHeight?: number; className?: string; caption?: string }) {
  if (!table.rows.length) return <Callout>No rows.</Callout>;
  const numericCols = table.columns.map((_, ci) => table.rows.every((r) => r[ci] === null || r[ci] === "" || isNum(r[ci])));
  return (
    <div className={clsx("card overflow-hidden", className)}>
      <div className="scroll-thin overflow-auto" style={{ maxHeight }} tabIndex={0} role="region" aria-label={caption ?? "Data table"}>
        <table className="w-full min-w-max border-collapse text-[13px]">
          {caption && <caption className="sr-only">{caption}</caption>}
          <thead className="sticky top-0 z-10 bg-subtle">
            <tr>
              {table.columns.map((c, i) => (
                <th key={c} scope="col" className={clsx("border-b border-line px-4 py-2.5 text-[12px] font-medium whitespace-nowrap text-ink-3", numericCols[i] ? "text-right" : "text-left")}>{c}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {table.rows.map((r, ri) => (
              <tr key={ri} className="border-b border-line-soft last:border-0 hover:bg-[#f7faff]">
                {r.map((v, ci) => (
                  <td key={ci} className={clsx("px-4 py-2.5 align-top", numericCols[ci] ? "tnum text-right whitespace-nowrap text-ink" : "max-w-[46ch] text-ink-body")}>
                    {v === null || v === "" ? <span className="text-[#a6b2c4]">–</span> : typeof v === "boolean" ? (v ? "yes" : "no") : String(v)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ tabs (underline indicator, shared layout animation) */
export function Tabs({ tabs, value, onValueChange, className, idPrefix }: {
  tabs: { value: string; label: ReactNode; content: ReactNode }[]; value?: string; onValueChange?: (v: string) => void; className?: string; idPrefix?: string;
}) {
  const [inner, setInner] = useState(tabs[0]?.value);
  const cur = value ?? inner;
  const uid = useId();
  const layoutId = `${idPrefix ?? uid}-tab-underline`;
  return (
    <RTabs.Root value={cur} onValueChange={(v) => { setInner(v); onValueChange?.(v); }} className={className}>
      <RTabs.List className="scroll-thin relative -mx-1 flex gap-1 overflow-x-auto border-b border-line px-1 sm:gap-6" aria-label="Sections">
        {tabs.map((t) => (
          <RTabs.Trigger key={t.value} value={t.value}
            className="relative h-11 shrink-0 px-2 text-[14px] font-medium whitespace-nowrap text-ink-3 transition-colors hover:text-ink data-[state=active]:text-ink sm:px-0">
            {t.label}
            {cur === t.value && <motion.span layoutId={layoutId} className="absolute inset-x-0 -bottom-px h-[2px] rounded-full bg-brand" transition={{ type: "spring", stiffness: 520, damping: 42 }} />}
          </RTabs.Trigger>
        ))}
      </RTabs.List>
      {tabs.map((t) => (
        <RTabs.Content key={t.value} value={t.value} className="pt-6 focus-visible:outline-none">
          <motion.div initial={{ opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.22, ease: [0.2, 0.7, 0.2, 1] }}>{t.content}</motion.div>
        </RTabs.Content>
      ))}
    </RTabs.Root>
  );
}

/* ------------------------------------------------------------------ segmented control */
export function Segmented({ value, onChange, options, label, size = "md" }: {
  value: string; onChange: (v: string) => void; options: { value: string; label: ReactNode }[]; label: string; size?: "sm" | "md";
}) {
  return (
    <ToggleGroup.Root type="single" value={value} onValueChange={(v) => v && onChange(v)} aria-label={label}
      className="inline-flex w-fit max-w-full flex-wrap gap-1 rounded-lg border border-line bg-[#f1f5fa] p-1">
      {options.map((o) => (
        <ToggleGroup.Item key={o.value} value={o.value}
          className={clsx("relative rounded-md px-3 font-medium text-ink-2 transition-colors hover:text-ink data-[state=on]:text-ink",
            size === "sm" ? "h-8 text-[13px]" : "h-9 text-[13.5px] max-sm:h-10")}>
          {value === o.value && <motion.span layoutId={`seg-${label}`} className="absolute inset-0 rounded-md bg-surface shadow-[0_1px_2px_rgb(11_23_54/0.10),0_0_0_1px_rgb(11_23_54/0.04)]" transition={{ type: "spring", stiffness: 560, damping: 44 }} />}
          <span className="relative">{o.label}</span>
        </ToggleGroup.Item>
      ))}
    </ToggleGroup.Root>
  );
}

/* ------------------------------------------------------------------ select */
export function Select({ value, onChange, options, label, hideLabel, className, triggerClassName }: {
  value: string; onChange: (v: string) => void; options: { value: string; label: string; group?: string; hint?: string }[]; label: string; hideLabel?: boolean;
  className?: string; triggerClassName?: string;
}) {
  const id = useId();
  const groups = Array.from(new Set(options.map((o) => o.group ?? "")));
  const current = options.find((o) => o.value === value);
  return (
    <div className={clsx("flex min-w-0 flex-col gap-1.5", className)}>
      <label id={id} className={clsx("text-[12px] font-medium text-ink-3", hideLabel && "sr-only")}>{label}</label>
      <RSelect.Root value={value} onValueChange={onChange}>
        <RSelect.Trigger aria-labelledby={id}
          className={clsx("group inline-flex h-10 min-w-0 items-center justify-between gap-2 rounded-md border border-line-strong bg-surface px-3 text-left text-[14px] text-ink shadow-[0_1px_2px_rgb(11_23_54/0.04)] transition-colors hover:border-[#b8c4d6] data-[state=open]:border-brand max-sm:h-11", triggerClassName)}>
          <span className="truncate"><RSelect.Value>{current?.label}</RSelect.Value></span>
          <RSelect.Icon><Icon.ChevronDown size={16} className="text-ink-3 transition-transform group-data-[state=open]:rotate-180" /></RSelect.Icon>
        </RSelect.Trigger>
        <RSelect.Portal>
          <RSelect.Content position="popper" sideOffset={6} collisionPadding={12}
            className="z-[80] max-h-[min(420px,var(--radix-select-content-available-height))] w-[var(--radix-select-trigger-width)] min-w-[240px] overflow-hidden rounded-lg border border-line bg-surface shadow-[var(--shadow-pop)] data-[state=open]:animate-[fadein_120ms_ease-out]">
            <RSelect.Viewport className="p-1">
              {groups.map((g) => (
                <RSelect.Group key={g}>
                  {g && <RSelect.Label className="px-2.5 pt-2.5 pb-1 font-mono text-[10.5px] tracking-[0.1em] text-ink-3 uppercase">{g}</RSelect.Label>}
                  {options.filter((o) => (o.group ?? "") === g).map((o) => (
                    <RSelect.Item key={o.value} value={o.value}
                      className="relative flex cursor-pointer items-center rounded-md py-2 pr-8 pl-2.5 text-[14px] text-ink-body outline-none select-none data-[highlighted]:bg-brand-soft data-[highlighted]:text-ink data-[state=checked]:font-medium">
                      <div className="flex flex-col">
                        <RSelect.ItemText>{o.label}</RSelect.ItemText>
                        {o.hint && <span className="text-[12px] text-ink-3">{o.hint}</span>}
                      </div>
                      <RSelect.ItemIndicator className="absolute right-2.5"><Icon.Check size={15} className="text-brand" /></RSelect.ItemIndicator>
                    </RSelect.Item>
                  ))}
                </RSelect.Group>
              ))}
            </RSelect.Viewport>
          </RSelect.Content>
        </RSelect.Portal>
      </RSelect.Root>
    </div>
  );
}

/* ------------------------------------------------------------------ disclosure */
export function Disclosure({ title, children, defaultOpen = false }: { title: ReactNode; children: ReactNode; defaultOpen?: boolean }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <Collapsible.Root open={open} onOpenChange={setOpen} className="card overflow-hidden">
      <Collapsible.Trigger className="flex w-full items-center justify-between gap-3 px-5 py-4 text-left text-[14px] font-medium text-ink hover:bg-subtle">
        {title}<Icon.ChevronDown size={16} className={clsx("shrink-0 text-ink-3 transition-transform duration-200", open && "rotate-180")} />
      </Collapsible.Trigger>
      <AnimatePresence initial={false}>
        {open && (
          <Collapsible.Content forceMount asChild>
            <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.24, ease: [0.2, 0.7, 0.2, 1] }} className="overflow-hidden">
              <div className="border-t border-line px-5 py-5">{children}</div>
            </motion.div>
          </Collapsible.Content>
        )}
      </AnimatePresence>
    </Collapsible.Root>
  );
}

/* ------------------------------------------------------------------ bullet list */
export function Bullets({ items, className }: { items: ReactNode[]; className?: string }) {
  return (
    <ul className={clsx("space-y-2 text-[13.5px] leading-[1.6] text-ink-2", className)}>
      {items.map((x, i) => (
        <li key={i} className="flex gap-3"><span className="mt-[9px] size-1 shrink-0 rounded-full bg-brand" aria-hidden="true" /><span>{x}</span></li>
      ))}
    </ul>
  );
}

/* ------------------------------------------------------------------ loading / error */
export function Skeleton({ className, style }: { className?: string; style?: React.CSSProperties }) {
  return <div className={clsx("skeleton", className)} style={style} aria-hidden="true" />;
}

export function LoadingBlock({ height = 320, className }: { height?: number; className?: string }) {
  return (
    <div className={clsx("card p-6", className)} role="status" aria-label="Loading">
      <Skeleton className="h-3 w-40" />
      <Skeleton className="mt-3 h-5 w-72 max-w-full" />
      <Skeleton className="mt-6 w-full" style={{ height: height - 110 }} />
    </div>
  );
}

export function ErrorState({ error }: { error: unknown }) {
  const e = error as { message?: string; filename?: string };
  return (
    <div role="alert" className="flex gap-3 rounded-lg border border-alert-line bg-alert-soft px-5 py-4 text-[14px] leading-[1.6] text-[#5b2410]">
      <Icon.Alert size={18} className="mt-0.5 shrink-0 text-alert" />
      <div>
        <b className="font-semibold text-alert">This view cannot be shown. </b>
        {e?.filename ? <>Data file <code className="font-mono text-[12.5px]">{e.filename}</code> failed a check. </> : null}
        {e?.message ?? "The analysis service did not answer."} No values are displayed for it.
      </div>
    </div>
  );
}

/* a soft refetch indicator: content stays, a thin bar shows work in progress */
export function Fetching({ active }: { active: boolean }) {
  return (
    <AnimatePresence>
      {active && (
        <motion.div className="pointer-events-none absolute inset-x-0 top-0 z-10 h-[2px] overflow-hidden rounded-full" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
          <motion.div className="h-full w-1/3 bg-brand" animate={{ x: ["-100%", "300%"] }} transition={{ duration: 0.9, repeat: Infinity, ease: "easeInOut" }} />
        </motion.div>
      )}
    </AnimatePresence>
  );
}
