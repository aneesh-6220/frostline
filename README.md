# NorthLink

NASA Space Apps 2026 (Halifax), challenge "Be An Earth System Trend Detective!".
How are freezing conditions changing along northern Canadian ice roads, are the trends statistically supported, and how do they compare with recorded road opening and closing dates? Not a safety or prediction tool.

Start with `docs/HANDOFF_README.md`. Status: road data, methods, tested metric code are done; the NASA daily temperature file (`data/processed/nasa_daily_temperature.csv`) still has to be downloaded.

Run the tests: `python3 -I -m unittest discover -s tests -v`
