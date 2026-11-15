"""Frostline web API: a thin, read-only HTTP layer over the approved scientific modules in UI/frostline.

No statistic is computed here. Every number comes from frostline.analysis (which calls the approved
scripts/northlink_recompute.py functions), frostline.evidence and frostline.brief, reading only UI/data_real.

Run:  python -m uvicorn api.server:app --port 8765   (from the repository root)
"""
from __future__ import annotations

import dataclasses
import json
import math
import os
import sys

import numpy as np
import pandas as pd
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import FileResponse, JSONResponse, Response
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "UI"))

from frostline import analysis as an  # noqa: E402
from frostline import brief as br  # noqa: E402
from frostline import evidence as ev  # noqa: E402
from frostline.data import DataError, data_dir, load_dataset  # noqa: E402
from frostline.registry import (DEFAULT_LOCATION, DEFAULT_VARIABLE, LITERATURE, POWER_ACK, ROAD_KIND_LABEL,  # noqa: E402
                                SOURCES, VARIABLES)

WEB_DIR = os.path.join(ROOT, "web")


class RevalidatingStatic(StaticFiles):
    """Static files that browsers must revalidate (cheap 304 via ETag), so an updated client is picked up on reload."""

    def file_response(self, *args, **kwargs):
        resp = super().file_response(*args, **kwargs)
        resp.headers["Cache-Control"] = "no-cache"
        return resp


# ------------------------------------------------------------------ helpers
def jsonable(o):
    if dataclasses.is_dataclass(o) and not isinstance(o, type):
        return {f.name: jsonable(getattr(o, f.name)) for f in dataclasses.fields(o)}
    if isinstance(o, dict):
        return {str(k): jsonable(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [jsonable(v) for v in o]
    if isinstance(o, pd.DataFrame):
        return [jsonable(r) for r in o.to_dict(orient="records")]
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating, float)):
        v = float(o)
        return None if math.isnan(v) or math.isinf(v) else v
    if isinstance(o, (np.bool_,)):
        return bool(o)
    return o


def ok(payload) -> JSONResponse:
    return JSONResponse(jsonable(payload))


def fail(status: int, message: str) -> JSONResponse:
    return JSONResponse({"error": message}, status_code=status)


def dataset():
    return load_dataset()


def caveat() -> str:
    with open(os.path.join(data_dir(), "canonical_facts.json")) as fh:
        return json.load(fh).get("bias_caveat", "")


def loc_dict(loc) -> dict:
    d = jsonable(loc)
    d["is_primary_pair"] = loc.is_primary_pair
    d["road_kind_label"] = ROAD_KIND_LABEL.get(loc.road_kind, loc.road_kind)
    d["cell"] = loc.cell
    return d


def var_dict(v) -> dict:
    d = jsonable(v)
    d["unit_per_decade"] = v.unit_per_decade
    d["source"] = jsonable(SOURCES[v.source_id])
    return d


def parse_window(req: Request, ds, location_id: str, variable_id: str):
    lo, hi = an.available_range(ds, location_id, variable_id)
    first = int(req.query_params.get("first", lo))
    last = int(req.query_params.get("last", hi))
    if first > last:
        raise ValueError("The first winter must not be after the last winter.")
    if first < lo or last > hi:
        raise ValueError(f"This record spans winters {lo}/{str(lo + 1)[-2:]} to {hi}/{str(hi + 1)[-2:]}; choose a period inside it.")
    return first, last, lo, hi


def guarded(fn):
    async def handler(req: Request):
        try:
            return fn(req)
        except DataError as e:
            return fail(503, f"Required data file problem: {e}. No numbers are shown rather than falling back to other data.")
        except (KeyError, ValueError) as e:
            msg = e.args[0] if e.args else str(e)
            return fail(422, str(msg))
    return handler


# ------------------------------------------------------------------ endpoints
def meta(req: Request):
    ds = dataset()
    locs = an.locations(ds)
    out_locs = [loc_dict(l) for l in locs.values() if l.id != "custom"]
    variables = []
    for v in VARIABLES.values():
        avail = []
        for l in locs.values():
            try:
                a, b = an.available_range(ds, l.id, v.id)
                avail.append({"location_id": l.id, "first": a, "last": b})
            except (KeyError, ValueError):
                pass
        d = var_dict(v)
        d["availability"] = avail
        variables.append(d)
    return ok(dict(locations=out_locs, variables=variables, default_location=DEFAULT_LOCATION, default_variable=DEFAULT_VARIABLE,
                   compare_variables=list(an.COMPARE_VARIABLES), min_seasons=an.MIN_SEASONS, bias_caveat=caveat(),
                   power_ack=POWER_ACK, literature=jsonable(LITERATURE), sources=jsonable(SOURCES), data_digest=ds.digest))


def investigation(req: Request):
    ds = dataset()
    lid, vid = req.query_params.get("location", DEFAULT_LOCATION), req.query_params.get("variable", DEFAULT_VARIABLE)
    if vid not in VARIABLES:
        raise KeyError(f"Unknown variable '{vid}'.")
    first, last, lo, hi = parse_window(req, ds, lid, vid)
    loc, var = an.locations(ds)[lid], VARIABLES[vid]
    s = an.get_series(ds, lid, vid)
    f = an.trend(ds, lid, vid, first, last)
    years = [y for y in s.years if first <= y <= last]
    fitted = an.fitted_line(f, years) if f.estimated else []
    rep = ev.assess(ds, lid, vid, first, last)
    return ok(dict(
        location=loc_dict(loc), variable=var_dict(var), first=first, last=last, range=[lo, hi],
        series=[{"year": y, "value": v} for y, v in zip(s.years, s.values)],
        fitted=[{"year": y, "value": v} for y, v in zip(years, fitted)],
        finding=f.as_dict(), plain_language=an.plain_language(ds, f),
        stat_rows=[{"label": k, "value": v} for k, v in br.stat_rows(ds, f)],
        coverage=an.coverage(ds, lid, first, last) if var.kind == "environmental" else None,
        evidence=dict(headline=rep.headline, suitability=rep.suitability,
                      dimensions=[dict(key=d.key, title=d.title, state=d.state, tone=d.tone, summary=d.summary, reasons=list(d.reasons))
                                  for d in rep.dimensions],
                      layers=[dict(key=l.key, title=l.title, question=l.question, items=list(l.items)) for l in rep.layers],
                      files=list(rep.files)),
        bias_caveat=caveat() if var.is_temperature else None, source_file=s.source_file, series_note=s.note))


def compare(req: Request):
    ds = dataset()
    vid = req.query_params.get("variable", DEFAULT_VARIABLE)
    a, b = req.query_params.get("a", "dettah_bay"), req.query_params.get("b", "aklavik_delta")
    if a == b:
        raise ValueError("Choose two different locations to compare.")
    if vid not in an.COMPARE_VARIABLES:
        raise ValueError("Regional comparison is defined for Oct-Dec FDD, Oct-Dec mean and Jan-Mar mean temperature only.")
    la, ha = an.available_range(ds, a, vid)
    lb, hb = an.available_range(ds, b, vid)
    lo, hi = max(la, lb), min(ha, hb)
    first, last = int(req.query_params.get("first", lo)), int(req.query_params.get("last", hi))
    if first > last or first < lo or last > hi:
        raise ValueError(f"Matched winters for these locations span {lo} to {hi}; choose a period inside it.")
    c = an.compare(ds, vid, a, b, first, last)
    locs = an.locations(ds)
    sa, sb = an.get_series(ds, a, vid), an.get_series(ds, b, vid)
    return ok(dict(variable=var_dict(VARIABLES[vid]), first=first, last=last, range=[lo, hi],
                   a=loc_dict(locs[a]), b=loc_dict(locs[b]),
                   series_a=[{"year": y, "value": v} for y, v in zip(sa.years, sa.values) if first <= y <= last],
                   series_b=[{"year": y, "value": v} for y, v in zip(sb.years, sb.values) if first <= y <= last],
                   common_years=list(c.common_years), finding_a=c.a.as_dict(), finding_b=c.b.as_dict(), diff=c.diff.as_dict(),
                   formal=c.formal, sentence=c.sentence, bias_caveat=caveat() if VARIABLES[vid].is_temperature else None))


def road(req: Request):
    ds = dataset()
    lid = req.query_params.get("location", DEFAULT_LOCATION)
    loc = an.locations(ds)[lid]
    rec = an.road_record(ds, lid)
    out = {}
    for vid in ("open_day", "close_day", "open_to_close_days"):
        if vid not in VARIABLES:
            continue
        try:
            lo, hi = an.available_range(ds, lid, vid)
            first = int(req.query_params.get("first", lo)); last = int(req.query_params.get("last", hi))
            first, last = max(first, lo), min(last, hi)
            out[vid] = dict(variable=var_dict(VARIABLES[vid]), finding=an.trend(ds, lid, vid, first, last).as_dict(), range=[lo, hi])
        except (KeyError, ValueError) as e:
            out[vid] = dict(error=str(e))
    env = {}
    for vid in ("fdd_octdec", "mean_octdec_c"):
        try:
            s = an.get_series(ds, lid, vid)
            env[vid] = dict(variable=var_dict(VARIABLES[vid]), series=[{"year": y, "value": v} for y, v in zip(s.years, s.values)])
        except (KeyError, ValueError):
            pass
    return ok(dict(location=loc_dict(loc), record=rec, trends=out, environment=env,
                   status_counts=an.road_status_counts(ds, lid), overlap=an.window_overlap(ds, lid),
                   associations=an.associations(ds, lid), all_ci_include_zero=an.all_ci_include_zero(an.associations(ds, lid)),
                   road_caveat=an.T_ROAD, bias_caveat=caveat()))


def station(req: Request):
    ds = dataset()
    s = an.station_fdd(ds)
    return ok(dict(years=list(s.years_all), nasa=list(s.nasa_all), station=list(s.station_all), n_complete=s.n_complete,
                   nasa_mean=s.nasa_mean, station_mean=s.station_mean, pct_over=s.pct_over, pearson_r=s.pearson_r,
                   nasa_finding=s.nasa.as_dict(), station_finding=s.station.as_dict(), diff_finding=s.diff.as_dict()))


def _brief(req: Request):
    ds = dataset()
    lid, vid = req.query_params.get("location", DEFAULT_LOCATION), req.query_params.get("variable", DEFAULT_VARIABLE)
    first, last, _, _ = parse_window(req, ds, lid, vid)
    return br.build(ds, lid, vid, first, last)


def brief_html(req: Request):
    b = _brief(req)
    headers = {} if req.query_params.get("inline") else {"Content-Disposition": f'attachment; filename="{b.filename_stem}.html"'}
    return Response(b.html, media_type="text/html; charset=utf-8", headers=headers)


def brief_csv(req: Request):
    b = _brief(req)
    return Response(b.csv, media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": f'attachment; filename="{b.filename_stem}.csv"'})


def brief_json(req: Request):
    b = _brief(req)
    return Response(b.json, media_type="application/json",
                    headers={"Content-Disposition": f'attachment; filename="{b.filename_stem}.json"'})


async def index(req: Request):
    return FileResponse(os.path.join(WEB_DIR, "index.html"), headers={"Cache-Control": "no-cache"})


async def health(req: Request):
    try:
        ds = dataset()
        return JSONResponse({"status": "ok", "data_digest": ds.digest})
    except DataError as e:
        return JSONResponse({"status": "error", "error": str(e)}, status_code=503)


routes = [
    Route("/", index),
    Route("/api/health", health),
    Route("/api/meta", guarded(meta)),
    Route("/api/investigation", guarded(investigation)),
    Route("/api/compare", guarded(compare)),
    Route("/api/road", guarded(road)),
    Route("/api/station", guarded(station)),
    Route("/api/brief.html", guarded(brief_html)),
    Route("/api/series.csv", guarded(brief_csv)),
    Route("/api/brief.json", guarded(brief_json)),
    Mount("/static", RevalidatingStatic(directory=WEB_DIR), name="static"),
]

app = Starlette(routes=routes)
