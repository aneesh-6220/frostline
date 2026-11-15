> **WARNING: `UI/data/`, `UI/generate_data.py` and `UI/standalone_prototype.html` are a legacy PROTOTYPE on SYNTHETIC data.**
> Every row in `UI/data/` has `synthetic=true`, and the standalone prototype contains a James Bay threshold metric that is not valid for the NWT. None of these files is read, imported or served by the Frostline application. Do not show them to anyone as results. They remain only because existing tests check that they stay flagged as synthetic.

# Frostline - by Strongest Soldiers: application

*Trace the evidence behind changing winters.*

The production application is `frostline_app.py`. It reads only the approved real data in `data_real/` and stops with a visible error if a required file is missing, unreadable or flagged synthetic. There is no fallback.

## Run

From the repository root, with Python 3.12:

```bash
pip install -r UI/requirements.txt
streamlit run UI/frostline_app.py
```

`northlink_app.py` is a launcher kept for the earlier file name; it runs the same application.

## Views

| View | What it does |
|---|---|
| Observatory | Landing screen with a live NASA chart and indicators computed from the data |
| Guided demo | Six stages through the production components: problem, geography, NASA data, finding, transportation evidence, Evidence Brief |
| Atlas | Map of the two documented locations and their NASA grid cells; select by marker or list |
| Questions | Plain questions mapped to catalogued variables, with the variable catalogue |
| Trend Detective | Historical series, rate of change per decade, intervals, significance and evidence state for the selection |
| Compare | The same variable at two locations on matched winters, with a test on the difference |
| Corridor | Road history, environmental record, timeline, associations, all NWT routes, evidence conclusion |
| Evidence | The Evidence Engine, the source disagreement explorer and the multiple-testing audit |
| Brief | Preview and download of the Evidence Brief (HTML, CSV, JSON) |
| Methods | Methods, data and citations, NASA resource status, AI-use disclosure, limits, extension guide |

## Structure

`frostline/` holds the package: `data.py` (strict loader), `registry.py` (locations, variables, questions, sources), `analysis.py` (findings built with the approved statistics in `scripts/`), `evidence.py` (Evidence Engine), `brief.py` (exports), `charts.py`, `ui.py` and `views/`. See `docs/EXTENDING_FROSTLINE.md` and `docs/FROSTLINE_IMPLEMENTATION_MATRIX.md`.

## Tests

```bash
python3 -I -m unittest discover -s tests
```

`tests/test_frostline_app.py` holds the application acceptance tests.
