"""The Frostline Evidence Brief: a self-contained research artifact for one investigation.

The brief is assembled deterministically from the same Finding and EvidenceReport objects the interface
displays, through the same formatting functions, so exported statistics equal on-screen statistics. No
generative model writes any part of it. Three files are produced:

    HTML  a readable, printable report (inline SVG chart, no scripts, no network needed; print to PDF from a browser)
    CSV   the per-winter values behind the chart, with the fitted trend
    JSON  the machine-readable finding, evidence assessment and provenance
"""
from __future__ import annotations

import datetime as dt
import html
import io
import json
from dataclasses import dataclass

from . import APP_NAME, APP_VERSION, METHOD_ID, TAGLINE, TEAM_NAME
from . import analysis as an
from . import evidence as ev
from . import fmt
from .data import code_version
from .registry import LITERATURE, POWER_ACK, QUESTIONS, SOURCES, VARIABLES


@dataclass(frozen=True)
class Brief:
    title: str
    html: str
    csv: str
    json: str
    filename_stem: str


def _e(s) -> str:
    return html.escape(str(s), quote=True)


def stat_rows(ds, f: an.Finding) -> list:
    """Label and value pairs for a finding. The interface and the brief both render exactly this list."""
    var = VARIABLES[f.variable_id]
    d = var.slope_decimals
    rows = [("Period", f"{fmt.period(f.first, f.last)} (winter y runs Oct 1 of y to Mar 31 of y+1)"),
            ("Sample size", f"n = {f.n} winters" + ("" if f.n == f.n_expected else f" of {f.n_expected} in the period")),
            ("Evidence state", f.state_label)]
    if f.estimated:
        rows += [("Rate of change (Theil-Sen)", f"{fmt.num(f.slope, d, True)} {var.unit_per_decade} ({f.direction})"),
                 ("95% interval (Theil-Sen)", f"{fmt.interval(f.ci_low, f.ci_high, d)} {var.unit_per_decade}"),
                 ("95% interval (moving-block bootstrap)", f"{fmt.interval(f.bb_low, f.bb_high, d)} {var.unit_per_decade}"),
                 ("Mann-Kendall p (unadjusted)", fmt.pval(f.p))]
        if f.q is not None:
            rows.append(("Adjusted q (Benjamini-Hochberg)", f"{fmt.pval(f.q)} within {an.FAMILY_LABEL.get(f.q_family, f.q_family)}"))
        else:
            rows.append(("Adjusted q", "not reported: exploratory, not adjusted for multiple testing (user-selected window)"))
        rows.append(("Residual lag-1 autocorrelation", fmt.num(f.lag1, 2, True) + (" (flag raised: p may be optimistic)" if f.autocorr_flag else " (flag not raised)")))
    else:
        rows += [("Rate of change", fmt.NOT_ESTIMATED), ("95% interval", fmt.NOT_ESTIMATED), ("Mann-Kendall p", fmt.NOT_ESTIMATED)]
    return rows


def series_csv(ds, f: an.Finding) -> str:
    var, loc = VARIABLES[f.variable_id], an.locations(ds)[f.location_id]
    s = an.get_series(ds, f.location_id, f.variable_id)
    buf = io.StringIO()
    buf.write(f"# {APP_NAME} Evidence Brief data. {var.label}; {loc.name}; source: {SOURCES[var.source_id].name}; app data digest {ds.digest}\n")
    buf.write(f"# analysis period {fmt.period(f.first, f.last)}; empty value = no usable record for that winter (never zero-filled)\n")
    buf.write("season_start_year,winter,value,unit,in_analysis_period,theil_sen_fit\n")
    for y, v in zip(s.years, s.values):
        inside = f.first <= y <= f.last
        fit = an.fitted_line(f, [y])[0] if (f.estimated and inside) else None
        buf.write(f"{y},{fmt.winter(y)},{'' if not fmt.is_num(v) else repr(float(v))},{var.unit},{str(inside).lower()},{'' if fit is None else f'{fit:.6g}'}\n")
    return buf.getvalue()


def _svg_chart(ds, f: an.Finding, w: int = 760, h: int = 300) -> str:
    """A small static chart for the report: observed values, the Theil-Sen line and its slope interval."""
    var = VARIABLES[f.variable_id]
    s = an.get_series(ds, f.location_id, f.variable_id).window(f.first, f.last).dropna()
    if s.empty:
        return ""
    xs, ys = [int(v) for v in s.season_start_year], [float(v) for v in s.value]
    ml, mr, mt, mb = 70, 18, 14, 40
    x0, x1 = min(xs) - 0.5, max(xs) + 0.5
    bx = sorted(set(float(x) for x in xs) | ({float(f.pivot_year)} if f.estimated else set()))
    lo_band, hi_band = an.slope_band(f, bx) if f.estimated else ([], [])
    allv = ys + lo_band + hi_band
    y0, y1 = min(allv), max(allv)
    pad = (y1 - y0) * 0.08 or 1.0
    y0, y1 = y0 - pad, y1 + pad
    px = lambda x: ml + (x - x0) / (x1 - x0) * (w - ml - mr)
    py = lambda y: mt + (1 - (y - y0) / (y1 - y0)) * (h - mt - mb)
    out = [f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="{_e(var.label)} per winter with the Theil-Sen trend" xmlns="http://www.w3.org/2000/svg">']
    for k in range(5):
        v = y0 + (y1 - y0) * k / 4
        out.append(f'<line x1="{ml}" x2="{w - mr}" y1="{py(v):.1f}" y2="{py(v):.1f}" stroke="#d9dee7" stroke-width="1"/>')
        out.append(f'<text x="{ml - 8}" y="{py(v) + 4:.1f}" text-anchor="end" font-size="11" fill="#4a5568">{v:,.{var.decimals}f}</text>')
    step = 4 if len(xs) > 20 else 2
    for x in xs:
        if (x - xs[0]) % step == 0:
            out.append(f'<text x="{px(x):.1f}" y="{h - mb + 16}" text-anchor="middle" font-size="11" fill="#4a5568">{fmt.winter(x)}</text>')
    if f.estimated:
        a, b = min(xs), max(xs)
        poly = [f"{px(x):.1f},{py(v):.1f}" for x, v in zip(bx, hi_band)] + [f"{px(x):.1f},{py(v):.1f}" for x, v in zip(bx[::-1], lo_band[::-1])]
        out.append(f'<polygon points="{" ".join(poly)}" fill="#8a97ab" fill-opacity="0.22"/>')
        fit = an.fitted_line(f, [a, b])
        out.append(f'<line x1="{px(a):.1f}" y1="{py(fit[0]):.1f}" x2="{px(b):.1f}" y2="{py(fit[1]):.1f}" stroke="#101828" stroke-width="2.2"/>')
    pts = " ".join(f"{px(x):.1f},{py(y):.1f}" for x, y in zip(xs, ys))
    out.append(f'<polyline points="{pts}" fill="none" stroke="#2a78d6" stroke-width="1.2"/>')
    for x, y in zip(xs, ys):
        out.append(f'<circle cx="{px(x):.1f}" cy="{py(y):.1f}" r="4" fill="#2a78d6" stroke="#ffffff" stroke-width="1.5"><title>Winter {fmt.winter(x)}: {y:,.{var.decimals}f} {_e(var.unit)}</title></circle>')
    out.append(f'<text x="14" y="{(h - mb + mt) / 2:.0f}" font-size="11" fill="#4a5568" text-anchor="middle" transform="rotate(-90 14 {(h - mb + mt) / 2:.0f})">{_e(var.unit)}</text>')
    out.append("</svg>")
    return "".join(out)


_CSS = """
:root{color-scheme:light}
body{font-family:Inter,'Segoe UI',system-ui,-apple-system,sans-serif;color:#101828;background:#f4f6fa;margin:0;line-height:1.55}
main{max-width:860px;margin:0 auto;background:#fff;padding:44px 52px 56px}
header{border-bottom:3px solid #0b1220;padding-bottom:18px;margin-bottom:26px}
.brand{font-size:12px;letter-spacing:.16em;text-transform:uppercase;color:#2a5c9a;font-weight:700}
h1{font-size:25px;line-height:1.25;margin:8px 0 6px}
h2{font-size:16px;margin:30px 0 10px;padding-top:14px;border-top:1px solid #dfe4ec}
h3{font-size:13.5px;margin:16px 0 4px}
p,li{font-size:13.5px}.meta{color:#475467;font-size:12.5px}
table{border-collapse:collapse;width:100%;font-size:13px;margin:8px 0}
th,td{text-align:left;padding:7px 10px;border-bottom:1px solid #e4e8ef;vertical-align:top}
th{width:38%;color:#344054;font-weight:600;background:#f8fafc}
.state{display:inline-block;padding:3px 10px;border-radius:999px;font-size:12px;font-weight:700;border:1px solid #98a2b3;background:#f2f4f7}
.finding{background:#f1f6fd;border-left:4px solid #2a78d6;padding:12px 16px;margin:14px 0;font-size:14.5px}
.caveat{background:#fff8e6;border-left:4px solid #d99a00;padding:10px 14px;margin:12px 0;font-size:13px}
.dim{border:1px solid #e4e8ef;border-radius:8px;padding:10px 14px;margin:8px 0}
.dim b{font-size:13.5px}.tag{font-size:11.5px;font-weight:700;margin-left:8px;padding:2px 8px;border-radius:999px;border:1px solid #98a2b3}
.good{background:#e9f7ec}.warn{background:#fff4d6}.alert{background:#fde9e2}.muted{background:#f2f4f7}
ul{padding-left:20px;margin:6px 0}code{font-size:12px;background:#f2f4f7;padding:1px 5px;border-radius:4px}
footer{margin-top:30px;border-top:1px solid #dfe4ec;padding-top:14px;color:#475467;font-size:12px}
@media print{body{background:#fff}main{padding:0;max-width:none}h2{break-after:avoid}.dim,.finding,table{break-inside:avoid}}
"""


def build(ds, location_id: str, variable_id: str, first: int, last: int, question_id: str | None = None, generated: dt.datetime | None = None) -> Brief:
    """Assemble the Evidence Brief for exactly this investigation."""
    loc, var = an.locations(ds)[location_id], VARIABLES[variable_id]
    f = an.trend(ds, location_id, variable_id, first, last)
    rep = ev.assess(ds, location_id, variable_id, first, last)
    src = SOURCES[var.source_id]
    q = QUESTIONS.get(question_id) if question_id else None
    question = q.text if q else f"How has {var.phrase} changed at {loc.short if loc.mapped else loc.name}?"
    generated = generated or dt.datetime.now(dt.timezone.utc)
    stamp = generated.strftime("%Y-%m-%d %H:%M UTC")
    version = code_version()
    title = f"{var.label}: {loc.name}, winters {fmt.period(f.first, f.last)}"
    stats = stat_rows(ds, f)
    caveat = ds.facts["bias_caveat"]

    H = []
    H.append(f"<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
             f"<title>{_e(APP_NAME)} Evidence Brief: {_e(title)}</title><style>{_CSS}</style></head><body><main>")
    H.append(f"<header><div class='brand'>{_e(APP_NAME)} Evidence Brief · by {_e(TEAM_NAME)}</div><h1>{_e(title)}</h1>"
             f"<div class='meta'>Investigation question: <b>{_e(question)}</b><br>Generated {stamp} · app data digest <code>{ds.digest}</code> · code version <code>{_e(version)}</code></div></header>")
    H.append(f"<div class='finding'><span class='state'>{_e(f.state_label)}</span><p style='margin:8px 0 4px'>{_e(an.plain_language(ds, f))}</p><p style='margin:0'>{_e(f.sentence)}</p></div>")
    if var.is_temperature:
        H.append(f"<div class='caveat'><b>Required caveat for NASA temperature values.</b> {_e(caveat)} Absolute NASA values are not local conditions.</div>")
    for sentence in f.extra_sentences:
        H.append(f"<div class='caveat'>{_e(sentence)}</div>")

    H.append("<h2>1. Location</h2><table>")
    H.append(f"<tr><th>Study location</th><td>{_e(loc.name)}" + (f" ({_e(loc.region)})" if loc.region else "") + "</td></tr>")
    if loc.mapped:
        c = loc.cell
        H.append(f"<tr><th>Sampling coordinates</th><td>{loc.lat:.2f} N, {abs(loc.lon):.2f} W. {_e(loc.sampling_point)}</td></tr>")
        if var.kind == "environmental":
            H.append(f"<tr><th>NASA grid cell (calculated)</th><td>MERRA-2 0.5 x 0.625 degree cell centred {c['center_lat']:.3f} N, {abs(c['center_lon']):.3f} W"
                     + (f"; cell-average elevation {loc.cell_elevation_m} m (POWER file header)" if loc.cell_elevation_m else "") + "</td></tr>")
    else:
        H.append("<tr><th>Sampling coordinates</th><td>Approximate team-chosen point; not part of the approved app data.</td></tr>")
    H.append(f"<tr><th>Road</th><td>{_e(loc.road_name)}. {_e(loc.setting)}</td></tr>")
    if loc.access:
        H.append(f"<tr><th>Access context</th><td>{_e(loc.access)}</td></tr>")
    H.append("</table>")

    H.append("<h2>2. Variable and data</h2><table>")
    H.append(f"<tr><th>Variable</th><td>{_e(var.label)} (<code>{_e(var.id)}</code>), in {_e(var.unit)}</td></tr>")
    H.append(f"<tr><th>Definition</th><td>{_e(var.definition)}</td></tr>")
    H.append(f"<tr><th>Why it is relevant</th><td>{_e(var.why)}</td></tr>")
    H.append(f"<tr><th>Source</th><td>{_e(src.name)} ({_e(src.kind)})" + (f", parameter <code>{_e(var.power_parameter)}</code>" if var.power_parameter else "") + f". {_e(src.note)}</td></tr>")
    H.append(f"<tr><th>Resolution</th><td>{_e(var.temporal_resolution)}; {_e(var.spatial_resolution)}</td></tr>")
    H.append(f"<tr><th>Historical coverage</th><td>Available winters {fmt.period(var.valid_first, var.valid_last)}; this brief analyses {fmt.period(f.first, f.last)}.</td></tr>")
    H.append(f"<tr><th>Data-quality condition</th><td>{_e(var.quality)}</td></tr></table>")

    H.append("<h2>3. Historical record and trend</h2>")
    H.append(_svg_chart(ds, f))
    H.append("<p class='meta'>Points: one value per winter. Dark line: Theil-Sen estimate. Grey band: 95% interval of the slope. " +
             ("Values are NASA estimates for a grid cell, not station observations." if var.kind == "environmental" else "Values are the government record of operations.") + "</p>")
    H.append("<table>" + "".join(f"<tr><th>{_e(k)}</th><td>{_e(v)}</td></tr>" for k, v in stats) + "</table>")
    H.append(f"<p><b>Interpretation.</b> {_e(f.sentence)}</p>")

    H.append("<h2>4. Evidence assessment</h2>")
    H.append(f"<p><b>{_e(rep.headline)}</b></p><p>{_e(rep.suitability)}</p>")
    H.append("<p class='meta'>Each dimension is judged separately from the data. There is no overall score.</p>")
    for d in rep.dimensions:
        H.append(f"<div class='dim'><b>{_e(d.title)}</b><span class='tag {d.tone}'>{_e(d.state)}</span><div>{_e(d.summary)}</div><ul>"
                 + "".join(f"<li>{_e(r)}</li>" for r in d.reasons) + "</ul></div>")

    if loc.is_primary_pair:
        H.append("<h2>5. Road-operation evidence</h2>")
        H.append("<p>" + " ".join(_e(s) for s in ev.corridor_conclusion(ds, location_id)) + "</p>")
        H.append(f"<div class='caveat'>{_e(an.T_ROAD)}</div>")
    else:
        H.append("<h2>5. Road-operation evidence</h2><p>This is a supplementary corridor. Only its precomputed results and per-winter values are available; no corridor case study is offered.</p>")

    H.append("<h2>6. What the evidence shows, layer by layer</h2>")
    for layer in rep.layers:
        H.append(f"<h3>{_e(layer.title)}</h3><ul>" + "".join(f"<li>{_e(i)}</li>" for i in layer.items) + "</ul>")

    H.append("<h2>7. Method and reproducibility</h2><table>")
    H.append(f"<tr><th>Analysis method</th><td>{_e(METHOD_ID)}</td></tr>")
    H.append("<tr><th>Estimator and test</th><td>Theil-Sen slope per decade with its 95% interval; Mann-Kendall test with tie correction; moving-block bootstrap interval "
             "(blocks of ceil(n^(1/3)), 2000 resamples, fixed seed); at least 15 complete winters; no estimate for mostly tied series.</td></tr>")
    H.append("<tr><th>Multiple testing</th><td>Benjamini-Hochberg q is reported only for the fixed windows and declared families; a user-selected window carries an unadjusted p only.</td></tr>")
    H.append(f"<tr><th>Result provenance</th><td>{'Precomputed result in <code>' + _e(f.stored_source) + '</code>, cross-checked against a live recomputation.' if f.cross_checked else 'Recomputed for this window from the per-winter values with the approved functions.'}</td></tr>")
    H.append("<tr><th>Data files used</th><td>" + ", ".join(f"<code>{_e(n)}</code> (sha256 {ds.file_hashes[n][:12]})" for n in rep.files if n in ds.file_hashes) + "</td></tr>")
    H.append(f"<tr><th>Versions</th><td>{_e(APP_NAME)} {APP_VERSION}; code <code>{_e(version)}</code>; app data digest <code>{ds.digest}</code></td></tr>")
    H.append("<tr><th>To reproduce</th><td><code>python3 -I scripts/regenerate_all.py --check</code> rebuilds every derived file from the cached raw sources; "
             "the <code>period_trend</code> function of the recompute module in <code>scripts/</code> returns the statistics above for this window.</td></tr>")
    H.append("<tr><th>Review status</th><td>Exploratory analysis. No independent statistical sign-off has been recorded.</td></tr></table>")

    H.append("<h2>8. Sources</h2><ul>")
    cited = [var.source_id] + [k for k in ("merra2", "nwt_t108", "eccc") if k != var.source_id]
    for k in cited:
        H.append(f"<li>{_e(SOURCES[k].citation)} <a href='{_e(SOURCES[k].url)}'>{_e(SOURCES[k].url)}</a></li>")
    H.append("</ul>")
    H.append(f"<p class='meta'>POWER acknowledgement: {_e(POWER_ACK)}</p>")
    H.append("<p class='meta'>Context literature: " + " ".join(_e(x.split(' https://')[0]) + "." for x in LITERATURE[:2] + LITERATURE[3:5]) + "</p>")
    H.append(f"<footer>{_e(APP_NAME)}: {_e(TAGLINE)} Built by {_e(TEAM_NAME)} for the NASA Space Apps Challenge 2026 with AI assistance; statistics are generated by tested scripts from public data. "
             "This brief is not a road-safety assessment, a prediction or a statement of cause. NASA does not endorse this project.</footer></main></body></html>")

    payload = dict(
        app=APP_NAME, team=TEAM_NAME, app_version=APP_VERSION, code_version=version, generated_utc=stamp, method=METHOD_ID, data_digest=ds.digest,
        question=question, location=dict(id=loc.id, name=loc.name, role=loc.role, road_id=loc.road_id, lat=loc.lat, lon=loc.lon, merra2_cell=loc.cell),
        variable=dict(id=var.id, label=var.label, unit=var.unit, definition=var.definition, source=src.name, source_kind=src.kind, parameter=var.power_parameter),
        finding=f.as_dict(), statistics_as_displayed=[dict(label=k, value=v) for k, v in stats],
        interpretation=f.sentence, plain_language=an.plain_language(ds, f),
        evidence=dict(headline=rep.headline, suitability=rep.suitability,
                      dimensions=[dict(key=d.key, title=d.title, state=d.state, summary=d.summary, reasons=list(d.reasons)) for d in rep.dimensions],
                      layers=[dict(key=l.key, title=l.title, items=list(l.items)) for l in rep.layers]),
        required_caveat=caveat if var.is_temperature else None, files={n: ds.file_hashes[n] for n in rep.files if n in ds.file_hashes},
        review_status="exploratory; no independent statistical sign-off recorded")
    stem = f"frostline_brief_{loc.id}_{var.id}_{f.first}_{f.last}"
    return Brief(title=title, html="".join(H), csv=series_csv(ds, f), json=json.dumps(payload, indent=2, default=str), filename_stem=stem)
