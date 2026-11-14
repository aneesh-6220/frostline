# NorthLink · UI

Frontend implementation and interactive interfaces for NorthLink: winter climate trend intelligence for northern Canadian seasonal roads.

## Structure

- `northlink_app.py`: Complete 6-part NorthLink user journey implemented in Streamlit:
  1. Corridor overview with keyless CARTO Positron Leaflet map and northern Canada overview.
  2. Environmental metric selector (Freezing Degree-Days, Thaw-Day Count, and 380 °C-day threshold date for James Bay).
  3. Interactive historical chart with annual observations, OLS regression trend line, and 95% confidence band.
  4. Trend magnitude and uncertainty cards with Mann-Kendall rank correlation test and operating window takeaways.
  5. Optional comparative view across shared historical seasons (1994–2024).
  6. Comprehensive Evidence Audit with quality control protocols, NASA POWER REST query specifications, and analytical limitations.
- `requirements.txt`: Python package dependencies (`streamlit`, `pandas`, `altair`, `numpy`).
- `data/`: Locked-schema dataset containing:
  - `corridors.csv`
  - `climate_annual.csv`
  - `road_seasons.csv`
  - `trends.csv`
- `standalone_prototype.html`: Lightweight, zero-dependency standalone HTML prototype with Leaflet basemap.

## Running the Application

```bash
pip install -r requirements.txt
streamlit run northlink_app.py
```
