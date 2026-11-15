# Frostline - by Strongest Soldiers

*Trace the evidence behind changing winters.*

NASA Space Apps 2026 (Halifax), challenge "Be An Earth System Trend Detective!".
Question: how are freezing-season conditions (NASA POWER / MERRA-2 reanalysis) and recorded ice-road opening and closing dates changing in the Northwest Territories, and are the changes statistically supported? Exploratory analysis. Not a safety, ice-thickness or prediction tool.

Start with `docs/FABLE_52_START_HERE.md` (single entry point), then `docs/FABLE_HANDOFF_FINAL.md` and `docs/APP_IMPLEMENTATION_CONTRACT.md`. Approved findings: `docs/APPROVED_FINDINGS.md` (generated). Submission draft: `submission/SUBMISSION_DRAFT.md`. Rules for what may be claimed: `docs/SCIENTIFIC_METHODS.md`. Numbers: `docs/RESULTS.md` (generated).

Status: the Frostline application is built on the real data in `UI/data_real/` (branch `frostline-implementation`). Run it from the repository root with `pip install -r UI/requirements.txt` and `streamlit run UI/frostline_app.py` (Python 3.12). What is implemented, how each feature was verified and what is still open: `docs/FROSTLINE_IMPLEMENTATION_MATRIX.md`. Submission assets: `submission/`. Still open: public deployment, the NASA listed-resource extraction (Giovanni) and statistical sign-off. The files under `UI/data/` are a legacy synthetic prototype that the application never reads (see `UI/README.md`).

Reproduce everything from the cached raw data (no network): `python3 -I scripts/regenerate_all.py`
Check that committed outputs match: `python3 -I scripts/regenerate_all.py --check`
Run the tests: `python3 -I -m unittest discover -s tests -v`
