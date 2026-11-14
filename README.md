# NorthLink

NASA Space Apps 2026 (Halifax), challenge "Be An Earth System Trend Detective!".
Question: how are freezing-season conditions (NASA POWER / MERRA-2 reanalysis) and recorded ice-road opening and closing dates changing in the Northwest Territories, and are the changes statistically supported? Exploratory analysis. Not a safety, ice-thickness or prediction tool.

Start with `docs/FABLE_52_START_HERE.md` (single entry point), then `docs/FABLE_HANDOFF_FINAL.md` and `docs/APP_IMPLEMENTATION_CONTRACT.md`. Approved findings: `docs/APPROVED_FINDINGS.md` (generated). Submission draft: `submission/SUBMISSION_DRAFT.md`. Rules for what may be claimed: `docs/SCIENTIFIC_METHODS.md`. Numbers: `docs/RESULTS.md` (generated).

Status: data, statistics, documentation and tests are complete for the remediation described in the handoff; open items are listed there. The Streamlit prototype in `UI/` still runs on synthetic data (`UI/data/`) and must not be shown as real until it is repointed to `UI/data_real/` (see `UI/README.md`).

Reproduce everything from the cached raw data (no network): `python3 -I scripts/regenerate_all.py`
Check that committed outputs match: `python3 -I scripts/regenerate_all.py --check`
Run the tests: `python3 -I -m unittest discover -s tests -v`
