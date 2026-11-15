import clsx from "clsx";
import { motion } from "motion/react";
import type { ReactNode } from "react";
import { apiUrl, type Sel } from "../lib/api";
import { useInv } from "../lib/investigation";
import type { Dimension, Figure, Finding, Layer, Report, Tone } from "../lib/types";
import { Plot } from "./Plot";
import { Badge, Callout, Caption, Disclosure, DownloadLink, KV } from "./ui";

const TONE_RULE: Record<Tone, string> = { good: "before:bg-good", neutral: "before:bg-[#94a3b8]", warn: "before:bg-[#d98a06]", alert: "before:bg-alert", muted: "before:bg-[#cbd5e1]" };

/* One result with everything the contract requires beside it: n, period, units, intervals, p, q, status and provenance. */
export function FindingCard({ f, title, showTable = true, tableOpen = true, className }: { f: Finding; title?: string; showTable?: boolean; tableOpen?: boolean; className?: string }) {
  const { boot } = useInv();
  return (
    <div className={clsx("flex flex-col gap-3", className)}>
      <section className={clsx("card relative overflow-hidden p-5 sm:p-6 before:absolute before:inset-y-0 before:left-0 before:w-[3px]", TONE_RULE[f.tone])}>
        <div className="flex flex-wrap items-center justify-between gap-2">
          <span className="text-[12.5px] font-medium text-ink-3">{title ?? f.display.title}</span>
          <Badge tone={f.tone}>{f.state_label}</Badge>
        </div>
        {f.estimated ? (
          <>
            <div className="mt-4 flex flex-wrap items-baseline gap-x-2.5 gap-y-1">
              <motion.span key={f.display.slope} initial={{ opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}
                className="tnum text-[40px] leading-none font-semibold tracking-[-0.045em] text-navy">{f.display.slope}</motion.span>
              <span className="text-[13.5px] font-medium text-ink-2">{f.display.unit} · {f.display.direction}</span>
            </div>
            <p className="tnum mt-2 text-[13px] text-ink-3">{f.display.meta}</p>
          </>
        ) : (
          <>
            <div className="mt-4 text-[30px] leading-none font-semibold tracking-[-0.03em] text-navy">Not estimated</div>
            <p className="mt-2 text-[13px] text-ink-3">{f.display.meta}</p>
          </>
        )}
        <p className="mt-4 text-[14px] leading-[1.6] text-ink-body">{f.sentence}</p>
        {f.extra_sentences.map((s, i) => <p key={i} className="mt-2 text-[13px] leading-[1.6] text-ink-2">{s}</p>)}
        <div className="mt-5 border-t border-line-soft pt-3 text-[12px] leading-[1.55] text-ink-3">{f.display.provenance}</div>
      </section>
      {showTable && f.stat_rows && (
        <Disclosure title="Full statistical record" defaultOpen={tableOpen}><KV rows={f.stat_rows} keyWidth="44%" /></Disclosure>
      )}
      {f.is_temperature && <Callout kind="caveat" label="Reanalysis caveat">{boot.bias_caveat}</Callout>}
    </div>
  );
}

/* A result-shaped panel for values that are not a single trend finding (a comparison, an association, a conclusion). */
export function ResultPanel({ label, badge, value, unit, meta, paragraphs = [], dim = [], source, tone = "neutral", lead }: {
  label: string; badge?: ReactNode; value?: string; unit?: string; meta?: string; paragraphs?: string[]; dim?: string[]; source?: string; tone?: Tone; lead?: boolean;
}) {
  return (
    <section className={clsx("card relative overflow-hidden p-5 sm:p-6 before:absolute before:inset-y-0 before:left-0 before:w-[3px]", TONE_RULE[tone])}>
      <div className="flex flex-wrap items-center justify-between gap-2"><span className="text-[12.5px] font-medium text-ink-3">{label}</span>{badge}</div>
      {value && (
        <div className="mt-4 flex flex-wrap items-baseline gap-x-2.5 gap-y-1">
          <span className="tnum text-[40px] leading-none font-semibold tracking-[-0.045em] text-navy">{value}</span>
          {unit && <span className="text-[13.5px] font-medium text-ink-2">{unit}</span>}
        </div>
      )}
      {meta && <p className="tnum mt-2 text-[13px] text-ink-3">{meta}</p>}
      {paragraphs.map((p, i) => <p key={i} className={clsx("mt-4 leading-[1.6] text-ink-body", lead && i === 0 ? "text-[16px] text-ink" : "text-[14px]")}>{p}</p>)}
      {dim.map((p, i) => <p key={i} className="mt-2 text-[13.5px] leading-[1.6] text-ink-2">{p}</p>)}
      {source && <div className="mt-5 border-t border-line-soft pt-3 text-[12px] leading-[1.55] text-ink-3">{source}</div>}
    </section>
  );
}

export function ChartCard({ kicker, title, aside, figure, caption, label, onPointClick, className, children }: {
  kicker?: ReactNode; title?: ReactNode; aside?: ReactNode; figure: Figure | undefined; caption?: ReactNode; label: string; onPointClick?: (p: any) => void; className?: string; children?: ReactNode;
}) {
  return (
    <div className={clsx("card p-4 sm:p-5", className)}>
      {(kicker || title || aside) && (
        <div className="mb-2 flex flex-wrap items-start justify-between gap-3 px-1">
          <div>
            {kicker && <div className="text-[12.5px] font-medium text-ink-3">{kicker}</div>}
            {title && <div className="mt-0.5 text-[15px] font-semibold tracking-[-0.01em] text-ink">{title}</div>}
          </div>
          {aside}
        </div>
      )}
      <Plot figure={figure} label={label} onPointClick={onPointClick} />
      {children}
      {caption && <Caption className="px-1">{caption}</Caption>}
    </div>
  );
}

export function DimensionGrid({ report, cols = 2 }: { report: Report; cols?: 2 | 3 }) {
  return (
    <div className={clsx("ruled", cols === 3 ? "md:grid-cols-2 xl:grid-cols-3" : "md:grid-cols-2")}>
      {report.dimensions.map((d: Dimension, i) => (
        <motion.div key={d.key} className="flex flex-col p-5 sm:p-6" initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3, delay: i * 0.04 }}>
          <div className="mb-3 flex items-start justify-between gap-3">
            <h3 className="text-[14.5px] leading-[1.35] font-semibold">{d.title}</h3>
            <Badge tone={d.tone}>{d.state}</Badge>
          </div>
          <p className="mb-3 text-[14px] leading-[1.55] text-ink">{d.summary}</p>
          <ul className="space-y-1.5">
            {d.reasons.map((r, j) => <li key={j} className="flex gap-2.5 text-[13px] leading-[1.55] text-ink-2"><span className="mt-[8px] size-1 shrink-0 rounded-full bg-[#9fb0c8]" />{r}</li>)}
          </ul>
          {d.sources.length > 0 && <div className="mt-auto pt-4 font-mono text-[11px] text-ink-3">From: {d.sources.join(", ")}</div>}
        </motion.div>
      ))}
    </div>
  );
}

const LAYER_LETTER: Record<string, string> = { observations: "A", derived: "B", inference: "C", corroboration: "D", limitations: "E", questions: "F" };
export function LayerList({ layers }: { layers: Layer[] }) {
  return (
    <ol className="flex flex-col gap-6">
      {layers.map((l) => (
        <li key={l.key} className="grid grid-cols-[32px_1fr] gap-3">
          <span className="grid size-8 place-items-center rounded-md border border-brand-tint bg-brand-soft font-mono text-[12px] font-semibold text-brand">{LAYER_LETTER[l.key] ?? "·"}</span>
          <div>
            <h3 className="text-[14.5px] font-semibold">{l.title}</h3>
            <p className="mt-0.5 mb-2 text-[12.5px] text-ink-3">{l.question}</p>
            <ul className="space-y-1.5">{l.items.map((x, i) => <li key={i} className="text-[13.5px] leading-[1.6] text-ink-2">{x}</li>)}</ul>
          </div>
        </li>
      ))}
    </ol>
  );
}

export function BriefDownloads({ sel, question }: { sel: Sel; question: string | null }) {
  const p = { ...sel, question, download: true };
  return (
    <div className="grid gap-3 sm:grid-cols-3">
      <DownloadLink variant="primary" href={apiUrl("/brief", { ...p, format: "html" })}>Evidence Brief (HTML)</DownloadLink>
      <DownloadLink href={apiUrl("/brief", { ...p, format: "csv" })}>Data (CSV)</DownloadLink>
      <DownloadLink href={apiUrl("/brief", { ...p, format: "json" })}>Analysis record (JSON)</DownloadLink>
    </div>
  );
}

/* Six-stage path indicator (guided demo) and the plain stepper (observatory). */
export function Steps({ labels, active, onSelect }: { labels: string[]; active?: number; onSelect?: (i: number) => void }) {
  return (
    <div>
      <ol className="flex flex-wrap gap-x-5 gap-y-3">
        {labels.map((l, i) => {
          const state = active === undefined ? "idle" : i === active ? "on" : i < active ? "done" : "idle";
          const El = onSelect ? "button" : "span";
          return (
            <li key={l}>
              <El {...(onSelect ? { onClick: () => onSelect(i), type: "button" } : {})} aria-current={state === "on" ? "step" : undefined}
                className={clsx("flex items-center gap-2 text-[13px] transition-colors", state === "on" ? "font-medium text-ink" : state === "done" ? "text-ink-2" : "text-ink-3", onSelect && "hover:text-ink")}>
                <span className={clsx("tnum grid size-[22px] place-items-center rounded-full border text-[11px] font-semibold transition-colors",
                  state === "on" ? "border-brand bg-brand text-white" : state === "done" ? "border-brand-tint bg-brand-soft text-brand" : "border-line-strong text-ink-3")}>{i + 1}</span>
                {l}
              </El>
            </li>
          );
        })}
      </ol>
      {active !== undefined && (
        <div className="mt-5 h-[3px] overflow-hidden rounded-full bg-line" aria-hidden="true">
          <motion.div className="h-full rounded-full bg-brand" animate={{ width: `${((active + 1) / labels.length) * 100}%` }} transition={{ duration: 0.4, ease: [0.2, 0.7, 0.2, 1] }} />
        </div>
      )}
    </div>
  );
}
