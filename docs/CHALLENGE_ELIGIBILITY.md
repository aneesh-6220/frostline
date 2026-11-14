# Challenge eligibility check: "Be An Earth System Trend Detective!"

Checked 2026-11-14 on the live official pages (opened in a browser; the site is client-rendered so the text was extracted from the page data).
Page: https://www.spaceappschallenge.org/2026/challenges/earth-system-trend-detective/ (category Advanced; skills Earth Science, Software; last published 2026-11-13).
FAQ: https://www.spaceappschallenge.org/resources/participant-faqs/

## What the challenge asks (paraphrased)
Build a tool that lets a user pick Earth science variables from missions or models, shows how they change over time in a chosen region, and says what is changing, where, by how much, and whether the change is statistically significant. The objectives list four elements: choose variables, acquire them for a region, generate and visualize a time series long enough for statistics, and perform a basic analysis giving a rate of change with a significance test (the page names a t-test, the Mann-Kendall test, or confidence intervals). Linear trends are described as a good start; seasonal-cycle removal and non-linear trends are explicitly beyond the intended scope. Likely audience: high-school and college students and the public with some science background. Suggested but optional: simple variable definitions, a short question flow, a couple of demonstration examples, and use of daily or monthly data. Finding a trend that is not significant is described as still interesting.

## Resources tab (verbatim list of titles)
NASA data and resources: Giovanni; Hydrology Time Series (GES DISC); AppEEARS; NOAA Climate Data Online; a SeaWiFS chlorophyll time-series paper (NTRS 20090042747). Space Agency Partner resources: KNMI Climate Explorer; two trend-statistics articles (Medium; Statsig); Canadian Space Agency: RADARSAT Constellation Mission data, Geo.ca, SWOT mission page, a CSA ecosystem-monitoring page, a SAR Python tutorial. The page states NASA does not endorse non-US-Government sites and participants must follow each site's data-use terms, and that more resources may be added.

The Background text names MERRA-2 and GLDAS as example models and MODIS, OMI, AIRS and GPM as example instruments.

## Findings for Frostline

| Question | Answer | Status |
|---|---|---|
| Does the page require use of a specific dataset? | No requirement found in the challenge text or Resources tab. | VERIFIED (absence in the page text read) |
| Is NASA POWER T2M acceptable? | POWER is not on the Resources list. T2M is a MERRA-2 variable (an Earth science model product the Background names). Acceptable on the page's own wording ("variables ... produced by Earth science models"), but not confirmed by an organizer or local judge. | PLAUSIBLE, not confirmed |
| Are non-NASA data allowed (ECCC stations, NWT road records)? | Nothing in the pages read forbids them; NOAA and CSA sources are listed. Terms of each source must be followed. | NOT FORBIDDEN, not confirmed |
| Fit to the brief | The brief describes a general variable-and-region selection tool. Frostline as built is a case study of one road corridor family with a fixed variable set. This may score lower on generality than a variable picker, and there is a challenge-specific risk that a winter-road narrative is read as off-scope. This is an assessment, not a rule. | RISK (judgment) |
| Statistical expectation | A trend with rate and a significance test (Mann-Kendall, CI) is exactly what is asked; the repo implements Theil-Sen, Mann-Kendall and CIs. Multiple-comparison and leakage controls go beyond the stated scope. | MATCH |
| Project submission | Submit through the team project page on spaceappschallenge.org; the Project Submission Guide was due on 2026-11-13 and has not been read here. | UNVERIFIED (guide not read) |
| AI ("Super Intelligence") use | Allowed; the submission must describe how such tools were used during development. Frostline code and docs were produced with AI assistance and this must be disclosed in the submission. | VERIFIED (FAQ) |
| Team rules | Teams of 1 to 6 for Local Events; one team, one challenge. Local event date, time and judging format (Halifax, Sun 2026-11-15 3 PM) come from the team brief and were not re-verified on the Local Events page. | PARTLY VERIFIED |

## NASA Global Award resource requirement: NOT YET DEMONSTRATED (updated 2026-11-14 evening)

The team supplied the official Resources list (it matches the verbatim list above). The Global Award guidance, as relayed by the team, requires meaningful use of at least one NASA data source from the chosen challenge's Resources. The NASA-listed sources are Giovanni, Hydrology Time Series (GES DISC), AppEEARS and NOAA Climate Data Online (the last is NOAA, not NASA). The challenge text also names MERRA-2 as a suitable model.

| Question | Finding | Status |
|---|---|---|
| Does our current data path use a listed NASA source? | No. The temperatures come from NASA POWER, which is not on the list. POWER's meteorology is MERRA-2, a product that Giovanni also serves, but our files were not obtained through Giovanni, so the listed-source requirement is **not demonstrated**. This repository must not describe it as met. | NOT DEMONSTRATED |
| Is POWER/MERRA-2 scientifically appropriate for the challenge? | Yes on the challenge's own wording (model variables are allowed). This is separate from the Global Award rule. | PLAUSIBLE |
| Giovanni extraction (this review) | Attempted. The Giovanni page loads, but Earthdata Login is required to plot or download and no signed-in session exists in the review browser. Credentials must not be entered by an assistant. No data were obtained. | BLOCKED, owner Cason |
| Hydrology Time Series (Data Rods) | The legacy endpoint redirected to a GES DISC notice titled "The Hydrology Data Rods service will be discontinued no earlier than October 31, 2025 and transitioned to a new data access method". No data were obtained; do not plan on it. | NOT USABLE as tested |
| AppEEARS | Not attempted (needs the same Earthdata login). It serves MODIS products, which are a NASA instrument family the challenge names. A point sample of a MODIS snow or land-surface-temperature product would be a second eligible route. The existing Planetary Computer script (`docs/PLANETARY_COMPUTER_TODO.md`) uses the same MODIS products but is not itself a listed resource. | NOT ATTEMPTED |
| Organizer view | Whether POWER counts toward the Global Award requirement has not been asked. | ASK at the Halifax event |

Do not delay application development on this. The app, the findings and the statistics do not depend on it.

### What a Giovanni extraction would and would not add
POWER and Giovanni MERRA-2 are not independent datasets. A Giovanni pull is useful because (a) it uses a listed NASA tool on a model the challenge names, and (b) it verifies that POWER T2M equals the MERRA-2 product at the same cell (`giovanni_vs_power_check.csv`). Monthly means are used **only** for seasonal and annual mean-temperature trends. They never replace daily values: FDD, thaw days and road-date metrics stay on the POWER daily series (`docs/SCIENTIFIC_METHODS.md`). Expect the Giovanni monthly trends to resemble the POWER ones; that is a consistency check, not a new finding.

### Manual action for Cason (about 30 minutes, needs an Earthdata login, which is free)
1. Open https://giovanni.gsfc.nasa.gov/giovanni/ and log in.
2. Plot type **Time Series, Area-Averaged** (a point is acceptable; Giovanni returns the cell containing it).
3. Dates 2001-10-01 to 2025-06-30 (UTC).
4. Variable: MERRA-2 monthly mean "2-meter air temperature", collection **M2TMNXSLV** (MERRA-2 tavgM_2d_slv_Nx), variable **T2M**. Confirm the collection short name and version in the variable picker and record them.
5. Location: lat 62.43, lon -114.34 (the same point used for POWER, in MERRA-2 cell centre 62.5 N, -114.375 W). Repeat for lat 68.29, lon -134.37 for Aklavik.
6. Download the data as CSV. Keep the header lines: the ingest script refuses a file whose header does not name M2TMNXSLV and T2M.
7. Save as `data/raw/nasa/giovanni/giovanni_M2TMNXSLV_T2M_dettah_bay.csv` and `..._aklavik_delta.csv`. Do not edit the files.
8. Add the files to the checksum manifest: from `data/raw` run `find . -type f | sort | xargs sha256sum > ../../tests/raw_checksums.sha256`, then check the diff only adds the new files.
9. Run `python3 -I scripts/regenerate_all.py`. It ingests the files (`scripts/ingest_giovanni_monthly.py`) and writes `giovanni_monthly_t2m_seasonal.csv`, `giovanni_monthly_t2m_trends.csv` and `giovanni_vs_power_check.csv` to `data/processed/` and `UI/data_real/`.
10. Record in this file the exact dataset identifier, version, variable, coordinates, units, period and access date shown in the Giovanni header, and change the table above only for what was actually demonstrated.
Until step 9 succeeds, no document, slide or submission text may claim a Giovanni extraction or that the NASA-resource requirement is met. The ingest script is tested only on a synthetic fixture created in a temporary folder, never in `data/`.
