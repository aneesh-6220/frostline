import { AnimatePresence, motion } from "motion/react";
import { useNavigate, useSearchParams } from "react-router";
import { BriefDownloads, ChartCard, DimensionGrid, FindingCard, ResultPanel, Steps } from "../components/domain";
import { MapView } from "../components/MapView";
import { Icon } from "../components/icons";
import { Button, Callout, Caption, ErrorState, LoadingBlock, MetricStrip, Section, Skeleton } from "../components/ui";
import { useDemoRoad, useEvidence, useInvestigation, useObservatory } from "../lib/api";
import { useInv, type Change } from "../lib/investigation";
import { LocationPicker } from "./Atlas";

const STAGES = ["The problem", "The geography", "The NASA data", "The scientific finding", "The transportation evidence", "The Evidence Brief"];

function StageHeader({ title, lede }: { title: string; lede?: string }) {
  return (
    <header className="mb-7 max-w-[780px]">
      <h1 className="text-[28px] leading-[1.12] font-semibold tracking-[-0.03em] text-balance sm:text-[34px]">{title}</h1>
      {lede && <p className="prose-frost mt-3 text-pretty">{lede}</p>}
    </header>
  );
}

function Problem() {
  const { data } = useObservatory();
  return (
    <>
      <StageHeader title="Winter is the road" lede="Across northern Canada, seasonal roads are built each winter on frozen lakes and rivers. They connect communities and carry supplies, and they exist only while the cold holds. People say winters are changing. Checking that claim properly is hard: it takes NASA climate data, daily records, seasonal indicators, trend statistics, government road records and a clear sense of what can and cannot be concluded." />
      {data ? <MetricStrip items={data.intro_metrics} /> : <Skeleton className="h-[230px] w-full rounded-lg" />}
      <Callout kind="brand" className="mt-4">Frostline turns that workflow into one investigation. It reports what the evidence supports and what it does not. It is not a road-safety tool and it predicts nothing.</Callout>
    </>
  );
}

function Geography() {
  const { boot, sel, set } = useInv();
  const prim = boot.primary.map((id) => boot.locations[id]);
  const loc = boot.locations[sel.loc];
  return (
    <>
      <StageHeader title="Choose a real northern case study" lede="Two documented ice roads in the Northwest Territories, about 1,100 km apart and very different in kind. Pick one; the rest of the demo follows your choice." />
      <div className="grid items-start gap-6 lg:grid-cols-[minmax(0,1.35fr)_minmax(0,1fr)]">
        <div>
          <MapView locations={prim} selected={sel.loc} zoomed={false} onSelect={(id) => set({ loc: id })} height={400} />
          <Caption>Markers: calculated sampling points. Rectangles: NASA grid cells. No road geometry is drawn.</Caption>
        </div>
        <div className="flex flex-col gap-4">
          <LocationPicker locations={prim} selected={sel.loc} onSelect={(id) => set({ loc: id })} />
          <div className="card p-5 sm:p-6">
            <div className="text-[12.5px] font-medium text-ink-3 capitalize">{loc.role} case study</div>
            <h2 className="mt-1 text-[17px] font-semibold tracking-[-0.015em]">{loc.name}</h2>
            <p className="mt-2 text-[13.5px] leading-[1.6] text-ink-2">{loc.setting}</p>
            <p className="mt-2 text-[13.5px] leading-[1.6] text-ink-2">{loc.access}</p>
          </div>
        </div>
      </div>
    </>
  );
}

function NasaData() {
  const { boot, sel } = useInv();
  const { data, error } = useInvestigation(sel, 400);
  const v = boot.variables[sel.var];
  const loc = boot.locations[sel.loc];
  return (
    <>
      <StageHeader title={`NASA data: ${v.phrase} at ${loc.short}`} lede={`${v.why} ${v.definition} Each point is one winter of NASA POWER daily data, a MERRA-2 reanalysis value for the grid cell containing the road.`} />
      {error ? <ErrorState error={error} /> : (
        <ChartCard figure={data?.chart} label={`${v.short} at ${loc.short}`} caption="Hover any winter to read its value. Change the variable or period in the investigation bar and the chart follows." />
      )}
      {v.is_temperature && <Callout kind="caveat" label="Reanalysis caveat" className="mt-4">{boot.bias_caveat}</Callout>}
    </>
  );
}

function Finding() {
  const { sel } = useInv();
  const { data, error } = useInvestigation(sel, 390);
  return (
    <>
      <StageHeader title="Has it changed, and how sure are we?" lede="A rate of change per decade, a 95% interval, a significance test and a correction for the number of tests run. A result that is not statistically resolved is still a scientific result." />
      {error ? <ErrorState error={error} /> : !data ? <LoadingBlock height={460} /> : (
        <div className="grid items-start gap-6 lg:grid-cols-[minmax(0,1.5fr)_minmax(0,1fr)]">
          <div className="flex min-w-0 flex-col gap-4">
            <ChartCard figure={data.chart} label="Trend chart" />
            <Callout kind="brand" label="In plain language">{data.plain}</Callout>
          </div>
          <FindingCard f={data.finding} />
        </div>
      )}
    </>
  );
}

function Road() {
  const { boot, sel } = useInv();
  const { data, error } = useDemoRoad(sel.loc);
  const loc = boot.locations[sel.loc];
  return (
    <>
      <StageHeader title={`What the road record shows at ${loc.short}`} lede="The territorial government publishes the date each road opened and closed, every winter since 1993/94. This is a record of operations, shown beside the NASA data, never merged with it." />
      {error ? <ErrorState error={error} /> : !data ? <LoadingBlock height={520} /> : (
        <div className="grid items-start gap-6 lg:grid-cols-[minmax(0,1.5fr)_minmax(0,1fr)]">
          <ChartCard figure={data.chart} label={`Environmental and operational timeline for ${loc.short}`} />
          <div className="flex flex-col gap-4">
            <FindingCard f={data.finding} showTable={false} />
            <ResultPanel label="Evidence conclusion" dim={data.conclusion} />
          </div>
        </div>
      )}
    </>
  );
}

function BriefStage() {
  const { sel, question } = useInv();
  const { data, error } = useEvidence(sel);
  return (
    <>
      {error ? <ErrorState error={error} /> : !data ? <LoadingBlock height={420} /> : (
        <>
          <StageHeader title="Audit the evidence, then take it with you" lede={`${data.report.headline} ${data.report.suitability}`} />
          <DimensionGrid report={data.report} cols={3} />
        </>
      )}
      <Section title="Reusable finding">
        <BriefDownloads sel={sel} question={question} />
        <Caption>The brief contains the question, location, data, trend, uncertainty, evidence assessment, limitations, sources and file hashes for this exact investigation.</Caption>
      </Section>
    </>
  );
}

export default function Demo() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const { searchFor } = useInv();
  const step = Math.max(0, Math.min(STAGES.length - 1, Number(params.get("step") ?? 0) || 0));

  const goStep = (s: number) => {
    s = Math.max(0, Math.min(STAGES.length - 1, s));
    let change: Change | undefined;
    if (s === 2 || s === 3) change = { variable: "fdd_octdec", question: "freezing" };
    else if (s === 4) change = { variable: "open_day", question: "roads" };
    navigate({ pathname: "/demo", search: `${searchFor(change)}&step=${s}` }, { preventScrollReset: false });
    window.scrollTo({ top: 0, behavior: "smooth" });
  };
  const Stage = [Problem, Geography, NasaData, Finding, Road, BriefStage][step];

  return (
    <div>
      <div className="kicker mb-4">Guided demo · stage {step + 1} of {STAGES.length}</div>
      <Steps labels={STAGES} active={step} onSelect={goStep} />
      <div className="mt-10">
        <AnimatePresence mode="wait">
          <motion.div key={step} initial={{ opacity: 0, x: 12 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -12 }} transition={{ duration: 0.22, ease: [0.2, 0.7, 0.2, 1] }}>
            <Stage />
          </motion.div>
        </AnimatePresence>
      </div>
      <div className="mt-10 flex flex-wrap items-center gap-3 border-t border-line pt-6">
        <Button onClick={() => goStep(step - 1)} disabled={step === 0} icon={<Icon.ArrowLeft size={16} />}>Back</Button>
        {step < STAGES.length - 1 ? (
          <Button variant="primary" onClick={() => goStep(step + 1)} iconRight={<Icon.ArrowRight size={16} />}>Next: {STAGES[step + 1]}</Button>
        ) : (
          <Button variant="primary" onClick={() => navigate({ pathname: "/trends", search: searchFor() })} iconRight={<Icon.ArrowRight size={16} />}>Explore freely</Button>
        )}
        <span className="ml-auto text-[12.5px] text-ink-3 max-sm:hidden">Every stage uses the same components and data as the free-exploration views.</span>
      </div>
    </div>
  );
}
