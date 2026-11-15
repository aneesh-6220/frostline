# Frostline judge presentation strategy

Written 2026-11-15 from the application as it runs on branch `frostline-final-qualification` (commit `f3edb22` or later). Every number quoted below was read from the running app and reproduced independently (`scripts/independent_verification.py`, plus two live NASA POWER requests recomputed by separate code). If the app shows a different number on the day, say the app's number.

Halifax judging: 15:00 Atlantic (team-reported). NASA submission closes 23:59 local.

---

## 0. The one idea judges should remember

> **Frostline turns "are northern winters changing?" into a reproducible NASA-data investigation that tells you how much, how sure, and what it cannot tell you.**

Do not try to be remembered for the number of features. Be remembered for one honest workflow done unusually well: **choose a place → pull NASA data → measure the change → judge the evidence → export it.**

The narrative spine, in four beats:

1. **Problem.** Ice roads in the Northwest Territories exist only while the cold holds. People ask whether winters are changing. Answering properly takes NASA data, daily cleaning, seasonal indicators, trend statistics, government records and restraint. Students and analysts rarely get all of that right.
2. **Distinctive solution.** Any northern point on a real map → live NASA POWER request → a rate of change *with* its uncertainty and a significance test that matches exactly what you selected → an Evidence Brief someone else can reproduce.
3. **Real result.** NASA's 46-year Giovanni MERRA-2 record for the Dettah / Yellowknife cell: autumn (Sep to Nov) warmed about **+0.60 °C per decade** (95% interval +0.23 to +0.97; q = 0.013), and it is the **only one of seven** seasonal tests that survives correction. Early winter (Oct to Dec) is +0.54 but not resolved (q = 0.179). The Dettah ice road's recorded opening day moved **about 9 days per decade later** over 1993/94 to 2024/25 (q = 0.002 across 51 route tests), but that is fragile in the shorter window and Frostline does not claim the climate caused it.
4. **Trust.** We show where NASA disagrees with the ground station (-5.5 °C in Oct to Dec), how many of 126 tests would look significant by chance (20 nominal, 0 after correction), and every caveat travels into the exported brief.

---

## A. 15-second explanation (no climate background needed)

> "Frostline lets you click anywhere in Canada's North, pulls decades of NASA temperature data for that spot, and tells you how much winter has changed and how confident you can be, with a report you can download and check."

## B. 30-second pitch

> "Ice roads connect northern communities, but only while winter holds. Everyone says winters are changing; checking it properly means finding NASA data, cleaning daily records, fitting trends and knowing what the numbers can't say. Frostline does that in one workflow: pick a place on the map, get real NASA observations, see the rate of change with its uncertainty, and export an Evidence Brief. For the Yellowknife area, NASA's 46-year record shows autumn warming of about 0.6 °C per decade, statistically supported, and the government record shows the Dettah ice road opening about nine days per decade later, without claiming one caused the other."

## C. 90-second pitch

> "Across the Northwest Territories, seasonal roads are built on frozen lakes and rivers every winter. They carry fuel and food, and they exist only while the cold holds. The question 'have winters changed here?' sounds simple, but answering it honestly means pulling NASA climate data, handling daily records, computing seasonal indicators like freezing degree-days, fitting trends, testing significance, correcting for running many tests, and comparing against the ground.
>
> Frostline does that workflow end to end. On a real map you choose a location. For any point between 50 and 75 degrees north, Frostline requests 44 winters of daily temperature from NASA's POWER API, validates units and missing days, and computes a Theil-Sen trend, a 95% interval and a Mann-Kendall test, the methods the challenge itself names. For the Dettah ice road near Yellowknife we add NASA's 46-year MERRA-2 record extracted through Giovanni, a listed challenge resource, and 32 winters of government road-opening dates.
>
> What we found: autumn at that grid cell warmed about 0.6 °C per decade since 1980, the one of seven seasonal tests that survives multiple-testing correction. The ice road opens about nine days per decade later. We do not claim the warming caused that, and the app says so.
>
> What makes Frostline credible is what it refuses to hide: NASA's reanalysis runs 5.5 °C colder than the airport station in early winter, 20 of 126 tests look significant by chance but none survives correction, and every result exports as an Evidence Brief with sources, file hashes and limitations, so anyone can reproduce it."

---

## D. Three-minute live demonstration (main demo)

**Before judging (mandatory, 10 minutes before):**

1. Restart the server so it runs the committed code. A server started before the last code change can show stale behaviour (seen today: a server started at 11:17 kept serving pre-11:18 code).
2. Open the app (public URL if deployed, otherwise `streamlit run UI/frostline_app.py` on the presenter laptop). Desktop browser, window at least 1400 px wide, zoom 100% or 110%. Dark room: the dark theme reads well on projectors.
3. **Warm the live demo point.** Map → expand "Case studies and coordinates" → Latitude 66.93, Longitude -125.31 → "Explore these coordinates" → "Retrieve NASA POWER daily data". This makes a real request and caches the real response. During the demo the same request is answered from the cache and the app *says* "served from memory cache / disk cache" with the original retrieval time. That is honest; do not describe it as "live right now" if it was served from cache. Say "retrieved from NASA's API this afternoon."
4. Click "Back to the curated case studies". Go to the Observatory. Close other tabs.

**Script (narration in quotes; actions in brackets):**

| Time | Page | Action | Narration |
|---|---|---|---|
| 0:00 to 0:25 | Observatory | [Nothing; let them read the title] | "Across Canada's North, ice roads are built on frozen lakes every winter and exist only while the cold holds. People say winters are changing. Frostline lets anyone test that with NASA data, honestly. Here's the workflow: choose a place, pull NASA data, measure the change, judge the evidence, export it." |
| 0:25 to 0:35 | Observatory | [Point to the "Road record · Dettah" card] | "This is why it matters locally: the government record shows the Dettah ice road near Yellowknife opening about nine days later per decade since 1993. Is the climate record changing too? Let's look." |
| 0:35 to 1:15 | Map | [Click **Explore the Data on the map**. Hover the blue Dettah marker and its shaded square.] | "This is a real map. The square is the actual NASA grid cell, about 55 km tall, so we never pretend the data are a point measurement." [Click an empty spot near 66.9 N, 125.3 W, or use the warmed coordinates via the form] "Any point in the North works. One click requests 44 winters of daily temperature from NASA POWER." [Click Retrieve; scroll to step 4] "Early-winter freezing degree-days here fell by about 68 per decade, 95% interval minus 112 to minus 20. The app labels it exploratory, because a point you pick by clicking is not corrected for multiple testing." |
| 1:15 to 2:15 | Giovanni record | [Click **Back to the curated case studies**, then **Open the NASA Giovanni record**. Choose Season → Autumn (Sep to Nov).] | "For Dettah we went further: 46 years of NASA MERRA-2 monthly temperature through Giovanni, one of the challenge's listed NASA tools. Autumn warmed about 0.6 °C per decade, interval 0.23 to 0.97. We tested seven seasons and corrected for that; autumn is the one that survives, q = 0.013." [Open "How sure is this? Statistical details" for two seconds to show the seven-row table] "Early winter, October to December, is +0.54, but not resolved after correction, and we show that too. A trend that isn't resolved is still a result." |
| 2:15 to 2:35 | Giovanni record | [Scroll to "Export these findings"; click **Download Evidence Brief (HTML)**; open the file] | "Every investigation exports. This brief has the inputs, the trend, the interval, all seven tests, the file hashes and what the data are not. Anyone can reproduce it from the repository." |
| 2:35 to 3:00 | (stay) | [Optional: scroll to "Is the extraction consistent", r = 1.0] | "Three things we're careful about: this is reanalysis for a grid cell, not a station; NASA runs about 5.5 °C colder than the Yellowknife airport in early winter, and we show that; and we don't claim warming caused the later road openings. Frostline is for getting the evidence right, not for making the road safe or predicting it. Thank you." |

If time runs short, cut the live point (0:35 to 1:15) to 15 seconds and keep Giovanni and the export.

**What to avoid in the three minutes:** the Guided demo's six stages (excellent for self-guided judges, too slow live), Questions, Compare, Corridor and Methods. Mention they exist only if asked.

## E. Extended five-minute technical demonstration (for judges who want depth)

1. **Map (60 s).** Show the dashed supported area, the grid-cell rectangles, the selection panel ("What is not available: road-operation dates, ice measurements, station checks"). Open "Statistical details, missing data and source metadata": requested and returned coordinates, the exact request URL, 15,888 daily values, 0 missing, POWER version v2.10.3, retrieval time. Open "Winter-by-winter values": valid days per season. Explain: a winter enters the trend only with every day present.
2. **Statistics (90 s), Giovanni page.** Theil-Sen = median of all pairwise slopes (robust to outliers). Mann-Kendall p from the signs of all pairs with tie correction. Benjamini-Hochberg across the 7 seasonal tests. Change the Period slider to 2000 to 2025: autumn becomes +0.75 with interval -0.12 to +1.70, labelled exploratory with no q. "Shorter window, wider interval: the app recomputes everything and drops the adjusted q because that window wasn't pre-declared."
3. **Ground truth (45 s), Evidence page.** NASA versus ECCC Yellowknife A: -5.5 °C in Oct to Dec over 8,574 paired days; NASA Oct to Dec FDD 46.5% above the station but year-to-year correlation r = 0.92. "So we use NASA for change over time, never for absolute local cold."
4. **Road record (45 s), Corridor or Guided demo stage 5.** Dettah opening day +9.0 days per decade, 1993/94 to 2024/25, q = 0.002 among 51 route tests. Then say the caveats yourself: chosen after its trend was seen (selection bias), not supported in 2001/02 to 2024/25 (q = 0.085), and no causal claim. Snow on the ground in late November correlates with opening (rho +0.64) and is labelled a hypothesis.
5. **Reproducibility (30 s).** `python3 -I scripts/regenerate_all.py --check` rebuilds every derived file from raw data byte for byte; 204 automated tests; an independent script re-derives the main numbers from the raw Giovanni CSV and the raw government workbook without using the production code.
6. **Close (30 s).** What it cannot do and what is next (section H).

## F. Visual strategy: slides

Use **at most three slides**, and only if the format requires slides. The app is the presentation.

| Slide | Content | Why it is a slide, not the app |
|---|---|---|
| 1. Title | "Frostline · Trace the evidence behind changing winters" · team name · one photo-free line: "Ice roads exist only while the cold holds." | Sets context while the laptop connects |
| 2. Workflow | Five boxes: Choose a place → NASA data (POWER daily API, Giovanni MERRA-2) → Trend + uncertainty → Evidence (limits, disagreements, corrections) → Export. Under it: "Theil-Sen · Mann-Kendall · Benjamini-Hochberg · 204 tests · byte-for-byte regeneration" | Architecture is hard to show by clicking |
| 3. Fallback / closing | Two result lines (Giovanni autumn +0.60 °C/decade, q = 0.013; Dettah opening +9 days/decade, no causal claim) + "What Frostline does not do" + repository URL (and app URL once it exists) | Doubles as the offline fallback and the last thing on screen |

The existing `submission/frostline_slides.html/.pdf` predate today's Giovanni and map work; rebuild these three slides from the running app rather than reusing older screenshots. Show charts in the app, not in slides.

## G. Team responsibilities (six people; not everyone needs to speak)

Coherence beats equal airtime. Recommended: **two speakers, one driver, three Q&A specialists.** Names are placeholders except where the repository already records an owner for a topic (blockers document); the team should confirm.

| Role | Responsibility | Suggested |
|---|---|---|
| Lead speaker | Delivers 0:00 to 0:35 and 2:35 to 3:00 (problem, why it matters, close) | Strongest communicator |
| Science speaker | Delivers the Map and Giovanni sections; answers "how sure" | Whoever best explains Theil-Sen and q in plain words |
| Driver | Clicks only; never speaks during the demo; knows the warm-up steps and the fallback | Most confident with the app |
| Statistics Q&A | Multiple testing, intervals, autocorrelation, sample size | Yao (statistical review owner in `OUTSTANDING_EXTERNAL_BLOCKERS.md`) |
| Data Q&A | Giovanni provenance, POWER API, station comparison, road records | Cason (Giovanni and route-data owner in the same document) |
| Engineering Q&A | Architecture, caching, tests, deployment, AI-assisted development | Whoever ran the deployment |

Rule for Q&A: the person named answers first, in under 30 seconds; nobody else adds unless the answer was wrong.

## H. Judge-question contingency plan

Short answers to say out loud. Fuller versions are in `docs/FROSTLINE_JUDGE_TECHNICAL_DEFENSE.md`.

- **"Is the trend real or noise?"** "For the 46-year Giovanni autumn series the 95% interval excludes zero and it survives correction across the seven seasons we tested. For the 24-winter daily series it doesn't; we say 'not resolved', which isn't the same as 'no change'."
- **"Did climate change cause the later road openings?"** "We don't claim that. Opening dates depend on ice thickness, snow, budgets and crews. The app keeps environmental and road evidence side by side and never merges them."
- **"Did you cherry-pick autumn?"** "We tested all seven seasonal aggregates and corrected across all seven; the app shows all seven, including the six that don't survive. We didn't preregister, so we call everything exploratory."
- **"Is NASA POWER a listed resource?"** "No, POWER isn't on the list; Giovanni is, and we used Giovanni for the 46-year record. POWER and Giovanni serve the same MERRA-2 model, and we checked they agree to within 0.4 °C every month."
- **"24 winters is short."** "Yes. That's why the shorter record mostly isn't resolved and why we added the 46-year Giovanni record and 44-winter live requests."
- **"Isn't this just Giovanni with extra steps?"** "Giovanni gives you a time series. Frostline gives you the seasonal indicator, a trend with uncertainty, multiple-testing control, ground-truth disagreement, road records and a reproducible brief, for any point, in one place."
- **"How much did AI write?"** "Most of the code was written with AI assistance, and we disclose that. What we did: chose the question and data, checked the numbers against raw files with independent code, ran the browser tests and decided what the app is allowed to claim." (Only say what is true for your team; see `submission/AI_USE_DISCLOSURE.md`, which still has team placeholders.)
- **"What can't it do?"** "Measure ice, judge road safety, predict opening dates or establish causes. It's an evidence tool."

## I. Demonstration failure fallback

| Failure | What you see | What to do (never fake a result) |
|---|---|---|
| NASA POWER down or slow | Spinner over 60 s, or "NASA POWER could not be reached" | Say: "NASA's API isn't answering; the app reports that instead of inventing numbers." Then use the pre-warmed point (served from cache with its original retrieval time) or skip to the Giovanni page, which needs no network |
| Map tiles fail | Grey map, markers still visible | Say so. Use "Case studies and coordinates" (works without the map). Topographic and OpenStreetMap alternatives are in the layer menu, top right |
| Public URL slow (cold start) | Streamlit "waking up" page | Open the URL 10 minutes before judging. Keep the laptop server running as a second tab |
| No internet at all | Map tiles and live POWER unavailable | Run locally: `streamlit run UI/frostline_app.py`. Observatory, Giovanni record, Guided demo, Evidence and every curated brief work offline from committed files |
| Laptop failure | Nothing | `submission/frostline_slides.pdf` and `submission/sample_evidence_brief_dettah_opening_day.html` on a second device or USB stick; describe them as static exports |
| Number on screen differs from this script | Different digits | Read the app's number. Never "correct" it verbally to match the script |

## J. Readiness checklist (presenter, before 15:00)

- [ ] Server restarted after the final commit; sidebar shows the expected data digest.
- [ ] Demo point warmed; Giovanni Autumn selected once to confirm +0.60 and q = 0.013.
- [ ] Evidence Brief downloads and opens on the presentation machine.
- [ ] Browser zoom checked on the projector; notifications off.
- [ ] Driver and speakers have rehearsed once against a timer.
- [ ] Nobody says "predicts", "safe", "caused by", "validated by ground stations" or "deployed" unless the deployment URL has been opened in a private window.
