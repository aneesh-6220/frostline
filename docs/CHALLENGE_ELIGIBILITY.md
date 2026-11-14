# Challenge eligibility check: "Be An Earth System Trend Detective!"

Checked 2026-11-14 on the live official pages (opened in a browser; the site is client-rendered so the text was extracted from the page data).
Page: https://www.spaceappschallenge.org/2026/challenges/earth-system-trend-detective/ (category Advanced; skills Earth Science, Software; last published 2026-11-13).
FAQ: https://www.spaceappschallenge.org/resources/participant-faqs/

## What the challenge asks (paraphrased)
Build a tool that lets a user pick Earth science variables from missions or models, shows how they change over time in a chosen region, and says what is changing, where, by how much, and whether the change is statistically significant. The objectives list four elements: choose variables, acquire them for a region, generate and visualize a time series long enough for statistics, and perform a basic analysis giving a rate of change with a significance test (the page names a t-test, the Mann-Kendall test, or confidence intervals). Linear trends are described as a good start; seasonal-cycle removal and non-linear trends are explicitly beyond the intended scope. Likely audience: high-school and college students and the public with some science background. Suggested but optional: simple variable definitions, a short question flow, a couple of demonstration examples, and use of daily or monthly data. Finding a trend that is not significant is described as still interesting.

## Resources tab (verbatim list of titles)
NASA data and resources: Giovanni; Hydrology Time Series (GES DISC); AppEEARS; NOAA Climate Data Online; a SeaWiFS chlorophyll time-series paper (NTRS 20090042747). Space Agency Partner resources: KNMI Climate Explorer; two trend-statistics articles (Medium; Statsig); Canadian Space Agency: RADARSAT Constellation Mission data, Geo.ca, SWOT mission page, a CSA ecosystem-monitoring page, a SAR Python tutorial. The page states NASA does not endorse non-US-Government sites and participants must follow each site's data-use terms, and that more resources may be added.

The Background text names MERRA-2 and GLDAS as example models and MODIS, OMI, AIRS and GPM as example instruments.

## Findings for NorthLink

| Question | Answer | Status |
|---|---|---|
| Does the page require use of a specific dataset? | No requirement found in the challenge text or Resources tab. | VERIFIED (absence in the page text read) |
| Is NASA POWER T2M acceptable? | POWER is not on the Resources list. T2M is a MERRA-2 variable (an Earth science model product the Background names). Acceptable on the page's own wording ("variables ... produced by Earth science models"), but not confirmed by an organizer or local judge. | PLAUSIBLE, not confirmed |
| Are non-NASA data allowed (ECCC stations, NWT road records)? | Nothing in the pages read forbids them; NOAA and CSA sources are listed. Terms of each source must be followed. | NOT FORBIDDEN, not confirmed |
| Fit to the brief | The brief describes a general variable-and-region selection tool. NorthLink as built is a case study of one road corridor family with a fixed variable set. This may score lower on generality than a variable picker, and there is a challenge-specific risk that a winter-road narrative is read as off-scope. This is an assessment, not a rule. | RISK (judgment) |
| Statistical expectation | A trend with rate and a significance test (Mann-Kendall, CI) is exactly what is asked; the repo implements Theil-Sen, Mann-Kendall and CIs. Multiple-comparison and leakage controls go beyond the stated scope. | MATCH |
| Project submission | Submit through the team project page on spaceappschallenge.org; the Project Submission Guide was due on 2026-11-13 and has not been read here. | UNVERIFIED (guide not read) |
| AI ("Super Intelligence") use | Allowed; the submission must describe how such tools were used during development. NorthLink code and docs were produced with AI assistance and this must be disclosed in the submission. | VERIFIED (FAQ) |
| Team rules | Teams of 1 to 6 for Local Events; one team, one challenge. Local event date, time and judging format (Halifax, Sun 2026-11-15 3 PM) come from the team brief and were not re-verified on the Local Events page. | PARTLY VERIFIED |

## MERRA-2 / Giovanni direct extraction: UNVERIFIED
An independent extraction from Giovanni was attempted through the browser and not completed: the tool needs an Earthdata login for full access, which cannot be entered here. POWER and MERRA-2 are not independent, so a Giovanni pull would verify provenance (that POWER T2M equals the MERRA-2 product at the same cell), not add independent data.
Manual steps for a team member with an Earthdata account:
1. Open https://giovanni.gsfc.nasa.gov/giovanni/ and log in.
2. Plot type "Time Series, Area-Averaged"; date range 2001-10-01 to 2025-06-30 (UTC).
3. Region: point box at 62.4 N, -114.375 W (the cell centre is 62.5 N, -114.375 W; confirm the cell used by POWER, whose header reports the average elevation 204.71 m for the region).
4. Variable: MERRA-2 "2-meter air temperature" (M2T1NXSLV hourly or M2SDNXSLV daily; confirm the exact collection name in the picker, it was not confirmed here).
5. Download the CSV. Compare daily means to `data/raw/nasa/power_daily_T2M_dettah_bay.csv`. Note that Giovanni daily averaging is in UTC; POWER's header says LST.
Until done, treat "POWER T2M equals MERRA-2 T2M" as the provider's statement, not our verification.
