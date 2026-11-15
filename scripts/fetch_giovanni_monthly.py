#!/usr/bin/env python3
"""Fetch the MERRA-2 monthly 2 m temperature series for the two study points from NASA Giovanni (a listed challenge resource).

Needs an Earthdata Login token (free; https://urs.earthdata.nasa.gov/ -> Generate Token) in the environment variable
EARTHDATA_TOKEN or in a git-ignored .env file at the repository root. The token is sent only to the Giovanni API host and is
never written to disk or printed.

The response is saved VERBATIM to data/raw/nasa/giovanni/giovanni_M2TMNXSLV_T2M_<location_id>.csv. This script adds no header
and changes no value, so scripts/ingest_giovanni_monthly.py still decides on its own whether the file names collection
M2TMNXSLV and variable T2M; if the service response does not, ingest refuses it and the manual Giovanni web route in
docs/CHALLENGE_ELIGIBILITY.md applies. A provenance sidecar (request URL without the token, UTC time, HTTP status, SHA-256)
is written next to each file.

Status: written during the global audit (2026-11-15). The endpoint was confirmed to exist (it answers 401 "Bad or missing
token" without credentials); a successful authenticated download has NOT been run by the auditor, who holds no credentials.

Usage:  python3 -I scripts/fetch_giovanni_monthly.py [--dry-run]
Then:   update tests/raw_checksums.sha256 and run python3 -I scripts/regenerate_all.py (steps 8-10 in CHALLENGE_ELIGIBILITY.md).
"""
import argparse
import datetime as dt
import hashlib
import json
import os
import sys
import urllib.parse
import urllib.request

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
API = "https://api.giovanni.earthdata.nasa.gov/timeseries"
DATA_ID = "M2TMNXSLV_5_12_4_T2M"            # MERRA-2 tavgM_2d_slv_Nx (M2TMNXSLV) v5.12.4, variable T2M (K)
TIME = "2001-10-01T00:00:00/2025-06-30T23:59:59"
POINTS = {"dettah_bay": (62.43, -114.34), "aklavik_delta": (68.29, -134.37)}   # the same points used for NASA POWER
OUT = os.path.join(ROOT, "data", "raw", "nasa", "giovanni")


def token() -> str:
    t = os.environ.get("EARTHDATA_TOKEN", "").strip()
    env = os.path.join(ROOT, ".env")
    if not t and os.path.isfile(env):
        for line in open(env, encoding="utf-8"):
            k, _, v = line.partition("=")
            if k.strip() == "EARTHDATA_TOKEN":
                t = v.strip().strip('"').strip("'")
    return t


def url_for(lat: float, lon: float) -> str:
    return API + "?" + urllib.parse.urlencode({"data": DATA_ID, "location": f"[{lat},{lon}]", "time": TIME})


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="print the requests without sending them")
    a = ap.parse_args()
    if a.dry_run:
        for lid, (lat, lon) in POINTS.items():
            print(lid, url_for(lat, lon))
        return 0
    tok = token()
    if not tok:
        print("EARTHDATA_TOKEN is not set (environment or .env). Nothing was fetched.", file=sys.stderr)
        return 2
    os.makedirs(OUT, exist_ok=True)
    for lid, (lat, lon) in POINTS.items():
        url = url_for(lat, lon)
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {tok}"})
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                body, status = r.read(), r.status
        except urllib.error.HTTPError as e:
            print(f"{lid}: HTTP {e.code} from Giovanni; nothing written. Response: {e.read()[:300]!r}", file=sys.stderr)
            return 1
        if status != 200 or not body.strip():
            print(f"{lid}: HTTP {status} with an empty body; nothing written.", file=sys.stderr)
            return 1
        path = os.path.join(OUT, f"giovanni_M2TMNXSLV_T2M_{lid}.csv")
        with open(path, "wb") as fh:
            fh.write(body)                       # verbatim; no header added, no value changed
        meta = dict(request_url=url, data_id=DATA_ID, point=[lat, lon], retrieved_utc=dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                    http_status=status, sha256=hashlib.sha256(body).hexdigest(), bytes=len(body))
        with open(path + ".provenance.json", "w", encoding="utf-8") as fh:
            json.dump(meta, fh, indent=2)
        print(f"{lid}: wrote {path} ({len(body)} bytes)")
    print("Next: update tests/raw_checksums.sha256, run python3 -I scripts/regenerate_all.py, then record the dataset header in docs/CHALLENGE_ELIGIBILITY.md.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
