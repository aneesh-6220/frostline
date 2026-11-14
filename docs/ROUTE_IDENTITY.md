# Route identity, sampling points and record semantics

Status legend: VERIFIED (checked against a named source in this review, 2026-11-14), SECONDARY (press or reference pages quoting GNWT records), UNVERIFIED.
The primary record is NWT Bureau of Statistics Table 108 (source: GNWT Department of Infrastructure), workbook `data/raw/roads/NWT_Table108_...xlsx`.

## Dettah (`road_id` dettah, sampling point `dettah_bay`)

| Item | Finding | Status |
|---|---|---|
| Official record name | "Dettah Ice Road", sheet "Ice Roads", 32 winters 1993/94 to 2024/25, no missing or flagged rows | VERIFIED from workbook |
| What it is | A 6.5 km seasonal ice road across Yellowknife Bay (north arm of Great Slave Lake) between Yellowknife (Rotary Park end) and Dettah. GNWT communications in 2025 also call it the "Dettah ice crossing". It is a single short crossing, not a road network and not a river crossing. | SECONDARY (NNSL, Cabin Radio, CBC; Wikipedia gives 6.5 km) |
| Alternative | A 27 km all-season road via the Ingraham Trail connects the same places, so the ice road saves about 15 to 20 minutes and is not a sole lifeline | SECONDARY (Wikipedia, Cabin Radio) |
| Community coordinates | Dettah 62.41111 N, 114.30833 W (Wikipedia); Yellowknife-side Rotary Park end about 62.454 N, 114.369 W (Environment Canada forecast point, approximate) | VERIFIED (Dettah), approximate (Yellowknife end) |
| Sampling point | `dettah_bay` 62.43 N, -114.34 W is our calculated midpoint of the two ends. It is a point on or near the crossing, not a measurement location. POWER reports the cell-average elevation as 204.71 m. | calculated |
| NASA cell | Dettah, Yellowknife, the midpoint and the ECCC station are all in the same MERRA-2 0.5 x 0.625 degree cell (lat index 305, lon index 105) | calculated |
| Station | ECCC Yellowknife A, 62.463 N, 114.440 W (ECCC API record for station 51058), elevation 205.7 m, WMO 71936, Climate ID 2204100/2204101; station IDs 1706 (to 2012) and 51058 (from 2013). About 6.3 km from the sampling point | VERIFIED (coordinates, elevation, IDs) |
| Definition of "open" | Opening is to light vehicles (under 5,000 kg) first, after ice about 34 to 36 cm thick; heavier loads follow later. Opening is therefore not "full usable" status. Closing is a government decision, and the workbook does not record temporary closures. | SECONDARY (NNSL quoting the Department; Cabin Radio, CBC) |
| Agreement with press | Workbook values match published GNWT-sourced statements: opened 2019-01-11 and 2020-01-11 (the joint latest on record), 2024-12-21 (earliest since 2014-12-19), 2024-01-28 opening (construction began Jan 25, "latest on record" then). One day difference reported earlier for 2024-01-28 vs Jan 29 is unresolved; workbook value kept. | SECONDARY |
| Reporting changes | None found for 1993 to 2024. Not proven absent. Operational factors (overflow at the Yellowknife end, construction crew timing, snow clearing) affect the opening date independent of climate. | UNVERIFIED |

## Aklavik (`road_id` aklavik, sampling point `aklavik_delta`)

| Item | Finding | Status |
|---|---|---|
| Official record name | "Aklavik Ice Road", sheet "Ice Roads", 32 winters, no missing or flagged rows | VERIFIED from workbook |
| What it is | The seasonal ice road between Aklavik (Peel River, Mackenzie Delta) and Inuvik, through channels of the delta. Length is reported inconsistently: 112 km (Town of Inuvik), 116 km (Wikipedia road list), 117 km (Spectacular NWT). A GNWT construction contract describes the Aklavik part as 85 km from Aklavik to the Aklavik/Tuktoyaktuk junction ice road (the rest was shared with the Inuvik to Tuktoyaktuk ice road, closed after the highway opened in 2017). The exact alignment and which segment the workbook dates describe are **ambiguous**. | SECONDARY; length and segment UNRESOLVED |
| Straight-line distance | Aklavik to Inuvik is about 55 to 63 km straight; the road is roughly twice that because it follows the delta channels | SECONDARY |
| Coordinates | Aklavik 68.22028 N, 135.01167 W; Inuvik 68.36083 N, 133.72972 W (Wikipedia) | VERIFIED |
| Sampling point | `aklavik_delta` 68.29 N, -134.37 W is the straight-line midpoint of Aklavik and Inuvik. The real road does not follow a straight line, so the point may lie off the alignment. Whether this cell represents the whole road is not verified. | calculated; representativeness UNVERIFIED |
| Station | ECCC Aklavik A (1623 to 2014, 52962 from 2018) and Inuvik (41883 Climate, 51477 Inuvik A from 2018, plus 1669, 31470): Aklavik A is at the west end, Inuvik at the east end; no station sits at the midpoint | partly verified |
| Agreement with press | 2023/24 opened 2024-01-12, the first January opening since 2006 (our 2005 winter, 2006-01-13); 1997/98 opened Jan 26 (our 1997 value); 2023 delay attributed by the Department to heavy snow insulating the ice (Inuvik snow on ground at a record for December). | SECONDARY |
| Definition of "open" | Opened by the Department once construction is complete and ice is safe; 20-year average Dec 21 open, Apr 28 close (Town of Inuvik, Mar 2022). A sudden mid-season closure after a crack was reported by CBC (year not confirmed here); such closures are not recorded in the workbook. | SECONDARY |

## Consequences for analysis (enforced in `docs/SCIENTIFIC_METHODS.md`)

1. A Dettah and Aklavik comparison is a comparison of a 6.5 km lake crossing with weight classes against a roughly 112 to 117 km delta road with a different construction regime. It is a "different setting" contrast, not a replication. Differences between the two in road dates must not be attributed to climate.
2. Climate comparison between the two cells (regional_comparison.csv) is allowed only as a comparison of the two NASA cells' climate series, with the bias caveat in `TEMPERATURE_BIAS_DIAGNOSIS.md`. It must not be described as road-condition evidence.
3. Interval (closing date minus opening date) is not the number of usable days.
4. For any route not Dettah or Aklavik, identity is limited to the workbook name; sampling coordinates are approximate points chosen by the team and not verified as on the road (see `GEOGRAPHIC_SCOPE.md`).

Sources consulted (2026-11-14): GNWT Table 108 workbook (statsnwt.ca node 1073); NNSL Yellowknifer reports on the Dettah ice road; Cabin Radio reports (Dettah 2024/25 and 2025/26, Aklavik 2023/24); CBC North (Dettah late openings); Spectacular NWT; Town of Inuvik highway information (Mar 2022); GNWT contract record CT100968 and CT101502 (opennwt.ca); Wikipedia (Dettah, Inuvik, Aklavik, NWT highways list); ECCC api.weather.gc.ca station 51058 record.
