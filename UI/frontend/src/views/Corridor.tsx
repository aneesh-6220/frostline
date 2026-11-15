import { Slider } from "radix-ui";
import { useEffect, useState } from "react";
import { ChartCard, FindingCard, ResultPanel } from "../components/domain";
import { Plot } from "../components/Plot";
import { Icon } from "../components/icons";
import { Badge, Button, Callout, Caption, DataTable, ErrorState, Fetching, Kicker, KV, LoadingBlock, PageHeader, Section, Segmented, Select, Skeleton, Tabs } from "../components/ui";
import { useAssociations, useConclusion, useCorridor, useCorridorEnv, useCorridorRoad, useRoutes, useTimeline } from "../lib/api";
import { useInv, winter } from "../lib/investigation";

const ROAD_VARS = ["open_day", "close_day", "open_to_close_days"];
const ENV_VARS = ["fdd_octdec", "mean_octdec_c", "mean_janmar_c", "tmax_mean_mar15_apr15_c"];

function RoadHistory() {
  const { boot, sel } = useInv();
  const [measure, setMeasure] = useState(ROAD_VARS.includes(sel.var) ? sel.var : "open_day");
  const { data, error, isFetching } = useCorridorRoad(sel.loc, measure);
  return (
    <div>
      <Kicker className="mb-3">Road-operations results · government record</Kicker>
      <Segmented label="Road measure" value={measure} onChange={setMeasure} options={ROAD_VARS.map((v) => ({ value: v, label: boot.variables[v].short }))} />
      {error ? <ErrorState error={error} /> : !data ? <LoadingBlock className="mt-5" height={420} /> : (
        <>
          <div className="relative mt-5"><Fetching active={isFetching} /><ChartCard figure={data.chart} label={`${boot.variables[measure].short} over the full record`} /></div>
          <div className="mt-6 grid items-start gap-6 md:grid-cols-2">
            <FindingCard f={data.full} tableOpen={false} />
            <FindingCard f={data.nasa} tableOpen={false} />
          </div>
          <Callout className="mt-4">{data.note}</Callout>
          <DataTable className="mt-6" table={data.table} maxHeight={300} caption="Road record by winter" />
        </>
      )}
    </div>
  );
}

function Environment() {
  const { boot, sel } = useInv();
  const [v, setV] = useState(ENV_VARS.includes(sel.var) ? sel.var : "fdd_octdec");
  const { data, error, isFetching } = useCorridorEnv(sel.loc, v);
  return (
    <div>
      <Kicker className="mb-3">Environmental results · NASA reanalysis</Kicker>
      <Segmented label="Environmental variable" value={v} onChange={setV} options={ENV_VARS.map((x) => ({ value: x, label: boot.variables[x].short }))} />
      {error ? <ErrorState error={error} /> : !data ? <LoadingBlock className="mt-5" height={420} /> : (
        <>
          <div className="mt-5 grid items-start gap-6 lg:grid-cols-[minmax(0,1.6fr)_minmax(0,1fr)]">
            <div className="relative min-w-0"><Fetching active={isFetching} /><ChartCard figure={data.chart} label={`${boot.variables[v].short} trend`} /></div>
            <FindingCard f={data.finding} showTable={false} />
          </div>
          <Callout className="mt-4">{data.thaw_note}</Callout>
        </>
      )}
    </div>
  );
}

function Timeline() {
  const { boot, sel } = useInv();
  const [v, setV] = useState("fdd_octdec");
  const [year, setYear] = useState<number | null>(null);
  const [draft, setDraft] = useState<number | null>(null);
  const { data, error, isFetching } = useTimeline(sel.loc, v, year);
  useEffect(() => { if (data && draft === null) setDraft(data.year); }, [data, draft]);
  const years = data?.years ?? [];
  return (
    <div>
      <Kicker className="mb-2">Environmental and operational timeline</Kicker>
      <p className="prose-frost mb-5 max-w-[86ch]">Two panels on one winter axis, each with its own units. The upper panel is NASA data; the lower panel is the government record.</p>
      <div className="mb-5 grid gap-5 md:grid-cols-2">
        <Select label="Environmental variable" value={v} onChange={setV} options={ENV_VARS.map((x) => ({ value: x, label: boot.variables[x].label }))} />
        <div className="flex flex-col gap-1.5">
          <div className="flex items-baseline justify-between"><span className="text-[12px] font-medium text-ink-3">Inspect a winter</span>
            <span className="tnum text-[13px] font-medium text-ink">{draft !== null ? winter(draft) : "…"}</span></div>
          {years.length > 0 && draft !== null ? (
            <Slider.Root className="relative flex h-10 touch-none items-center select-none" min={years[0]} max={years[years.length - 1]} step={1} value={[draft]}
              onValueChange={(x) => setDraft(x[0])} onValueCommit={(x) => setYear(x[0])} aria-label="Inspect a winter">
              <Slider.Track className="relative h-1.5 grow rounded-full bg-[#e3e9f2]"><Slider.Range className="absolute h-full rounded-full bg-brand" /></Slider.Track>
              <Slider.Thumb aria-valuetext={winter(draft)} className="block size-5 rounded-full border-2 border-brand bg-white shadow-[0_1px_3px_rgb(11_23_54/0.25)] focus-visible:shadow-[0_0_0_6px_rgb(37_99_235/0.2)] focus-visible:outline-none" />
            </Slider.Root>
          ) : <Skeleton className="h-10" />}
        </div>
      </div>
      {error ? <ErrorState error={error} /> : !data ? <LoadingBlock height={560} /> : (
        <>
          <div className="relative"><Fetching active={isFetching} /><ChartCard figure={data.chart} label="Environmental values and recorded operating windows on a shared winter axis" /></div>
          <div className="mt-6 grid items-start gap-6 lg:grid-cols-2">
            <div className="card p-5 sm:p-6"><h3 className="mb-4 text-[17px] font-semibold">Winter {data.winter}</h3><KV rows={data.record} keyWidth="40%" /></div>
            <div className="flex flex-col gap-4">
              {data.overlap && <Callout kind="caveat" label="Retrospective information">{data.overlap}</Callout>}
              <Callout>{data.note}</Callout>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

function Associations() {
  const { sel } = useInv();
  const { data, error } = useAssociations(sel.loc);
  return (
    <div>
      <Kicker className="mb-2">Exploratory associations · association, not cause</Kicker>
      <p className="prose-frost mb-5 max-w-[86ch]">Spearman rank correlations between NASA climate predictors and road dates. Each predictor window ends the day before the earliest opening (or closing) ever recorded for the road, so it never includes information from after the outcome.</p>
      {error ? <ErrorState error={error} /> : !data ? <LoadingBlock height={300} /> : (
        <>
          <DataTable table={data.table} caption="Leak-free exploratory associations" />
          <Callout className="mt-4">{data.note}</Callout>
          {data.overlap && <Caption>{data.overlap}</Caption>}
          {data.snow && (
            <Section title="Snow hypothesis · hypothesis, not a cause">
              <div className="grid items-start gap-6 lg:grid-cols-[minmax(0,1.5fr)_minmax(0,1fr)]">
                <ChartCard figure={data.snow.chart} label="Snow on the ground on Nov 28 against the Dettah opening day" />
                <ResultPanel label="Snow on the ground, Nov 28 · Dettah opening day" badge={<Badge tone="warn">Hypothesis</Badge>} value={data.snow.value} unit={data.snow.unit}
                  meta={data.snow.meta} paragraphs={[data.snow.text]} source={data.snow.source} tone="warn" />
              </div>
            </Section>
          )}
        </>
      )}
    </div>
  );
}

function Routes() {
  const { boot } = useInv();
  const [metric, setMetric] = useState("open_day");
  const [win, setWin] = useState("1993");
  const { data, error, isFetching } = useRoutes(metric, win);
  return (
    <div>
      <Kicker className="mb-2">Selection-adjusted view · all NWT routes</Kicker>
      <p className="prose-frost mb-5 max-w-[86ch]">Dettah was chosen after its trend had been seen. To adjust for that, the same test is run for every NWT route with at least 15 verified winters (17 routes, 3 measures, 51 tests) and corrected across all of them.</p>
      <div className="mb-5 flex flex-col gap-3 xl:flex-row">
        <Segmented label="Road measure" value={metric} onChange={setMetric} options={ROAD_VARS.map((v) => ({ value: v, label: boot.variables[v].short }))} />
        <Segmented label="Window" value={win} onChange={setWin} options={[
          { value: "1993", label: "1993/94 to 2024/25 (all-route family of 51 tests)" },
          { value: "2001", label: "2001/02 to 2024/25 (nine corridors with NASA data)" }]} />
      </div>
      {error ? <ErrorState error={error} /> : !data ? <LoadingBlock height={560} /> : (
        <>
          <div className="card relative p-4 sm:p-5"><Fetching active={isFetching} /><Plot figure={data.chart} label="Road-date slopes by route with 95% intervals" /></div>
          <DataTable className="mt-6" table={data.table} maxHeight={320} caption="Route trends" />
          <Callout className="mt-4">{data.note}</Callout>
        </>
      )}
    </div>
  );
}

function Conclusion() {
  const { sel, go } = useInv();
  const { data, error } = useConclusion(sel.loc);
  return error ? <ErrorState error={error} /> : !data ? <LoadingBlock height={260} /> : (
    <div>
      <ResultPanel label={data.label} paragraphs={data.paragraphs} source={data.source} lead />
      <div className="mt-5 flex flex-wrap gap-3">
        <Button onClick={() => go("/evidence")} iconRight={<Icon.ArrowRight size={16} />}>Audit this evidence</Button>
        <Button variant="primary" onClick={() => go("/brief")} iconRight={<Icon.ArrowRight size={16} />}>Export the Evidence Brief</Button>
      </div>
    </div>
  );
}

export default function Corridor() {
  const { sel } = useInv();
  const { data, error } = useCorridor(sel.loc);
  return (
    <div>
      {error ? <ErrorState error={error} /> : !data ? <LoadingBlock height={260} /> : (
        <>
          <PageHeader eyebrow={data.kicker} title={data.name} lede={data.setting} />
          <div className="grid items-start gap-6 lg:grid-cols-[minmax(0,1.2fr)_minmax(0,1fr)]">
            <div className="card p-5 sm:p-6"><KV rows={data.rows} keyWidth="32%" /></div>
            <div className="flex flex-col gap-3">
              <Callout kind="caveat" label="Read this first">{data.caution}</Callout>
              <Callout kind="caveat" label="About the road record">{data.road_note}</Callout>
            </div>
          </div>
        </>
      )}
      <Tabs key={sel.loc} className="mt-12" idPrefix="corridor" tabs={[
        { value: "road", label: "Road history", content: <RoadHistory /> },
        { value: "env", label: "Environmental record", content: <Environment /> },
        { value: "timeline", label: "Timeline", content: <Timeline /> },
        { value: "assoc", label: "Associations", content: <Associations /> },
        { value: "routes", label: "All NWT routes", content: <Routes /> },
        { value: "conclusion", label: "Evidence conclusion", content: <Conclusion /> },
      ]} />
    </div>
  );
}
