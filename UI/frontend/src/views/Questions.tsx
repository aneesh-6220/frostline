import clsx from "clsx";
import { motion } from "motion/react";
import { useState } from "react";
import { Icon } from "../components/icons";
import { Badge, Button, Callout, Caption, DataTable, Disclosure, ErrorState, LoadingBlock, PageHeader, Section, Segmented } from "../components/ui";
import { useMethods, useQuestion } from "../lib/api";
import { useInv } from "../lib/investigation";

const VIEW_PATH: Record<string, string> = { detective: "/trends", compare: "/compare", corridor: "/corridor" };

function Catalogue() {
  const { data } = useMethods();
  return data ? <DataTable table={data.catalogue} maxHeight={420} caption="Variable catalogue" /> : <LoadingBlock height={300} />;
}

export default function Questions() {
  const { boot, sel, question, go } = useInv();
  const qids = Object.keys(boot.questions);
  const [qid, setQid] = useState(question && qids.includes(question) ? question : qids[0]);
  const [locId, setLocId] = useState(sel.loc);
  const { data, error } = useQuestion(qid, locId);

  return (
    <div>
      <PageHeader eyebrow="Guided discovery" title="What would you like to investigate?"
        lede="Choose a question. Frostline recommends variables that are actually available for your location and says why each one fits. The mapping is a fixed, documented catalogue, not a language model." />
      <div className="grid items-start gap-6 lg:grid-cols-[minmax(0,1.6fr)_minmax(0,1fr)]">
        <div className="card divide-y divide-line overflow-hidden" role="radiogroup" aria-label="Question">
          {qids.map((id) => {
            const on = id === qid;
            return (
              <button key={id} role="radio" aria-checked={on} onClick={() => setQid(id)}
                className={clsx("relative flex w-full items-center gap-4 px-5 py-4 text-left transition-colors", on ? "bg-brand-soft" : "hover:bg-subtle")}>
                {on && <motion.span layoutId="q-active" className="absolute inset-y-0 left-0 w-[3px] bg-brand" />}
                <span className={clsx("grid size-5 shrink-0 place-items-center rounded-full border-2 transition-colors", on ? "border-brand" : "border-line-strong")}>
                  {on && <span className="size-2 rounded-full bg-brand" />}
                </span>
                <span className={clsx("text-[15px] leading-[1.45]", on ? "font-medium text-ink" : "text-ink-2")}>{boot.questions[id].text}</span>
              </button>
            );
          })}
        </div>
        <div className="flex flex-col gap-2">
          <span className="text-[12px] font-medium text-ink-3">Location</span>
          <Segmented label="Location" value={locId} onChange={setLocId} options={boot.primary.map((id) => ({ value: id, label: boot.locations[id].short }))} />
          <p className="mt-2 text-[13px] leading-[1.6] text-ink-3">Recommendations follow the variables available at this location. Choosing one opens the next view with the question, location and variable selected.</p>
        </div>
      </div>

      <Section title={`Recommended for: ${boot.questions[qid].text}`}>
        {error ? <ErrorState error={error} /> : !data ? <LoadingBlock height={260} /> : (
          <>
            <p className="prose-frost mb-5 max-w-[80ch]">{data.blurb}</p>
            <div className={clsx("grid gap-4", data.recommendations.length >= 3 ? "md:grid-cols-3" : "md:grid-cols-2")}>
              {data.recommendations.map((r, i) => (
                <motion.div key={`${qid}-${r.variable}`} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3, delay: i * 0.05 }}
                  className="card flex flex-col p-5 sm:p-6">
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-[12px] font-medium text-ink-3">{r.kicker}</span>
                    <Badge tone={r.tone}>{r.state_label}</Badge>
                  </div>
                  <h3 className="mt-3 text-[16.5px] font-semibold tracking-[-0.015em]">{r.label}</h3>
                  <p className="mt-2 text-[14px] leading-[1.6] text-ink">{r.fit}</p>
                  <p className="mt-2 text-[13.5px] leading-[1.6] text-ink-2">{r.why}</p>
                  <div className="mt-auto pt-4 text-[12px] leading-[1.55] text-ink-3">{r.source}</div>
                  <Button variant={i === 0 ? "primary" : "secondary"} className="mt-4 w-full" iconRight={<Icon.ArrowRight size={16} />}
                    onClick={() => go(VIEW_PATH[data.next_view] ?? "/trends", { loc: locId, variable: r.variable, question: qid })}>
                    Investigate {r.phrase}
                  </Button>
                </motion.div>
              ))}
            </div>
            <Caption>{data.footnote}</Caption>
            {data.thaw_note && <Callout className="mt-4">{data.thaw_note}</Callout>}
          </>
        )}
      </Section>

      <div className="mt-10">
        <Disclosure title="Variable catalogue: every variable Frostline can analyse">
          <Catalogue />
          <Caption>Only variables with real data and a documented method are offered. Not offered and never to be added: ice thickness, safety or usability scores, any prediction, any threshold test, and freezing degree-days from monthly means.</Caption>
        </Disclosure>
      </div>
    </div>
  );
}
