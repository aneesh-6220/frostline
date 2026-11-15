"""NASA Giovanni MERRA-2 monthly 2 m temperature: analysis of the ingested extraction (scripts/ingest_giovanni_monthly.py).

Every number here is computed from UI/data_real/giovanni_*.csv, which the strict ingest derived from the raw Giovanni export in
data/raw/nasa/giovanni/. Monthly reanalysis means are used for monthly, seasonal and annual MEAN temperature only. They are
never used to reconstruct daily freezing-degree days or thaw days, and they are not road-operation records.
"""
from __future__ import annotations

import html
import io
import json
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import stats

from . import analysis as an
from . import fmt

nm = an.nm
SEASON_ORDER = ("ANN", "DJF", "MAM", "JJA", "SON", "octdec_mean_c", "janmar_mean_c")
SEASON_LABEL = {"ANN": "Calendar year (Jan to Dec)", "DJF": "Winter (Dec to Feb)", "MAM": "Spring (Mar to May)", "JJA": "Summer (Jun to Aug)",
                "SON": "Autumn (Sep to Nov)", "octdec_mean_c": "Early winter (Oct to Dec)", "janmar_mean_c": "Midwinter (Jan to Mar)"}
YEAR_NOTE = {"DJF": "year of its January and February", "octdec_mean_c": "year the winter starts", "janmar_mean_c": "year the winter starts (Jan to Mar of the next year)"}
NORMAL = (1991, 2020)
MIN_YEARS = 15
DATASET_NAME = "MERRA-2 tavgM_2d_slv_Nx (M2TMNXSLV) version 5.12.4, variable T2M, through NASA Giovanni"
CITATION = ("Global Modeling and Assimilation Office (GMAO) (2015), MERRA-2 tavgM_2d_slv_Nx: 2d, Monthly mean, Time-Averaged, Single-Level, "
            "Assimilation, Single-Level Diagnostics V5.12.4, Greenbelt, MD, USA, Goddard Earth Sciences Data and Information Services Center "
            "(GES DISC), doi:10.5067/AP1B0BA5PD2K. Accessed through NASA Giovanni (https://giovanni.gsfc.nasa.gov/).")
WHAT_IT_IS_NOT = ("Monthly MERRA-2 reanalysis means for one 0.5 x 0.625 degree grid cell. They are model-based estimates constrained by observations, "
                  "not station measurements; they are not the daily NASA POWER values used for freezing-degree days; and they are not road-operation records.")


def available(ds) -> bool:
    return bool(ds.giovanni)


def locations(ds) -> list:
    return sorted(ds.giovanni["giovanni_monthly_t2m.csv"].location_id.unique()) if available(ds) else []


def monthly(ds, location_id: str) -> pd.DataFrame:
    m = ds.giovanni["giovanni_monthly_t2m.csv"]
    m = m[m.location_id == location_id].copy()
    m["date"] = pd.to_datetime(dict(year=m.year, month=m.month, day=1))
    return m.reset_index(drop=True)


def provenance(ds, location_id: str) -> dict:
    p = ds.giovanni["giovanni_provenance.csv"]
    p = p[p.location_id == location_id]
    return {r.key: ("" if pd.isna(r.value) else str(r.value)) for r in p.itertuples()}


def power_check(ds, location_id: str) -> dict:
    c = ds.giovanni["giovanni_vs_power_check.csv"]
    c = c[c.location_id == location_id]
    return c.iloc[0].to_dict() if len(c) else {}


def stored_trends(ds, location_id: str) -> pd.DataFrame:
    t = ds.giovanni["giovanni_monthly_t2m_trends.csv"]
    return t[t.location_id == location_id].reset_index(drop=True)


def season_series(ds, location_id: str, season: str) -> pd.DataFrame:
    """year, value_c, n_months for one aggregate. Incomplete aggregates are kept as NaN rows (they are reported, not filled)."""
    if season in ("octdec_mean_c", "janmar_mean_c"):
        s = ds.giovanni["giovanni_monthly_t2m_seasonal.csv"]
        s = s[s.location_id == location_id]
        n = s["n_months_octdec" if season == "octdec_mean_c" else "n_months_janmar"]
        return pd.DataFrame({"year": s.season_start_year.astype(int), "value_c": s[season].astype(float), "n_months": n.astype(int)}).reset_index(drop=True)
    c = ds.giovanni["giovanni_t2m_calendar_seasons.csv"]
    c = c[(c.location_id == location_id) & (c.season == season)]
    return pd.DataFrame({"year": c.year.astype(int), "value_c": c.mean_c.astype(float), "n_months": c.n_months.astype(int)}).reset_index(drop=True)


def year_range(ds, location_id: str, season: str) -> tuple:
    s = season_series(ds, location_id, season).dropna(subset=["value_c"])
    return int(s.year.min()), int(s.year.max())


@dataclass(frozen=True)
class GTrend:
    location_id: str
    season: str
    first: int
    last: int
    years: tuple
    values: tuple
    excluded_incomplete: int
    n: int
    slope_per_decade: float
    ci_low: float
    ci_high: float
    p: float
    lag1: float
    status: str
    full_record: bool
    q: float | None
    family_size: int | None
    intercept: float

    @property
    def estimated(self) -> bool:
        return self.status == "ok"


def trend(ds, location_id: str, season: str, first: int | None = None, last: int | None = None) -> GTrend:
    lo, hi = year_range(ds, location_id, season)
    first, last = max(lo, int(first if first is not None else lo)), min(hi, int(last if last is not None else hi))
    s = season_series(ds, location_id, season)
    s = s[(s.year >= first) & (s.year <= last)]
    excluded = int(s.value_c.isna().sum())
    s = s.dropna(subset=["value_c"])
    t = nm.trend(s.year, s.value_c, min_points=MIN_YEARS)
    intercept = float(np.median(s.value_c - t.slope_per_year * s.year)) if t.status == "ok" else float("nan")
    full = (first, last) == (lo, hi)
    q = fam = None
    if full:
        row = stored_trends(ds, location_id)
        row = row[row.metric == season]
        if len(row):
            q, fam = float(row.q_bh_within_location.iloc[0]), int(row.family_size.iloc[0])
    return GTrend(location_id, season, first, last, tuple(int(y) for y in s.year), tuple(float(v) for v in s.value_c), excluded, t.n,
                  t.slope_per_decade, t.ci_low_per_decade, t.ci_high_per_decade, t.mk_p, t.lag1_autocorr_resid, t.status, full, q, fam, intercept)


def fitted(t: GTrend) -> list:
    return [t.intercept + t.slope_per_decade / 10 * y for y in t.years]


def evidence_state(t: GTrend) -> str:
    if not t.estimated:
        return an.INSUFFICIENT
    if t.full_record and t.q is not None:
        return an.SUPPORTED if t.q < an.ALPHA else an.UNRESOLVED
    return an.EXPLORATORY


def _lc(s: str) -> str:
    return s[:1].lower() + s[1:]


def plain_language(t: GTrend) -> str:
    label = _lc(SEASON_LABEL[t.season])
    if not t.estimated:
        return f"Not estimated: the {label} series from {t.first} to {t.last} has {t.n} complete years and at least {MIN_YEARS} are required."
    direction = "warmed" if t.slope_per_decade > 0 else "cooled"
    total = t.slope_per_decade * (t.last - t.first) / 10
    s = (f"In NASA's MERRA-2 monthly record for this grid cell, the {label} mean temperature {direction} by about {fmt.num(abs(t.slope_per_decade), 2)} °C per decade "
         f"from {t.first} to {t.last} (about {fmt.num(abs(total), 1)} °C over the period). ")
    lo_hi = f"The 95% interval runs from {fmt.num(t.ci_low, 2, True)} to {fmt.num(t.ci_high, 2, True)} °C per decade"
    if t.ci_low <= 0 <= t.ci_high:
        s += lo_hi + ", which includes no change, so the record does not establish a trend. That is not proof of no change."
    else:
        s += lo_hi + ", which excludes no change."
        if t.full_record and t.q is not None:
            s += (f" After adjusting for the {t.family_size} seasonal tests run on this record (Benjamini-Hochberg q = {fmt.pval(t.q)}) "
                  + ("the trend remains supported." if t.q < an.ALPHA else "it is inconclusive."))
        else:
            s += " This window was chosen by the user, so the result is exploratory and not adjusted for multiple testing."
    return s


def climatology(ds, location_id: str, base: tuple = NORMAL) -> pd.DataFrame:
    m = monthly(ds, location_id)
    b = m[(m.year >= base[0]) & (m.year <= base[1])].dropna(subset=["t2m_c"])
    g = b.groupby("month").t2m_c.agg(["mean", "std", "min", "max", "count"]).reset_index()
    return g


def anomalies(ds, location_id: str, base: tuple = NORMAL) -> pd.DataFrame:
    m = monthly(ds, location_id)
    clim = climatology(ds, location_id, base).set_index("month")["mean"]
    m["anomaly_c"] = m.t2m_c - m.month.map(clim)
    return m


def period_contrast(ds, location_id: str, season: str, a: tuple, b: tuple) -> dict:
    """Mean of period b minus mean of period a, with a Welch 95% interval (years treated as independent; lag-1 is reported separately)."""
    s = season_series(ds, location_id, season).dropna(subset=["value_c"])
    x = s[(s.year >= a[0]) & (s.year <= a[1])].value_c.to_numpy()
    y = s[(s.year >= b[0]) & (s.year <= b[1])].value_c.to_numpy()
    if len(x) < 3 or len(y) < 3:
        return dict(diff=float("nan"), lo=float("nan"), hi=float("nan"), n_a=len(x), n_b=len(y), a=a, b=b)
    d = y.mean() - x.mean()
    va, vb = x.var(ddof=1) / len(x), y.var(ddof=1) / len(y)
    se = np.sqrt(va + vb)
    df = (va + vb) ** 2 / (va ** 2 / (len(x) - 1) + vb ** 2 / (len(y) - 1))
    h = stats.t.ppf(0.975, df) * se
    return dict(diff=float(d), lo=float(d - h), hi=float(d + h), n_a=len(x), n_b=len(y), a=a, b=b, mean_a=float(x.mean()), mean_b=float(y.mean()))


# ------------------------------------------------------------------ export
def export_csv(ds, t: GTrend) -> str:
    s = season_series(ds, t.location_id, t.season)
    s = s[(s.year >= t.first) & (s.year <= t.last)].copy()
    s.insert(0, "aggregate", SEASON_LABEL[t.season])
    s["included_in_trend"] = s.value_c.notna()
    s["theil_sen_fit_c"] = [round(t.intercept + t.slope_per_decade / 10 * y, 4) if t.estimated else "" for y in s.year]
    buf = io.StringIO()
    buf.write(f"# Source: {DATASET_NAME}; derived from {provenance(ds, t.location_id).get('source_file', '')}\n")
    s.to_csv(buf, index=False)
    return buf.getvalue()


def brief_html(ds, t: GTrend, generated: str, code_version: str = "unknown") -> str:
    p = provenance(ds, t.location_id)
    chk = power_check(ds, t.location_id)
    rows_tr = stored_trends(ds, t.location_id)
    e = html.escape
    tr_rows = "".join(f"<tr><td>{e(SEASON_LABEL.get(r.metric, r.metric))}</td><td>{r.first_year} to {r.last_year}</td><td>{r.n}</td>"
                      f"<td>{fmt.num(r.slope_per_decade, 2, True)}</td><td>{fmt.interval(r.ci95_low, r.ci95_high, 2)}</td><td>{fmt.pval(r.mk_p)}</td>"
                      f"<td>{fmt.pval(r.q_bh_within_location)}</td></tr>" for r in rows_tr.itertuples())
    prov_rows = "".join(f"<tr><th>{e(k.replace('_', ' '))}</th><td>{e(v)}</td></tr>" for k, v in p.items())
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Frostline Evidence Brief - Giovanni monthly temperature</title>
<style>body{{font-family:-apple-system,Segoe UI,Inter,sans-serif;max-width:860px;margin:32px auto;padding:0 16px;color:#111;line-height:1.5}}
table{{border-collapse:collapse;width:100%;margin:8px 0 20px;font-size:14px}}th,td{{border:1px solid #ccc;padding:6px 8px;text-align:left;vertical-align:top}}
.lead{{font-size:18px}}.note{{background:#fff7e0;border-left:4px solid #e5b454;padding:8px 12px}}code{{font-size:12px;word-break:break-all}}</style></head><body>
<h1>Frostline Evidence Brief: NASA Giovanni monthly temperature</h1>
<p>Generated {e(generated)} by Frostline (Strongest Soldiers), code {e(code_version)}. Every value below is computed from the Giovanni export named under Provenance.</p>
<h2>Selected inputs</h2><table><tr><th>Grid point (Giovanni-resolved)</th><td>{e(p.get('data_grid_point_wsen', ''))} (west, south, east, north)</td></tr>
<tr><th>Requested box</th><td>{e(p.get('user_bounding_box_wsen', ''))}</td></tr><tr><th>Aggregate</th><td>{e(SEASON_LABEL[t.season])}</td></tr>
<tr><th>Years analysed</th><td>{t.first} to {t.last} ({t.n} complete; {t.excluded_incomplete} incomplete excluded)</td></tr></table>
<h2>Main finding</h2><p class="lead">{e(plain_language(t))}</p>
<table><tr><th>Theil-Sen slope</th><td>{fmt.num(t.slope_per_decade, 3, True)} °C per decade</td></tr><tr><th>95% interval</th><td>{fmt.interval(t.ci_low, t.ci_high, 3)}</td></tr>
<tr><th>Mann-Kendall p (unadjusted)</th><td>{fmt.pval(t.p)}</td></tr><tr><th>Residual lag-1 autocorrelation</th><td>{fmt.num(t.lag1, 2)}</td></tr>
<tr><th>Benjamini-Hochberg q</th><td>{fmt.pval(t.q) if t.q is not None else 'not applicable (user-selected window)'}</td></tr></table>
<h2>All full-record seasonal trends (one family of {len(rows_tr)} tests)</h2><table><tr><th>Aggregate</th><th>Years</th><th>n</th><th>°C per decade</th><th>95% interval</th><th>p</th><th>q</th></tr>{tr_rows}</table>
<h2>Consistency check against NASA POWER daily data</h2><p>Over {chk.get('n_months', '')} months ({e(str(chk.get('first', '')))} to {e(str(chk.get('last', '')))}) the Giovanni monthly
means differ from the monthly mean of POWER daily values by {chk.get('mean_diff_giovanni_minus_power_c', '')} °C on average (largest {chk.get('max_abs_diff_c', '')} °C; correlation {chk.get('pearson_r', '')}).
Both come from MERRA-2, so this checks the access route and processing, not the reanalysis itself.</p>
<h2>What these data are not</h2><p class="note">{e(WHAT_IT_IS_NOT)} Monthly means are never used here to reconstruct daily freezing-degree days.
The Dettah ice-road dates and the station comparison are separate evidence and are not part of this brief.</p>
<h2>Provenance</h2><table>{prov_rows}</table><p>Citation: {e(CITATION)}</p>
<h2>Methods</h2><p>Kelvin to Celsius: C = K - 273.15. Values equal to the Giovanni fill value would be treated as missing (none occur). Seasonal and annual means use only complete sets of months.
Trend: Theil-Sen slope with 95% interval; Mann-Kendall test with tie correction (two-sided); residual lag-1 autocorrelation reported. Multiple testing: Benjamini-Hochberg across the seasonal tests run on this record.</p>
</body></html>"""


def record_json(ds, t: GTrend, generated: str) -> str:
    return json.dumps(dict(source=DATASET_NAME, provenance=provenance(ds, t.location_id), aggregate=t.season, first=t.first, last=t.last, n=t.n,
                           excluded_incomplete=t.excluded_incomplete, slope_per_decade=t.slope_per_decade, ci95=[t.ci_low, t.ci_high], p_unadjusted=t.p,
                           q_bh=t.q, lag1=t.lag1, status=t.status, plain_language=plain_language(t), generated=generated), indent=2, default=float)
