"""JSON-safe conversion of analysis objects. NaN and infinities become null; numpy scalars become Python numbers."""
from __future__ import annotations

import dataclasses
import math

import numpy as np
import pandas as pd


def clean(x):
    """Recursively convert to JSON-safe values. Missing values are null, never zero."""
    if x is None or isinstance(x, (bool, str)):
        return x
    if isinstance(x, (np.bool_,)):
        return bool(x)
    if isinstance(x, (int, np.integer)):
        return int(x)
    if isinstance(x, (float, np.floating)):
        v = float(x)
        return v if math.isfinite(v) else None
    if dataclasses.is_dataclass(x) and not isinstance(x, type):
        return {f.name: clean(getattr(x, f.name)) for f in dataclasses.fields(x)}
    if isinstance(x, dict):
        return {str(k): clean(v) for k, v in x.items()}
    if isinstance(x, (list, tuple, set)):
        return [clean(v) for v in x]
    if isinstance(x, np.ndarray):
        return [clean(v) for v in x.tolist()]
    if isinstance(x, pd.DataFrame):
        return records(x)
    if isinstance(x, pd.Series):
        return [clean(v) for v in x.tolist()]
    if x is pd.NA or x is pd.NaT:
        return None
    return str(x)


def records(df: pd.DataFrame) -> list:
    return [{str(k): clean(v) for k, v in row.items()} for row in df.to_dict(orient="records")]


def table(columns: list, rows: list) -> dict:
    """A display table: ordered column names and rows of display values (as the Streamlit dataframes showed them)."""
    return {"columns": list(columns), "rows": [clean([r.get(c) for c in columns]) for r in rows]}


def frame_table(df: pd.DataFrame) -> dict:
    return table(list(df.columns), df.to_dict(orient="records"))
