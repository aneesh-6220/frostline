# Frostline final UX audit (premium UI pass)

Branch `frostline-premium-ui`, started from `4a07947` (`frostline-final-qualification`). The deployed app at
frostline.streamlit.app was not changed, and nothing was pushed or deployed. Screenshots: `docs/ui_review/before/` and `docs/ui_review/after/`.
Files are named `<view>_<width>.jpg` (first screen) and `<view>_1440_full.jpg` (full page).

## Starting point

The release candidate was already restrained and scientifically careful: a dark observatory palette, one accent, ruled metric strips,
evidence-state chips and honest captions. This pass was therefore surgical. It did not rebuild anything. Most views needed no change.

## Confirmed problems (seen in a real browser)

| # | Problem | Evidence |
|---|---|---|
| 1 | The top navigation had 11 flat items. At 1440px the last two (**Brief** and **Methods**) were hidden behind a "2 more" overflow, so the export step of the core journey was not visible on a laptop. | `before/observatory_1440.jpg` (right edge of header) |
| 2 | The landing page explained the product three times: the hero, a list of the six demo stage names, and a "What you can do here" block of three rows. | `before/observatory_1440_full.jpg` |
| 3 | Trend Detective opened the full statistical record by default. The right column ran about 900px past the chart, which left a large empty area beside the table of winters, and the advanced statistics competed with the result. | `before/detective_1440_full.jpg` |
| 4 | Map chrome did not match the app. The attribution bar was white and about 15px with a large flag icon, the controls were default white Leaflet, the iframe flashed white while loading, and a long paragraph acted as the legend. | `before/atlas_1440_full.jpg` |
| 5 | The live NASA POWER explorer chart reversed the encoding used everywhere else (white points with a blue trend line, against blue points with a white trend line elsewhere). | browser walkthrough, map → retrieve |
| 6 | Chart tick and axis labels were 11.5px in tertiary grey, small for a projector. | all charts |
| 7 | At 768px the hero headline wrapped to five lines. | `after` iteration, fixed |

## Changes implemented

| # | Change | Files | Why it helps |
|---|---|---|---|
| 1 | Grouped navigation: Home, Map, Guided demo, Evidence Brief at top level. **Explore** and **Understand** menus hold the other seven views. URL paths are unchanged. | `UI/frostline_app.py` | Every view is visible at every desktop width. The primary path (place → evidence → export) reads left to right. |
| 2 | Replaced the stage-name list with a five-step journey (Choose a place → Retrieve NASA data → Measure the trend → Weigh the evidence → Export a brief). Removed the redundant "What you can do here" rows. The scope note now sits beside "Why it matters" with the release counts. | `views/observatory.py`, `ui.py` (`journey`) | One explanation of the workflow instead of three. The scope limitation stays on the first page. |
| 3 | The full statistical record is now collapsed by default. The summary line gains p and the multiplicity-adjusted q (or "not adjusted for multiple testing" for a user window), so no essential qualification moves behind the expander. | `ui.py` (`finding_card`) | Results come first and the columns are balanced. Uncertainty stays visible at summary level. This also tidies Corridor and Compare, which use the same card. |
| 4 | Map restyle: 560px height, dark loading background, compact dark attribution (still fully visible), dark controls, layer menu, tooltips and scale. A one-line legend with real swatches replaces the paragraph. | `views/atlas.py` (`MAP_CSS`), `ui.py` (`.fl-legend`) | The map reads as part of the product and the legend can be scanned. Tile attribution is preserved, as provider terms require. |
| 5 | The explorer chart now uses the shared encoding, and its y-axis is labelled with the variable name and unit. | `views/atlas.py` | Charts mean the same thing everywhere. |
| 6 | Chart ticks, axis titles and legends set to 12.5px. | `charts.py` | Legible on a projector, with no change to data or layout logic. |
| 7 | Hero headline 36px below 1100px wide; journey labels never break mid-word. | `ui.py` | Tablet layout no longer stacks a five-line headline. |

Five regression tests were added in `tests/test_premium_ui.py`: navigation coverage, q visible while the record is collapsed, the landing journey, map attribution and legend, and chart encoding.

## Deliberately left unchanged

- All scientific computation, data files, findings, statistical rules, copy restrictions and exports.
- The landing headline and button labels. They are pinned by `test_home_begins_the_demo_and_reaches_a_real_chart` as approved release copy.
- **Begin an Investigation** still opens the Guided demo; the map is the secondary action. Swapping them would contradict the pinned test's intent.
- The hero chart still shows a statistically unresolved trend. It is real data and an honest first impression, and replacing it with a more dramatic series would be presentation-driven selection.
- Giovanni record, Evidence, Brief, Methods, Questions and Guided demo layouts. Inspection found no problem worth the risk of change.
- The phone map height. A CSS override to 420px clipped the Leaflet container and hid the attribution, so it was reverted.

## Browser acceptance (simulated usability review, not user research)

No independent participant was available. These are systematic walkthroughs by the implementer.

| Check | Result |
|---|---|
| Overflow at 375 / 768 / 1440 / 1920 px, 11 views each | No horizontal scroll on any of the 44 combinations (`scrollWidth == viewport`) |
| Map click → live NASA POWER retrieval (59.98 N, 116.69 W) | 15,888 daily values retrieved; trend −25.0 °C·days per decade, 95% interval −78.5 to 25.7, "Exploratory window" chip, chart rendered |
| Giovanni season change (calendar year → spring) | Result recomputed and relabelled |
| Guided demo Next × 5 | Stages 2 to 6 reached, scroll reset to top each time, stage 6 shows all three exports |
| Evidence Brief downloads | HTML 27 KB, CSV 1.4 KB, JSON 13.5 KB downloaded; JSON data digest `a1f1cd6387875487` matches the sidebar |
| Phone map | Leaflet container 560px, attribution visible, 18 tiles loaded |

**A. First-time judge.** The headline, lede and five-step journey state what Frostline does. The two actions are distinct, and the live chart shows real NASA data with its uncertainty band. Within 30 seconds a judge can start. Weakness: the headline is a question, so the product noun ("investigation tool") appears only in the lede and the scope note.

**B. Student or educator.** Map → retrieve → result panel → plain-language sentence works without statistics training. The chip says "not statistically resolved" and the sentence adds "That is not proof of no change."

**C. Scientific reviewer.** The interval, p and q are on the summary line. The full record, method, provenance file names, digest and Methods view are one click away. Exports carry code version and data digest.

## Remaining limitations

- While an exploratory map point is active, the sidebar still describes the curated case-study investigation. This is accurate but can confuse.
- The default basemap (Esri Dark Gray Canvas) is low-contrast by design. The topographic basemap is one click away in the layer menu.
- The phone map is 560px tall in an 812px viewport. It is usable, but scrolling past it needs a drag outside the map.
- The Streamlit top-menu dropdown styling is Streamlit's own. It was not overridden, to avoid brittle selectors.
- The landing metric strip has four dense paragraphs. Each carries a required qualification, so it was not shortened.

## Quality gate (candid)

| Question | Assessment |
|---|---|
| Credible scientific product? | Yes. It was already close; this pass removed the most visible rough edges. |
| Purpose immediately apparent? | Mostly. The lede does the work the question-style headline does not. |
| Next step obvious? | Yes. Two actions, a five-step path, and the export always visible in the navigation. |
| Map useful and integrated? | Improved. Its chrome now matches; the basemap remains muted. |
| Charts understandable? | Yes, with consistent encoding and larger labels. |
| Conclusions accurate? | Unchanged. No finding, method or caveat was altered. |
| Limitations visible without clutter? | Yes. The q value moved up and the long record moved down. |
| Consistent design language? | Yes. Documented in `docs/FROSTLINE_UI_DESIGN_SYSTEM.md`. |
| Mobile and desktop? | Verified at four widths. |
| Any element that does not help? | No decorative elements were found or added. |
| Complexity added without usability gain? | No. Net copy and layout decreased. |
