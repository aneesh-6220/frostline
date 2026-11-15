"""Strict loader for the approved application data in UI/data_real.

Rules (docs/APP_IMPLEMENTATION_CONTRACT.md section 1):
  * only this directory is read; the app makes no network call for data and never writes here;
  * a missing or unreadable required file, a missing required column, an empty table or any row with
    synthetic == True raises DataError naming the file; callers show the error and stop. No fallback exists;
  * optional Giovanni files are loaded only when all of them are present.

The directory can be pointed elsewhere with FROSTLINE_DATA_DIR. That is explicit configuration for tests and
for a regenerated copy of the same files; it is never used as an automatic fallback.
"""
from __future__ import annotations

import functools
import hashlib
import json
import os
from dataclasses import dataclass, field

import pandas as pd

from .schema import OPTIONAL_FILES, REQUIRED_COLUMNS, REQUIRED_JSON

UI_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO_ROOT = os.path.dirname(UI_DIR)
DEFAULT_DATA_DIR = os.path.join(UI_DIR, "data_real")


class DataError(Exception):
    """A required data file is absent or unusable. The message names the file."""

    def __init__(self, filename: str, reason: str):
        self.filename = filename
        self.reason = reason
        super().__init__(f"{filename}: {reason}")


def data_dir() -> str:
    return os.path.abspath(os.environ.get("FROSTLINE_DATA_DIR") or DEFAULT_DATA_DIR)


@dataclass(frozen=True)
class Dataset:
    directory: str
    tables: dict = field(repr=False)
    facts: dict = field(repr=False)
    file_hashes: dict = field(repr=False)
    digest: str = ""
    giovanni: dict | None = field(default=None, repr=False)

    def __getitem__(self, name: str) -> pd.DataFrame:
        key = name if name.endswith(".csv") else name + ".csv"
        return self.tables[key]

    def __hash__(self):
        return hash((self.directory, self.digest))

    def __eq__(self, other):
        return isinstance(other, Dataset) and (self.directory, self.digest) == (other.directory, other.digest)


def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def _read_csv(directory: str, name: str, columns) -> pd.DataFrame:
    path = os.path.join(directory, name)
    if not os.path.isfile(path):
        raise DataError(name, "required data file is missing")
    try:
        df = pd.read_csv(path)
    except Exception as exc:  # unreadable or malformed
        raise DataError(name, f"file could not be read ({type(exc).__name__})") from exc
    missing = [c for c in columns if c not in df.columns]
    if missing:
        raise DataError(name, "required column(s) missing: " + ", ".join(missing))
    if len(df) == 0:
        raise DataError(name, "file has no rows")
    if "synthetic" in df.columns and df["synthetic"].astype(str).str.strip().str.lower().eq("true").any():
        raise DataError(name, "contains rows flagged synthetic; synthetic values are never displayed")
    return df


def _signature(directory: str) -> tuple:
    sig = []
    for name in list(REQUIRED_COLUMNS) + list(REQUIRED_JSON) + list(OPTIONAL_FILES):
        path = os.path.join(directory, name)
        try:
            st = os.stat(path)
            sig.append((name, st.st_size, st.st_mtime_ns))
        except OSError:
            sig.append((name, None, None))
    return tuple(sig)


@functools.lru_cache(maxsize=8)
def _load(directory: str, signature: tuple) -> Dataset:
    tables, hashes = {}, {}
    for name, columns in REQUIRED_COLUMNS.items():
        tables[name] = _read_csv(directory, name, columns)
        hashes[name] = _sha256(os.path.join(directory, name))
    facts = None
    for name in REQUIRED_JSON:
        path = os.path.join(directory, name)
        if not os.path.isfile(path):
            raise DataError(name, "required data file is missing")
        try:
            with open(path, encoding="utf-8") as fh:
                facts = json.load(fh)
        except Exception as exc:
            raise DataError(name, f"file could not be read ({type(exc).__name__})") from exc
        for key in ("bias_caveat", "bias", "periods", "locations", "status_counts", "extended_126", "all_routes_family", "families", "thaw", "snow", "leakage"):
            if key not in facts:
                raise DataError(name, f"required key missing: {key}")
        hashes[name] = _sha256(path)
    giovanni = None
    present = [n for n in OPTIONAL_FILES if os.path.isfile(os.path.join(directory, n))]
    if len(present) == len(OPTIONAL_FILES):
        giovanni = {}
        for name in OPTIONAL_FILES:
            try:
                giovanni[name] = pd.read_csv(os.path.join(directory, name))
            except Exception as exc:
                raise DataError(name, f"optional Giovanni file could not be read ({type(exc).__name__})") from exc
            hashes[name] = _sha256(os.path.join(directory, name))
    digest = hashlib.sha256("".join(f"{k}:{hashes[k]}\n" for k in sorted(hashes)).encode()).hexdigest()[:16]
    return Dataset(directory=directory, tables=tables, facts=facts, file_hashes=hashes, digest=digest, giovanni=giovanni)


def load_dataset(directory: str | None = None) -> Dataset:
    """Load and validate every required file. Raises DataError; never substitutes other data."""
    d = os.path.abspath(directory) if directory else data_dir()
    if not os.path.isdir(d):
        raise DataError(os.path.basename(d) or d, "data directory is missing")
    return _load(d, _signature(d))


def code_version() -> str:
    """Short git commit of the running code, or 'unknown' outside a git checkout."""
    try:
        import subprocess

        r = subprocess.run(["git", "rev-parse", "--short=12", "HEAD"], cwd=REPO_ROOT, capture_output=True, text=True, timeout=5)
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()
    except Exception:
        pass
    return "unknown"
