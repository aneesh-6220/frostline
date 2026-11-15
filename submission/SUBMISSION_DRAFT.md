# Frostline - by Strongest Soldiers: submission and presentation draft

*Trace the evidence behind changing winters.*

Status: DRAFT for the team to edit. Every number below is checked by `tests/test_handoff_layer.py` against `UI/data_real/canonical_facts.json`. Items in [BRACKETS] are to be filled in by a named team member after the fact; do not invent them. No AI-generated imagery is used.

## Problem statement
Seasonal winter roads, built on frozen lakes and rivers, are critical links for remote communities in northern Canada. Public discussion of "shorter winter road seasons" often mixes weather, ice conditions and operating decisions. Frostline asks a narrower question: what do independent public records show about how winter conditions and road opening and closing dates have changed, and how sure can we be?

## Challenge alignment ("Be An Earth System Trend Detective!")
The user chooses a location, a variable and a period; the app shows the time series, the rate of change per decade, a confidence interval and a Mann-Kendall significance test, and states in plain words whether the change is distinguishable from no change. Where the challenge calls a non-significant result still interesting, Frostline reports it as exactly that. [Link to the live demonstration: ____]

## What the application does
Frostline is one connected investigation, built on the real data in `UI/data_real/` (entrypoint `UI/frostline_app.py`):
- **Observatory and guided demo**: a six-stage path through the production app, from the problem to an exported finding.
- **Northern Atlas**: the two documented locations and their NASA grid cells; select by map marker or list.
- **Question discovery**: plain questions mapped to catalogued variables, with the reason each variable fits.
- **Trend Detective**: the per-winter series, rate of change per decade, two confidence intervals, a Mann-Kendall test, an adjusted value where one is defined, and one of five evidence states. Changing the period recomputes everything and labels a user-chosen window exploratory.
- **Regional comparison**: the same variable on matched winters, with a test on the difference series.
- **Corridor investigation and timeline**: government opening and closing dates beside the NASA record, labelled as association, never cause.
- **Evidence Engine and source disagreement explorer**: seven separately judged aspects of evidence quality with reasons read from the data, and the NASA-against-station disagreement shown openly. There is no overall score.
- **Evidence Brief**: a downloadable report (HTML, CSV, JSON) with the question, data, trend, uncertainty, limits, sources and file hashes.
Feature-by-feature status and how each was verified: `docs/FROSTLINE_IMPLEMENTATION_MATRIX.md`. Architecture: `submission/ARCHITECTURE.md`.

## Scientific contribution
An open, reproducible, deliberately cautious analysis, not a new method. It uses Theil-Sen slopes, Mann-Kendall tests and block-bootstrap intervals, controls for multiple testing across declared families, and removes predictor windows that overlapped the outcome. It documents a measured disagreement between NASA reanalysis temperatures and a station and carries that caveat into every temperature display.

## Prior work and originality limits
Winter-road climate sensitivity has been studied, for example in Ontario's western James Bay region (Hori et al., 2016 to 2018), for the Tibbitt to Contwoyto road (Song et al., 2026; Mullan et al., 2021). Frostline does not replicate or extend those studies and does not apply their thresholds (the 380 degree-day figure is a James Bay result). Its contribution is an open comparison of two Northwest Territories routes with a public, reproducible record and a statement of limits. Full citations: `docs/REFERENCES.md`. Statistical sign-off by a named reviewer is pending [owner: Yao].

## NASA data use
Temperatures, precipitation and companion variables come from NASA POWER daily data (MERRA-2 reanalysis, 0.5 x 0.625 degree cells). POWER itself is not on the challenge's Resources list; whether it satisfies the Global Award resource requirement has not been confirmed [to ask an organizer]. An extraction of MERRA-2 monthly temperature through Giovanni is planned but **not yet done** [owner: Cason; status: ____]. Do not state it as done until `giovanni_*` files exist in `UI/data_real/`. POWER acknowledgement (required wording): see `docs/REFERENCES.md`.

## Other sources
Environment and Climate Change Canada station records (Yellowknife A, Aklavik, Inuvik). NWT Bureau of Statistics Table 108 (data from the Government of the Northwest Territories, Department of Infrastructure) for road opening and closing dates, 1993/94 to 2024/25. Press and reference pages used only for route identity (`docs/ROUTE_IDENTITY.md`).

## Real finding and its uncertainty
- In the government record the Dettah ice road opened about 9.0 days per decade later over 1993-2024 (95% CI 3.6 to 12.4 days, n = 32 winters; adjusted q = 0.002 across 51 route-level tests). Over 2001-2024 the estimate is similar but not significant after correction in the 126-test family, and it is sensitive to the earliest years. The result is exploratory and selection-biased because Dettah was chosen after its trend was seen.
- NASA temperature trends at the two locations over 24 winters are not distinguishable from no change (20 of 126 trend tests had p < 0.05 against about 6 expected by chance; none passed correction). This is not proof of no change.
- NASA POWER temperatures run colder than the Yellowknife station (3.4 to 7.3 C in Oct-Dec monthly means), so absolute NASA values are not local conditions.
- A snow association with Dettah opening dates is a hypothesis; snow itself shows no trend, so it does not explain the change.

## Real-world relevance
Winter roads connect communities and carry supplies. A transparent record of how opening and closing dates have changed, with its uncertainty, is useful context for discussion. Frostline does not assess whether any road is safe and does not tell anyone when to use one.

## What Frostline does not claim
No road-safety assessment or prediction. No claim that warming, snow or anything else caused a change in opening dates. No claim of community adoption, stakeholder interviews, endorsements or scientific review beyond what has actually occurred [none recorded].

## AI-use disclosure
The code, data pipeline and documentation in this repository were developed with substantial AI assistance (Claude by Anthropic, including Claude Code, and the Fable 5.2 model for application implementation), directed and reviewed by the team. A fuller account is in `submission/AI_USE_DISCLOSURE.md`. AI output is not treated as evidence: every number is generated by scripts from public data and checked by automated tests; the team [has / has not: ____] independently verified the statistics. [Team to state exactly which parts were AI-generated and which were verified by humans.]

## Submission assets in this repository
- Slides (seven, from real screens): `submission/frostline_slides.html` and its PDF export in the same folder.
- Local judging script and 30-second video shot list: `submission/DEMO_SCRIPT.md`. No video has been recorded.
- Real screenshots: the `submission/screenshots/` folder (thirteen images).
- A real exported Evidence Brief: `submission/sample_evidence_brief_dettah_opening_day.html`.
- Deployment steps and status: `submission/DEPLOYMENT.md`. The application is not deployed yet.

## Links to fill in after deployment
- Public project page: [____]
- Live application: [____]
- Repository (private during the hackathon; make public only by team decision): [____]
- Demonstration video, if any: [____]
