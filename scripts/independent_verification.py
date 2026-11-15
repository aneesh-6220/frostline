"""Independent re-derivation of Frostline's principal numbers, written separately from the production pipeline.

It deliberately does NOT import scripts/northlink_*.py, UI/frostline/* or scipy.stats.theilslopes. It reads the raw files
(the Giovanni CSV export and the NWT Table 108 workbook) and recomputes, with its own implementations:

  * Theil-Sen slope (median of pairwise slopes) and Sen's (1968) rank-based 95% interval,
  * the Mann-Kendall S statistic, tie-corrected variance, continuity-corrected z and two-sided p,
  * Benjamini-Hochberg q-values,
  * Kelvin to Celsius conversion and seasonal aggregation for the Giovanni record,
  * Dettah opening day of winter from the raw workbook dates.

Run: python3 -I scripts/independent_verification.py      (prints a table; exits non-zero on disagreement)
"""
from __future__ import annotations

import csv
import datetime as dt
import math
import os
import sys
from statistics import NormalDist

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
GIOVANNI = os.path.join(ROOT, "data", "raw", "nasa", "giovanni",
                        "g4.areaAvgTimeSeries.M2TMNXSLV_5_12_4_T2M.19800101-20251231.114W_62N_113W_62N.csv")
ROADS = os.path.join(ROOT, "data", "raw", "roads", "NWT_Table108_Winter_Road_Opening_and_Closing_Dates_1993_94_to_2024.xlsx")
Z975 = NormalDist().inv_cdf(0.975)


# ------------------------------------------------------------------ statistics (own implementations)
def pairwise_slopes(x, y):
    out = []
    for i in range(len(x)):
        for j in range(i + 1, len(x)):
            if x[j] != x[i]:
                out.append((y[j] - y[i]) / (x[j] - x[i]))
    return sorted(out)


def median(v):
    v = sorted(v)
    n = len(v)
    return v[n // 2] if n % 2 else 0.5 * (v[n // 2 - 1] + v[n // 2])


def tie_term(values):
    counts = {}
    for v in values:
        counts[v] = counts.get(v, 0) + 1
    return sum(t * (t - 1) * (2 * t + 5) for t in counts.values())


def mk_var(x, y):
    n = len(y)
    return (n * (n - 1) * (2 * n + 5) - tie_term(y)) / 18.0


def theil_sen(x, y):
    """Slope, and Sen's rank-based 95% interval (ties in x and y removed from the variance, as in Sen 1968 / scipy)."""
    s = pairwise_slopes(x, y)
    slope = median(s)
    n = len(x)
    var = (n * (n - 1) * (2 * n + 5) - tie_term(x) - tie_term(y)) / 18.0
    c = Z975 * math.sqrt(var)
    nn = len(s)
    lo_i = int(round((nn - c) / 2.0)) - 1
    hi_i = int(round((nn + c) / 2.0))
    lo_i, hi_i = max(0, min(nn - 1, lo_i)), max(0, min(nn - 1, hi_i))
    return slope, s[lo_i], s[hi_i]


def mann_kendall_p(y):
    n = len(y)
    s = sum((y[j] > y[i]) - (y[j] < y[i]) for i in range(n) for j in range(i + 1, n))
    var = mk_var(list(range(n)), y)
    z = 0.0 if s == 0 else (s - 1) / math.sqrt(var) if s > 0 else (s + 1) / math.sqrt(var)
    return 2 * (1 - NormalDist().cdf(abs(z)))


def bh(p):
    m = len(p)
    order = sorted(range(m), key=lambda i: p[i])
    q = [0.0] * m
    running = 1.0
    for rank in range(m, 0, -1):
        i = order[rank - 1]
        running = min(running, p[i] * m / rank)
        q[i] = running
    return q


# ------------------------------------------------------------------ Giovanni record
def giovanni_monthly():
    rows = {}
    with open(GIOVANNI, newline="") as fh:
        started = False
        for r in csv.reader(fh):
            if not started:
                started = bool(r) and r[0].strip() == "time"
                continue
            if not r or not r[0].strip():
                continue
            d = dt.date.fromisoformat(r[0].strip()[:10])
            k = float(r[1])
            rows[(d.year, d.month)] = None if k >= 1e14 else k - 273.15
    return rows


def giovanni_seasons(m):
    """Returns {aggregate: [(year, value_c)]} for complete aggregates only."""
    def mean_of(keys):
        vals = [m.get(k) for k in keys]
        return None if any(v is None for v in vals) else sum(vals) / len(vals)
    out = {k: [] for k in ("ANN", "DJF", "MAM", "JJA", "SON", "octdec_mean_c", "janmar_mean_c")}
    for y in range(1979, 2026):
        spec = {"ANN": [(y, mm) for mm in range(1, 13)], "DJF": [(y - 1, 12), (y, 1), (y, 2)], "MAM": [(y, 3), (y, 4), (y, 5)],
                "JJA": [(y, 6), (y, 7), (y, 8)], "SON": [(y, 9), (y, 10), (y, 11)], "octdec_mean_c": [(y, 10), (y, 11), (y, 12)],
                "janmar_mean_c": [(y + 1, 1), (y + 1, 2), (y + 1, 3)]}
        for k, keys in spec.items():
            v = mean_of(keys)
            if v is not None:
                out[k].append((y, v))
    return out


# ------------------------------------------------------------------ Dettah road record
def dettah_open_days():
    import openpyxl  # only third-party dependency; reads dates exactly as published
    import warnings
    warnings.simplefilter("ignore")
    ws = openpyxl.load_workbook(ROADS, data_only=True)["Ice Roads"]
    col = None
    out = {}
    for r in ws.iter_rows(values_only=True):
        if col is None:
            for i, c in enumerate(r):
                if isinstance(c, str) and "Dettah" in c:
                    col = i
            continue
        lab = r[0]
        if isinstance(lab, str) and len(lab) == 7 and lab[4] == "/":
            y = int(lab[:4])
            o = r[col]
            if isinstance(o, dt.datetime):
                out[y] = (o.date() - dt.date(y, 10, 1)).days + 1
    return out


def main() -> int:
    ok = True
    print("== Giovanni MERRA-2 monthly T2M (raw CSV, own code) ==")
    m = giovanni_monthly()
    print(f"months {len(m)}, missing {sum(v is None for v in m.values())}, first {min(m)}, last {max(m)}, "
          f"Jan 1980 = {m[(1980, 1)]:.3f} C (242.269669 K - 273.15)")
    seasons = giovanni_seasons(m)
    stored = {}
    with open(os.path.join(ROOT, "UI", "data_real", "giovanni_monthly_t2m_trends.csv"), newline="") as fh:
        for r in csv.DictReader(fh):
            stored[r["metric"]] = r
    names, ps, res = [], [], {}
    for k, ser in seasons.items():
        x = [float(a) for a, _ in ser]
        # The production files store seasonal means to 4 decimals. At that precision JJA 2008 and 2013 tie, which moves the
        # JJA Mann-Kendall p from 0.5197 (full precision) to 0.5258 (stored) and MAM/JJA q from 0.606 to 0.613. No verdict changes.
        y = [round(b, 4) for _, b in ser]
        sl, lo, hi = theil_sen(x, y)
        p = mann_kendall_p(y)
        names.append(k)
        ps.append(p)
        res[k] = (len(y), x[0], x[-1], sl * 10, lo * 10, hi * 10, p)
    qs = dict(zip(names, bh(ps)))
    print(f"{'aggregate':<15}{'n':>4}{'years':>11}{'slope/dec':>11}{'95% CI':>18}{'p':>9}{'q(BH,7)':>9}   stored slope / q")
    for k in names:
        n, a, b, s, lo, hi, p = res[k]
        st = stored[k]
        agree = abs(s - float(st["slope_per_decade"])) < 0.002 and abs(qs[k] - float(st["q_bh_within_location"])) < 0.002 \
            and abs(lo - float(st["ci95_low"])) < 0.002 and abs(hi - float(st["ci95_high"])) < 0.002 and int(st["n"]) == n
        ok &= agree
        print(f"{k:<15}{n:>4}{int(a):>6}-{int(b):<4}{s:>+11.3f}   [{lo:+.3f}, {hi:+.3f}]{p:>9.4f}{qs[k]:>9.4f}   "
              f"{st['slope_per_decade']} / {st['q_bh_within_location']}  {'OK' if agree else 'MISMATCH'}")

    print("\n== Dettah ice road opening day (raw NWT workbook, own code; day 1 = Oct 1) ==")
    od = dettah_open_days()
    for first, last, want_slope in ((1993, 2024, 9.0), (2001, 2024, 10.3)):
        yrs = [y for y in sorted(od) if first <= y <= last]
        x, y = [float(v) for v in yrs], [float(od[v]) for v in yrs]
        sl, lo, hi = theil_sen(x, y)
        p = mann_kendall_p(y)
        agree = abs(sl * 10 - want_slope) < 0.06
        ok &= agree
        print(f"{first}/{(first + 1) % 100:02d}-{last}/{(last + 1) % 100:02d}: n={len(y)} slope {sl * 10:+.2f} d/decade, "
              f"95% CI [{lo * 10:+.2f}, {hi * 10:+.2f}], MK p={p:.4f}   approved {want_slope:+.1f}  {'OK' if agree else 'MISMATCH'}")
    print("\nRESULT:", "all independent values agree with the app" if ok else "DISAGREEMENT FOUND")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
