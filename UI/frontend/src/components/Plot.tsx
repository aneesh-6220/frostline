import clsx from "clsx";
import { useEffect, useRef, useState } from "react";
import type { Figure } from "../lib/types";
import { Skeleton } from "./ui";

/*
 * Renders a Plotly figure produced by frostline/charts.py (recoloured for the light theme by UI/api/chart_theme.py).
 * plotly.js is loaded on first use, so the first screen does not wait for it.
 */
type PlotlyLib = typeof import("plotly.js-dist-min");
let plotlyPromise: Promise<PlotlyLib> | null = null;
export const loadPlotly = () => (plotlyPromise ??= import("plotly.js-dist-min").then((m: any) => (m.default ?? m) as PlotlyLib));

const CONFIG = {
  displaylogo: false,
  responsive: true,
  displayModeBar: "hover" as const,
  modeBarButtonsToRemove: ["lasso2d", "select2d", "autoScale2d", "zoomIn2d", "zoomOut2d", "toImage"],
  scrollZoom: false,
};

type Bucket = "s" | "m" | "l";
const bucketOf = (w: number): Bucket => (w < 560 ? "s" : w < 820 ? "m" : "l");

function adapt(layout: Record<string, any>, b: Bucket) {
  const l = structuredClone(layout);
  if (b === "s") {
    const m = l.margin ?? {};
    l.margin = { ...m, r: Math.min(m.r ?? 16, 28), l: (m.l ?? 60) > 120 ? 128 : Math.min(m.l ?? 60, 52) };
    if (l.legend) l.legend = { ...l.legend, font: { ...(l.legend.font ?? {}), size: 11 } };
    l.font = { ...(l.font ?? {}), size: 11 };
  }
  if (b !== "l") l.dragmode = false;
  return l;
}

export function Plot({ figure, className, label, onPointClick, config, fallback }: {
  figure: Figure | undefined; className?: string; label: string; onPointClick?: (point: any) => void; config?: Record<string, unknown>;
  fallback?: Figure; /* drawn instead when the figure cannot render (for example, map tiles that cannot load offline) */
}) {
  const ref = useRef<HTMLDivElement>(null);
  const [ready, setReady] = useState(false);
  const [failed, setFailed] = useState(false);
  const [bucket, setBucket] = useState<Bucket>("l");
  const height = (figure?.layout as any)?.height ?? 380;
  const clickRef = useRef(onPointClick);
  clickRef.current = onPointClick;

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    setBucket(bucketOf(el.clientWidth));
    const ro = new ResizeObserver(() => setBucket(bucketOf(el.clientWidth)));
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  useEffect(() => {
    let cancelled = false;
    if (!figure) return;
    loadPlotly().then((Plotly) => {
      const el = ref.current as any;
      if (cancelled || !el) return;
      const cfg = { ...CONFIG, ...(config ?? {}) } as any;
      const done = () => {
        if (cancelled) return;
        setReady(true);
        if (!el.__flClick) {
          el.on("plotly_click", (ev: any) => clickRef.current?.(ev?.points?.[0]));
          el.__flClick = true;
        }
      };
      const fig = failed && fallback ? fallback : figure;
      Plotly.react(el, fig.data as any, adapt(fig.layout, bucket) as any, cfg).then(done).catch(() => {
        if (cancelled) return;
        if (fallback && !failed) { Plotly.purge(el); setFailed(true); } else setReady(true);
      });
    });
    return () => { cancelled = true; };
  }, [figure, bucket, config, failed, fallback]);

  useEffect(() => () => { const el = ref.current; if (el) loadPlotly().then((P) => P.purge(el)); }, []);

  return (
    <div className={clsx("relative w-full", className)} style={{ minHeight: height }} role="figure" aria-label={label}>
      {!ready && <Skeleton className="absolute inset-0" />}
      {/* the plot node's className must never change after Plotly adds its own classes to it */}
      <div className={clsx("w-full transition-opacity duration-300", ready ? "opacity-100" : "opacity-0")}><div ref={ref} className="w-full" /></div>
    </div>
  );
}
