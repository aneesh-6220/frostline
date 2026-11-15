"""Frostline application package (Strongest Soldiers, NASA Space Apps 2026).

Layers, from data to screen:
  schema.py    required files and columns of UI/data_real
  data.py      strict loader: hard failure on missing, unreadable or synthetic data; no fallback
  registry.py  locations, variables, guiding questions and source citations
  analysis.py  investigation objects built with the approved statistics in scripts/northlink_*.py
  evidence.py  the Evidence Engine: structured, source-derived evidence assessment
  brief.py     the downloadable Evidence Brief (HTML, CSV, JSON) from the same analysis objects
  charts.py    Plotly figures
  ui.py        shared Streamlit components and the shared investigation state
  views/       one module per application view

No module in this package implements a statistical method. Trend estimates come from
northlink_recompute.period_trend (Theil-Sen, Mann-Kendall, moving-block bootstrap).
"""

APP_NAME = "Frostline"
TEAM_NAME = "Strongest Soldiers"
TAGLINE = "Trace the evidence behind changing winters."
APP_VERSION = "1.0.0"
METHOD_ID = "frostline-trend-v1 (Theil-Sen slope, Mann-Kendall test, moving-block bootstrap, seed 20261114)"
