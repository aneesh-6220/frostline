# Frostline - by Strongest Soldiers

*Trace the evidence behind changing winters.*

NASA Space Apps 2026 (Halifax), challenge "Be An Earth System Trend Detective!".
Question: how are freezing-season conditions (NASA POWER / MERRA-2 reanalysis) and recorded ice-road opening and closing dates changing in the Northwest Territories, and are the changes statistically supported? Exploratory analysis. Not a safety, ice-thickness or prediction tool.

Start with `docs/FABLE_52_START_HERE.md` (single entry point), then `docs/FABLE_HANDOFF_FINAL.md` and `docs/APP_IMPLEMENTATION_CONTRACT.md`. Approved findings: `docs/APPROVED_FINDINGS.md` (generated). Submission draft: `submission/SUBMISSION_DRAFT.md`. Rules for what may be claimed: `docs/SCIENTIFIC_METHODS.md`. Numbers: `docs/RESULTS.md` (generated).

Status: the Frostline application is built on the real data in `UI/data_real/`. The current app lives on `main`. Run it from the repository root with `pip install -r UI/requirements.txt` and `streamlit run UI/frostline_app.py` (Python 3.12). What is implemented, how each feature was verified and what is still open: `docs/FROSTLINE_IMPLEMENTATION_MATRIX.md`. Submission assets: `submission/`. The NASA Giovanni MERRA-2 monthly record (1980 to 2025) is integrated; see `docs/SCIENTIFIC_METHODS.md` section M. Still open: public deployment, statistical sign-off and the eligibility record in `docs/CHALLENGE_ELIGIBILITY.md`. The files under `UI/data/` are a legacy synthetic prototype that the application never reads (see `UI/README.md`).

Branches: `main` is the current app. `remediation-final`, `fable-ready`, `frostline-implementation`, `frostline-global-audit`, `frostline-map-giovanni-release` and `alternative-ui` are earlier stages kept for history; `docs/FABLE_52_START_HERE.md` describes the hand-off as it stood when `fable-ready` was cut. `presentation-improvements` adds plain-language answers, verdict badges, axis reading hints, a three-step story and a global-context panel on the home page.

Reproduce everything from the cached raw data (no network): `python3 -I scripts/regenerate_all.py`
Check that committed outputs match: `python3 -I scripts/regenerate_all.py --check`
Run the tests: `python3 -I -m unittest discover -s tests -v`
