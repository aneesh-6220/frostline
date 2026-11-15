import { ChartCard, FindingCard } from "../components/domain";
import { Plot } from "../components/Plot";
import { Icon } from "../components/icons";
import { Button, Callout, Caption, DataTable, ErrorState, Fetching, KV, LoadingBlock, PageHeader, Section, Tabs } from "../components/ui";
import { useInvestigation } from "../lib/api";
import { period, useInv } from "../lib/investigation";

export default function Detective() {
  const { boot, sel, question, go } = useInv();
  const { data, error, isFetching } = useInvestigation(sel);
  const loc = boot.locations[sel.loc];
  const v = boot.variables[sel.var];
  const q = question ? boot.questions[question] : null;

  return (
    <div>
      <PageHeader eyebrow={"Trend Detective" + (q ? ` · ${q.text}` : "")} title={v.label} lede={`${loc.name}. ${v.definition}`} />
      {error ? <ErrorState error={error} /> : !data ? (
        <div className="grid gap-6 lg:grid-cols-[1.7fr_1fr]"><LoadingBlock height={520} /><LoadingBlock height={420} /></div>
      ) : (
        <>
          <div className="grid items-start gap-6 lg:grid-cols-[minmax(0,1.7fr)_minmax(0,1fr)]">
            <div className="flex min-w-0 flex-col gap-4">
              <div className="relative">
                <Fetching active={isFetching} />
                <ChartCard kicker={`${loc.short} · winters ${period(sel.first, sel.last)}`} title={`${v.short} (${v.unit})`} figure={data.chart}
                  label={`${v.short} at ${loc.short}, one point per winter, with the Theil-Sen trend`} caption={data.chart_caption} />
              </div>
              <Callout kind="brand" label="In plain language">{data.plain}</Callout>
            </div>
            <FindingCard f={data.finding} />
          </div>

          {data.exploratory_caveat && (
            <Callout kind="caveat" label="Exploratory window" className="mt-6">
              You selected your own period, which changes the statistical question. The p-value shown is exploratory and not adjusted for multiple testing, and no adjusted q is
              reported. Use the approved-window buttons in the period control to return to an approved fixed window.
            </Callout>
          )}
          {data.thaw_note && <Callout className="mt-4">{data.thaw_note}</Callout>}

          <Tabs className="mt-12" idPrefix="detective" tabs={[
            { value: "winters", label: "Inspect the winters", content: (
              <>
                <DataTable table={data.season_table} maxHeight={360} caption="Per-winter values" />
                <Caption>An empty value means no usable record for that winter. Missing values are never replaced with zero or interpolated.</Caption>
              </>) },
            { value: "why", label: "Why this variable", content: <div className="card p-5 sm:p-6"><KV rows={data.why_rows} keyWidth="28%" /></div> },
            { value: "robust", label: "Robustness", content: (
              data.robustness.kind === "table" ? (<><DataTable table={data.robustness.table} caption="Robustness variants" /><Caption>{data.robustness.caption}</Caption></>)
                : data.robustness.kind === "forest" ? (<><p className="prose-frost mb-4 max-w-[80ch]">{data.robustness.caption}</p><div className="card p-4 sm:p-5"><Plot figure={data.robustness.chart} label="Slope at all nine corridors with 95% intervals" /></div></>)
                  : <Callout>{data.robustness.caption}</Callout>) },
            { value: "method", label: "Method and provenance", content: <div className="card p-5 sm:p-6"><KV rows={data.method_rows} keyWidth="28%" /></div> },
          ]} />

          <Section title="Continue the investigation">
            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
              <Button onClick={() => go("/compare")} iconRight={<Icon.ArrowRight size={16} />}>Compare with another region</Button>
              <Button onClick={() => go("/corridor")} iconRight={<Icon.ArrowRight size={16} />}>Investigate the corridor</Button>
              <Button onClick={() => go("/evidence")} iconRight={<Icon.ArrowRight size={16} />}>Audit the evidence</Button>
              <Button variant="primary" onClick={() => go("/brief")} iconRight={<Icon.ArrowRight size={16} />}>Export the Evidence Brief</Button>
            </div>
          </Section>
        </>
      )}
    </div>
  );
}
