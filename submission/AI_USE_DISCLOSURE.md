# AI-use disclosure (draft for the team to confirm)

Frostline was built with substantial AI assistance. This is a factual account of where AI was used. Items in [BRACKETS] must be completed by the team; they are not to be invented.

## What AI did

| Area | AI involvement |
|---|---|
| Research and scoping | AI-assisted literature search and source checking. References were checked against publisher records and abstracts, not full texts (`docs/REFERENCES.md` records the check for each). |
| Data pipeline and statistics | The scripts in `scripts/` (data builders, Theil-Sen, Mann-Kendall, block bootstrap, multiple-testing corrections, leakage audit) were written with Claude (Anthropic) through Claude Code, with the team directing the work. |
| Scientific remediation | An AI-led review found and removed earlier errors: pooled significance tests, predictor windows that overlapped the outcome, a wrongly described hypothesis status and two impossible road dates. |
| Application | The Frostline application (`UI/frostline_app.py`, `UI/frostline/`), its acceptance tests and the automated browser checks were written by Claude Fable 5.2 through Claude Code. |
| Documentation and submission text | Drafted with AI assistance, including this file, the implementation matrix, the demo script and the slide text. |
| Screenshots | Captured automatically from the running application. They are real screens, not generated images. |

## What AI did not do

- No number shown in the app, the Evidence Brief or the slides is written by a language model. Every statistic is computed by tested scripts from public data.
- No generative model runs inside the application. Interpretation sentences are fixed templates chosen by the computed statistical status.
- No AI-generated imagery, audio or video is used.
- AI did not provide scientific sign-off. The methods are labelled exploratory until a human reviewer signs off.

## Human verification

- Independent statistical review: [not yet recorded; owner Yao].
- Team review of the application and its wording: [to be stated by the team].
- Parts written or edited directly by team members: [to be stated by the team].

## Tools

Claude by Anthropic (Claude Code; Claude Fable 5.2 for the application build). [Add any other tool the team used.]
