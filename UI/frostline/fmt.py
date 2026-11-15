"""Display formatting shared by the interface and the Evidence Brief, so the two can never disagree.

Full precision stays in the data; rounding happens only here (docs/SCIENTIFIC_METHODS.md section L).
"""
from __future__ import annotations

import datetime as dt
import math

NOT_ESTIMATED = "not estimated"


def is_num(x) -> bool:
    return x is not None and isinstance(x, (int, float)) and not (isinstance(x, float) and math.isnan(x))


def num(x, decimals: int = 1, signed: bool = False) -> str:
    if not is_num(x):
        return NOT_ESTIMATED
    v = round(float(x), decimals)
    if v == 0:
        v = 0.0  # never print a negative zero
    return f"{v:+.{decimals}f}" if signed else f"{v:.{decimals}f}"


def interval(lo, hi, decimals: int = 1) -> str:
    if not (is_num(lo) and is_num(hi)):
        return NOT_ESTIMATED
    return f"{num(lo, decimals)} to {num(hi, decimals)}"


def pval(p) -> str:
    """p-values to 3 decimals, '<0.001' below that."""
    if not is_num(p):
        return NOT_ESTIMATED
    return "<0.001" if p < 0.001 else f"{p:.3f}"


def winter(y: int) -> str:
    """Winter y runs Oct 1 of y to Mar 31 of y+1 and is written 2001/02."""
    return f"{int(y)}/{str(int(y) + 1)[-2:]}"


def period(first: int, last: int) -> str:
    return f"{winter(first)} to {winter(last)}"


def day_to_date_label(day, season_start_year: int | None = None) -> str:
    """Day number (days since Oct 1) as a calendar label. A non-leap reference year is used when no winter is given."""
    if not is_num(day):
        return NOT_ESTIMATED
    base = dt.date(season_start_year if season_start_year else 2001, 10, 1)
    d = base + dt.timedelta(days=int(round(day)))
    return f"{d.strftime('%b')} {d.day}"


def iso_to_label(iso: str) -> str:
    d = dt.date.fromisoformat(str(iso)[:10])
    return f"{d.strftime('%b')} {d.day}, {d.year}"


def count(n) -> str:
    return f"{int(n):,}"
