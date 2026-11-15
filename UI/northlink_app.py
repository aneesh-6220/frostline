"""Compatibility launcher for the earlier entrypoint file name.

The Frostline application is UI/frostline_app.py, which calls
st.set_page_config(page_title="Frostline - by Strongest Soldiers"). This file is kept only so that older
commands and deployment settings that name it keep working; it runs the same production app.

The legacy synthetic prototype that used to live here (including its James Bay threshold metric) has been
removed. The production app reads only UI/data_real and has no synthetic fallback.
"""
import os
import runpy

runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), "frostline_app.py"), run_name="__main__")
