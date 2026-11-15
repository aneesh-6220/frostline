"""Frostline - by Strongest Soldiers. Production entrypoint.

Run from the repository root:

    streamlit run UI/frostline_app.py

The app reads only the approved files in UI/data_real (docs/APP_IMPLEMENTATION_CONTRACT.md). If a required
file is missing, unreadable or flagged synthetic it shows an error naming the file and renders nothing else.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st  # noqa: E402

from frostline import APP_NAME, TEAM_NAME, data, ui  # noqa: E402
from frostline.views import atlas, brief_view, compare, corridor, demo, detective, evidence_view, giovanni_view, methods, observatory, questions  # noqa: E402

st.set_page_config(page_title="Frostline - by Strongest Soldiers", page_icon=os.path.join(ui.ASSETS, "mark.svg"), layout="wide", initial_sidebar_state="auto")
ui.inject_theme()
ui.brand()

try:
    ds = data.load_dataset()
except data.DataError as exc:
    st.error(f"Frostline cannot start: required data file **{exc.filename}** is not usable ({exc.reason}). "
             "No values are shown and no other data are substituted. Restore the file with `python3 -I scripts/regenerate_all.py`.", icon=":material/error:")
    st.stop()

ui.init_state(ds)

VIEWS = [
    ("observatory", "Observatory", observatory, ":material/ac_unit:"),
    ("demo", "Guided demo", demo, ":material/play_circle:"),
    ("atlas", "Map", atlas, ":material/map:"),
    ("questions", "Questions", questions, ":material/help:"),
    ("detective", "Trend Detective", detective, ":material/show_chart:"),
    ("compare", "Compare", compare, ":material/compare_arrows:"),
    ("giovanni", "Giovanni record", giovanni_view, ":material/satellite_alt:"),
    ("corridor", "Corridor", corridor, ":material/route:"),
    ("evidence", "Evidence", evidence_view, ":material/fact_check:"),
    ("brief", "Brief", brief_view, ":material/description:"),
    ("methods", "Methods", methods, ":material/menu_book:"),
]


def _page(key, title, module, icon, default):
    def run():
        module.render(ds)
    run.__name__ = f"view_{key}"
    return st.Page(run, title=title, icon=icon, url_path=key, default=default)


start = st.session_state.get("start_view", "observatory")
if start not in {v[0] for v in VIEWS}:
    start = "observatory"
ui.PAGES.clear()
for key, title, module, icon in VIEWS:
    ui.PAGES[key] = _page(key, title, module, icon, key == start)

nav = st.navigation(list(ui.PAGES.values()), position="top")
try:
    ui.console(ds)
    nav.run()
except data.DataError as exc:
    st.error(f"This view cannot be shown: data file **{exc.filename}** failed a consistency check ({exc.reason}). No values are displayed for it.", icon=":material/error:")
    st.stop()
ui.footer()
ui.tabbar(next((k for k, p in ui.PAGES.items() if p.title == nav.title), None))
