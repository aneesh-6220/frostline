"""Light theme for the unchanged frostline.charts figures.

frostline/charts.py builds every figure (data, hover text, annotations, axes) for a dark surface. The web frontend
is light, so the figure JSON is recoloured here, token for token, before it is sent. Only colours and the font
family change; no trace, value, label or geometry is touched.
"""
from __future__ import annotations

import json
import re

FONT = "'Geist Variable', 'Geist', Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"

# exact strings first (tokens that share an RGB base but play different roles)
EXACT = {
    "rgba(163,174,189,0.14)": "rgba(37,99,235,0.10)",     # BAND: 95% slope interval -> soft blue
    "rgba(163,174,189,0.09)": "rgba(15,23,42,0.06)",      # GRID
    "rgba(163,174,189,0.28)": "rgba(15,23,42,0.22)",      # AXIS
}

# dark token RGB -> light token RGB (alpha is kept)
RGB = {
    (11, 14, 19): (255, 255, 255),      # BG (marker rings, hollow markers)
    (18, 22, 29): (255, 255, 255),      # SURFACE
    (231, 236, 242): (11, 23, 54),      # INK and TREND -> deep navy
    (163, 174, 189): (71, 85, 105),     # INK_2 -> slate 600
    (125, 136, 152): (100, 116, 139),   # INK_3 / NEUTRAL -> slate 500
    (76, 155, 232): (37, 99, 235),      # C_PRIMARY / COLD -> primary blue
    (224, 119, 63): (234, 88, 12),      # C_SECOND -> orange 600 (keeps the entity contrast with blue)
    (76, 195, 138): (5, 150, 105),      # C_THIRD -> emerald 600
    (229, 180, 84): (217, 119, 6),      # WARN -> amber 600
    (224, 119, 106): (220, 38, 38),     # WARM -> red 600
    (27, 33, 43): (255, 255, 255),      # HOVER_BG
    (46, 54, 68): (226, 232, 240),      # HOVER_LINE
}

_HEX = re.compile(r"^#([0-9a-fA-F]{6})$")
_RGBA = re.compile(r"^rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(?:,\s*([0-9.]+)\s*)?\)$")


def _recolour(s: str) -> str:
    key = s.replace(" ", "")
    if key in EXACT:
        return EXACT[key]
    m = _HEX.match(s)
    if m:
        h = m.group(1)
        rgb = (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
        if rgb in RGB:
            r, g, b = RGB[rgb]
            return f"#{r:02X}{g:02X}{b:02X}"
        return s
    m = _RGBA.match(s)
    if m:
        rgb = tuple(int(m.group(i)) for i in (1, 2, 3))
        if rgb in RGB:
            r, g, b = RGB[rgb]
            a = m.group(4)
            return f"rgba({r},{g},{b},{a})" if a is not None else f"rgb({r},{g},{b})"
    return s


def _walk(x, key=""):
    if isinstance(x, dict):
        return {k: _walk(v, k) for k, v in x.items()}
    if isinstance(x, list):
        return [_walk(v, key) for v in x]
    if isinstance(x, str):
        if key == "family":
            return FONT
        return _recolour(x)
    return x


def themed(fig) -> dict:
    """Plotly figure -> JSON-ready dict {data, layout} in the light palette."""
    d = json.loads(fig.to_json())
    d.get("layout", {}).pop("template", None)
    d = _walk(d)
    layout = d.setdefault("layout", {})
    layout["autosize"] = True
    layout.pop("width", None)
    layout.setdefault("hoverlabel", {})["bordercolor"] = "#E2E8F0"
    return {"data": d.get("data", []), "layout": layout}
