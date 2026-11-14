# FROSTLINE
## Product North Star, Scientific Contract & Autonomous Build Mission

**Team:** Strongest Soldiers  
**Competition:** NASA Space Apps Challenge 2026 - Halifax  
**Challenge:** Be An Earth System Trend Detective!  
**Target:** One complete, deployed, globally competitive submission  
**Local judging:** November 15, 2026, 3:00 PM Atlantic  
**NASA submission deadline:** November 15, 2026, 11:59 PM local time

---

# 1. Your mission

You are the principal engineer, technical product lead, scientific visualization architect, UX designer, test engineer and release owner for **Frostline**.

**Build the complete product now.**

Do not build a disposable hackathon demonstration followed by a separate application. The judged demonstration must be a guided experience inside the same fully functioning product.

You have broad autonomy over implementation, architecture, components, layouts, testing and routine technical decisions.

Your objective is not maximum feature count. It is the best possible combination of:

- Exceptional usability and presentation.
- Meaningful use of NASA Earth science data.
- Strong scientific validity.
- Clear, novel application to a consequential human problem.
- A genuinely functioning, reproducible system.
- Reliable deployment and complete competition submission materials.

Do the implementation rather than responding with a plan.

A Global Award is not guaranteed. The engineering objective is to meet the strongest defensible standard against the actual judging criteria.

# 2. Repository and scientific authority

**Private GitHub repository:**

https://github.com/aneesh-6220/nasa-space-apps-2026

**Authoritative starting branch:** `fable-ready`

**Expected base commit:**

`17829f8447fb3b9bcb5c369800ca1ce9d5ddfafc`

Verify that this exact commit exists and that the current remote branch is compatible with it. Inspect the working tree before changing anything.

Create a dedicated implementation branch, preferably:

`frostline-implementation`

Preserve teammate work. Do not force-push, alter raw downloads, change repository visibility or overwrite unreviewed scientific artifacts.

Read and obey:

1. `docs/FABLE_52_START_HERE.md`
2. `docs/FABLE_HANDOFF_FINAL.md`
3. `docs/APP_IMPLEMENTATION_CONTRACT.md`
4. `docs/APP_DATA_SCHEMA.md`
5. `docs/SCIENTIFIC_METHODS.md`
6. `docs/APPROVED_FINDINGS.md`
7. `docs/RESULTS.md`
8. `docs/CHALLENGE_ELIGIBILITY.md`
9. `docs/DATA_SOURCES.md`
10. `docs/GEOGRAPHIC_SCOPE.md`
11. `submission/SUBMISSION_DRAFT.md`

Inspect all referenced datasets, existing application code, processing scripts and tests.

**Authority order:**

- Verified raw data and approved scientific methods determine analytical truth.
- Generated authoritative results determine displayed numeric findings.
- The application contract determines valid interactions and input/output schemas.
- This document determines product direction, presentation, architecture priorities and completion standards.

Never resolve a scientific inconsistency by inventing data or changing the methodology to get a more compelling result.

The preparation branch reportedly passes:

```bash
python3 -I -m unittest discover -s tests
python3 -I scripts/regenerate_all.py --check
```

Expected baseline: 95 passing tests and deterministic regeneration.

Verify that baseline independently.

Implement the remaining application-level acceptance criteria identified in the engineering contract, particularly AC-2, AC-6, AC-7, AC-9 through AC-12 and AC-14.

# 3. What Frostline actually is

**Product positioning**

Frostline is a guided Earth-system trend investigation platform that helps people understand how environmental conditions are changing across northern Canada and what the evidence suggests about seasonal transportation.

**Headline**

FROSTLINE

**Tagline**

Trace the evidence behind changing winters.

**Primary promise**

Explore NASA climate data, detect historical environmental trends, compare northern locations, and investigate their relationship to documented winter-road operations.

## The problem

Seasonal winter roads and frozen-water crossings are important parts of northern transportation infrastructure.

Changes in weather and climate may affect the environmental conditions on which seasonal routes depend. However, atmospheric temperatures, local ice conditions, maintenance, construction practices and recorded opening dates are not interchangeable measurements.

Environmental data are distributed among scientific services. Transportation records are maintained separately. Statistical uncertainty and geographical limitations can make both difficult to interpret.

Frostline brings these sources together into a guided investigative workflow.

## The real user

Design primarily for:

**A science-curious non-specialist:** Someone who wants to understand whether a northern environmental condition is changing.

**A student or educator:** Someone learning how scientific time series, trends and uncertainty work.

**An exploratory researcher or adaptation planner:** Someone who wants an accessible, documented starting point for investigating historical environmental and operational relationships.

Do not imply that Frostline has been adopted, endorsed or validated by northern communities, road operators or government agencies.

Do not market it as an operational planning authority.

## What existing tools already do

NASA Giovanni can generate environmental time series.

KNMI Climate Explorer provides established climate analysis capabilities.

ClimateData.ca already publishes meaningful research connecting freezing accumulation, historical/projected climate conditions and winter-road implications.

Frostline must not claim these methods are new.

**Our differentiated contribution is the workflow:**

*Ask a human question → inspect NASA data → test the trend → compare locations → connect with documented road observations → examine an evidence audit → export a reproducible investigation.*

Make this workflow genuinely simpler and more informative than navigating separate datasets and research reports.

# 4. Design for all five NASA judging criteria

NASA evaluates Impact, Creativity, Validity, Relevance and Presentation. Treat these as product requirements, not merely pitch language.

## Impact

Show why northern seasonal transportation is consequential using documented government and scientific context.

Connect the application to realistic uses: historical understanding, climate education, preliminary research and long-term adaptation discussions.

Do not claim road-closure predictions or quantified benefits that have not been demonstrated.

## Creativity

Make Frostline more than a static dashboard.

Its distinctive features should be:

- A question-driven scientific investigation.
- Interactive geography linked to real data.
- A clear separation between environmental trends and operational outcomes.
- An Evidence Audit that makes uncertainty understandable.
- A shareable or downloadable evidence summary.

These are product-level innovations, not claims of original climate science.

## Validity

Every chart and statistic must come from approved datasets and documented methods.

Show relevant uncertainty and source limitations.

Preserve reproducibility, multiple-testing safeguards and explicit limits on causal interpretation.

## Relevance

The main screen must clearly demonstrate the NASA challenge:

- Select an Earth-system variable.
- See its historical behavior.
- Determine trend direction and magnitude.
- Evaluate significance.
- Compare geographic differences.

Road records provide context, but do not replace the required NASA environmental investigation.

## Presentation

The interface must communicate the value in seconds, work smoothly during a live demonstration and require minimal specialist knowledge.

Use progressive disclosure. The first screen must be simple; deeper evidence must be accessible on demand.

Do not assume judges will read the entire documentation.

# 5. The complete user experience

Build one coherent, responsive application with these integrated capabilities.

## A. Welcome and Guided Investigation

The first screen must immediately communicate the environmental problem and invite users to start exploring.

Hero:

**How is winter changing across Canada's North?**

Supporting text:

*Use NASA Earth science data to investigate historical winter conditions and the evidence behind seasonal transportation changes.*

Primary action:

**Start Investigation**

Provide three plain-language questions:

1. **Are winters getting warmer?**
2. **Is freezing accumulation changing?**
3. **Are above-freezing days becoming more frequent?**

Selecting a question should open the relevant real dataset and analysis, not a static explanation.

Use a preselected real example so the first meaningful visualization is immediately available.

## B. Interactive Geographic Explorer

Include an attractive, scientifically accurate location map using the approved repository coordinates.

Initial approved investigation locations:

- `dettah_bay`
- `aklavik_delta`

Use the documented human-readable labels.

Prefer Streamlit/PyDeck or another well-supported integration consistent with the implementation.

Required interactions:

- Select a location by clicking its marker.
- Update the relevant climate chart and evidence.
- Synchronize the map with the conventional location selector.
- Show a short, accurate description of the location and nearby transportation infrastructure.
- Distinguish sampling points from actual road geometries.

Do not require Google Maps credentials or billing.

Do not invent route lines, spatial heatmaps, ice thickness or climate-risk surfaces.

The entire investigation must remain usable if map tiles fail.

## C. Earth-System Trend Detective - core functionality

Allow users to choose from all scientifically approved environmental indicators.

Initially:

- Seasonal mean two-metre air temperature.
- October–December freezing degree-days.
- January–March above-freezing-day frequency.
- Any additional verified NASA variables approved through the existing scientific pipeline.

For each selection, present:

**Observed history**

An interactive historical time-series chart showing actual data points or seasonal values.

**Trend estimate**

A clearly differentiated fitted trend line using the approved estimator.

**Magnitude**

A value per decade, with appropriate scientific units.

**Uncertainty**

A justified confidence interval and clear significance or inconclusive status.

**Context**

Location, time period, dataset name, sample size and source.

**Interpretation**

Two or three sentences describing what the findings support, without exaggeration.

All displayed numerical statistics must come from authoritative generated outputs or validated scientific functions.

If the historical period changes, recalculate with approved functions or restrict the selector to approved precomputed periods.

Never reuse an incompatible confidence interval or multiplicity-adjusted q-value.

An inconclusive trend must be described as unresolved, not as proof of no change.

If a statistical estimator is undefined or unsuitable, display an informative unavailable state rather than zero or an invented result.

## D. Compare Northern Locations

Allow two approved locations to be compared on the same indicator and matched years.

Display:

- Two aligned historical series.
- Comparable units and scales.
- Trend magnitude for each.
- Appropriate uncertainties.
- A plain-language description of differences.
- Geographic and observational limitations.

Only claim a statistically established difference between trends if the approved methods actually support that comparison.

A significant result in one location and a nonsignificant result in another does not establish that the trends differ.

If formal difference testing is unavailable, label the comparison descriptive.

## E. Winter-Road Evidence

Show verified historical operating records separately from NASA climate measurements.

Include:

- Historical opening dates.
- Historical closing dates where valid.
- First-opening-to-final-closing calendar intervals where supported.
- Approved operational trend estimates.
- Exploratory environmental relationships only where the evidence permits.

Make the distinction visually explicit:

**Environmental measurements** versus **Recorded road operations**.

The existing data report a historically later-opening Dettah ice road trend. Treat this as an exploratory finding and load exact results from authoritative files.

Do not claim atmospheric warming caused the trend.

Dettah has an alternative year-round road route. Do not describe its ice crossing as its only transportation connection.

Aklavik has a different geography and seasonal-access context. Use only the verified road identity.

Opening-to-closing calendar intervals do not necessarily equal total usable road days.

Do not generate predictions about ice safety, road opening dates, truck routes or future accessibility.

## F. The Frostline Evidence Audit - signature capability

Each investigation must include an elegant, accessible evidence panel.

Organize it into:

**1. What we measured**

Exact variable, units, period and location.

**2. What changed**

Observed values, estimated trend and uncertainty.

**3. How confident are we?**

Statistical method, sample size, significance status, multiple-testing qualification and relevant assumptions.

**4. Where did the data come from?**

NASA collection, product version, source service, coordinates and original attribution.

**5. What did we check?**

Relevant ground-station validation, missingness and reproducibility tests.

**6. What can we conclude?**

A precise explanation of supported and unsupported interpretations.

Use readable scientific language without sacrificing accuracy.

Create an exportable evidence report or CSV download when practical, based on actual selected data and corresponding statistics.

Never generate numerical reports using an unverified AI narrative or fabricated values.

The Evidence Audit should be the application's distinctive feature-not an unreadable disclaimer.

# 6. Scientific integrity contract

These requirements override visual design choices.

## Source limitations

NASA POWER historical temperature data are principally derived from MERRA-2 reanalysis, representing spatial grid-cell estimates rather than precise measurements at road surfaces.

The existing audit reports a substantial negative temperature bias against nearby Environment Canada station observations.

Do not remove, conceal or correct that discrepancy through an arbitrary offset.

Clearly indicate that absolute FDD values are model-derived estimates and may differ from actual local atmospheric or ground conditions.

A high correlation between datasets does not establish agreement in absolute values or historical slopes.

## Statistical validity

Preserve the existing approved Theil–Sen, Mann–Kendall, uncertainty, multiplicity and leakage safeguards.

Do not create new statistical methods merely to make the dashboard more interactive.

Distinguish exploratory analysis from confirmatory inference.

Do not imply that statistical significance proves causality.

Do not present a lack of significance as proof that an environmental effect is absent.

Do not present invalid pooled significance calculations.

Do not treat a retrospectively chosen case as preregistered.

## Scientific nonclaims

Frostline must NEVER claim to:

- Measure safe ice thickness.
- Determine whether a winter road is safe.
- Predict when specific routes will open.
- Recommend trucking or travel decisions.
- Prove that a detected road-opening trend was caused by climate change.
- Establish community adoption or government endorsement.
- Provide verified findings for locations not in approved data.

These restrictions must be reflected in UI content and regression tests.

## Synthetic data

Remove or isolate legacy synthetic production code.

The old James Bay 380°C-day benchmark must not appear in the NWT investigation.

Production views must never silently fall back to synthetic data.

Retain synthetic fixtures only in clearly isolated tests.

# 7. NASA-resource eligibility

This is a mandatory competition gate.

The official challenge Resources include NASA Giovanni and AppEEARS.

The current repository uses NASA POWER daily temperature data. POWER itself is not explicitly listed in the official Resources provided by the team.

**Qualifying resource use remains unconfirmed.**

Cason is separately responsible for obtaining or verifying a genuine NASA data extraction through an officially listed resource.

The preferred additional series is:

NASA Giovanni → MERRA-2 monthly two-metre air temperature → approved northern location → documented historical time series.

The verified monthly MERRA-2 collection is `M2TMNXSLV`, variable `T2M`.

If a real Giovanni export becomes available:

1. Use the existing strict ingest pathway.
2. Validate its product, units, coordinates and dates.
3. Obtain scientific sign-off.
4. Integrate it meaningfully into the temperature-trend investigator.
5. Document exactly how this source contributes to the project.

Do not use monthly means to calculate daily freezing-degree-day totals or daily thaw counts.

If no qualifying export is available, do not invent one or claim eligibility.

Complete the application independently while clearly reporting the eligibility blocker.

The captain must verify the qualifying-source requirement before final submission.

# 8. Engineering architecture

Use the existing verified codebase as the foundation.

**Preferred application stack**

- Python
- Streamlit
- Plotly
- pandas / NumPy / SciPy
- Existing validated scientific analysis modules
- PyDeck for geographic interaction, if reliable

Do not migrate to Next.js or build unnecessary backend services unless the actual repository provides a compelling architectural reason.

Retain the existing scientific pipeline and data contracts.

The repository reportedly contains 20 approved application data files under `UI/data_real/`, along with per-winter outputs and `scripts/northlink_recompute.py`.

Verify exact paths and schemas.

Separate:

- Immutable raw sources.
- Reproducible data processing.
- Validated derived statistics.
- Application data access.
- Presentation components.
- Tests.

Use caching for deterministic analysis outputs and dataset loading.

The demo must work without live NASA API calls.

External basemap tiles may be used, but a failed mapping service must not break scientific exploration.

Avoid unnecessary databases, authentication, telemetry services or background job infrastructure.

The final application must be maintainable and understandable, not merely impressive-looking code.

# 9. Visual direction

Build an unusually polished scientific dashboard.

**Design language**

A contemporary northern-observatory aesthetic: midnight navy, glacier cyan, cool gray, white space and restrained warning accents.

Use polished typography, concise copy, meaningful negative space, consistent component spacing and beautiful data visualizations.

Visual priorities:

1. Scientific charts are central, not decorative.
2. The map helps users choose meaningful locations.
3. Important observations can be understood at a glance.
4. Statistics remain legible at laptop presentation size.
5. Detailed methodology is available through progressive disclosure.
6. Layout and labels remain accessible on mobile.

Use deliberate color coding, adequate contrast and color-blind-conscious chart palettes.

No unnecessary animations, generic stock-science decoration or misleading satellite-style imagery.

Do not let aesthetics delay functional integration.

# 10. Built-in judging experience

Create a **Guided Demo** mode inside the production app.

This must use the same real data and analytical functions as ordinary exploration.

It is not a fake demo, separate build or scripted mock result.

The flow should be:

**Scene 1 - The question**

Present the real northern transportation context in one concise explanation.

**Scene 2 - The location**

Show the mapped case study and select a relevant location.

**Scene 3 - The NASA investigation**

Select an approved environmental variable and display real historical data.

**Scene 4 - The result**

Show trend magnitude, uncertainty and interpretation.

**Scene 5 - The real-world evidence**

Show documented winter-road operating histories and clarify what is-and is not-established by the environmental data.

**Scene 6 - The Evidence Audit**

Demonstrate the scientific provenance and reproducibility that distinguish Frostline.

The entire journey must be navigable reliably during a short live presentation.

Provide a visible **Exit Guided Demo / Explore Freely** action.

Avoid any manual setup, authentication, freeform coordinate entry or live data download.

Build a short presenter script based exclusively on functioning features and approved results.

# 11. Real-world usefulness and future extensibility

Treat this as a meaningful scientific prototype, not a purported operational product.

Its credible immediate uses are:

- Climate education.
- Exploratory assessment of historical northern winter conditions.
- Understanding differences between locations.
- Communicating statistical uncertainty.
- Identifying questions requiring more research.
- Bringing environmental and transportation observations into one view.

The design should be extensible to additional verified NASA variables, regions and transport records.

However, do not add unsupported arbitrary locations simply to make the application seem global.

A credible future roadmap may include:

- Additional northern corridors.
- Verified snow and freeze/thaw satellite indicators.
- Comparisons with additional ground observations.
- Expert and community feedback.
- More rigorous spatial and operational validation.

These are future opportunities, not implemented features.

Do not claim community collaboration, adoption, validated decision support or current prediction capability without evidence.

# 12. Implementation order - one release, internal checkpoints

There is ONE final product, not two separate releases.

Work autonomously through these internal checkpoints.

### Checkpoint A - Scientific baseline

Confirm repository state and existing 95-test suite.

Inspect actual datasets, contracts and legacy app.

### Checkpoint B - Working real-data product

Remove synthetic production paths.

Make one complete NASA environmental investigation work from selection to chart to validated interpretation.

### Checkpoint C - Complete scientific workflow

Implement all approved metrics, locations, trends, uncertainty, comparisons and road records.

### Checkpoint D - Distinctive product experience

Build the geographic explorer, Evidence Audit and Guided Demo.

### Checkpoint E - Visual and functional polish

Improve navigation, responsive layout, scientific communication and error handling.

### Checkpoint F - Release validation

Run the full scientific and application tests.

Launch and interact with the actual app. Fix defects.

### Checkpoint G - Deployment and submission package

Deploy the product, verify public accessibility and prepare the submission materials.

Commit stable checkpoints, keeping the application runnable.

Do not return a plan in place of implementation.

If optional enhancements threaten release reliability, omit them cleanly.

# 13. Test and acceptance contract

Preserve all existing scientific tests.

Add application-level tests establishing that:

- All production science outputs use approved real data.
- No synthetic values are displayed.
- No obsolete James Bay metric remains.
- Every metric selector loads the correct observations and units.
- Location and map selection update all relevant content.
- Trend estimates match approved results.
- Period changes cannot display incompatible fixed-window statistics.
- Confidence intervals and corrected significance values are presented honestly.
- Undefined or mostly tied data produce correct unavailable states.
- Geographic comparisons use consistent years.
- Road records are matched to the correct seasons and routes.
- Causal and safety overclaims are absent.
- The Evidence Audit shows appropriate provenance and validation limitations.
- The app works without live API responses.
- Main navigation and the Guided Demo complete successfully.

Run the documented scientific test suite and deterministic regeneration check.

Also launch the application and perform real integration or headless-browser tests where supported.

Do not declare deployment successful without actually confirming the hosted app is accessible.

Do not declare tests passing without executing them.

# 14. Global and local submission requirements

Prepare a complete submission package.

**Required deliverables:**

- Fully working Frostline application.
- Publicly accessible application link.
- Publicly accessible project information or code artifact with appropriate licensing, subject to captain approval.
- A short official demonstration: either a video of no more than 30 seconds or a presentation of no more than seven slides.
- Local judging presentation outline.
- Scientific documentation.
- Data and software attributions.
- AI-use disclosure.
- Honest description of actual capabilities and limitations.
- Instructions to reproduce the application and analytical results.
- Verified screenshots for use if the live demo fails.
- Exact implementation branch and commit SHA.

All project links must be tested without authentication in a private browsing session.

Because the development repository is private, do not assume reviewers can access it.

The captain must authorize any change of repository visibility. If required, prepare a sanitized, properly licensed public release without exposing secrets.

Follow NASA's submission and intellectual-property requirements.

For any submitted video or images, avoid identifiable minors' faces, voices or personal information, consistent with the event's legal restrictions.

The official NASA project page must be completed before the November 15, 11:59 PM local deadline.

**Do not assume that post-deadline improvements count toward judging.**

# 15. Submission narrative

Prepare clear, grounded copy explaining:

**Problem**

Northern seasonal transportation depends on environmental conditions whose historical changes can be difficult to investigate and interpret.

**Solution**

Frostline turns NASA Earth-system data and relevant transportation records into a guided, interactive scientific investigation.

**How it works**

Users select a northern location and environmental indicator, examine historical observations, evaluate statistical trends, compare regions and access a transparent Evidence Audit.

**What we found**

Use only independently validated findings from the final repository. Distinguish NASA environmental trends from NWT operational trends.

**Why it matters**

It makes relevant Earth science more understandable and helps people examine questions relevant to northern adaptation.

**What makes it different**

A single guided workflow connecting environmental investigation, real-world evidence, statistical uncertainty and reproducibility.

**Limitations**

Not a real-time safety tool, ice-thickness measurement system or causal proof of climate-driven road delays.

Create a concise project description suitable for NASA submission, an accurate technical summary and speaker notes for a local judging presentation.

Do not claim Frostline is the world's first climate detective or that its scientific methods are unprecedented.

# 16. Execution autonomy and collaboration

You own the Frostline application implementation.

Cason owns additional data acquisition and source eligibility.

Yao owns independent scientific sign-off.

Louie supports interface testing and design feedback.

Ethan owns the final pitch and submission narrative.

The captain owns integration and release approval.

Make ordinary engineering decisions autonomously.

Do not repeatedly ask for approval on styling, component structure, code organization or test implementation.

Debug dependency problems, import issues, runtime failures and failing tests as part of the assignment.

If a step requires credentials, hosting account authentication, irreversible repository changes or a decision outside your authority, document the exact human action and continue independent work.

Use subagents only when they provide genuine parallel value, with separate file ownership and clear integration responsibility.

Do not create competing scientific code paths.

Keep the captain informed through concise milestone reports.

# 17. The final standard

The work is complete only when all of the following are demonstrated:

**Functional:** The app starts, navigates and works with real approved data.

**Scientific:** Charts and statistics agree with validated analysis, and important limitations are visible.

**Relevant:** A user can investigate NASA environmental variables and their historical trends.

**Distinctive:** The guided experience and Evidence Audit deliver value beyond simply displaying charts.

**Compelling:** A judge can understand and experience the product with minimal explanation.

**Reliable:** The app has passed automated tests and an end-to-end interaction check.

**Accessible:** Reviewers can open the public application and submission assets.

**Reproducible:** Original sources, processing methods and displayed results can be traced.

**Compliant:** Attribution, AI disclosure, licensing and challenge-specific NASA data requirements have been addressed or explicitly escalated for human resolution.

**Delivered:** Final code, tests, setup instructions, deployment, screenshots, submission copy and branch/commit are reported accurately.

At the end, report:

1. Exact implementation branch and commit.
2. Complete feature inventory: working, partial or unavailable.
3. Tests actually run and results.
4. App startup and deployment status.
5. Verified public link, if available.
6. Scientific sign-off and NASA eligibility status.
7. Remaining blockers with exact owners and actions.
8. What the captain should do next.

**The release goal is a complete scientific investigation experience that combines compelling communication with real analytical integrity.**

Build Frostline now. Do not stop at planning, mockups or unverified claims of completion.

---

# Authoritative research and competition references

**NASA 2026 challenge:**  
https://www.spaceappschallenge.org/2026/challenges/be-an-earth-system-trend-detective/

**NASA Space Apps 2026 dates and submission:**  
https://www.spaceappschallenge.org/2026/

**NASA Space Apps legal terms:**  
https://www.spaceappschallenge.org/legal/

**NASA Space Apps official organizer discussions:**  
https://github.com/nasa/spaceapps/discussions

**NASA POWER daily API:**  
https://power.larc.nasa.gov/docs/services/api/temporal/daily/

**NASA POWER meteorological provenance:**  
https://power.larc.nasa.gov/docs/methodology/data/sources_meteorology/

**NASA Giovanni:**  
https://giovanni.gsfc.nasa.gov/

**NASA MERRA-2 monthly collection:**  
https://data.nasa.gov/dataset/merra-2-tavgm-2d-slv-nx-2dmonthly-meantime-averagedsingle-levelassimilationsingle-level-di-892ac

**Northwest Territories transportation network:**  
https://www.inf.gov.nt.ca/en/transportation

**ClimateData.ca existing winter-road research:**  
https://climatedata.ca/winter-ice-roads-in-northern-ontario/

**Streamlit Community Cloud deployment:**  
https://docs.streamlit.io/deploy/streamlit-community-cloud