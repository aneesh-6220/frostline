#!/usr/bin/env python3
"""Build data/processed/road_operations.csv from the NWT Table 108 workbook.

Usage: python3 -I scripts/build_road_operations.py <workbook.xlsx> <out.csv>

Rules (see docs/DATA_QUALITY.md):
  * A date field is filled ONLY when both the open and close cells are real
    dates, the open date falls in Oct-Dec of season_start_year or Jan-May of the next
    calendar year, the close date is after the open date, and the close date
    falls in Jan-Jul of season_start_year+1 (see validate_dates).
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


def validate_dates(o, c, y):
    """Return (ok, reason). Opening must fall in Oct-Dec of the season start year y or Jan-May of y+1;
    closing must fall in Jan-Jul of y+1 and after opening. The earlier rule accepted any month in year y
    (e.g. 2023-02-12 for the 2023/24 winter), which let a 413-day 'season' through."""
    od, cd = o.date(), c.date()
    open_ok = (od.year == y and od.month in (10, 11, 12)) or (od.year == y + 1 and od.month in (1, 2, 3, 4, 5))
    close_ok = cd.year == y + 1 and cd.month in (1, 2, 3, 4, 5, 6, 7)
    if not open_ok:
        return False, "opening date outside Oct-Dec of the season start year or Jan-May of the next year"
    if not close_ok:
        return False, "closing date outside Jan-Jul of the year after the season start"
    if not cd > od:
        return False, "closing date not after opening date"
    return True, ""


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
                    ok, why = validate_dates(o, c, y)
                    if ok:
                        status, od, cd = "verified", o.date().isoformat(), c.date().isoformat()
                    else:
                        status = "flagged_inconsistent"
                        note = f"raw open={o.date()} close={c.date()} fails date checks ({why}); excluded, not corrected (suspected source typo; confirm with GNWT)"
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
