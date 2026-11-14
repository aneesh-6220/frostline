# FROSTLINE
## The Scientific Investigation Platform for a Changing North

**Product North Star · Engineering Mandate · Scientific Contract · Global-Award Submission Plan**

**Team:** Strongest Soldiers  
**Competition:** NASA Space Apps Challenge 2026 - Halifax  
**Challenge:** Be An Earth System Trend Detective!  
**Local judging:** November 15, 2026, 3:00 PM Atlantic  
**NASA submission:** November 15, 2026, 11:59 PM Atlantic

**Implementation owner:** Claude Fable 5.2, highest available extended coding effort appropriate for the task.

---

# I. THE MISSION

You are responsible for building **Frostline into an outstanding, functioning, scientifically rigorous Earth-system investigation platform**.

Work as the principal product engineer, scientific visualization architect, user-experience designer, integration engineer, and release engineer.

Your objective is to create one complete product with:

1. A compelling guided investigation for local judges.
2. A genuinely reusable research workflow for real users.
3. Meaningful integration of NASA Earth science data.
4. Correct and reproducible statistical analysis.
5. An innovative system for evaluating evidence quality.
6. Scientifically grounded connections to northern seasonal transportation.
7. A polished public application and complete NASA submission package.

**Do not build a disposable demo followed by another application. The demo must be a guided path through the actual finished product.**

Execute the implementation. Do not stop after writing a plan.

Build the most ambitious scientifically defensible product possible without compromising the working release, data integrity, or submission deadline.

The priority is not the number of features implemented. It is the amount of reliable, meaningful user value delivered.

---

# II. THE STRATEGIC VISION

## Frostline's core identity

**FROSTLINE**

*Trace the evidence behind changing winters.*

**Product statement:**

Frostline transforms NASA Earth-system data into accessible scientific investigations, helping people discover how northern environmental conditions are changing, assess the strength of the evidence, and explore relationships with documented seasonal transportation operations.

## The real problem

Environmental change is not difficult to discuss. It is difficult to investigate rigorously.

Someone interested in how winter conditions have changed near a northern community may need to:

- Discover relevant NASA climate datasets.
- Determine which environmental indicators are meaningful.
- Download and clean historical measurements.
- Understand temporal and spatial resolution.
- Calculate seasonal metrics.
- Fit trends and evaluate uncertainty.
- Compare different places fairly.
- Locate government transportation records.
- Align environmental and operational timescales.
- Determine what conclusions are and are not justified.
- Document and communicate the findings.

That is a fragmented and technically demanding workflow.

**Frostline compresses this workflow into a guided, reproducible investigation.**

## What users should obtain

A user should be able to answer:

**What environmental change can be detected here?**

**How much has the variable changed over time?**

**How statistically convincing is the trend?**

**Does the pattern differ somewhere else?**

**Do available transportation records show related changes?**

**How trustworthy are the underlying measurements?**

**What evidence is still missing?**

The final output is a source-backed, reproducible **Frostline Evidence Brief** that the user can understand, download, share, and investigate further.

## Product boundaries

Frostline is a scientific investigation and research-communication tool.

It is not:

- An ice-thickness measurement system.
- A real-time road safety monitor.
- A route recommendation service.
- A road-opening prediction engine.
- A validated operational decision-support system.
- Proof that climate change caused a particular road-opening trend.

Do not overclaim the product's capability to make it appear more commercially significant.

---

# III. SCIENTIFIC FOUNDATION AND REPOSITORY AUTHORITY

## Repository

Private GitHub repository:

https://github.com/aneesh-6220/nasa-space-apps-2026

Authoritative starting branch:

`fable-ready`

Expected base commit:

`17829f8447fb3b9bcb5c369800ca1ce9d5ddfafc`

Verify the actual remote commit and working tree.

Create a separate `frostline-implementation` branch. Preserve all other team activity.

## Read before editing

1. `docs/FABLE_52_START_HERE.md`
2. `docs/FABLE_HANDOFF_FINAL.md`
3. `docs/SCIENTIFIC_METHODS.md`
4. `docs/APP_IMPLEMENTATION_CONTRACT.md`
5. `docs/APP_DATA_SCHEMA.md`
6. `docs/APPROVED_FINDINGS.md`
7. `docs/RESULTS.md`
8. `docs/CHALLENGE_ELIGIBILITY.md`
9. `docs/DATA_SOURCES.md`
10. `docs/DATA_QUALITY.md`
11. `docs/GEOGRAPHIC_SCOPE.md`
12. `submission/SUBMISSION_DRAFT.md`

Also inspect every referenced application dataset, code module, processing script, and test.

The scientific specification and generated outputs are authoritative. This north star controls product design and execution, but does not authorize inventing or changing scientific findings.

## Existing foundation

The handoff reportedly includes:

- NASA POWER daily temperature records.
- MERRA-2 data provenance.
- Dettah and Aklavik study locations.
- NWT winter-road operating records.
- Environment Canada station observations.
- Seasonal environmental indicators.
- Historical road-operation trend estimates.
- Statistical uncertainty and multiple-testing corrections.
- A reproducible scientific pipeline.
- Twenty application data files under `UI/data_real/`.
- A reference scientific data layer.
- Ninety-five passing automated tests.

Verify the actual state instead of assuming every claim is correct.

Establish the baseline:

```bash
python3 -I -m unittest discover -s tests
python3 -I scripts/regenerate_all.py --check
```

Maintain a green scientific suite throughout the build.

Do not manually edit source observations, approved generated data, or authoritative numerical results.

---

# IV. THE COMPETITIVE OBJECTIVE

Design Frostline to excel against all five NASA judging criteria.

## 1. IMPACT - Solve a meaningful information problem

Demonstrate how Frostline reduces the barriers to understanding northern climate trends and their possible transportation implications.

Use the NWT operating records and published research as genuine evidence of real-world relevance.

The application should have a concrete user outcome: an evidence-backed investigation that previously required several specialized services and manual analysis steps.

Present realistic future uses in climate education, research, and preliminary adaptation studies.

Never fabricate stakeholder validation, deployment, savings, avoided disruptions, or operational adoption.

## 2. CREATIVITY - Create a novel investigation workflow

The innovation is not merely plotting temperature or computing Theil–Sen slopes.

It is the integration of:

- Human-centered scientific questions.
- Geographical exploration.
- Relevant environmental-variable discovery.
- Historical trend analysis.
- Comparison across regions.
- Transportation records.
- Evidence-quality diagnostics.
- Data-source disagreement.
- Research limitations.
- Exportable, reproducible findings.

Create a product experience that is more coherent than separately opening a NASA data portal, statistical notebook, mapping interface and government spreadsheet.

## 3. VALIDITY - Make the science trustworthy

Every numerical claim must trace to a real dataset and documented method.

Show scientific uncertainty where it matters.

Preserve statistical safeguards, correct temporal definitions, source provenance, independent validation and exploratory-analysis limitations.

No fake confidence, invented predictions or unsupported causal claims.

## 4. RELEVANCE - Directly solve NASA's selected challenge

The user must be able to select an Earth-system variable, select an approved geography, examine a meaningful historical time series, quantify its trend and assess statistical significance.

The application should also enable geographic comparisons and explanation of variable choice.

Winter-road outcomes are the real-world application, not the substitute for environmental investigation.

## 5. PRESENTATION - Make the project memorable

Judges must understand Frostline quickly and experience genuine interaction.

Design a polished guided journey that tells a coherent story without oversimplifying its evidence.

The interface must stand on its own when opened without a presenter.

### Potential global-award alignment

Aim to demonstrate qualities associated with:

- Best Use of Science.
- Best Use of Data.
- Best Use of Technology.
- Galactic Impact.
- Local Impact.
- Best Use of Storytelling.

These are historical award-category reference points, not a promise that the categories or selection process are unchanged in 2026.

Do not build separate features merely to target award labels.

---

# V. PRODUCT ARCHITECTURE: ONE CONNECTED INVESTIGATION

Frostline must feel like one product rather than disconnected pages.

Structure the experience around three levels:

## Level A - Guided Discovery

For newcomers and judges.

Begin with an understandable question, show the appropriate data, explain the results, and connect them to meaningful context.

## Level B - Research Explorer

For students and scientific users.

Allow approved location, variable, period, and regional-comparison choices with scientifically correct recomputation or corresponding verified results.

## Level C - Evidence Workspace

For users who need a reusable research output.

Show exact metadata, methodology, validation, assumptions, limitations, and exports.

All three levels must share the same real data and analysis engine.

Do not create a separate mockup for Guided Discovery.

---

# VI. COMPLETE FEATURE SPECIFICATION

## Feature 1 - Frostline Observatory

Create an exceptional home screen.

Hero:

**How is winter changing across Canada's North?**

Supporting text:

*Follow NASA Earth science data from measurement to discovery, and investigate what the evidence reveals about seasonal transportation.*

Primary action:

**Begin an Investigation**

Secondary action:

**Explore the Data**

Show a concise representation of Frostline's process:

**Location → Environmental Evidence → Trend → Comparison → Road History → Evidence Brief**

Use real data-derived summary indicators where available.

Never invent a large headline number solely for visual impact.

The first screen must work without login or configuration.

### Acceptance

A new user understands the basic purpose in 10 seconds and reaches a real graph within one interaction.

---

## Feature 2 - Interactive Northern Atlas

Build an interactive geographic explorer using verified coordinates.

Primary case studies:

- Dettah.
- Aklavik.

Additional preloaded locations may be exposed only after validation of their actual datasets and metadata.

Required capabilities:

- View northern Canadian study locations on a clear map.
- Select a location through a map marker or searchable selector.
- See geographic and transportation context.
- Display the underlying climate sampling point and source grid-cell information when available.
- Change every downstream chart and evidence panel when the location changes.
- Open the location's full investigation.

Preferred implementation: Streamlit with PyDeck or a dependable equivalent.

Do not require Google Maps credentials or cloud billing.

Map tiles are optional to the app's functionality; location selectors must continue working if tiles fail.

Only draw actual road geometries if sourced and verified. Never fabricate route lines or claim an atmospheric grid cell represents every road segment.

### Acceptance

A selected map point and every associated chart, metric, source and label always correspond to the same verified location.

---

## Feature 3 - Intelligent Question-to-Variable Discovery

NASA's challenge explicitly emphasizes helping users find variables that can reveal change.

Implement a transparent, scientifically controlled variable-discovery interface.

For example:

**What would you like to investigate?**

- Are early winters becoming warmer?
- Is freezing accumulation changing?
- Are midwinter thaw conditions changing?
- Do patterns differ between northern locations?
- How do environmental observations compare with road-opening records?

The selection should recommend appropriate scientifically supported metrics, with a brief explanation of why each metric is relevant.

Initially support:

- Mean seasonal two-metre air temperature.
- Early-season freezing degree-days.
- Midwinter above-freezing-day counts.
- Approved monthly MERRA-2 temperature trends, when a verified qualifying extraction exists.
- Additional variables only if actual data and validated methodology support them.

Do not make the suggestions using an unconstrained language model.

Prefer a transparent, deterministic recommendation system backed by a documented variable catalogue.

Each variable must have:
- Identifier.
- Units.
- Scientific definition.
- Data source.
- Spatial resolution.
- Temporal resolution.
- Valid period.
- Supported location list.
- Data-quality conditions.
- Available trend methods.
- Interpretation limitations.

### Acceptance

Every recommended metric is actually available and scientifically appropriate for the selected geography and question.

---

## Feature 4 - Advanced Trend Detective

This is the scientific center of Frostline.

For every approved environmental metric and location, display:

- Actual historical observations.
- Correctly labeled time-series chart.
- The selected historical period.
- Estimated direction of change.
- Magnitude per decade.
- Appropriate confidence interval.
- Supported significance assessment.
- Sample size.
- Data completeness.
- NASA source and product lineage.
- Plain-language scientific interpretation.

Use polished interactive Plotly charts with tooltips, correctly labeled units and clearly distinguished observation versus fitted trend.

Users should be able to inspect individual seasons and see the underlying recorded values.

### Trend integrity

Use the existing approved trend-analysis code.

Respect:

- Seasonal definitions.
- Missing-data exclusions.
- Treatment of ties.
- Autocorrelation limitations.
- Confidence-interval construction.
- Multiple-testing corrections.
- Retrospective selection bias.
- Statistical tests that may be undefined for some indicators.

When historical periods change, use the validated recomputation path or explicitly restrict inference to approved precomputed windows.

Do not display an old adjusted q-value for a new exploratory window.

Do not mistake an inconclusive trend for a finding of no change.

### Visual communication

Replace oversimplified binary "significant/not significant" storytelling with more informative states:

- Supported historical trend.
- Trend not statistically resolved.
- Exploratory comparison.
- Insufficient data.
- Inference unavailable.

Explain why the status applies.

### Acceptance

Each displayed statistical result is numerically traceable to the authoritative scientific pipeline, and uncertainty cannot be lost when changing the selected investigation.

---

## Feature 5 - Regional Trend Comparison

Allow scientifically meaningful environmental comparisons between approved locations.

Required:

- Same environmental indicator.
- Same units.
- Overlapping, matched historical years.
- Separate trend estimates.
- Confidence intervals.
- A clear explanation of the observed geographic differences.
- Formal difference-of-trends inference only when approved.

Provide both aligned time-series charts and a concise comparison summary.

Never infer that two slopes differ merely because one p-value is below 0.05 and the other is not.

If formal comparison inference is unavailable, describe the comparison as descriptive.

The UI must clearly distinguish differences in underlying geography, route type and sampling resolution.

### Acceptance

Every comparison uses common years and communicates accurately whether differences are established or merely observed.

---

## Feature 6 - Corridor Investigation

This is the main real-world utility layer.

For each supported corridor, create a unified case-study view combining:

1. Verified geographical context.
2. Road type and community connection.
3. Relevant environmental indicators.
4. Historical environmental trends.
5. Actual government road-opening and closing records.
6. Exploratory environmental/operational associations.
7. Source disagreements and limitations.
8. A coherent evidence conclusion.

### Dettah

The historical ice-road opening record has a reported later-opening trend, but the source selection was exploratory and the atmospheric evidence does not establish its cause.

Dettah has an alternative year-round road connection.

Do not portray the ice crossing as its only road access.

### Aklavik

Aklavik's seasonal ice-road situation provides an important distinct transportation context.

Confirm the exact approved road identity and geographic scope against repository documentation and authoritative sources.

Do not treat it as statistically interchangeable with Dettah.

### Important operational distinctions

- First opening to final closing is not automatically total usable days.
- Temporary closures may not be captured.
- Operational decisions may involve construction, ice surveys, maintenance, snowfall and other non-temperature influences.
- Local ice safety cannot be inferred from gridded air temperature.

### Acceptance

A user can complete a meaningful corridor-specific investigation without making unsupported causal or safety inferences.

---

## Feature 7 - Environmental and Operational Timeline

Create an optional synchronized timeline that shows historical environmental metrics and road-operation outcomes in parallel.

The purpose is to make temporal relationships understandable.

For example:

- Early-season freezing accumulation.
- Recorded opening dates.
- Seasonal temperature history.
- Recorded closing dates.

Use separate, clear axes and units.

Allow season selection and hover-based inspection.

Indicate the periods during which environmental information was actually available relative to the recorded road event.

Do not imply that a retrospective association is a predictive relationship.

Do not generate artificial alignment to make the data appear more correlated.

### Acceptance

Every timeline observation can be traced to its correct season, record, source and date convention.

---

## Feature 8 - Frostline Evidence Engine

This is the signature product feature and should receive exceptional design and engineering attention.

For each investigation, automatically assemble a structured evidence assessment.

The engine must distinguish:

**A. Observations**

What was actually measured or estimated by a dataset.

**B. Derived indicators**

What was calculated from those observations.

**C. Statistical inference**

Which trends or associations were estimated and with what uncertainty.

**D. External corroboration**

Whether independent measurements support or contradict the result.

**E. Limitations**

What the evidence cannot establish.

**F. Unanswered questions**

What additional evidence would strengthen the investigation.

### Evidence quality dimensions

Assess these separately and transparently:

- Temporal completeness.
- Source provenance.
- Spatial representativeness.
- Ground-observation agreement where available.
- Statistical precision.
- Whether the analysis is exploratory.
- Temporal alignment of environmental and operational variables.

Do not generate a simplistic "87% scientifically reliable" score or an arbitrary road-safety index.

Use clear evidence states with explicit, source-derived reasons.

### Example of useful scientific communication

"The historical road-opening record supports a later-opening trend. The available modeled atmospheric freezing metric does not establish a corresponding long-term change. Ground-station observations also disagree materially with the modeled absolute freezing accumulation. Additional local ice and operational records would help investigate the relationship."

This example illustrates the required restraint. Actual wording must reflect approved, calculated results.

### Acceptance

A user understands not only what the trend estimate is, but also whether the data are suitable for answering their original question.

---

## Feature 9 - Source Disagreement and Sensitivity Explorer

Frostline must not conceal the substantial existing NASA-versus-station temperature discrepancy.

Create a visual comparison that shows:

- NASA-derived values.
- Matched station observations where available.
- Historical overlap.
- Bias and error summaries.
- Differences in derived freezing accumulation.
- Applicable trend comparison.
- Important limitations of spatial and temporal correspondence.

Use approved validation datasets.

Distinguish a gridded reanalysis product from a station measurement.

Do not automatically bias-correct NASA data unless a validated correction method is explicitly approved.

If additional sensitivity analyses already exist in the repository, expose them through a carefully explained advanced panel.

Never imply that high year-to-year correlation proves accurate absolute values or trend equivalence.

### Acceptance

The scientific data-quality caveat is understandable and discoverable, while the main workflow remains readable.

---

## Feature 10 - Reproducible Frostline Evidence Brief

Every completed investigation should produce a professional, downloadable research artifact.

It should contain:

- Investigation title and question.
- Location and coordinates.
- Environmental variable and definition.
- Historical coverage.
- Data source and product version.
- Graph or data summary.
- Trend rate and uncertainty.
- Relevant significance assessment.
- Data-quality findings.
- Applicable road-operation evidence.
- Scientific interpretation.
- Known limitations.
- Unanswered questions.
- Source references.
- Analysis-method identifier.
- Date generated.
- Relevant dataset and code version identifiers.

Prefer a well-designed HTML report, with PDF export if reliable. Also offer underlying CSV download.

The report must be assembled deterministically from real analysis objects and approved interpretation templates.

Do not send raw observations to an unverified generative API to fabricate narrative conclusions.

Provide a reproducibility path back to the source records and methods.

### Acceptance

A new user can complete an investigation and leave with a coherent, accurately labeled evidence report that can be inspected independently of Frostline.

---

## Feature 11 - Guided Judge Demo

Build a fully integrated Guided Demo inside Frostline.

It uses the same production data and components as the research interface.

Structure it as a concise six-stage experience:

1. **The problem:** Why changing winter conditions matter.
2. **The geography:** Select a real northern case study.
3. **The NASA data:** Show a historical environmental variable.
4. **The scientific finding:** Explain trend and uncertainty.
5. **The transportation evidence:** Show actual operating records without claiming causation.
6. **The Evidence Brief:** Export the investigation and show transparency.

Make it visually polished, reliable and navigable in a short local presentation.

Include a graceful transition into full interactive exploration.

Do not require live data downloads, user accounts or external credentials during the demo.

Provide a demo script based exclusively on implemented features and verified results.

### Acceptance

A presenter can complete the guided workflow without encountering a broken page, missing chart or confusing statistical state.

---

## Feature 12 - Research Mode and Extensibility

The product should be designed to expand beyond two manually prepared cases.

Create a clean location-and-variable registry so additional datasets can be incorporated without rewriting the frontend.

If safely implementable, support an advanced research mode for additional locations with NASA POWER data acquisition.

Such a mode must include:

- Clearly separated experimental status.
- Explicit sampling coordinates.
- Data-source provenance.
- Validated units and missingness.
- Rate limiting and caching.
- Appropriate historical window requirements.
- No unsupported linkage to historical road records.
- No safety conclusions.
- Statistical outputs only after appropriate validation.

The primary demo must work entirely from committed, approved data.

Do not advertise unlimited arbitrary-location support unless it genuinely works and has been tested.

Additional regional atlas locations should only appear after their data have passed the scientific quality gates.

### Acceptance

The architecture can accommodate another verified northern location without requiring a new statistical implementation or a rewritten product interface.

---

# VII. NASA DATA ELIGIBILITY - A HARD RELEASE GATE

Official challenge resources provided by the team include NASA Giovanni, Hydrology Time Series and AppEEARS.

The existing NASA POWER datasets are legitimate NASA-derived climate data, but POWER is not explicitly named in the supplied Resources list.

The preferred eligibility resolution is a real NASA Giovanni extraction from MERRA-2.

Suggested collection:

`M2TMNXSLV`

Variable:

`T2M`

Temporal resolution:

Monthly.

Use the extracted temperature data meaningfully in Frostline's scientific investigation.

Possible application:

- Long-term monthly or seasonal temperature trends.
- Regional MERRA-2 climate comparison.
- Independent access-route cross-check of temperature statistics, with correct recognition that POWER and Giovanni may share MERRA-2 inputs.

Never call these two extractions independent environmental observations when their underlying source is shared.

Never derive daily FDD totals or daily thaw counts from monthly temperature means.

Implement and test the repository's strict Giovanni ingestion adapter.

If Cason provides an authentic extraction, validate and integrate it.

If it is not yet available, complete all other implementation work and report the eligibility blocker to the captain.

Do not manufacture files or imply a source has been integrated when it has not.

Before release, the team must verify and document meaningful use of an eligible NASA resource.

---

# VIII. DATA AND STATISTICAL NON-NEGOTIABLES

The following constraints apply to every feature.

## 1. Scientific measurements

Keep observed, modeled and derived values distinct.

Use appropriate units and exact source metadata.

Do not represent NASA grid-cell means as direct measurements on a road surface.

## 2. Statistical analysis

Preserve approved estimators, confidence intervals, significance methods and multiple-testing safeguards.

No uncontrolled hypothesis searches disguised as confirmatory discoveries.

## 3. Exploratory period selection

Changing the window changes the statistical question.

Use validated recomputation or display descriptive results with appropriate caveats.

Do not reuse fixed-family adjusted q-values in incompatible new analyses.

## 4. Comparison validity

Match years and scientific definitions.

Only claim statistically established geographic differences when a proper comparison test supports them.

## 5. Causality

Correlation, regression and coincident trends do not establish causation.

Do not make specific operational predictions using variables measured after the outcome occurred.

## 6. Model limitations

Disclose the substantial NASA temperature bias relative to the available station reference.

The cause of that discrepancy is unresolved.

## 7. Data reliability

No missing measurements treated as zero.

No fabricated interpolation.

No synthetic production values.

No unsupported geographic routes or heatmaps.

No use of the obsolete James Bay freezing threshold as a general NWT benchmark.

## 8. Human review

The scientific pipeline's test suite and AI-generated research do not substitute for Yao's independent review of public claims.

Do not mark statistical conclusions as human-approved unless the approval actually occurred.

---

# IX. DESIGN AND TECHNICAL EXECUTION

## Preferred engineering stack

Build from the existing repository.

Prefer:

- Python.
- Streamlit.
- Plotly.
- pandas, NumPy, SciPy.
- Existing validated statistical modules.
- PyDeck for map interaction.
- Existing unittest infrastructure.
- Streamlit AppTest and browser testing where supported.

Do not rewrite the entire application in a different framework without a concrete, verified benefit.

## Architecture principles

- Immutable source data.
- Reproducible scientific processing.
- Versioned derived data.
- Typed or validated application data contracts.
- Separate presentation components.
- Deterministic scientific interpretation.
- No required live NASA API call for the default investigation.
- Minimal external dependencies.
- Fast startup.
- Reliable caching.
- Graceful handling of optional-resource failures.

## Product UX

Use a sophisticated northern-observatory visual identity.

Suggested palette:

- Deep navy and slate.
- Glacier cyan.
- Cool neutrals.
- Restrained amber for caveats.

Scientific graphs must remain more visually prominent than decorative material.

Use accessible color choices, meaningful typography, responsive layout and clear interactive affordances.

Avoid excessive animation or styling that reduces speed or clarity.

## Naming

Public product:

**Frostline**

Team:

**Strongest Soldiers**

Replace outdated public-facing NorthLink and Asterfen branding without breaking internal data paths or provenance.

## Security and accessibility

- No hardcoded credentials.
- No exposure of Earthdata authentication tokens.
- No accounts required for public access.
- No sensitive or identifying user records.
- Readable charts and accessible controls.
- Clear external-resource attribution.
- Safe link handling and input validation.
- Rate limiting for any optional live data acquisition.

---

# X. IMPLEMENTATION STRATEGY

Build one final application through internal checkpoints.

## Checkpoint 1 - Establish the baseline

Verify the actual repository state, inputs, scientific methods and tests.

Inspect the legacy UI and identify all synthetic or obsolete paths.

## Checkpoint 2 - Complete the scientific core

Connect real data to the primary climate investigation.

Ensure the main metric selection, charts, trends, uncertainty and evidence outputs work.

## Checkpoint 3 - Complete the core research workflow

Implement the Northern Atlas, variable discovery, regional comparison and corridor investigation.

## Checkpoint 4 - Deliver the distinctive features

Implement the Evidence Engine, source-disagreement view, evidence export and guided judge demo.

## Checkpoint 5 - Expand where justified

Integrate authenticated Giovanni data and any additional scientifically approved locations or variables.

Only build advanced exploratory acquisition after the core product is stable.

## Checkpoint 6 - Product polish and full verification

Test actual interactions, scientific accuracy, visual coherence, responsiveness and error handling.

## Checkpoint 7 - Public release and submission

Deploy, verify public access, create fallback materials and assemble final submission assets.

Throughout execution:

- Keep the app runnable.
- Commit stable milestones.
- Repair failures rather than stopping.
- Report genuine external blockers promptly.
- Avoid overlapping teammate file ownership.
- Do not stop at a plan, screenshots or an untested mockup.

---

# XI. RELEASE ACCEPTANCE TESTS

A release is not complete until the following have been demonstrated.

## Science

- All existing scientific regression tests pass.
- Data regeneration is deterministic.
- Numerical outputs match approved results.
- Missingness and invalid states are handled correctly.
- Statistical and source caveats appear where needed.
- No fabricated scientific values are displayed.

## Functionality

- Guided investigation works from beginning to end.
- Location selection updates all relevant content.
- Environmental-variable selection works.
- Trend charts display verified observations.
- Historical-period changes preserve inference correctness.
- Geographic comparisons use matching periods.
- Road operations are correctly aligned.
- Evidence Audit displays real metadata.
- Evidence Brief exports accurate numbers and references.
- No synthetic or obsolete production charts appear.

## User experience

- App is understandable without a presenter.
- Default investigation loads quickly.
- Charts are readable.
- Navigation is intuitive.
- Mobile and laptop layouts are usable.
- A failed map tile request cannot disable the data explorer.
- Error messages are informative.
- No dead controls or placeholder buttons.

## Testing

- Existing 95-test scientific baseline preserved or improved.
- Remaining contract acceptance tests implemented.
- App-level integration tests added.
- Actual running application smoke-tested.
- Guided-demo flow exercised.
- Generated evidence exports checked against source values.
- Headless/browser testing performed where available.
- Failures documented honestly.

## Deployment

- Public application URL works without login.
- Important external links work.
- App does not depend on live NASA API availability.
- Private source repository remains protected unless captain authorizes publication.
- Public source or project artifact complies with NASA requirements.
- Demo fallback is prepared.
- Submission links verified in a private browsing window.

---

# XII. THE COMPLETE NASA SUBMISSION PACKAGE

Produce the materials needed to explain and evaluate Frostline independently.

## Project description

A concise problem, solution, novelty, technical method, impact and limitations statement.

## Technical documentation

System architecture, data sources, variable catalogue, scientific methodology and reproducibility.

## Demonstration

Prepare material suitable for either a video of no more than 30 seconds or a presentation of no more than seven slides, subject to the final official 2026 submission guide.

Use only genuine working screens and approved findings.

## Local judging

Prepare a short interactive presentation:

- What is the problem?
- Why does the problem matter?
- Why NASA Earth science data?
- What does Frostline do?
- What can judges actually try?
- What did the evidence show?
- What remains uncertain?
- Why is this useful?

Include a fallback recording or screenshots.

## References

Cite every incorporated NASA dataset, external data source, scientific paper, software library and third-party asset as required.

## AI-use disclosure

Document actual AI-assisted implementation, research, code generation, writing and media creation.

Do not falsely claim that all work was performed manually.

## Safety and intellectual property

Avoid misleading NASA endorsement and unauthorized NASA branding.

Do not expose secrets.

Obtain appropriate rights and permissions for any external imagery, music or other content.

Follow the applicable rules for any submitted identifiable minors.

## Submission timing

Local presentation takes place on November 15 at 3 PM Atlantic.

The NASA project page must be submitted by November 15 at 11:59 PM local time.

Do not rely on post-deadline improvements to qualify the submitted project.

---

# XIII. TEAM OWNERSHIP

**Shaurya + Fable**

Own the complete application implementation, integration tests, deployment engineering and software handoff.

**Cason**

Owns qualifying NASA resource acquisition, dataset provenance and remaining road-record validation.

**Yao**

Owns independent scientific interpretation review and sign-off.

**Louie**

Owns UI feedback, end-to-end user testing and presentation support.

**Ethan**

Owns human-impact research, source-backed storytelling, slides and submission narrative.

**Captain**

Owns scope decisions, branch integration, deployment access, release approval and NASA submission completion.

Do not overwrite work owned by other agents or teammates.

---

# XIV. REQUIRED FINAL ENGINEERING REPORT

After implementation, deliver:

1. Exact branch and commit SHA.
2. Complete implemented-feature inventory.
3. Working public app URL, if deployed.
4. Scientific test results.
5. Application integration-test results.
6. Known defects and blocked features.
7. NASA eligibility status.
8. Scientific review status.
9. Verified screenshots or demo material.
10. Setup and reproduction commands.
11. Submission material locations.
12. Exact remaining human actions.

Distinguish completed, tested, partially implemented and unavailable functionality.

Do not claim deployment or validation without evidence.

---

# XV. THE ULTIMATE DEFINITION OF DONE

A new user can open Frostline and:

1. Select a real northern location.
2. Choose a relevant NASA Earth-system variable.
3. View genuine historical measurements.
4. Understand how that variable changed and how uncertain the trend is.
5. Compare conditions across documented regions.
6. Explore appropriate real transportation evidence.
7. Identify limitations and unresolved explanations.
8. Export a complete, source-backed Evidence Brief.
9. Reproduce the scientific result.
10. Leave with a clearer, scientifically defensible understanding of a meaningful environmental question.

A local judge can experience this in a polished guided demonstration.

A global evaluator can inspect the data, methods, application, limitations and citations without depending on the presentation.

**The final result must be a useful scientific product, not an elaborate prototype that only looks convincing.**

Build Frostline to this standard.

Begin by inspecting the repository and executing the established scientific tests, then implement the complete application and verify it end to end.

---

# XVI. AUTHORITATIVE RESEARCH AND DATA REFERENCES

**NASA challenge**  
https://www.spaceappschallenge.org/2026/challenges/earth-system-trend-detective/

**NASA Space Apps 2026**  
https://www.spaceappschallenge.org/2026/

**Official challenge resources supplied by the team**  
https://giovanni.gsfc.nasa.gov/  
https://appeears.earthdatacloud.nasa.gov/

**NASA POWER daily API**  
https://power.larc.nasa.gov/docs/services/api/temporal/daily/

**NASA POWER meteorological provenance**  
https://power.larc.nasa.gov/docs/methodology/data/sources_meteorology/

**NASA MERRA-2 monthly collection**  
https://data.nasa.gov/dataset/merra-2-tavgm-2d-slv-nx-2dmonthly-meantime-averagedsingle-levelassimilationsingle-level-di-892ac

**NWT government road operating dates**  
https://www.statsnwt.ca/en/node/1073

**NWT road infrastructure and route definitions**  
https://www.inf.gov.nt.ca/en/transportation

**Existing winter-road climate research**  
https://climatedata.ca/winter-ice-roads-in-northern-ontario/

**NASA Space Apps legal requirements**  
https://www.spaceappschallenge.org/legal/

**NASA project submission and resource information**  
https://www.spaceappschallenge.org/resources/