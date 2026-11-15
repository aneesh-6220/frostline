"""Live NASA POWER adapter: daily point data from the documented POWER Daily API, validated and cached.

Endpoint: https://power.larc.nasa.gov/api/temporal/daily/point (https://power.larc.nasa.gov/docs/services/api/temporal/daily/).
No API key is needed or used. Requests are cached (memory and disk) by their canonical parameters, and live calls from one
process are spaced at least MIN_INTERVAL_S apart, following POWER's guidance to avoid repeated identical requests.

Only one variable is exposed, deliberately: T2M (daily mean air temperature at 2 m, degrees Celsius), the variable the
Frostline analysis engine was validated on. Other POWER parameters are not offered until they are validated.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import os
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

ENDPOINT = "https://power.larc.nasa.gov/api/temporal/daily/point"
DOCS_URL = "https://power.larc.nasa.gov/docs/services/api/temporal/daily/"
COMMUNITY = "SB"            # the community used for the curated Frostline downloads (T2M is identical across communities)
PARAMETERS = {"T2M": dict(label="Daily mean air temperature at 2 m", unit="C", source="MERRA-2")}
FIRST_WINTER = 1981         # POWER MERRA-2 daily meteorology begins 1981-01-01, so winter 1981/82 is the first complete one
LAST_WINTER = 2024          # winter 2024/25 ends 2025-03-31, inside the published record
# Supported coverage: northern North America, where winter roads and seasonal ice matter. POWER itself is global.
COVERAGE = dict(south=50.0, north=75.0, west=-170.0, east=-55.0)
COORD_DECIMALS = 2          # requests are made at 0.01 degree; POWER returns one 0.5 x 0.625 degree MERRA-2 cell anyway
MIN_INTERVAL_S = 1.0
TIMEOUT_S = 60
PLAUSIBLE_C = (-70.0, 45.0)
MERRA2_DLAT, MERRA2_DLON = 0.5, 0.625


class PowerError(Exception):
    """A request that could not be completed or a response that failed validation. The message is shown to the user."""


@dataclass
class PowerResult:
    daily: pd.DataFrame                 # date, temperature_c (NaN = missing)
    meta: dict = field(default_factory=dict)


def in_coverage(lat: float, lon: float) -> bool:
    return COVERAGE["south"] <= lat <= COVERAGE["north"] and COVERAGE["west"] <= lon <= COVERAGE["east"]


def canonical_point(lat: float, lon: float) -> tuple:
    return round(float(lat), COORD_DECIMALS), round(float(lon), COORD_DECIMALS)


def merra2_cell(lat: float, lon: float) -> dict:
    clat = round(round(lat / MERRA2_DLAT) * MERRA2_DLAT, 4)
    clon = round(-180 + round((lon + 180) / MERRA2_DLON) * MERRA2_DLON, 4)
    return dict(center_lat=clat, center_lon=clon, south=clat - MERRA2_DLAT / 2, north=clat + MERRA2_DLAT / 2, west=clon - MERRA2_DLON / 2, east=clon + MERRA2_DLON / 2)


def validate_request(lat: float, lon: float, first_winter: int, last_winter: int, parameter: str = "T2M") -> None:
    if parameter not in PARAMETERS:
        raise PowerError(f"Variable {parameter} is not supported. Supported: {', '.join(PARAMETERS)}.")
    if not (math.isfinite(lat) and math.isfinite(lon)):
        raise PowerError("Coordinates must be numbers.")
    if not in_coverage(lat, lon):
        raise PowerError(f"{lat:.2f}, {lon:.2f} is outside Frostline's supported area ({COVERAGE['south']:.0f} to {COVERAGE['north']:.0f} N, "
                         f"{abs(COVERAGE['west']):.0f} to {abs(COVERAGE['east']):.0f} W).")
    if not (FIRST_WINTER <= first_winter <= last_winter <= LAST_WINTER):
        raise PowerError(f"Winters must lie between {FIRST_WINTER}/{(FIRST_WINTER + 1) % 100:02d} and {LAST_WINTER}/{(LAST_WINTER + 1) % 100:02d}.")


def request_params(lat: float, lon: float, first_winter: int, last_winter: int, parameter: str = "T2M") -> dict:
    la, lo = canonical_point(lat, lon)
    return {"parameters": parameter, "community": COMMUNITY, "longitude": f"{lo:.2f}", "latitude": f"{la:.2f}",
            "start": f"{first_winter}1001", "end": f"{last_winter + 1}0331", "format": "JSON"}


def request_url(params: dict) -> str:
    return ENDPOINT + "?" + urllib.parse.urlencode(params)


def cache_key(params: dict) -> str:
    return hashlib.sha256(json.dumps(params, sort_keys=True).encode()).hexdigest()[:24]


def cache_dir() -> str:
    d = os.environ.get("FROSTLINE_CACHE_DIR") or os.path.join(tempfile.gettempdir(), "frostline_power_cache")
    os.makedirs(d, exist_ok=True)
    return d


def parse(payload: dict, params: dict, parameter: str = "T2M") -> PowerResult:
    """Validate a POWER daily JSON response and return the daily series. Raises PowerError on anything unexpected."""
    if not isinstance(payload, dict):
        raise PowerError("NASA POWER returned something that is not a JSON object.")
    msgs = payload.get("messages") or []
    if "properties" not in payload:
        detail = "; ".join(str(m) for m in msgs) or str(payload.get("detail") or payload.get("errors") or "no data section")
        raise PowerError(f"NASA POWER returned no data: {detail}")
    header = payload.get("header") or {}
    fill = header.get("fill_value", -999.0)
    pinfo = (payload.get("parameters") or {}).get(parameter) or {}
    unit = pinfo.get("units")
    if unit not in ("C", "°C"):
        raise PowerError(f"Unexpected unit for {parameter}: {unit!r} (expected C).")
    raw = ((payload.get("properties") or {}).get("parameter") or {}).get(parameter)
    if not isinstance(raw, dict) or not raw:
        raise PowerError(f"The response contains no {parameter} values.")
    try:
        dates = pd.to_datetime(list(raw.keys()), format="%Y%m%d")
    except (ValueError, TypeError) as exc:
        raise PowerError("The response contains malformed dates.") from exc
    vals = pd.to_numeric(pd.Series(list(raw.values()), dtype="object"), errors="coerce").astype(float).to_numpy()
    fill_mask = np.isclose(vals, float(fill)) | ~np.isfinite(vals)
    vals = np.where(fill_mask, np.nan, vals)
    implausible = (~np.isnan(vals)) & ((vals < PLAUSIBLE_C[0]) | (vals > PLAUSIBLE_C[1]))
    vals = np.where(implausible, np.nan, vals)
    df = pd.DataFrame({"date": dates, "temperature_c": vals}).sort_values("date").reset_index(drop=True)
    if df.date.duplicated().any():
        raise PowerError("The response contains duplicate dates.")
    want = pd.date_range(pd.to_datetime(params["start"]), pd.to_datetime(params["end"]), freq="D")
    missing_dates = want.difference(pd.DatetimeIndex(df.date))
    coords = (payload.get("geometry") or {}).get("coordinates") or [None, None, None]
    rlon, rlat = coords[0], coords[1]
    qlat, qlon = float(params["latitude"]), float(params["longitude"])
    if rlat is None or rlon is None or abs(float(rlat) - qlat) > 0.01 or abs(float(rlon) - qlon) > 0.01:
        raise PowerError(f"NASA POWER answered for {rlat}, {rlon} instead of the requested {qlat}, {qlon}.")
    meta = dict(
        endpoint=ENDPOINT, url=request_url(params), parameter=parameter, parameter_label=pinfo.get("longname", PARAMETERS[parameter]["label"]), unit="°C",
        api_name=(header.get("api") or {}).get("name", ""), api_version=(header.get("api") or {}).get("version", ""), title=header.get("title", ""),
        sources=", ".join(header.get("sources") or []), time_standard=header.get("time_standard", ""), fill_value=fill,
        requested_lat=qlat, requested_lon=qlon, returned_lat=float(rlat), returned_lon=float(rlon),
        returned_elevation_m=coords[2] if len(coords) > 2 else None, grid_cell=merra2_cell(qlat, qlon),
        start=params["start"], end=params["end"], n_days_expected=len(want), n_days_returned=len(df),
        n_fill_or_missing=int(fill_mask.sum()) + len(missing_dates), n_implausible=int(implausible.sum()), messages=[str(m) for m in msgs],
    )
    return PowerResult(df, meta)


_MEM: dict = {}
_LOCK = threading.Lock()
_LAST_CALL = [0.0]


def _http_get_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "Frostline/1.0 (NASA Space Apps 2026 research app)", "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_S) as r:
            body = r.read()
    except urllib.error.HTTPError as exc:
        detail = ""
        try:
            detail = json.loads(exc.read().decode("utf-8", "replace")).get("messages") or ""
        except Exception:
            pass
        raise PowerError(f"NASA POWER answered HTTP {exc.code}{': ' + str(detail) if detail else ''}.") from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise PowerError(f"NASA POWER could not be reached ({type(exc).__name__}). The curated case studies still work offline.") from exc
    try:
        return json.loads(body.decode("utf-8"))
    except ValueError as exc:
        raise PowerError("NASA POWER returned a response that is not valid JSON.") from exc


def fetch_daily(lat: float, lon: float, first_winter: int, last_winter: int, parameter: str = "T2M", fetcher=None, use_disk: bool = True) -> PowerResult:
    """Retrieve, validate and cache daily POWER data for winters first..last (Oct 1 of first to Mar 31 after last)."""
    validate_request(lat, lon, first_winter, last_winter, parameter)
    params = request_params(lat, lon, first_winter, last_winter, parameter)
    key = cache_key(params)
    with _LOCK:
        if key in _MEM:
            payload, retrieved, src = _MEM[key][0], _MEM[key][1], "memory cache"
        else:
            payload = retrieved = None
            path = os.path.join(cache_dir(), key + ".json") if use_disk else None
            if path and os.path.isfile(path):
                try:
                    with open(path, encoding="utf-8") as fh:
                        rec = json.load(fh)
                    payload, retrieved, src = rec["payload"], rec["retrieved_utc"], "disk cache"
                except Exception:
                    payload = None
            if payload is None:
                wait = MIN_INTERVAL_S - (time.monotonic() - _LAST_CALL[0])
                if wait > 0:
                    time.sleep(wait)
                payload = (fetcher or _http_get_json)(request_url(params))
                _LAST_CALL[0] = time.monotonic()
                retrieved, src = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "live NASA POWER request"
                parse(payload, params, parameter)   # never cache a response that fails validation
                if path:
                    try:
                        with open(path, "w", encoding="utf-8") as fh:
                            json.dump({"retrieved_utc": retrieved, "params": params, "payload": payload}, fh)
                    except OSError:
                        pass
            _MEM[key] = (payload, retrieved)
    res = parse(payload, params, parameter)
    res.meta.update(retrieved_utc=retrieved, served_from=src, cache_key=key)
    return res


def clear_memory_cache() -> None:
    with _LOCK:
        _MEM.clear()
