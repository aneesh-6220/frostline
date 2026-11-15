import { motion } from "motion/react";
import { useMemo } from "react";
import { Link } from "react-router";
import { Plot } from "../components/Plot";
import { Icon } from "../components/icons";
import { Badge, Callout, Caption, ErrorState, MetricStrip, Section, Skeleton } from "../components/ui";
import { useObservatory } from "../lib/api";
import { useInv } from "../lib/investigation";

/* Isotherms: a quiet field of contour lines, the "frost lines" the product is named for. Deterministic, no randomness. */
function Isotherms() {
  const paths = useMemo(() => {
    const out: string[] = [];
    for (let k = 0; k < 15; k++) {
      const base = 30 + k * 42;
      let d = "";
      for (let x = -20; x <= 1620; x += 20) {
        const y = base + 18 * Math.sin(x / 210 + k * 0.7) + 11 * Math.sin(x / 97 + k * 1.9) + 6 * Math.sin(x / 41 + k * 0.4) + k * Math.sin(x / 600) * 4;
        d += `${x === -20 ? "M" : "L"}${x},${y.toFixed(1)} `;
      }
      out.push(d);
    }
    return out;
  }, []);
  return (
    <svg className="pointer-events-none absolute inset-0 h-full w-full" viewBox="0 0 1600 640" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
      {paths.map((d, i) => (
        <motion.path key={i} d={d} fill="none" stroke={i % 5 === 2 ? "#60A5FA" : "#FFFFFF"} strokeOpacity={i % 5 === 2 ? 0.32 : 0.07} strokeWidth={i % 5 === 2 ? 1.2 : 1}
          initial={{ pathLength: 0 }} animate={{ pathLength: 1 }} transition={{ duration: 2.2, delay: i * 0.04, ease: [0.2, 0.7, 0.2, 1] }} />
      ))}
    </svg>
  );
}

const STEPS = ["Location", "Environmental evidence", "Trend", "Comparison", "Road history", "Evidence Brief"];

export function Observatory() {
  const { data, error } = useObservatory();
  const { searchFor, boot } = useInv();
  const begin = { pathname: "/demo", search: `${searchFor({ loc: boot.defaults.location, variable: boot.defaults.variable, question: null })}&step=0` };
  const explore = { pathname: "/trends", search: searchFor() };

  return (
    <div>
      {/* hero: full-bleed navy band */}
      <section className="relative mx-[calc(50%-50vw)] overflow-hidden bg-navy text-white lg:mx-[calc(50%-50vw+128px)]">
        <Isotherms />
        <div className="relative mx-auto grid max-w-[1240px] items-center gap-10 px-4 pt-12 pb-14 sm:px-6 sm:pt-16 lg:grid-cols-[minmax(0,0.95fr)_minmax(0,1.05fr)] lg:gap-12 lg:px-10 lg:pt-20 lg:pb-20">
          <div>
            <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}
              className="font-mono text-[11px] font-medium tracking-[0.14em] text-brand-ice uppercase">Frostline Observatory · NASA Earth science data, 2001 to 2025</motion.div>
            <motion.h1 initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, delay: 0.05 }}
              className="mt-5 max-w-[14ch] text-[40px] leading-[1.02] font-semibold tracking-[-0.045em] text-balance text-white sm:text-[56px] xl:text-[64px]">
              How is winter changing across Canada&rsquo;s North?
            </motion.h1>
            <motion.p initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, delay: 0.12 }}
              className="mt-6 max-w-[46ch] text-[16.5px] leading-[1.6] text-[#c3cee3]">
              Follow NASA Earth science data from measurement to discovery, and investigate what the evidence reveals about seasonal transportation.
            </motion.p>
            <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, delay: 0.18 }} className="mt-8 flex flex-wrap gap-3">
              <Link to={begin} className="inline-flex h-11 items-center gap-2 rounded-md bg-brand px-5 text-[14.5px] font-medium text-white shadow-[0_1px_0_rgb(255_255_255/0.2)_inset,0_8px_24px_-8px_rgb(37_99_235/0.7)] transition-colors hover:bg-[#3b74f0]">
                <Icon.Play size={17} />Begin an investigation
              </Link>
              <Link to={explore} className="inline-flex h-11 items-center gap-2 rounded-md border border-white/20 bg-white/5 px-5 text-[14.5px] font-medium text-white transition-colors hover:border-white/35 hover:bg-white/10">
                <Icon.Trend size={17} />Explore the data
              </Link>
            </motion.div>
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.6, delay: 0.3 }} className="mt-10">
              <div className="mb-3 text-[12px] font-medium text-[#8fa0bf]">The guided investigation</div>
              <ol className="flex flex-wrap gap-2">
                {STEPS.map((s, i) => (
                  <li key={s} className="flex items-center gap-2 rounded-full border border-white/12 bg-white/[0.04] py-1 pr-3 pl-1 text-[12.5px] text-[#d5ddec]">
                    <span className="tnum grid size-5 place-items-center rounded-full bg-white/10 text-[10.5px] font-semibold text-white">{i + 1}</span>{s}
                  </li>
                ))}
              </ol>
            </motion.div>
          </div>

          <motion.div initial={{ opacity: 0, y: 16, scale: 0.985 }} animate={{ opacity: 1, y: 0, scale: 1 }} transition={{ duration: 0.7, delay: 0.15, ease: [0.2, 0.7, 0.2, 1] }}
            className="rounded-xl bg-white p-4 text-ink-body shadow-[0_30px_80px_-24px_rgb(0_0_0/0.55),0_0_0_1px_rgb(255_255_255/0.08)] sm:p-5">
            {error ? <ErrorState error={error} /> : (
              <>
                <div className="flex flex-wrap items-start justify-between gap-3 px-1">
                  <div>
                    <div className="font-mono text-[10.5px] font-medium tracking-[0.12em] text-brand uppercase">Live from the data · Dettah, Yellowknife Bay</div>
                    <div className="mt-1.5 text-[15.5px] font-semibold tracking-[-0.015em] text-ink">Early-winter freezing degree-days, 24 winters of NASA data</div>
                  </div>
                  {data ? <Badge tone={data.hero_finding.tone}>{data.hero_finding.state_label}</Badge> : <Skeleton className="h-6 w-44 rounded-full" />}
                </div>
                <Plot figure={data?.hero_chart} label="Early-winter freezing degree-days at Dettah, 2001/02 to 2024/25, with the Theil-Sen trend and its 95% interval" />
                {data && <Caption className="px-1">{data.hero_caption}</Caption>}
              </>
            )}
          </motion.div>
        </div>
      </section>

      <Section title="What the evidence shows so far" aside="Computed from the approved data on every load">
        {data ? <MetricStrip items={data.metrics} /> : <Skeleton className="h-[260px] w-full rounded-lg" />}
      </Section>

      <div className="grid gap-x-12 lg:grid-cols-[1.1fr_1fr]">
        <Section title="What you can do here">
          <div className="card divide-y divide-line overflow-hidden">
            {[
              { n: "01", k: "Guided discovery", h: "Start from a question", p: "Pick a plain question about northern winters. Frostline recommends the NASA variables that can answer it and tells you why each one is relevant.", to: "/questions", cta: "Questions" },
              { n: "02", k: "Research explorer", h: "Quantify the change", p: "Choose a location, a variable and a period. See the real series, the rate of change per decade, its uncertainty and a significance test that always matches your selection.", to: "/trends", cta: "Trend Detective" },
              { n: "03", k: "Evidence workspace", h: "Judge the evidence, then export it", p: "The Evidence Engine separates observations, inference and limitations, exposes where sources disagree, and produces a reproducible Evidence Brief.", to: "/evidence", cta: "Evidence Engine" },
            ].map((r) => (
              <Link key={r.n} to={{ pathname: r.to, search: searchFor() }} className="group grid grid-cols-[36px_1fr_auto] items-start gap-3 p-5 transition-colors hover:bg-[#f7faff] sm:p-6">
                <span className="tnum pt-0.5 font-mono text-[12px] text-ink-3">{r.n}</span>
                <span>
                  <span className="block text-[12px] font-medium text-brand">{r.k}</span>
                  <span className="mt-0.5 block text-[15.5px] font-semibold tracking-[-0.015em] text-ink">{r.h}</span>
                  <span className="mt-1.5 block text-[13.5px] leading-[1.6] text-ink-2">{r.p}</span>
                </span>
                <span className="mt-6 flex items-center gap-1 text-[13px] font-medium text-ink-3 transition-colors group-hover:text-brand max-sm:hidden">
                  {r.cta}<Icon.ArrowRight size={15} className="transition-transform group-hover:translate-x-0.5" />
                </span>
              </Link>
            ))}
          </div>
        </Section>
        <Section title="Why it matters">
          <p className="prose-frost text-pretty">
            Seasonal roads built on frozen lakes and rivers connect northern communities and carry supplies each winter. Asking how winter conditions and road seasons have
            changed means finding NASA datasets, cleaning daily records, computing seasonal indicators, fitting trends, locating government records and working out what can
            honestly be concluded. Frostline compresses that workflow into one guided, reproducible investigation.
          </p>
          {data && <Caption>{data.release}</Caption>}
          <Callout className="mt-5" label="Scope">
            Frostline is a scientific investigation tool. It does not measure ice thickness, assess road safety, recommend routes or predict opening dates, and it does not show
            what produced any change in the road record.
          </Callout>
        </Section>
      </div>
    </div>
  );
}
