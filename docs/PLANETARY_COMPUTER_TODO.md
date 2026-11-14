# TODO for the next collaborator: MODIS satellite data from Microsoft Planetary Computer

**Status: OPTIONAL and NOT in the dataset. It is not required for the app and is not itself an official challenge resource (see `docs/CHALLENGE_ELIGIBILITY.md`).** Original note: **NOT in the dataset yet. Everything in `data/processed/` is NASA POWER (MERRA-2-derived) + ECCC stations + NWT road records.** The pull was started and deliberately stopped by the team lead; nothing partial was saved or committed.

## Why it is worth finishing
Gives a true satellite (NASA MODIS) record: 8-day snow cover and lake-ice class at the road point (10A2) and day/night land-surface temperature (11A2), 2001-2024 winters. This directly tests the snow-insulation hypothesis from `snow_vs_opening.csv` (the leak-free snow association in `docs/APPROVED_FINDINGS.md` section D) and closes the "no satellite data" gap.

## How (about 20 minutes, public, no login, read-only requests)
1. Open `https://planetarycomputer.microsoft.com/api/stac/v1/collections/modis-11A2-061` in a normal browser (must stay on that origin; shell and WebFetch cannot reach it).
2. Paste `scripts/planetary_computer_modis_pull.js` into the DevTools console. It runs 432 jobs (9 corridors x 2 collections x 24 winters), about 20k small requests.
3. Check `window.__job.done` / `.total`. When `.finished` is true, re-run anything in `window.__job.errors` (transient fetch failures; one known "no feats deline modis-11A2 2001" is probably just no scene).
4. Export `window.__job.rows` to CSV (columns in the script header) and save as `data/raw/nasa/modis_pc_points_2001_2024.csv`.

## Gotchas (learned the hard way)
- The 10A2 collection contains BOTH Terra (MOD) and Aqua (MYD). Same date can show different values (e.g. Terra "snow 200" vs Aqua "lake ice 100"). Always keep the sensor column and never mix them in one series.
- Only the tile that contains the point works (Dettah = h12v02, Aklavik = h13v02, close to a tile edge). Other tiles return 424 "outside dataset bounds".
- LST raw value x 0.02 = Kelvin; 0 = no data. Snow class codes: 25 no snow, 37 lake, 50 cloud, 100 lake ice, 200 snow.
- One pixel at an approximate point (500 m snow, 1 km LST). Dettah and Aklavik points are on ice-road lakes/channels (exactly what we want); the 7 supplementary points are approximate, so treat them as indicative.
- Cloud and polar night remove many winter samples: compute season metrics only from windows with enough valid composites, and state the coverage.

## Then
Compute per winter: fraction of valid Oct-Dec composites classed lake ice / snow, first composite with lake-ice class, Mar-Apr snow-loss date, mean night LST Oct-Dec. Use the same Theil-Sen/Mann-Kendall functions in `scripts/northlink_metrics.py`, add rows to `docs/RESULTS.md`, and keep claims exploratory.
