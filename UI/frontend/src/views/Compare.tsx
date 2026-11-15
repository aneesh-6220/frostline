import { ChartCard, FindingCard, ResultPanel } from "../components/domain";
import { Plot } from "../components/Plot";
import { Callout, Caption, DataTable, ErrorState, Fetching, KV, LoadingBlock, PageHeader, Section, Select, Tabs } from "../components/ui";
import { useCompare } from "../lib/api";
import { useInv } from "../lib/investigation";

export default function Compare() {
  const { boot, sel, set } = useInv();
  const { data, error, isFetching } = useCompare(sel.var, sel.first, sel.last);
  const env = Object.values(boot.variables).filter((v) => v.kind === "environmental" && v.tier === "core" && v.id !== "thaw_days_janmar");

  return (
    <div>
      <PageHeader eyebrow="Regional comparison" title="Does the pattern differ somewhere else?"
        lede="The same NASA variable at Dettah and Aklavik, on the winters present in both series. Slopes are said to differ only when a test on the difference supports it." />
      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-end">
        <Select label="Environmental variable" className="sm:w-[340px]" value={data?.variable ?? (env.some((v) => v.id === sel.var) ? sel.var : "fdd_octdec")}
          onChange={(v) => set({ variable: v })} options={env.map((v) => ({ value: v.id, label: v.label }))} />
        {data && (
          <div className="flex flex-col pb-1">
            <span className="text-[12px] font-medium text-ink-3">Matched winters</span>
            <span className="tnum text-[15px] font-semibold text-ink">{data.period}</span>
            <span className="text-[12px] text-ink-3">set the period in the investigation bar</span>
          </div>
        )}
      </div>
      {error ? <ErrorState error={error} /> : !data ? <LoadingBlock height={480} /> : (
        <>
          {data.substituted && <Callout className="mb-6">{data.substitute_note}</Callout>}
          <div className="grid items-start gap-6 lg:grid-cols-[minmax(0,1.6fr)_minmax(0,1fr)]">
            <div className="relative min-w-0">
              <Fetching active={isFetching} />
              <ChartCard figure={data.chart} label="Both locations on matched winters with their own Theil-Sen estimates" caption={data.chart_caption} />
            </div>
            <div className="flex flex-col gap-4">
              <ResultPanel label={data.diff.label} value={data.diff.value} unit={data.diff.unit} meta={data.diff.meta} paragraphs={[data.diff.sentence]} source={data.diff.source} tone={data.diff.tone} />
              <Callout>One location reaching a small p-value while the other does not would not show that their slopes differ. The valid question is whether the difference series has a trend.</Callout>
            </div>
          </div>

          <Section title="Each location on its own">
            <div className="grid items-start gap-6 md:grid-cols-2">
              <FindingCard f={data.a} showTable={false} />
              <FindingCard f={data.b} showTable={false} />
            </div>
            <DataTable className="mt-6" table={data.table} caption="Per-location results" />
            <Caption>{data.table_caption}</Caption>
          </Section>

          <Tabs className="mt-12" idPrefix="compare" tabs={[
            { value: "diff", label: "Difference series", content: (
              <><div className="card p-4 sm:p-5"><Plot figure={data.diff_chart} label="Difference series, first location minus second" /></div>
                <Caption>Each point is one winter's value at the first location minus the second. A trend in this series is what would indicate diverging conditions.</Caption></>) },
            { value: "nine", label: "All nine corridors", content: (
              <><p className="prose-frost mb-4 max-w-[86ch]">Descriptive panel: the same variable at all nine corridors with NASA data, winters 2001/02 to 2024/25, with q across the 126-test family. Filled markers would indicate q below 0.05. No pooled test across corridors is made: they share weather, so pooling would overstate the evidence.</p>
                <div className="card p-4 sm:p-5"><Plot figure={data.forest_chart} label="Slope at all nine corridors with 95% intervals" /></div></>) },
            { value: "settings", label: "How the settings differ", content: (
              <>
                <div className="grid gap-6 md:grid-cols-2">
                  {data.settings.map((s) => (
                    <div key={s.name} className="card p-5 sm:p-6"><h3 className="mb-4 text-[17px] font-semibold">{s.name}</h3><KV rows={s.rows} keyWidth="32%" /></div>
                  ))}
                </div>
                <Callout kind="caveat" label="Different settings" className="mt-4">
                  This compares the climate series of two NASA grid cells about 1,100 km apart. The two roads are different objects (a 6.5 km lake crossing and a delta road of more
                  than 100 km), so it is a contrast between settings, not a repeat of one experiment, and it says nothing about road dates.
                </Callout>
              </>) },
          ]} />
        </>
      )}
    </div>
  );
}
