"""Frostline web API: a read-only JSON layer over the unchanged `frostline` package.

The React frontend in UI/frontend talks only to this API. Nothing here computes a statistic: every number comes
from frostline.analysis / evidence / brief (and through them the approved scripts/northlink_*.py), and every
display string is formatted with frostline.fmt exactly as the Streamlit views formatted it.
"""
