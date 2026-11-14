# Geographic scope

Status: decision made. Verified items are marked VERIFIED; items needing a quick check are marked CHECK.

## Selected route
- **Primary: Dettah Ice Road (Yellowknife to Dettah, across Yellowknife Bay, Great Slave Lake), road_id `dettah`.**
- Official record name in the workbook: "Dettah Ice Road" (sheet "Ice Roads", NWT Bureau of Statistics Table 108).
- Road type: **ice road over a lake** (not a land winter road, not a river crossing, not a mining road).
- Communities served: Dettah and Ndilo (Yellowknives Dene First Nation) and Yellowknife. About 6 to 6.5 km; it shortens the trip around the bay by roughly 15 to 20 minutes (Cabin Radio, NNSL).
- Important context: an all-season road also connects the two places, so this road is a convenience and cultural-access route, not a sole lifeline. State this on the website; it is a limitation, not a flaw in the science.

## Why it was chosen (from our own audit, `scripts/build_road_operations.py`)
- 32 of 32 winters (1993/94 to 2024/25) have a valid opening and closing date. No missing entries and no flagged rows.
- It is an ice road built on lake ice, so freezing conditions matter more directly than for a land road.
- The NWT record matches independent news reports for the dates we checked: opened 2019-01-11 and 2020-01-11 (CBC), 2024/25 opened 2024-12-21 and closed 2025-04-08 (Cabin Radio), 2000-01-11 as a past record (CBC). One 1-day difference: workbook says 2024-01-28 opening, Cabin Radio says January 29 (CHECK; leave the workbook value as authoritative and note the difference).
- Next to Yellowknife A, a long-running Environment and Climate Change Canada station, about 6 km from the route midpoint (calculated), which gives us a real validation option.
- Clear trend in our data: opening about **9 days later per decade** (95% CI about 3.6 to 12.4, Mann-Kendall p = 0.0003); open-to-close interval about **10 days shorter per decade** (CI about -15.8 to -5.3, p = 0.0007). These are exploratory descriptive results, not conclusions (see SCIENTIFIC_METHODS.md).

## Chosen analysis period
- **Road records:** 1993/94 to 2024/25 (season_start_year 1993 to 2024), 32 winters.
- **NASA daily temperature (per the handoff):** winters 2001/02 to 2024/25 (season_start_year 2001 to 2024, 24 winters), Oct 1 2001 to Mar 31 2025. If a consistent longer record is available from the SAME product, use 1993 to 2024 so that it matches the road records; do not mix products.
- Season definition: winter y runs Oct 1 of y to Mar 31 of y+1; 2024/25 has season_start_year 2024.

## Temperature sampling locations
| location_id | Role | Latitude | Longitude | What it represents |
|---|---|---|---|---|
| `dettah_bay` | Primary | 62.43 | -114.34 | Midpoint of the Dettah ice road across Yellowknife Bay (calculated from the two ends). |
| `aklavik_delta` | Comparison | 68.29 | -134.37 | Midpoint between Aklavik and Inuvik in the Mackenzie Delta, for the Aklavik (Inuvik-Aklavik) ice road. |

Coordinate sources: Dettah 62.4111 N, 114.3083 W (Wikipedia, citing Statistics Canada); Aklavik 68.2203 N, 135.0117 W (Wikipedia), also 68 13' N, 135 00' W (NWT Bureau of Statistics); Yellowknife A station 62.463 N, 114.440 W, Climate ID 2204101 (Environment Canada API record) and WMO 71936. Inuvik is about 68.36 N, 133.73 W (CHECK against an official source). Midpoints are our calculation.

### Grid-cell note (important)
MERRA-2 and NASA POWER temperatures are about 0.5 x 0.625 degree (roughly 55 km x 25 km at this latitude) grid-cell values. Yellowknife, Dettah, the route midpoint and the station all fall in the same cell. A second sampling point near Dettah would be a duplicate, so the "second point" is the Aklavik delta corridor, about 1,100 km away.
Do not describe a temperature value for a cell as the temperature along every kilometre of the road, or on the ice surface.

## Location-to-road mapping
- `dettah_bay` is used for road `dettah`.
- `aklavik_delta` is used for road `aklavik`.
- Never use a temperature from one location with the road dates of the other, and never use any Ontario location with NWT roads.

## Known geographic and operational limitations
- Road opening depends on lake-ice thickness (the road opens at about 34 to 36 cm, per NNSL quoting the territorial department), snow cover that insulates the ice, overflow, construction crews and administrative decisions. Air temperature is only one input.
- The records are opening and closing dates, not usable days: temporary closures are not recorded in the workbook (CHECK with the Department of Infrastructure if needed). Open-to-close days must not be called "usable days".
- 32 winters is a short record for climate trends. Natural variability can look like a trend.
- NASA grid cells are large, and POWER and MERRA-2 are not independent (POWER's temperature comes from MERRA-2-derived inputs).
- The Dettah road is short and lake-based; results do not automatically apply to land winter roads or other lakes.
- The Aklavik comparison is a delta ice road, over river channels; its geography is different, so the comparison is "different setting", not "the same thing twice".
- The workbook ends at 2024/25. News reports describe a 2025/26 season (opened about December 22, 2025; expected to close April 24, 2026), but that is not in the official workbook and is NOT included.

## Why alternatives were rejected
| Candidate | Decision | Reason |
|---|---|---|
| Wrigley to Tulita winter road | Not primary | Land winter road, 32 seasons and a strong lengthening trend, but construction methods, snow management and rules can change the season independently of climate. Kept as a possible third case. |
| Tulita to Norman Wells, Norman Wells to Fort Good Hope, Deline, Sambaa K'e, Nahanni Butte | Not primary | Same reasoning as above; more corridors would dilute the story. Fort Good Hope has one inconsistent row excluded (1994/95). |
| Colville Lake winter road | Rejected | 25 seasons only; early years missing ("..") . |
| Whati winter road | Rejected | 28 seasons; replaced by the all-season Tlicho Highway on 2021-11-30 (workbook note "**"), so the record definition changed. |
| Wekweeti winter road | Rejected | Only 15 seasons (2010/11 onward). |
| Gameti winter road | Not primary | 32 seasons but no clear trend; little contrast with the primary. |
| Liard, Mackenzie (Tsiighetchic, Camsell Bend), Peel crossings | Rejected | River ice crossings with short operating windows and different physics; Peel has one inconsistent row (2006/07). |
| Tibbitt-Contwoyto winter road | Rejected | Private mining road; the operator controls timing and loads; not community-serving. |
| James Bay Winter Road (Ontario) | Not needed | Fallback only if no NWT route works; NWT was usable. |
