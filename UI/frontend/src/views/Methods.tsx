import { Icon } from "../components/icons";
import { Bullets, Callout, Caption, DataTable, Disclosure, ErrorState, KV, LoadingBlock, PageHeader, Section, Tabs } from "../components/ui";
import { useMethods } from "../lib/api";
import { useInv } from "../lib/investigation";

export default function Methods() {
  const { boot } = useInv();
  const { data, error } = useMethods();
  return (
    <div>
      <PageHeader eyebrow="Methods and sources" title="How Frostline works, and what it rests on"
        lede="Everything needed to inspect the investigation without a presenter: methods, data provenance, citations, the status of open requirements and the limits of the work." />
      {error ? <ErrorState error={error} /> : !data ? <LoadingBlock height={420} /> : (
        <Tabs idPrefix="methods" tabs={[
          { value: "methods", label: "Methods", content: (
            <>
              <div className="card p-5 sm:p-6"><KV rows={data.method_rows} keyWidth="28%" /></div>
              <Caption>Authoritative specification: docs/SCIENTIFIC_METHODS.md. Implementation: the metrics, statistics and recompute modules in the repository's scripts folder. The application contains no statistical method of its own.</Caption>
              <div className="mt-6"><Disclosure title="Variable catalogue"><DataTable table={data.catalogue} maxHeight={380} caption="Variable catalogue" /></Disclosure></div>
            </>) },
          { value: "data", label: "Data and citations", content: (
            <>
              <div className="card p-5 sm:p-6"><KV rows={data.data_rows} keyWidth="24%" /></div>
              <div className="mt-6 grid gap-4 md:grid-cols-2">
                {data.sources.map((s) => (
                  <div key={s.id} className="card flex flex-col p-5 sm:p-6">
                    <h3 className="text-[15.5px] font-semibold">{s.name}</h3>
                    <div className="mt-0.5 text-[12.5px] text-ink-3">{s.kind} · {s.resolution}</div>
                    <p className="mt-3 text-[13.5px] leading-[1.6] text-ink-body">{s.citation}</p>
                    {s.note && <p className="mt-2 text-[13px] leading-[1.6] text-ink-2">{s.note}</p>}
                    <a href={s.url} target="_blank" rel="noopener noreferrer" className="mt-auto inline-flex items-center gap-1.5 pt-4 text-[13px] font-medium break-all text-brand hover:text-brand-hover">
                      {s.url}<Icon.External size={14} className="shrink-0" />
                    </a>
                  </div>
                ))}
              </div>
              <Callout className="mt-6" label="POWER acknowledgement">{data.power_ack}</Callout>
              <div className="mt-6 flex flex-col gap-3">
                <Disclosure title="Context literature">
                  <Bullets items={data.literature} />
                  <Caption>Used for context and for what Frostline does not claim. Frostline does not replicate these studies and does not apply the James Bay freezing threshold reported in them.</Caption>
                </Disclosure>
                <Disclosure title="Software"><p className="text-[13.5px] leading-[1.6] text-ink-2">{data.software.join(", ")}.</p></Disclosure>
                <Disclosure title="File hashes (sha256)"><DataTable table={data.file_hashes} maxHeight={360} caption="File hashes" /></Disclosure>
              </div>
            </>) },
          { value: "nasa", label: "NASA resource status", content: (
            <>
              <h2 className="mb-4 text-[17px] font-semibold">NASA data use and the listed-resource requirement</h2>
              {data.giovanni ? (
                <>
                  <h3 className="mb-3 text-[15px] font-semibold">MERRA-2 monthly temperature through NASA Giovanni</h3>
                  <p className="prose-frost mb-4 max-w-[90ch]">Monthly mean 2 m air temperature (collection M2TMNXSLV, variable T2M) extracted through Giovanni for the same grid cells. POWER and Giovanni share the MERRA-2 source, so this is a consistency check on access routes, not an independent observation. Monthly means are used for seasonal mean-temperature trends only, never for freezing degree-days or thaw counts.</p>
                  <DataTable table={data.giovanni.trends} caption="Giovanni trends" />
                  <DataTable className="mt-4" table={data.giovanni.check} caption="Giovanni against POWER" />
                  <Callout kind="caveat" label="Reanalysis caveat" className="mt-4">{boot.bias_caveat}</Callout>
                  <Callout className="mt-4">A Giovanni extraction is present in the app data and is shown above. Whether it satisfies the Global Award resource requirement is for the team and organizers to confirm.</Callout>
                </>
              ) : (
                <>
                  <Callout kind="caveat" label="Status: not demonstrated">
                    Frostline's NASA data come from NASA POWER, whose meteorology is the MERRA-2 reanalysis. POWER is not on the challenge's listed Resources (NASA Giovanni and AppEEARS are).
                    A cross-extraction of MERRA-2 monthly temperature through Giovanni is prepared and has not been obtained. Meaningful use of a listed NASA resource is therefore not demonstrated in this release.
                  </Callout>
                  <div className="card mt-4 p-5 sm:p-6"><KV rows={data.giovanni_rows} keyWidth="28%" /></div>
                </>
              )}
              <Caption>Details and the manual extraction steps: docs/CHALLENGE_ELIGIBILITY.md.</Caption>
            </>) },
          { value: "ai", label: "AI-use disclosure", content: (
            <>
              <h2 className="mb-4 text-[17px] font-semibold">How AI was used</h2>
              <div className="card p-5 sm:p-6">
                <Bullets items={[
                  "The data pipeline, the statistical scripts, the documentation and this application were written with substantial AI assistance (Claude by Anthropic, including Claude Code), directed and reviewed by the team.",
                  "AI output is not treated as evidence. Every number on screen is produced by scripts from public data and checked by automated tests; none is written by a language model.",
                  "Interpretation sentences are fixed templates selected by the computed statistical status. No generative model runs inside the app, and no observation is sent to one.",
                  "No AI-generated imagery is used anywhere in the product.",
                  "The methods have not been signed off by an independent statistician. Until that happens, all results are labelled exploratory.",
                ]} />
              </div>
            </>) },
          { value: "limits", label: "Limits and review", content: (
            <>
              <h2 className="mb-4 text-[17px] font-semibold">What Frostline does not do</h2>
              <div className="card p-5 sm:p-6">
                <Bullets items={[
                  "It does not measure ice thickness, assess road safety, recommend routes or predict opening dates.",
                  "It does not show what produced any change in road dates. Associations are labelled as associations.",
                  "It does not present NASA grid-cell values as local observations, and it applies no bias correction.",
                  "It does not offer an arbitrary custom location: no data exist for one."]} />
              </div>
              <Section title="Known limitations">
                <div className="card p-5 sm:p-6">
                  <Bullets items={[
                    "24 winters of NASA data and 32 winters of road records are short records; natural variability can resemble a trend.",
                    "One reanalysis grid cell is not the whole road, and the cold-season bias against the station has no established cause.",
                    "The Aklavik alignment, segment and grid-cell representativeness are unverified.",
                    "Four road-record rows fail date checks and are excluded, not corrected. Temporary closures are not recorded.",
                    "The NASA record was not extended before winter 2001/02. Results are reproducible from cached sources; a live re-download was not compared.",
                    "Dettah was selected after its trend had been seen; no hypothesis was registered in advance."]} />
                </div>
              </Section>
              <Section title="Review status"><div className="card p-5 sm:p-6"><KV rows={data.review_rows} keyWidth="32%" /></div></Section>
            </>) },
          { value: "extend", label: "Extending Frostline", content: (
            <>
              <h2 className="mb-3 text-[17px] font-semibold">Research architecture</h2>
              <p className="prose-frost mb-5 max-w-[90ch]">Locations, variables and questions are entries in registries; findings and evidence reports are typed objects. A new verified location or variable is added through the data pipeline and a registry entry, and then every view, the Evidence Engine and the Evidence Brief work for it without new statistical code.</p>
              <DataTable table={data.locations_table} caption="Locations" />
              <div className="card mt-6 p-5 sm:p-6"><KV rows={data.extend_rows} keyWidth="28%" /></div>
              <Caption><span className="font-mono">{data.version_line}</span></Caption>
            </>) },
        ]} />
      )}
    </div>
  );
}
