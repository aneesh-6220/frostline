"""Statistical helpers for the Frostline remediation analysis (multiple testing, dependence-aware CIs).

Pure numpy/scipy. Deterministic: every resampling function takes an explicit seed.
Conventions: trends are per decade; years are winter start years.
"""
from __future__ import annotations

import math

import numpy as np
from scipy import stats


def bh_adjust(p) -> np.ndarray:
    """Benjamini-Hochberg adjusted p-values (q-values). NaN inputs stay NaN and are excluded from m."""
    p = np.asarray(p, float)
    out = np.full(p.shape, np.nan)
    ok = ~np.isnan(p)
    pv = p[ok]
    m = len(pv)
    if m == 0:
        return out
    order = np.argsort(pv)
    ranked = pv[order] * m / np.arange(1, m + 1)
    q = np.minimum.accumulate(ranked[::-1])[::-1]
    res = np.empty(m)
    res[order] = np.minimum(q, 1.0)
    out[ok] = res
    return out


def holm_adjust(p) -> np.ndarray:
    """Holm step-down adjusted p-values (family-wise error control)."""
    p = np.asarray(p, float)
    out = np.full(p.shape, np.nan)
    ok = ~np.isnan(p)
    pv = p[ok]
    m = len(pv)
    if m == 0:
        return out
    order = np.argsort(pv)
    adj = np.maximum.accumulate((m - np.arange(m)) * pv[order])
    res = np.empty(m)
    res[order] = np.minimum(adj, 1.0)
    out[ok] = res
    return out


def _theil_sen_slope(x: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    i, j = np.triu_indices(len(x), 1)
    dx = x[j] - x[i]
    keep = dx != 0
    slope = float(np.median((y[j] - y[i])[keep] / dx[keep]))
    return slope, float(np.median(y - slope * x))


def block_length(n: int) -> int:
    """Rule-of-thumb block length for short series: ceil(n^(1/3)) (n=24 -> 3, n=32 -> 4)."""
    return max(2, int(math.ceil(n ** (1.0 / 3.0))))


def block_bootstrap_slope(years, values, n_boot: int = 2000, seed: int = 20261114, level: float = 0.95):
    """Moving-block bootstrap of Theil-Sen residuals. Returns (slope_per_decade, lo, hi, block_len).

    Resamples blocks of consecutive residuals about the fitted Theil-Sen line, which keeps short-range
    serial dependence in the residuals. Assumes the trend is linear. NaNs are dropped first.
    """
    x = np.asarray(years, float)
    y = np.asarray(values, float)
    ok = ~(np.isnan(x) | np.isnan(y))
    x, y = x[ok], y[ok]
    n = len(y)
    if n < 10 or np.unique(y).size < 3:
        return (float("nan"),) * 3 + (0,)
    slope, icpt = _theil_sen_slope(x, y)
    fit = icpt + slope * x
    resid = y - fit
    L = block_length(n)
    nblocks = int(math.ceil(n / L))
    rng = np.random.default_rng(seed)
    starts = rng.integers(0, n - L + 1, size=(n_boot, nblocks))
    idx = (starts[:, :, None] + np.arange(L)[None, None, :]).reshape(n_boot, -1)[:, :n]
    ystar = fit[None, :] + resid[idx]
    i, j = np.triu_indices(n, 1)
    dx = x[j] - x[i]
    keep = dx != 0
    sl = np.median((ystar[:, j][:, keep] - ystar[:, i][:, keep]) / dx[keep][None, :], axis=1)
    a = (1 - level) / 2
    return slope * 10, float(np.quantile(sl, a) * 10), float(np.quantile(sl, 1 - a) * 10), L


def block_bootstrap_spearman(x, y, n_boot: int = 2000, seed: int = 20261114, level: float = 0.95):
    """Moving-block bootstrap of paired (x, y) observations ordered by year. Returns (rho, lo, hi, n, block_len)."""
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    ok = ~(np.isnan(x) | np.isnan(y))
    x, y = x[ok], y[ok]
    n = len(x)
    if n < 10 or np.unique(x).size < 3 or np.unique(y).size < 3:
        return (float("nan"),) * 3 + (n, 0)
    rho = float(stats.spearmanr(x, y)[0])
    L = block_length(n)
    nblocks = int(math.ceil(n / L))
    rng = np.random.default_rng(seed)
    starts = rng.integers(0, n - L + 1, size=(n_boot, nblocks))
    idx = (starts[:, :, None] + np.arange(L)[None, None, :]).reshape(n_boot, -1)[:, :n]
    vals = []
    for row in idx:
        xs, ys = x[row], y[row]
        if np.unique(xs).size < 2 or np.unique(ys).size < 2:
            continue
        vals.append(stats.spearmanr(xs, ys)[0])
    a = (1 - level) / 2
    vals = np.asarray(vals)
    return rho, float(np.quantile(vals, a)), float(np.quantile(vals, 1 - a)), n, L


def modal_fraction(v) -> float:
    v = np.asarray(v, float)
    v = v[~np.isnan(v)]
    if len(v) == 0:
        return float("nan")
    return float(np.unique(v, return_counts=True)[1].max() / len(v))
