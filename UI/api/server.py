"""Frostline web server: JSON API over the frostline package, plus the built React frontend.

Run from the repository root:

    pip install -r UI/api/requirements.txt
    uvicorn UI.api.server:app --port 8000          # or: python3 UI/api/server.py

The data are loaded once with the strict loader (frostline.data.load_dataset). If a required file is missing,
unreadable or flagged synthetic, every endpoint answers with an error that names the file, and the frontend shows
it. There is no fallback and no live download.
"""
from __future__ import annotations

import os
import sys
from urllib.parse import quote

UI_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if UI_DIR not in sys.path:
    sys.path.insert(0, UI_DIR)

from fastapi import FastAPI, HTTPException, Query, Request  # noqa: E402
from fastapi.middleware.gzip import GZipMiddleware  # noqa: E402
from fastapi.responses import FileResponse, JSONResponse, Response  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402

from frostline import analysis as an  # noqa: E402
from frostline import brief as brief_mod  # noqa: E402
from frostline import data  # noqa: E402
from frostline.registry import QUESTIONS, VARIABLES, variables_for  # noqa: E402

try:  # package import (uvicorn UI.api.server:app) or script run (python3 UI/api/server.py)
    from . import presenters as P
except ImportError:  # pragma: no cover
    from api import presenters as P  # type: ignore

DIST = os.path.join(UI_DIR, "frontend", "dist")

app = FastAPI(title="Frostline API", version="1.0.0", docs_url="/api/docs", openapi_url="/api/openapi.json", redoc_url=None)
app.add_middleware(GZipMiddleware, minimum_size=1024)


@app.exception_handler(data.DataError)
async def _data_error(_: Request, exc: data.DataError):
    return JSONResponse(status_code=500, content={"error": "data", "filename": exc.filename, "reason": exc.reason,
                                                  "message": f"Required data file {exc.filename} is not usable ({exc.reason}). No values are shown and no other data are substituted."})


def ds():
    return data.load_dataset()


# ------------------------------------------------------------------ validation (mirrors ui.init_state / set_investigation)
def _primary(loc: str) -> str:
    locs = an.locations(ds())
    if loc not in locs or not locs[loc].is_primary_pair:
        raise HTTPException(422, f"unknown or non-primary location '{loc}'")
    return loc


def _variable(loc: str, var: str) -> str:
    if var not in VARIABLES or var not in {v.id for v in variables_for(an.locations(ds())[loc])}:
        raise HTTPException(422, f"variable '{var}' is not available for '{loc}'")
    return var


def _window(loc: str, var: str, first: int | None, last: int | None) -> tuple:
    lo, hi = an.available_range(ds(), loc, var)
    if first is None or last is None:
        return lo, hi
    first, last = max(lo, int(min(first, last))), min(hi, int(max(first, last)))
    if first > last:
        return lo, hi
    return first, last


def _sel(loc, var, first, last):
    loc = _primary(loc)
    var = _variable(loc, var)
    first, last = _window(loc, var, first, last)
    return loc, var, first, last


# ------------------------------------------------------------------ endpoints
@app.get("/api/health")
def health():
    d = ds()
    return {"ok": True, "digest": d.digest}


@app.get("/api/bootstrap")
def bootstrap():
    d = ds()
    out = P.bootstrap(d)
    out["ranges"] = {lid: P.ranges(d, lid) for lid in out["primary"]}
    return out


@app.get("/api/observatory")
def observatory():
    return P.observatory(ds())


@app.get("/api/investigation")
def investigation(loc: str, var: str, first: int | None = None, last: int | None = None, height: int = Query(430, ge=240, le=700)):
    loc, var, first, last = _sel(loc, var, first, last)
    out = P.investigation(ds(), loc, var, first, last, height=height)
    out["selection"] = {"loc": loc, "var": var, "first": first, "last": last}
    return out


@app.get("/api/status")
def status(loc: str, var: str, first: int | None = None, last: int | None = None):
    """The compact evidence state shown in the investigation console."""
    loc, var, first, last = _sel(loc, var, first, last)
    d = ds()
    f = an.trend(d, loc, var, first, last)
    fixed = an.is_fixed_window(var, first, last)
    from frostline import fmt
    return {"state": f.state, "state_label": f.state_label, "tone": P.STATE_TONE[f.state], "n": f.n, "fixed": fixed,
            "meta": f"{fmt.period(first, last)} · n = {f.n} winters · " + ("approved fixed window" if fixed else "user-selected window: exploratory, not adjusted for multiple testing"),
            "selection": {"loc": loc, "var": var, "first": first, "last": last}}


@app.get("/api/questions/{qid}")
def question(qid: str, loc: str):
    if qid not in QUESTIONS:
        raise HTTPException(404, f"unknown question '{qid}'")
    return P.question(ds(), qid, _primary(loc))


@app.get("/api/compare")
def compare(var: str = "fdd_octdec", first: int | None = None, last: int | None = None):
    if var not in VARIABLES:
        raise HTTPException(422, f"unknown variable '{var}'")
    f, l = (first, last) if first is not None and last is not None else (-1, -1)
    return P.compare(ds(), var, int(f), int(l))


@app.get("/api/corridor/{loc}")
def corridor(loc: str):
    return P.corridor_overview(ds(), _primary(loc))


@app.get("/api/corridor/{loc}/road")
def corridor_road(loc: str, measure: str = "open_day"):
    return P.corridor_road(ds(), _primary(loc), measure)


@app.get("/api/corridor/{loc}/environment")
def corridor_env(loc: str, var: str = "fdd_octdec"):
    return P.corridor_env(ds(), _primary(loc), var)


@app.get("/api/corridor/{loc}/timeline")
def corridor_timeline(loc: str, var: str = "fdd_octdec", year: int | None = None, height: int = Query(560, ge=360, le=800)):
    return P.corridor_timeline(ds(), _primary(loc), var, year, height=height)


@app.get("/api/corridor/{loc}/associations")
def corridor_associations(loc: str):
    return P.corridor_associations(ds(), _primary(loc))


@app.get("/api/routes")
def routes(metric: str = "open_day", window: str = "1993"):
    return P.corridor_routes(ds(), metric, window)


@app.get("/api/corridor/{loc}/conclusion")
def corridor_conclusion(loc: str):
    return P.corridor_conclusion(ds(), _primary(loc))


@app.get("/api/demo/road/{loc}")
def demo_road(loc: str):
    return P.demo_road(ds(), _primary(loc))


@app.get("/api/evidence")
def evidence(loc: str, var: str, first: int | None = None, last: int | None = None):
    loc, var, first, last = _sel(loc, var, first, last)
    return P.evidence(ds(), loc, var, first, last)


@app.get("/api/evidence/disagreement")
def disagreement():
    return P.disagreement(ds())


@app.get("/api/evidence/multiple-testing")
def multiple_testing():
    return P.multiple_testing(ds())


@app.get("/api/evidence/multiple-testing.csv")
def multiple_testing_csv():
    t = ds()["multiple_testing_126"]
    return Response(t.to_csv(index=False), media_type="text/csv",
                    headers={"Content-Disposition": "attachment; filename=frostline_multiple_testing_126.csv"})


@app.get("/api/methods")
def methods():
    return P.methods(ds())


_BRIEF = {"html": ("text/html; charset=utf-8", "html"), "csv": ("text/csv; charset=utf-8", "csv"), "json": ("application/json", "json")}


@app.get("/api/brief")
def brief(loc: str, var: str, first: int | None = None, last: int | None = None, question: str | None = None,
          format: str = Query("html", pattern="^(html|csv|json)$"), download: bool = False):
    loc, var, first, last = _sel(loc, var, first, last)
    qid = question if question in QUESTIONS else None
    b = brief_mod.build(ds(), loc, var, first, last, qid)
    mime, ext = _BRIEF[format]
    body = {"html": b.html, "csv": b.csv, "json": b.json}[format]
    headers = {"X-Brief-Title": quote(b.title), "X-Brief-Filename": quote(f"{b.filename_stem}.{ext}")}
    if download:
        headers["Content-Disposition"] = f"attachment; filename=\"{b.filename_stem}.{ext}\""
    return Response(body, media_type=mime, headers=headers)


# ------------------------------------------------------------------ frontend (built SPA)
if os.path.isdir(DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(DIST, "assets")), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str):
        if path.startswith("api/"):
            raise HTTPException(404)
        target = os.path.join(DIST, path)
        if path and os.path.isfile(target) and os.path.realpath(target).startswith(os.path.realpath(DIST)):
            return FileResponse(target)
        return FileResponse(os.path.join(DIST, "index.html"), headers={"Cache-Control": "no-cache"})


if __name__ == "__main__":  # pragma: no cover
    import uvicorn

    uvicorn.run(app, host=os.environ.get("HOST", "127.0.0.1"), port=int(os.environ.get("PORT", "8000")))
