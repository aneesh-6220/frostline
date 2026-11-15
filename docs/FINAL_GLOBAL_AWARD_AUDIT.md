# Frostline final global-award audit (2026-11-15)

Independent audit, repair and local release verification of the Fable 5.2 implementation. Scope and rules: the audit brief of 2026-11-15. Everything below was run on this machine; nothing was pushed, merged or deployed.

## 1. Baseline

| Item | Value |
|---|---|
| Repository | `aneesh-6220/nasa-space-apps-2026`, cloned fresh to `/Users/aneeshmahatekar/projects/frostline/` |
| Remote branches | `main`, `fable-ready`, `frostline-implementation`, `remediation-final` |
| Latest Fable implementation | `frostline-implementation` = `main` = `3feb9a81ada0e2e42544c2dde249ef15cbe245c2` (Fable commits `6cc7c42` to `9b83339`, then one `.gitignore`/`.env.example` commit by a team member) |
| Audit branch | `frostline-global-audit`, created from `3feb9a8` |
| Baseline tests | 155 run, OK (Python 3.12.14, pinned `UI/requirements.txt`) |
| Baseline regeneration | `regenerate_all.py --check`: no-op; raw data digest `029362aa0568d065` |
| App data digest | `7037c7be7383fe25` (unchanged by the audit) |

## 2. Overall verdict

The Fable implementation is substantially sound. Every view renders on real data, every statistic is recomputed or cross-checked against the approved pipeline, and the scientific guardrails (no q on user windows, no estimate below 15 winters, thaw days not estimated, bias caveat on every temperature, no synthetic data path) hold under a 210-selection stress test. No CRITICAL defect was found. The defects found were in how the central finding is qualified on screen, in demo mechanics and in map legibility. The main remaining risks are external: the NASA listed-resource (Giovanni) requirement and the absence of a deployed URL.

## 3. Findings

| ID | Severity | Finding | Evidence | Status |
|---|---|---|---|---|
| F1 | HIGH | The headline Dettah opening-day card ("Supported historical trend", Observatory, demo stage 5, Corridor, Detective, Brief) omitted the selection-bias caveat that `APPROVED_FINDINGS.md` section B says must be shown, and did not say the result fails correction in the 2001/02 to 2024/25 window (q = 0.085). The caveat existed only on the Atlas, Corridor header and inside the Evidence Engine. | Demo stage 5 text before the fix | FIXED (`analysis._road_context_sentences`): selection caveat on every Dettah road result; window-sensitivity sentence on every fixed-window road result whose verdict differs between the two approved windows. Reaches cards, HTML brief and JSON. Tests: `tests/test_global_audit.py::RoadCaveats` |
| F2 | HIGH | Aklavik opening day (q = 0.048) and open-to-close (q = 0.020) are shown as "Supported" for 1993-2024, but both fail correction in 2001-2024 (q = 0.899, 0.844). `APPROVED_FINDINGS.md` calls the opening-day result "Fragile"; the card did not. | `road_record_trends_all_routes.csv`, `multiple_testing_126.csv` | FIXED by the same mechanism (window-sensitivity sentence) |
| F3 | MEDIUM | Observatory "Road record · Dettah" indicator stated the 1993-2024 result without selection bias or the NASA-era window outcome. | Observatory text | FIXED |
| F4 | MEDIUM | Guided demo: Next/Back kept the previous scroll position, so on a projector each new stage opened mid-page with its title off screen. | Browser: scrollTop unchanged after Next | FIXED (scroll to top on stage change, `st.html` with JavaScript). Verified in browser: 830 px to 0 px |
| F5 | MEDIUM | Atlas map was nearly unreadable for a first-time viewer: dark basemap, two markers, no orientation. | Screenshot | IMPROVED: labels for Great Slave Lake, Great Bear Lake, Beaufort Sea, Northwest Territories and the Arctic Circle reference line. Still no road geometry; tests assert the only line is the constant-latitude Arctic Circle |
| F6 | MEDIUM | `.env.example` referred to `scripts/fetch_giovanni_monthly.py`, which did not exist in the repository. | `ls scripts` | FIXED: script added (token-based Giovanni API request, verbatim save, provenance sidecar). Endpoint confirmed to exist; authenticated run NOT done |
| F7 | MEDIUM | The 2001-2024 road-date results are adjusted in the 126-test family F1 (Dettah opening q = 0.085). Within the 27-test road family F3 the same test has q = 0.018. The app and approved findings use F1 (the more conservative choice), so the "fragile" wording depends on that family choice. | `multiple_testing_126.csv` column `q_bh_within_family` | DISCLOSED here; the card names the family. Needs the statistics owner's decision (see blockers) |
| F8 | LOW | Server log: Streamlit warns once that the period slider has both a default and a session-state value. Logged only, not shown to users. A fix that dropped `value=` broke range mode (caught by AC-6 test) and was reverted. | Server log | ACCEPTED |
| F9 | LOW | Observatory headline "How is winter changing across Canada's North?" is broader than the data (two NWT points plus seven approximate corridors). It is a question, not a claim, and is mandated by the North Star and a test. | `observatory.py` | ACCEPTED, not changed |
| F10 | LOW | Plotly mode bar overlaps the legend on phone widths. No horizontal scroll at 375 px. | Mobile screenshot | ACCEPTED |
| F11 | LOW | `submission/screenshots/` were taken before F1 to F5 and do not show the new caveats or map labels. | Visual | OPEN (re-shoot if time allows) |

## 4. Scientific red-team results (independent reproduction)

Computed from `data/raw/` with code written for this audit (openpyxl, `scipy.stats.theilslopes`, a separately written tie-corrected Mann-Kendall), no repository analysis code:

| Quantity | Independent | App / approved | Agree |
|---|---|---|---|
| Dettah opening day 1993-2024, n | 32 winters, all with dates | 32 verified | yes |
| Dettah opening Theil-Sen per decade (95% CI) | +9.00 (+3.57 to +12.35) | +9.0 (3.6 to 12.4) | yes |
| Dettah opening MK p | 0.0003 | <0.001 | yes |
| Dettah open-to-close per decade | -10.24 (-15.83 to -5.29) | -10.2 (-15.8 to -5.3) | yes |
| Dettah opening 2001-2024 | +10.33 (+3.33 to +17.22), p 0.002 | +10.3 (3.3 to 17.2) | yes |
| Aklavik opening 1993-2024 | -6.67 (-14.17 to 0.00), p 0.024 | -6.7, q 0.048 | yes |
| NASA Oct-Dec FDD Dettah 2001-2024 | +14.6 (-107.9 to +111.1), p 0.785 | +15 (-108 to 111), p 0.785 | yes |
| NASA Oct-Dec FDD Aklavik 2001-2024 | -74.5 (-150.5 to +6.5), p 0.087 | -74 (-150 to 6) | yes |
| FDD definition | sum of max(0, -T2M) over 92 Oct-Dec days, 0 missing, degree-C | same | yes |
| NASA minus Yellowknife A | 8,574 paired days; -5.50 C Oct-Dec, -3.57 C Jan-Mar; monthly Oct -3.42, Nov -7.26, Dec -5.89 | "3.4 to 7.3 C colder", -5.50 / -3.57 | yes |

The Dettah headline reproduction is now a permanent test (`IndependentHeadline`).

Interpretation checks:
- The early-season NASA FDD trend is unresolved and the app never presents it as a cause of the later openings. Leak-free climate predictors are shown with intervals that all include zero, labelled association, not cause.
- "First opening to final closing" is labelled an interval, never usable or operating days; temporary closures are stated as unrecorded.
- No prediction, ice-thickness, safety or attribution statement was found in rendered text (AC-9 phrase test passes on every page).
- Multiplicity: q is shown only for the declared families and fixed windows; user windows show unadjusted p labelled exploratory.
- Caveat: Theil-Sen intervals assume independence; block-bootstrap intervals are shown beside them. Families are not independent, so q is indicative, as the app states.

## 5. Functional audit

Exercised in a real browser (1440x900 and 375x812) and headlessly (`AppTest`): all ten views, the six demo stages with Back/Next, location and variable selectors, exploratory-variable toggle, period slider and approved-window buttons, Atlas list selection, Compare, Corridor tabs, Evidence tabs, Brief downloads (HTML/CSV/JSON built and checked in tests), Methods. Cold render of every view: under 1.1 s. 210 location x variable x window selections run through trend, Evidence Engine and Brief with zero exceptions and zero invariant violations (no q on exploratory windows, no slope below 15 winters, slope inside its interval, thaw days never estimated).

## 6. Differentiation and competitiveness

Strengths a judge can see in three minutes: a real statistical investigation that recomputes for any selection; an Evidence Engine that separates observation, inference and limits with no composite score; open NASA-versus-station disagreement; multiplicity and selection-bias adjustment shown rather than hidden; a reproducible Evidence Brief with file hashes. These go beyond a conventional dashboard.

Weaknesses: geographic generality is limited (two documented points; seven corridors with fixed-window results only); the NASA listed-resource requirement is not demonstrated; there is no public URL yet; no human statistical sign-off.

Candid assessment: as a local-judging entry the product is strong and unusually honest. For a Global Award it is competitive on scientific rigor and communication, but it is at real risk of being ruled ineligible or marked down until a listed NASA resource (Giovanni) is demonstrably used and a working public URL is submitted. Those two human actions matter more than any further code change.

## 7. Commits on `frostline-global-audit`

See `docs/RELEASE_VERIFICATION.md` for the commit list, commands and results.
