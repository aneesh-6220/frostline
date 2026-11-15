# Frostline: local judging script and demonstration plan

Everything below uses implemented features and numbers the app computes from the approved data. `tests/test_frostline_app.py` checks the figures quoted here against the app. Do not add claims on stage that are not on screen.

## Before you start

- Open the app (hosted URL once deployed, or `streamlit run UI/frostline_app.py`). Use a laptop browser at full width.
- Keep `submission/frostline_slides.pdf` open in another tab as the fallback.
- The app needs no login and no live download. Only the map background uses the internet.

## The eight questions, in about four minutes

| Time | Say | Do |
|---|---|---|
| 0:00 | **The problem.** "People say northern winters are changing. Checking that properly means finding NASA data, cleaning daily records, computing seasonal indicators, fitting trends, finding government road records and deciding what can honestly be concluded." | Observatory is on screen. Point at the live chart. |
| 0:25 | **Why it matters.** "Seasonal roads on frozen lakes and rivers connect northern communities and carry supplies. They exist only while the cold holds." | Click **Begin an Investigation**. Stage 1. |
| 0:45 | **The geography.** "Two documented ice roads in the Northwest Territories, about 1,100 km apart: a 6.5 km lake crossing at Dettah and a delta road of more than 100 km at Aklavik. Dettah also has a year-round road, so this is not its only connection." | Next. Click a marker or a name. |
| 1:10 | **Why NASA data.** "Each point is one winter of NASA POWER daily temperature, which is the MERRA-2 reanalysis. Twenty-four winters, no missing days. It is a grid-cell value, not a thermometer on the ice, and we say so on screen." | Next. Hover a point. |
| 1:35 | **What Frostline does.** "A rate of change per decade, two confidence intervals, a Mann-Kendall test and a correction for the number of tests. Freezing accumulation at Dettah: +15 °C-days per decade, interval -108 to 111. Not statistically distinguishable from no change. That is not proof of no change, and it is still a result." | Next. Read the result card. |
| 2:05 | **What judges can try.** "Change the location, the variable or the period in the sidebar and every number is recomputed. Pick your own period and Frostline drops the adjusted value and labels the result exploratory." | Drag the period slider, then press an **Approved window** button. |
| 2:30 | **What the evidence shows.** "The government record shows the Dettah ice road opening later: +9.0 days per decade over 1993/94 to 2024/25, interval 3.6 to 12.4, and it survives correction across 51 route-level tests. In the NASA-era window alone (2001/02 on) it does not survive correction, so the card calls it fragile. The NASA climate record for the same place shows no resolved trend. We do not say what produced the later openings." | Next. Timeline and evidence conclusion. |
| 3:05 | **What remains uncertain.** "NASA runs 5.5 °C colder than the Yellowknife station in early winter. We show that instead of hiding it. Of 126 trend tests, 20 look significant alone and 0 survive correction. Dettah was chosen after we saw its trend, and we adjust for that." | Next. Evidence Engine cards. Optionally open Evidence, Source disagreement. |
| 3:35 | **Why it is useful.** "Every investigation ends in an Evidence Brief: the question, the data, the trend, the uncertainty, the limits and the file hashes to reproduce it." | Click **Download Evidence Brief (HTML)** and open it. Then **Explore freely**. |

## If a judge asks

- **Is this a road-safety tool?** No. It does not measure ice, assess safety or predict opening dates.
- **Did warming delay the Dettah road?** The evidence does not show what produced the change. Leak-free climate predictors show no association distinguishable from zero in 24 winters; an association with early snow at the airport is a hypothesis, not a mechanism.
- **Which NASA data?** NASA POWER daily, whose meteorology is MERRA-2. POWER is not on the challenge's listed Resources; a Giovanni extraction of MERRA-2 is prepared and has not been obtained. Say exactly that.
- **Has a statistician reviewed it?** Not yet. Results are labelled exploratory until that happens.
- **How was AI used?** See `submission/AI_USE_DISCLOSURE.md`. No number on screen is written by a language model.

## Thirty-second video shot list (to record from the running app; none has been recorded)

1. 0 to 4 s: Observatory hero and live chart.
2. 4 to 9 s: Atlas, click the Aklavik marker; the side panel changes.
3. 9 to 16 s: Trend Detective, Dettah opening day, result card "+9.0 days per decade".
4. 16 to 21 s: drag the period slider; the card turns to "Exploratory window".
5. 21 to 26 s: Evidence Engine cards, then Source disagreement chart.
6. 26 to 30 s: Evidence Brief download and the opened report.

Record real screens only. Do not add narration that goes beyond the script above.

## Fallback materials

`submission/frostline_slides.pdf` (seven slides from real screens), `submission/screenshots/` (thirteen screens) and `submission/sample_evidence_brief_dettah_opening_day.html` (a real exported brief).
