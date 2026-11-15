# Judge demo runbook (three minutes)

Operational checklist for the live demo. The narration with timings is `submission/DEMO_SCRIPT.md`; this file is what to do before and during it, and what to do when something fails. Every number shown comes from the running app on the real data.

## Ten minutes before

1. From the repository root: `.venv312/bin/streamlit run UI/frostline_app.py` (or the deployed URL once one exists). Python 3.12, `pip install -r UI/requirements.txt`.
2. Browser full screen, zoom 100% or 110% for the projector. Use the top navigation, not the phone tab bar.
3. Check the sidebar shows `Data digest 7037c7be7383fe25`.
4. Open Atlas once so map tiles are cached (the map background needs internet; markers and the list work without it).
5. Open `submission/frostline_slides.pdf` and `submission/sample_evidence_brief_dettah_opening_day.html` in other tabs as fallbacks.
6. Reset state: reload the page on Observatory.

## The run (about 3:00)

| Time | Screen | Action | Key line |
|---|---|---|---|
| 0:00 | Observatory | Point at the four indicators. | "NASA climate data and 32 winters of government road records, investigated with statistics that say how sure we are." |
| 0:20 | Demo stage 1 | Click **Begin an Investigation**. | The problem: roads exist only while the cold holds. |
| 0:35 | Stage 2 | **Next**. Point at Dettah and Aklavik. | Two real, very different roads; grid cells, no invented road lines. |
| 0:55 | Stage 3 | **Next**. Hover a winter. | NASA POWER daily (MERRA-2 reanalysis), 24 winters, a grid-cell value. |
| 1:15 | Stage 4 | **Next**. Read the card. | Early-winter freezing: +15 °C-days per decade, interval -108 to 111: not resolved, and that is a result. |
| 1:40 | Stage 5 | **Next**. Read the card, including the two caveat lines. | Dettah opens +9.0 days per decade later (1993/94 to 2024/25), survives correction across 51 routes; selection-biased and fragile in the NASA-era window. No cause is claimed. |
| 2:20 | Stage 6 | **Next**. Show the seven evidence cards. | Evidence quality judged dimension by dimension, no single score; NASA runs 5.5 °C colder than the station and we show it. |
| 2:45 | Stage 6 | Click **Download Evidence Brief (HTML)**, open it. | Reproducible: data, trend, uncertainty, limits, file hashes. |
| 3:00 | | Stop, or **Explore freely** if a judge wants to try a period. | |

Each stage opens at its top; if not, scroll up once before speaking.

## If a judge drives

- Change the period with the slider: the card becomes "Exploratory window" and q disappears. Press **Approved window** to return.
- Switch Location to Aklavik: every number changes; Aklavik is "a different setting", never a replication.

## If something fails

| Symptom | Recovery |
|---|---|
| Red "Frostline cannot start: required data file ..." | The data are missing or altered; nothing is shown by design. Switch to the slides PDF; afterwards run `python3 -I scripts/regenerate_all.py`. |
| Map background blank | No internet. Use the location buttons; say "the map background is optional". |
| App will not start | Show slides PDF and the sample brief HTML. |
| Download does nothing | Open `submission/sample_evidence_brief_dettah_opening_day.html` (same generator). |

## Never say

Safe or unsafe, predicted opening, usable days, "caused by warming", "NASA confirmed", "eligibility confirmed", "reviewed by a statistician", or any Giovanni result. Say instead: "the evidence does not show what produced the change", and "Giovanni extraction is prepared but not yet done".
