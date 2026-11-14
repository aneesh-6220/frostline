#!/usr/bin/env python3
"""Build data/processed/road_operations.csv from the NWT Table 108 workbook.

Usage: python3 -I scripts/build_road_operations.py <workbook.xlsx> <out.csv>

Rules (see docs/DATA_QUALITY.md):
  * A date field is filled ONLY when both the open and close cells are real
    dates, the open date falls in season_start_year (Oct-Dec) or the next
    calendar year (Jan-Jun), the close date is after the open date, and the
    close date falls within season_start_year+1 (or the same year for a
    season that closes in Dec, which does not occur in this workbook).
  * '..'  -> record_status = missing_not_available   (no dates)
  * '**'  -> record_status = not_applicable_note      (no dates; see note)
  * real dates that fail the checks -> record_status = flagged_inconsistent (no dates)
  * season_start_year is the year containing the preceding October (2024/25 -> 2024).
"""
import csv
import datetime as dt
import re
import sys
import warnings

warnings.filterwarnings("ignore")
import openpyxl

SOURCE_URL = "https://www.statsnwt.ca/en/node/1073"

ROAD_IDS = {
    "Wrigley to Tulita Winter Road": ("wrigley_tulita", "winter_road"),
    "Tulita to Norman Wells Winter Road": ("tulita_norman_wells", "winter_road"),
    "Norman Wells to Fort Good Hope Winter Road": ("norman_wells_fort_good_hope", "winter_road"),
    "Colville Lake Winter Road": ("colville_lake", "winter_road"),
    "Délįne Winter Road": ("deline", "winter_road"),
    "Sambaa K'e Winter Road": ("sambaa_ke", "winter_road"),
    "Nahanni Butte Winter Road": ("nahanni_butte", "winter_road"),
    "Wekweètì Winter Road": ("wekweeti", "winter_road"),
    "Whatì Winter Road": ("whati", "winter_road"),
    "Gamètì Winter Road": ("gameti", "winter_road"),
    "Aklavik Ice Road": ("aklavik", "ice_road"),
    "Dettah Ice Road": ("dettah", "ice_road"),
    "Liard River Crossing at Fort Simpson": ("liard_fort_simpson", "ice_crossing"),
    "Mackenzie River Crossing at Tsiighetchic": ("mackenzie_tsiighetchic", "ice_crossing"),
    "Peel River Crossing": ("peel_river", "ice_crossing"),
    "Mackenzie River Crossing at Camsell Bend": ("mackenzie_camsell_bend", "ice_crossing"),
    "Tibbitt-Contwoyto Winter Road": ("tibbitt_contwoyto", "mining_road"),
}


def clean(name):
    name = " ".join(name.split())
    name = re.sub(r"\s*\(Highway #1\)", "", name)
    return name


def main(xlsx, out):
    wb = openpyxl.load_workbook(xlsx, data_only=True)
    rows = []
    for ws in wb:
        names = {}
        for r in ws.iter_rows(values_only=True):
            r = list(r) + [None] * 40
            if r[0] is None and any(isinstance(v, str) and v.strip() for v in r[2:]):
                names = {j: clean(v) for j, v in enumerate(r) if isinstance(v, str) and v.strip()}
                continue
            if not (isinstance(r[0], str) and re.fullmatch(r"\d{4}/\d{2}", r[0].strip())):
                continue
            y = int(r[0][:4])
            for j, n in names.items():
                rid, rtype = ROAD_IDS[n]
                o, c = r[j], r[j + 1]
                status, od, cd, note = "", "", "", ""
                if isinstance(o, dt.datetime) and isinstance(c, dt.datetime):
                    ok = (o.year in (y, y + 1)) and (c.year == y + 1) and (c > o) and (o.month in (10, 11, 12, 1, 2, 3, 4))
                    if ok:
                        status, od, cd = "verified", o.date().isoformat(), c.date().isoformat()
                    else:
                        status = "flagged_inconsistent"
                        note = f"raw open={o.date()} close={c.date()} fails date checks; excluded"
                elif o == ".." or c == "..":
                    status, note = "missing_not_available", "workbook marks '..' (data not available)"
                elif o == "**" or c == "**":
                    status = "not_applicable_note"
                    note = "workbook marks '**': Tlicho Highway (Hwy 9) to Whati opened 2021-11-30; ice/winter road no longer the record"
                else:
                    status, note = "unknown_entry", f"raw open={o!r} close={c!r}"
                rows.append([rid, y, od, cd, status, SOURCE_URL, rtype, n, ws.title, note])
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["road_id", "season_start_year", "opening_date", "closing_date", "record_status",
                    "source_url", "road_type", "road_name", "source_sheet", "record_note"])
        w.writerows(rows)
    print(f"wrote {len(rows)} rows to {out}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
