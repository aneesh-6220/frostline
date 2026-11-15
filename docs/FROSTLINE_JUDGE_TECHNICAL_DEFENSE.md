# Frostline judge technical defense

For the six members of Strongest Soldiers. Each question has a **short answer** (say it in under 30 seconds) and, where useful, a **deeper answer** for a follow-up. Every number was checked on 2026-11-15 against the running app and, for the principal results, against independent code (`scripts/independent_verification.py`). File references point at the code that does the thing.

Ground rules when answering:

- Say the number the app shows. If you do not know, say "I don't know; here is where the app shows it" and open the page.
- Never say "caused", "predicts", "safe", "validated against ground truth" (for MERRA-2 versus MERRA-2), "statistically proven" or "deployed" (until a public URL has been opened in a private window).
- "Not statistically resolved" is not "no change". Say both halves.

---

## Part 1. Questions and answers

### Originality and importance

**1. What problem does Frostline actually solve?**
Short: Answering "has winter changed here, and how sure are we?" normally takes several separate workflows: finding NASA data, cleaning daily records, computing seasonal indicators, fitting trends, testing significance, correcting for many tests and checking against the ground. Frostline does all of that in one reproducible workflow for any northern point, and exports the result.
Deeper: The manual route is error-prone in specific ways Frostline guards against: silently filling missing days (Frostline excludes incomplete winters, `scripts/northlink_metrics.py::season_coverage`), reporting a p-value from a window chosen after looking (user windows never get a q, `UI/frostline/analysis.py::trend`), and treating reanalysis as a local measurement (bias caveat on every temperature result).

**2. Giovanni and KNMI Climate Explorer already plot time series. What's new?**
Short: They give you a series. Frostline gives you the winter-specific indicator (freezing degree-days from daily data), a trend with its interval and test, multiple-testing control, the disagreement with the ground station, government road records alongside, and a brief someone else can reproduce, for any clicked point.
Deeper: The contribution is the evidence-integrity layer, not a new statistic. We don't claim methodological novelty.

**3. Why ice roads?**
Short: They're a place where winter timing has concrete consequences: they exist only while ice holds, and the NWT government publishes every opening and closing date since 1993/94. That gives a real-world record to set beside the climate data.
Deeper: We deliberately keep road dates and climate data separate. The road record is operations (government decisions, light vehicles first), not ice measurement.

**4. Who would use this?**
Short: Students and teachers learning to test a climate claim properly; analysts doing a first-pass trend check for a northern location; adaptation planners who want the historical record with its caveats. Not operators deciding whether a road is safe.
Deeper: We have no user study and no adopting community. Don't claim either.

### Data provenance and eligibility

**5. Which NASA data do you use?**
Short: Two routes to the same NASA model, MERRA-2: daily 2 m air temperature from the NASA POWER API (curated locations and every live map point), and monthly 2 m temperature, product M2TMNXSLV version 5.12.4, extracted through NASA Giovanni for the Dettah cell, January 1980 to December 2025, 552 months.
Deeper: Giovanni files are in `data/raw/nasa/giovanni/` with SHA-256 hashes in `tests/raw_checksums.sha256`; the NetCDF was checked value by value against the CSV (`scripts/verify_giovanni_netcdf.py`).

**6. Is your project eligible for the Global Award NASA-resource rule?**
Short: Giovanni is on the challenge's Resources list and the 46-year record in the app comes from it. Whether that satisfies the rule is the organizers' decision; we've asked / will ask (update this when an organizer answers). NASA POWER on its own is not a listed resource.
Deeper: `docs/CHALLENGE_ELIGIBILITY.md` records the list and the status. Do not say eligibility is confirmed.

**7. Does Giovanni "validate" POWER?**
Short: No. Both serve the same MERRA-2 model, so their agreement (285 months, mean difference -0.001 °C, largest 0.394 °C, correlation 1.0) checks our access route and processing, not the science.
Deeper: The small monthly differences come from POWER days being local solar time while MERRA-2 monthly means are UTC.

**8. What's your ground truth?**
Short: Environment and Climate Change Canada's Yellowknife A station. Over 8,574 paired days, NASA is 5.5 °C colder in October to December. NASA Oct to Dec freezing degree-days are 46.5% above the station, but the year-to-year correlation is 0.92.
Deeper: So we use NASA for change over time, never for absolute local cold. Station data are a comparison, not a correction: no bias correction is applied anywhere (`docs/APPROVED_FINDINGS.md` E).

**9. Where do the road dates come from?**
Short: NWT Bureau of Statistics Table 108, opening and closing dates for 17 routes from 1993/94 to 2024/25: 544 route-winters, 512 verified.
Deeper: Only verified rows carry dates; 4 flagged-inconsistent, 24 missing and 4 note-only rows are left empty, never estimated (`scripts/northlink_recompute.py::road_series`).

### Geographic resolution and the map

**10. How precise is a map click?**
Short: The click is rounded to 0.01°, but the data describe a whole MERRA-2 grid cell, 0.5° latitude by 0.625° longitude, about 55 km tall. The map draws that cell so nobody mistakes it for a point measurement.
Deeper: `UI/frostline/power_api.py::merra2_cell` snaps to the MERRA-2 grid: latitude centres at multiples of 0.5°, longitude at -180 + k × 0.625°. Example: 64.32 N, 96.02 W falls in the cell centred at 64.5 N, 96.25 W.

**11. What exactly happens when I click the map?**
Short: The click becomes a coordinate, the app checks it's inside the supported area (50 to 75 N, 170 to 55 W), and a "Retrieve" button requests 44 winters of daily T2M from NASA POWER. The response is validated and cached, then run through the same metric and trend code as the curated results.
Deeper: `UI/frostline/views/atlas.py`: `st_folium` returns `last_clicked`; `new_click` ignores clicks already seen on a previous rerun; `resolve_click` classifies it (curated marker, exploratory point or outside); `_run_explorer` fetches and analyses.

**12. Why only 50 to 75 N in North America?**
Short: That's where seasonal ice roads matter and where we've checked the analysis makes sense. POWER itself is global; widening the area is a one-line change but we'd want to re-check the indicators first (for example, freezing degree-days are near zero far south).

**13. Are the map tiles allowed?**
Short: The default basemap is Esri's public ArcGIS Online tiles, attributed on the map, with OpenStreetMap as an alternative. We haven't re-read Esri's terms for this event; switching the default to OpenStreetMap is a one-line change if needed.
Deeper: `TILES` in `atlas.py`. CARTO was dropped because it now requires a key. Nothing on the map is invented: no road lines, risk layers or rasters.

### API integration, caching and reliability

**14. What request do you send to NASA POWER?**
Short: `GET https://power.larc.nasa.gov/api/temporal/daily/point?parameters=T2M&community=SB&longitude=…&latitude=…&start=19811001&end=20250331&format=JSON`. No key.
Deeper: `power_api.py::request_params`. We validate the unit is °C, the returned coordinates match the request, dates are unique, fill values (-999) become missing, and values outside -70 to 45 °C are removed. A response that fails validation is never cached.

**15. What if NASA's API is down during the demo?**
Short: The app shows "NASA POWER could not be reached" and no numbers. Curated case studies, the Giovanni record and every brief keep working from committed files.
Deeper: Errors are tied to the point they were raised for (fixed today; regression test `tests/test_final_qualification.py`). Timeout is 60 s.

**16. How does caching work?**
Short: Identical requests are cached in memory and on disk, keyed by a hash of the exact parameters, and live calls are spaced at least one second apart. The app shows whether a result came from a live request or the cache, with the original retrieval time.
Deeper: `fetch_daily` holds a lock while fetching. That serialises live requests across users of one server, which is polite to NASA but means one slow request makes others wait. Fine for a demo; a production version would queue requests instead.

**17. How do you know the code is right?**
Short: 204 automated tests; byte-for-byte regeneration of every derived file from the raw data; an independent script that re-derives the main numbers from the raw Giovanni CSV and the raw government workbook without importing any production code; and browser testing of every journey.
Deeper: The independent script agreed on all 7 Giovanni trends and both Dettah road windows. It also found a rounding tie: summer means for 2008 and 2013 are equal at the 4 decimals stored in the CSV, which moves the summer p-value from 0.520 to 0.526. No conclusion changes.

### Statistical methodology

**18. Why Theil-Sen rather than ordinary least squares?**
Short: Theil-Sen is the median of the slopes between every pair of years, so one extreme winter can't drag the trend. It's standard for short climate series and pairs naturally with the Mann-Kendall test.
Deeper: With n = 46 years there are 1,035 pairwise slopes; the estimate is their median. The 95% interval comes from the ranks of those slopes using the Kendall variance (Sen 1968), via `scipy.stats.theilslopes` in production and our own code in the independent check.

**19. What does the Mann-Kendall p-value mean here?**
Short: If there were truly no monotonic trend, it's the probability of seeing pairwise ups and downs at least this lopsided. For Giovanni autumn, p = 0.0018.
Deeper: S = Σ sign(y_j − y_i) over all pairs; Var(S) = [n(n−1)(2n+5) − Σ t(t−1)(2t+5)]/18 with tie correction; z with continuity correction; two-sided normal p (`northlink_metrics.py::mann_kendall`).

**20. What is a q-value?**
Short: A p-value adjusted for the number of tests run together, using Benjamini-Hochberg. q < 0.05 means that among the results we call "supported", we expect at most about 5% to be false discoveries.
Deeper: Sort the m p-values; q for the k-th smallest is min over j ≥ k of p_(j) × m / j. Autumn: 0.0018 × 7 / 1 = 0.0126.

**21. Did you choose autumn after seeing the results?**
Short: All seven seasonal aggregates were computed and corrected together, and the app shows all seven. Autumn is the only one that survives. We didn't register the family in advance, so the result is labelled exploratory.
Deeper: The seven are year, Dec to Feb, Mar to May, Jun to Aug, Sep to Nov, Oct to Dec, Jan to Mar. They overlap (Sep to Nov and Oct to Dec share two months), so the tests are positively dependent; Benjamini-Hochberg remains valid under that kind of positive dependence.

**22. Why do the road results use "126 tests" and "51 tests"?**
Short: Different questions, different families. The 51-test family is every road-date trend (open, close, interval) across all 17 routes over the full 1993/94 to 2024/25 record. The 126-test family is every trend (14 metrics × 9 corridors) in the shorter NASA-era window 2001/02 to 2024/25.
Deeper: Dettah opening day: +9.0 days per decade, q = 0.002 in the 51-family. In the NASA-era window it's +10.3 (95% interval +3.3 to +17.2) but q = 0.085 in the 126-family. If you corrected only among the 27 road tests in that window, q would be 0.018. Which family is right is an open methodological decision for our statistics reviewer; the app uses the more conservative one.

**23. Your confidence intervals assume independent years. Is that valid?**
Short: Not entirely, so we check. We report the lag-1 autocorrelation of the residuals and flag anything above 0.3, and road and curated results also carry a moving-block bootstrap interval that keeps short-range dependence.
Deeper: Block length ceil(n^(1/3)), 2,000 resamples, fixed seed 20261114 (`northlink_stats.py::block_bootstrap_slope`). Giovanni residual lag-1 values are all small (largest 0.20 in summer).

**24. Isn't 24 winters too short?**
Short: For detecting modest trends against large year-to-year swings, yes. That's why most 24-winter results are "not resolved", and why we added the 46-year Giovanni record and 44-winter live requests. Fifteen winters is our hard minimum.
Deeper: Dettah Oct to Dec freezing degree-days: +15 °C-days per decade with an interval of -108 to +111. The interval is wider than any plausible trend, so the honest answer is "this record can't tell".

**25. Clicking many map points is like running many tests. How do you handle that?**
Short: Correctly flagged: every live result says "exploratory, not adjusted for multiple testing". If you click twenty points, about one will look significant by chance.
Deeper: That's also why the 126-test summary is on the front page: 20 nominal p < 0.05, about 6.3 expected by chance, 0 after correction.

**26. Correlation versus causation: what does the snow result show?**
Short: Late-November snow on the ground at Yellowknife correlates with a later Dettah opening (Spearman rho +0.64, 23 winters). We label it a hypothesis. Snow insulates ice, which is a plausible mechanism, but a correlation can't establish it, and the snow series itself shows no resolved trend.

### Winter roads and limitations

**27. So is climate change delaying the Dettah ice road?**
Short: We can't say that and the app doesn't. The road opens later in the record, and the regional autumn record warmed, but opening decisions depend on ice thickness, snow, safety policy, budgets and crews. Those aren't in our data.

**28. Can Frostline predict when a road opens or whether it's safe?**
Short: No. It doesn't measure ice, assess safety or forecast. Those claims are prohibited in our own rules (`docs/APPROVED_FINDINGS.md` F) and absent from the app.

**29. What about Aklavik?**
Short: Aklavik's opening day moved about 6.7 days per decade *earlier* over 1993/94 to 2024/25 (q = 0.048), but that vanishes in 2001/02 to 2024/25 (-0.5). We also haven't verified which road segment the record describes. We show it as a contrast, with those caveats, not as a replication.

**30. Why is NASA so much colder than the station?**
Short: A reanalysis value is an average over a 55 km cell that includes lake and forest, at the cell's average elevation, while the airport station is one point near a town. Early winter over a freezing lake is especially hard for the model. We show the gap rather than correct it.

### Reproducibility, AI and team

**31. Can someone else reproduce your numbers?**
Short: Yes. Clone the repository, `pip install -r UI/requirements.txt` on Python 3.12, run `python3 -I scripts/regenerate_all.py --check`. It rebuilds every derived file from the raw data and confirms they match byte for byte. Every brief lists the file hashes it was computed from.

**32. How much of this did AI write?**
Short: A large share of the code and documents was written with AI assistance (Claude), which we disclose. Our work was choosing the question and data, exporting the Giovanni data, reviewing claims, testing in the browser and checking numbers against raw files with independent code.
Deeper: Say only what your team actually did. `submission/AI_USE_DISCLOSURE.md` still has bracketed items the team must complete; finish them before submitting. The git history shows commits by AI and by two team members; it does not record who reviewed what.

**33. Has a statistician signed off?**
Short: Not yet. The review is assigned to Yao and the open decisions are listed (section 3 below). Until then everything is labelled exploratory.

**34. Is the app public?**
Short: Only say "yes" after someone has opened the public URL in a private window. Until then: "The code is public on GitHub and runs locally with two commands; deployment is to Streamlit Community Cloud."

**35. How would this scale?**
Short: Add variables only after validating each one (POWER has dozens), add Giovanni extractions for more cells (the ingest matches files to locations automatically), widen the map area, and replace the single-server lock with a request queue. Expanding to ice-thickness or station networks would be new science, not just engineering.

**36. What would you do with another month?**
Short: Get the statistical sign-off, test with real users (a teacher and a northern planner), add a MODIS snow or lake-ice variable through AppEEARS so we have an independent satellite source, and run Giovanni extractions for Aklavik.

---

## Part 2. Team teach-back exercise

Run this at least once before judging. One person asks; the answerer may not look at notes; a third person checks against the app. Rotate. Pass mark: correct in substance in under 60 seconds.

1. Click a point on the map. Narrate every step until a number appears, naming the file that does each step.
2. Explain to a 15-year-old what a freezing degree-day is, then compute the FDD for three days at -10, -4 and +2 °C. (Answer: 10 + 4 + 0 = 14 °C-days.)
3. Explain Theil-Sen using five points on a whiteboard. Why is it robust?
4. The app says "+0.54 °C per decade, not resolved". A judge says "so it's not warming". Respond.
5. Why does the 2000 to 2025 Giovanni window show no q-value?
6. What is the difference between the 51-test, 126-test and 27-test families, and which one does the app use for Dettah 2001/02 to 2024/25?
7. Why is agreement between Giovanni and POWER not validation?
8. Name three things Frostline cannot do.
9. NASA is 5.5 °C colder than the station. Why can we still use NASA for trends?
10. What happens in the app if NASA POWER returns a value of -999 for one day in November 1997?
11. Where does the Evidence Brief get its numbers, and why must they match the screen?
12. How would you reproduce the autumn result on a fresh laptop with no internet?

## Part 3. Claims the team cannot currently support

Do not make these claims. Each needs the action listed first.

| Claim | Why it's unsupported | What would make it supportable |
|---|---|---|
| "Frostline is publicly deployed" | No public URL has been opened in a private window | Deploy (see `submission/DEPLOYMENT.md`) and test |
| "NASA confirmed we meet the Global Award resource rule" | No organizer has answered | Ask; record the answer and who gave it |
| "Our statistics have been independently reviewed" | No sign-off is recorded | Yao's review (Part 4) |
| "Warming caused later openings" / "snow causes delays" | Correlation and co-occurrence only | Not achievable with these data |
| "Frostline helps communities keep roads safe" / "has users" | No safety function, no user study, no adoption | User research; never a safety claim |
| "Ground-validated NASA data" | Giovanni versus POWER is the same model; the station disagrees by 5.5 °C | Say "compared with the station, which disagrees by…" |
| "Autumn warming at Yellowknife" (as a local fact) | One reanalysis grid cell, not the town | Say "at the MERRA-2 grid cell containing Dettah" |
| "Aklavik replicates Dettah" | Opposite sign, window-fragile, segment unverified | Route identity check with GNWT |
| Specific personal contributions | Not recorded in the repository | Team states them in `AI_USE_DISCLOSURE.md` |

## Part 4. Findings requiring Yao's independent sign-off

1. **Family choice for Dettah opening day 2001/02 to 2024/25**: 126-test family (q = 0.085, used by the app) versus 27-test road family (q = 0.018).
2. **Giovanni seven-season family**: whether the seven overlapping aggregates are the right family, and whether Benjamini-Hochberg is appropriate given their positive dependence (autumn q = 0.013).
3. **Dettah full-record opening day** (+9.0 days per decade, q = 0.002 in the 51-test family) given the documented selection bias.
4. **Aklavik** open day (q = 0.048) and open-to-close interval (q = 0.020), given window fragility and unverified route identity.
5. **Dependence handling**: lag-1 flag at 0.3 and block bootstrap with block length ceil(n^(1/3)) for n between 24 and 46.
6. **Snow association** (rho +0.64, q = 0.005 in a 5-predictor family) and its "hypothesis" label.
7. **Live exploratory points**: whether showing an unadjusted p beside the "exploratory" label is acceptable, or whether the p-value should be hidden.
