import { ChartCard, DimensionGrid, LayerList, ResultPanel } from "../components/domain";
import { Icon } from "../components/icons";
import { Badge, Bullets, Button, Callout, Caption, DataTable, Disclosure, DownloadLink, ErrorState, Fetching, Kicker, LoadingBlock, MetricStrip, PageHeader, Section, Tabs } from "../components/ui";
import { apiUrl, useDisagreement, useEvidence, useMultipleTesting } from "../lib/api";
import { useInv } from "../lib/investigation";

function Disagreement() {
  const { boot } = useInv();
  const { data, error } = useDisagreement();
  if (error) return <ErrorState error={error} />;
  if (!data) return <LoadingBlock height={420} />;
  return (
    <div>
      <Kicker className="mb-2">Source disagreement explorer · NASA reanalysis against a ground station</Kicker>
      <p className="prose-frost mb-5 max-w-[90ch]">NASA POWER temperature is a MERRA-2 reanalysis value for a grid cell roughly 55 km north to south and 25 to 32 km east to west. Yellowknife A is a single weather station inside that cell, about 6 km from the Dettah sampling point. They are different kinds of measurement, and they disagree.</p>
      <MetricStrip items={data.metrics} />
      <Callout kind="caveat" label="Reanalysis caveat" className="mt-4">{boot.bias_caveat}</Callout>
      <div className="mt-8 grid items-start gap-6 lg:grid-cols-2">
        <div>
          <h3 className="mb-3 text-[16px] font-semibold">Seasonal difference</h3>
          <ChartCard figure={data.bias_chart} label="Mean NASA minus station temperature by month" caption={data.bias_caption} />
        </div>
        <div>
          <h3 className="mb-3 text-[16px] font-semibold">Freezing accumulation, winter by winter</h3>
          <ChartCard figure={data.fdd_chart} label="Oct to Dec freezing degree-days, NASA against station" caption={data.fdd_caption} />
        </div>
      </div>
      <Section title="Trend sensitivity on the matched winters">
        <DataTable table={data.trend_table} caption="Trend on matched winters" />
        <Callout className="mt-4">{data.trend_note}</Callout>
      </Section>
      <div className="grid items-start gap-x-8 lg:grid-cols-2">
        <Section title="Aklavik and Inuvik stations">
          <DataTable table={data.aklavik_table} caption="Aklavik and Inuvik station comparison" />
          <Caption>{data.aklavik_caption}</Caption>
        </Section>
        <Section title="What this means for the investigation">
          <div className="card p-5 sm:p-6"><Bullets items={data.meaning} /></div>
        </Section>
      </div>
    </div>
  );
}

function MultipleTesting() {
  const { data, error } = useMultipleTesting();
  if (error) return <ErrorState error={error} />;
  if (!data) return <LoadingBlock height={420} />;
  return (
    <div>
      <Kicker className="mb-2">Multiple testing · why small p-values are not all findings</Kicker>
      <p className="prose-frost mb-5 max-w-[90ch]">{data.intro}</p>
      <MetricStrip items={data.metrics} />
      <ChartCard className="mt-6" figure={data.chart} label="All 126 unadjusted p-values ranked against the Benjamini-Hochberg line" caption={data.chart_caption} />
      <Section title="Declared test families">
        <DataTable table={data.families} caption="Declared test families" />
      </Section>
      <div className="mt-6">
        <Disclosure title="All 126 tests">
          <DataTable table={data.all} maxHeight={380} caption="All 126 tests" />
          <div className="mt-4"><DownloadLink href={apiUrl("/evidence/multiple-testing.csv")}>Download the 126-test table (CSV)</DownloadLink></div>
        </Disclosure>
      </div>
      <Callout className="mt-4">{data.note}</Callout>
    </div>
  );
}

export default function Evidence() {
  const { sel, go } = useInv();
  const { data, error, isFetching } = useEvidence(sel);
  return (
    <div>
      <PageHeader eyebrow="Frostline Evidence Engine" title="How far can this evidence be trusted?" lede={data?.lede} />
      {error ? <ErrorState error={error} /> : !data ? <LoadingBlock height={240} /> : (
        <div className="relative">
          <Fetching active={isFetching} />
          <ResultPanel label="Assessment for the current investigation" badge={<Badge tone={data.tone}>{data.state_label}</Badge>} paragraphs={[data.report.headline]}
            dim={[data.report.suitability]} tone={data.tone} lead />
        </div>
      )}
      <Tabs className="mt-12" idPrefix="evidence" tabs={[
        { value: "quality", label: "Evidence quality", content: data ? (
          <>
            <p className="prose-frost mb-5 max-w-[90ch]">Seven dimensions, each with a plain state and the specific reasons for it, read from the data. There is deliberately no overall score: one number would hide which part of the evidence is weak.</p>
            <DimensionGrid report={data.report} />
          </>) : <LoadingBlock height={400} /> },
        { value: "layers", label: "Evidence layers", content: data ? (
          <>
            <div className="grid gap-x-12 gap-y-6 lg:grid-cols-2">
              <LayerList layers={data.report.layers.filter((l) => ["observations", "derived", "inference"].includes(l.key))} />
              <LayerList layers={data.report.layers.filter((l) => ["corroboration", "limitations", "questions"].includes(l.key))} />
            </div>
            <Caption className="mt-6">Data files behind this assessment: {data.report.files.join(", ")}</Caption>
          </>) : <LoadingBlock height={400} /> },
        { value: "disagreement", label: "Source disagreement", content: <Disagreement /> },
        { value: "mt", label: "Multiple testing", content: <MultipleTesting /> },
      ]} />
      <div className="mt-10">
        <Button variant="primary" onClick={() => go("/brief")} iconRight={<Icon.ArrowRight size={16} />}>Export this investigation as an Evidence Brief</Button>
      </div>
    </div>
  );
}
