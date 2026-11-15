"""Exploratory climate analysis for an arbitrary point: live NASA POWER daily T2M run through the same metric and trend engine
(scripts/northlink_metrics.py) that produced Frostline's curated results.

Arbitrary points get climate analysis only. No road-operation record, station check or community-specific validation is
attached, because none exists for them; every output says so.
"""
from __future__ import annotations

import html
import io
import json
from dataclasses import dataclass

import numpy as np
import pandas as pd

from . import analysis as an
from . import fmt
from . import power_api as pa

nm = an.nm
MIN_WINTERS = 15
QUESTIONS = {
    "fdd_octdec": dict(question="Is early winter delivering less freezing? (Oct to Dec freezing degree-days)", short="Oct to Dec freezing degree-days",
                       unit="°C·days", decimals=0, warmer="down",
                       meaning="Freezing degree-days add up how far each day's mean temperature fell below 0 °C from October 1 to December 31. "
                               "Fewer means a milder early winter, with less cold available to build lake and river ice."),
    "mean_octdec_c": dict(question="Is early winter getting warmer? (Oct to Dec mean temperature)", short="Oct to Dec mean temperature",
                          unit="°C", decimals=2, warmer="up", meaning="Average of the daily mean temperatures from October 1 to December 31."),
    "mean_janmar_c": dict(question="Is midwinter getting warmer? (Jan to Mar mean temperature)", short="Jan to Mar mean temperature",
                          unit="°C", decimals=2, warmer="up", meaning="Average of the daily mean temperatures from January 1 to March 31."),
    "thaw_days_janmar": dict(question="Are midwinter thaws becoming more common? (Jan to Mar days above 0 °C)", short="Jan to Mar thaw days",
                             unit="days", decimals=1, warmer="up", meaning="Number of days from January 1 to March 31 whose daily mean temperature was above 0 °C."),
}
EXPLORATORY_CAVEAT = ("Exploratory climate analysis for a user-selected point. NASA POWER values describe a 0.5 x 0.625 degree MERRA-2 reanalysis grid cell, "
                      "not a station or a road. No road-operation records, ice measurements or community-specific validation exist in Frostline for this point, "
                      "so nothing here says when a road opens or whether travel is safe. The result is not adjusted for multiple testing.")


def winter_table(daily: pd.DataFrame, first: int, last: int) -> pd.DataFrame:
    rows = []
    for y in range(first, last + 1):
        cov_e, cov_m = nm.season_coverage(daily, y, "early"), nm.season_coverage(daily, y, "mid")
        rows.append(dict(season_start_year=y, winter=fmt.winter(y), fdd_octdec=nm.fdd(daily, y, "early"), mean_octdec_c=nm.seasonal_mean(daily, y, "early"),
                         mean_janmar_c=nm.seasonal_mean(daily, y, "mid"), thaw_days_janmar=nm.thaw_days(daily, y),
                         valid_days_octdec=cov_e.valid, expected_days_octdec=cov_e.expected, valid_days_janmar=cov_m.valid, expected_days_janmar=cov_m.expected))
    return pd.DataFrame(rows)


@dataclass(frozen=True)
class ExploreResult:
    lat: float
    lon: float
    question_id: str
    first: int
    last: int
    table: pd.DataFrame
    n: int
    excluded: int
    slope_per_decade: float
    ci_low: float
    ci_high: float
    p: float
    lag1: float
    status: str
    intercept: float
    meta: dict

    @property
    def estimated(self) -> bool:
        return self.status == "ok"

    @property
    def q(self) -> dict:
        return QUESTIONS[self.question_id]


def analyze(power: pa.PowerResult, lat: float, lon: float, question_id: str, first: int, last: int) -> ExploreResult:
    if question_id not in QUESTIONS:
        raise ValueError(f"unknown question {question_id}")
    tab = winter_table(power.daily, first, last)
    col = tab[question_id]
    t = nm.trend(tab.season_start_year, col, min_points=MIN_WINTERS)
    ok = col.notna()
    intercept = float(np.median(col[ok] - t.slope_per_year * tab.season_start_year[ok])) if t.status == "ok" else float("nan")
    return ExploreResult(lat, lon, question_id, first, last, tab, t.n, int((~ok).sum()), t.slope_per_decade, t.ci_low_per_decade, t.ci_high_per_decade,
                         t.mk_p, t.lag1_autocorr_resid, t.status, intercept, dict(power.meta))


def fitted(r: ExploreResult) -> list:
    return [r.intercept + r.slope_per_decade / 10 * y for y in r.table.season_start_year]


def headline(r: ExploreResult) -> str:
    q = r.q
    if not r.estimated:
        why = {"too_few_points": f"only {r.n} complete winters (at least {MIN_WINTERS} are needed)", "mostly_tied": "one value fills at least 75% of the winters",
               "constant_series": "every winter has the same value"}.get(r.status, r.status)
        return f"Not estimated for {q['short']}: {why}."
    d = q["decimals"]
    direction = "increased" if r.slope_per_decade > 0 else "decreased"
    s = (f"At {fmt.num(r.lat, 2)}° N, {fmt.num(abs(r.lon), 2)}° W, {q['short']} {direction} by about {fmt.num(abs(r.slope_per_decade), d)} {q['unit']} per decade "
         f"over winters {fmt.period(r.first, r.last)} (Theil-Sen, {r.n} winters). ")
    if r.ci_low <= 0 <= r.ci_high:
        s += (f"The 95% interval ({fmt.interval(r.ci_low, r.ci_high, d)}) includes no change, so this record does not establish a trend; that is not proof of no change.")
    else:
        warmer = (r.slope_per_decade > 0) == (q["warmer"] == "up")
        s += (f"The 95% interval ({fmt.interval(r.ci_low, r.ci_high, d)}) excludes no change and points to {'milder' if warmer else 'colder'} conditions; "
              f"Mann-Kendall p = {fmt.pval(r.p)} (unadjusted, exploratory).")
    return s


def evidence_rows(r: ExploreResult) -> list:
    m = r.meta
    return [
        ("Question", r.q["question"]), ("What the measure is", r.q["meaning"]),
        ("Selected point", f"{r.lat:.2f} N, {abs(r.lon):.2f} W (requested); NASA POWER answered for {m.get('returned_lat')}, {m.get('returned_lon')}"),
        ("NASA grid cell (calculated)", "MERRA-2 0.5 x 0.625 degree cell centred at {center_lat:.3f} N, {lon:.3f} W".format(center_lat=m["grid_cell"]["center_lat"], lon=abs(m["grid_cell"]["center_lon"]))
         + (f"; cell-average elevation {m.get('returned_elevation_m')} m" if m.get("returned_elevation_m") is not None else "")),
        ("Winters analysed", f"{fmt.period(r.first, r.last)}: {r.n} complete, {r.excluded} incomplete and excluded (not filled)"),
        ("Theil-Sen slope", f"{fmt.num(r.slope_per_decade, r.q['decimals'] + 1, True)} {r.q['unit']} per decade" if r.estimated else "not estimated"),
        ("95% interval", fmt.interval(r.ci_low, r.ci_high, r.q["decimals"] + 1) if r.estimated else "not estimated"),
        ("Mann-Kendall p (unadjusted)", fmt.pval(r.p) if r.estimated else "not estimated"),
        ("Residual lag-1 autocorrelation", fmt.num(r.lag1, 2) if r.estimated else "not estimated"),
        ("Missing or fill values", f"{m.get('n_fill_or_missing')} of {m.get('n_days_expected')} requested days; {m.get('n_implausible')} implausible values removed"),
        ("Data source", f"NASA POWER {m.get('api_name')} {m.get('api_version')}; {m.get('parameter')} ({m.get('parameter_label')}), {m.get('unit')}; source {m.get('sources')}; "
                        f"time standard {m.get('time_standard')}"),
        ("Retrieved", f"{m.get('retrieved_utc')} ({m.get('served_from')})"),
        ("Request", m.get("url", "")),
    ]


def export_csv(r: ExploreResult) -> str:
    t = r.table.copy()
    t["included_in_trend"] = t[r.question_id].notna()
    t["theil_sen_fit"] = [round(v, 4) for v in fitted(r)] if r.estimated else ""
    buf = io.StringIO()
    buf.write(f"# Frostline exploratory analysis; NASA POWER daily T2M; request {r.meta.get('url')}; retrieved {r.meta.get('retrieved_utc')}\n")
    t.to_csv(buf, index=False)
    return buf.getvalue()


def record_json(r: ExploreResult, generated: str) -> str:
    return json.dumps(dict(kind="exploratory", lat=r.lat, lon=r.lon, question=r.question_id, first_winter=r.first, last_winter=r.last, n=r.n, excluded=r.excluded,
                           slope_per_decade=r.slope_per_decade, ci95=[r.ci_low, r.ci_high], p_unadjusted=r.p, lag1=r.lag1, status=r.status, headline=headline(r),
                           caveat=EXPLORATORY_CAVEAT, source=r.meta, generated=generated), indent=2, default=str)


def _svg(r: ExploreResult, w: int = 760, h: int = 260) -> str:
    t = r.table.dropna(subset=[r.question_id])
    if t.empty:
        return ""
    xs, ys = t.season_start_year.to_numpy(float), t[r.question_id].to_numpy(float)
    x0, x1, y0, y1 = xs.min() - 0.5, xs.max() + 0.5, ys.min(), ys.max()
    pad = (y1 - y0) * 0.1 or 1
    y0, y1 = y0 - pad, y1 + pad
    X = lambda x: 50 + (x - x0) / (x1 - x0) * (w - 70)  # noqa: E731
    Y = lambda y: 20 + (y1 - y) / (y1 - y0) * (h - 50)  # noqa: E731
    pts = "".join(f"<circle cx='{X(a):.1f}' cy='{Y(b):.1f}' r='3.5' fill='#2f6fb5'/>" for a, b in zip(xs, ys))
    line = ""
    if r.estimated:
        f = [r.intercept + r.slope_per_decade / 10 * x for x in (xs.min(), xs.max())]
        line = f"<line x1='{X(xs.min()):.1f}' y1='{Y(f[0]):.1f}' x2='{X(xs.max()):.1f}' y2='{Y(f[1]):.1f}' stroke='#111' stroke-width='2'/>"
    lab = (f"<text x='50' y='{h - 8}' font-size='11'>{int(xs.min())}/{(int(xs.min()) + 1) % 100:02d}</text>"
           f"<text x='{w - 60}' y='{h - 8}' font-size='11'>{int(xs.max())}/{(int(xs.max()) + 1) % 100:02d}</text>"
           f"<text x='4' y='{Y(y1 - pad) + 4:.1f}' font-size='11'>{y1 - pad:.1f}</text><text x='4' y='{Y(y0 + pad) + 4:.1f}' font-size='11'>{y0 + pad:.1f}</text>")
    return (f"<svg viewBox='0 0 {w} {h}' width='100%' role='img' aria-label='{html.escape(r.q['short'])} by winter with Theil-Sen trend'>"
            f"<rect x='0' y='0' width='{w}' height='{h}' fill='#fafafa'/>{pts}{line}{lab}</svg>")


def brief_html(r: ExploreResult, generated: str, code_version: str = "unknown") -> str:
    e = html.escape
    rows = "".join(f"<tr><th>{e(k)}</th><td>{e(str(v))}</td></tr>" for k, v in evidence_rows(r))
    col = r.question_id
    trows = "".join(f"<tr><td>{e(w)}</td><td>{'' if pd.isna(v) else fmt.num(v, r.q['decimals'] + 1)}</td><td>{a}/{b}</td><td>{c}/{d}</td></tr>"
                    for w, v, a, b, c, d in zip(r.table.winter, r.table[col], r.table.valid_days_octdec, r.table.expected_days_octdec,
                                                r.table.valid_days_janmar, r.table.expected_days_janmar))
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Frostline Evidence Brief - exploratory point {r.lat:.2f} N {abs(r.lon):.2f} W</title>
<style>body{{font-family:-apple-system,Segoe UI,Inter,sans-serif;max-width:860px;margin:32px auto;padding:0 16px;color:#111;line-height:1.5}}
table{{border-collapse:collapse;width:100%;margin:8px 0 20px;font-size:14px}}th,td{{border:1px solid #ccc;padding:6px 8px;text-align:left;vertical-align:top}}
.lead{{font-size:18px}}.note{{background:#fff7e0;border-left:4px solid #e5b454;padding:8px 12px}}td{{word-break:break-word}}</style></head><body>
<h1>Frostline Evidence Brief: exploratory location</h1>
<p>Generated {e(generated)} by Frostline (Strongest Soldiers), code {e(code_version)}. Values were retrieved from NASA POWER and analysed with the same metric and trend code
as Frostline's curated case studies.</p>
<p class="note"><b>Exploratory.</b> {e(EXPLORATORY_CAVEAT)}</p>
<h2>Main finding</h2><p class="lead">{e(headline(r))}</p>{_svg(r)}
<h2>Inputs, results and source</h2><table>{rows}</table>
<h2>Winter-by-winter values</h2><table><tr><th>Winter</th><th>{e(r.q['short'])} ({e(r.q['unit'])})</th><th>Valid days Oct to Dec</th><th>Valid days Jan to Mar</th></tr>{trows}</table>
<h2>Methods</h2><p>Winter y runs from October 1 of y to March 31 of y+1. A season is used only if every day is present, unique and between -70 and 45 °C; incomplete seasons are excluded, never filled.
Trend: Theil-Sen slope with 95% interval; Mann-Kendall test with tie correction (two-sided, unadjusted); residual lag-1 autocorrelation reported.
NASA POWER Daily API: {e(pa.DOCS_URL)}. Data courtesy of the NASA Langley Research Center POWER Project funded through the NASA Earth Science Directorate Applied Science Program.</p>
</body></html>"""
