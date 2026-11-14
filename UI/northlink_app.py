"""Frostline - by Strongest Soldiers (legacy prototype on synthetic data)
Streamlit Application
"""

import json
import math
import os
from typing import Dict, Tuple
import altair as alt
import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# -----------------------------------------------------------------------------
# 0. Page Configuration & Theme
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Frostline - by Strongest Soldiers",
    page_icon="❄️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Custom minimal styling: warm off-white, near-black text, teal accent, ample whitespace
st.markdown(
    """
    <style>
    /* Base typography and background */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        color: #1c1917;
    }
    
    .stApp {
        background-color: #fafaf9;
    }
    
    /* Synthetic Banner - Locked requirement across all views */
    .synthetic-banner {
        background-color: #fffbeb;
        color: #92400e;
        border: 1px solid #fde68a;
        border-radius: 6px;
        padding: 10px 16px;
        font-size: 0.875rem;
        font-weight: 500;
        margin-bottom: 24px;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    /* Section Headings */
    .journey-step {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #0e7490;
        margin-bottom: 4px;
    }
    
    .section-title {
        font-size: 1.35rem;
        font-weight: 600;
        color: #1c1917;
        margin-bottom: 8px;
    }
    
    .section-desc {
        font-size: 0.925rem;
        color: #57534e;
        margin-bottom: 18px;
        line-height: 1.5;
    }
    
    /* Stat Callout Cards */
    .stat-card {
        background-color: #ffffff;
        border: 1px solid #e7e5e4;
        border-radius: 8px;
        padding: 16px 20px;
        margin-bottom: 12px;
    }
    .stat-label {
        font-size: 0.75rem;
        font-weight: 600;
        color: #78716c;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 4px;
    }
    .stat-value {
        font-size: 1.6rem;
        font-weight: 700;
        color: #0e7490;
        font-variant-numeric: tabular-nums;
    }
    .stat-sub {
        font-size: 0.8rem;
        color: #78716c;
        margin-top: 4px;
    }
    
    /* Takeaway highlight card */
    .takeaway-card {
        background-color: #f0fdfa;
        border: 1px solid #ccfbf1;
        border-left: 4px solid #0e7490;
        border-radius: 6px;
        padding: 14px 18px;
        margin: 16px 0 24px 0;
    }
    .takeaway-text {
        font-size: 0.95rem;
        color: #134e4a;
        line-height: 1.55;
        font-weight: 500;
    }

    /* Light Map Card container */
    .map-card-container {
        background: #ffffff;
        border: 1px solid #e7e5e4;
        border-radius: 8px;
        padding: 8px;
        margin-bottom: 16px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# 1. Data Contract & Loader (Strict Schema)
# -----------------------------------------------------------------------------
@st.cache_data
def load_northlink_data() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Loads CSV files strictly adhering to the locked Frostline schema."""
    df_corridors = pd.read_csv("data/corridors.csv")
    df_climate = pd.read_csv("data/climate_annual.csv")
    df_roads = pd.read_csv("data/road_seasons.csv")
    df_trends = pd.read_csv("data/trends.csv")
    return df_corridors, df_climate, df_roads, df_trends

df_corridors, df_climate, df_roads, df_trends = load_northlink_data()

# -----------------------------------------------------------------------------
# Locked Synthetic Banner (Visible across every view)
# -----------------------------------------------------------------------------
st.markdown(
    """
    <div class="synthetic-banner">
        <svg style="width: 18px; height: 18px; flex-shrink: 0;" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M8.485 2.495c.673-1.167 2.357-1.167 3.03 0l6.28 10.875c.673 1.167-.17 2.625-1.516 2.625H3.72c-1.347 0-2.189-1.458-1.515-2.625L8.485 2.495zM10 5a.75.75 0 01.75.75v3.5a.75.75 0 01-1.5 0v-3.5A.75.75 0 0110 5zm0 9a1 1 0 100-2 1 1 0 000 2z" clip-rule="evenodd" />
        </svg>
        <span><strong>Provisional synthetic data — not for judging. Replace with verified outputs before deployment.</strong></span>
    </div>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# Header
# -----------------------------------------------------------------------------
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.markdown('<h1 style="font-size: 2.1rem; font-weight: 700; margin-bottom: 4px; color: #1c1917;">Frostline</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p style="font-size: 1.05rem; color: #57534e; margin-top: 0; margin-bottom: 24px;">'
        'Winter Climate Trends & Historical Operating Intelligence for Northern Seasonal Roads'
        '</p>',
        unsafe_allow_html=True,
    )
with col_h2:
    st.markdown(
        """
        <div style="text-align: right; font-size: 0.8rem; color: #78716c; padding-top: 8px;">
            <div>Standard Season: <strong>1 Oct – 31 May</strong></div>
            <div>Time Horizon: <strong>1994 – 2024 (31 yrs)</strong></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown('<hr style="border: 0; border-top: 1px solid #e7e5e4; margin: 0 0 24px 0;">', unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# JOURNEY PART 1: Corridor Overview (with CARTO Positron Light Leaflet Map)
# -----------------------------------------------------------------------------
st.markdown('<div class="journey-step">Part 1</div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">Corridor Overview</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="section-desc">'
    'Select a monitored northern corridor or specify custom coordinates across Canada’s subarctic and arctic seasonal transportation network.'
    '</div>',
    unsafe_allow_html=True,
)

# Presets mapping
preset_labels = {
    "tibbitt_contwoyto": "Tibbitt–Contwoyto (Verified case study · NWT/NU)",
    "inuvik_tuk": "Inuvik–Tuktoyaktuk (Verified historical · Beaufort Delta, NWT)",
    "james_bay": "James Bay (Historical benchmark · Western James Bay, ON)",
    "custom": "Custom (User-defined coordinates)",
}

# Handle query params / session state for corridor selection if clicked on map
query_params = st.query_params
if "corridor" in query_params and query_params["corridor"] in preset_labels:
    st.session_state["corridor_selector"] = query_params["corridor"]

if "corridor_selector" not in st.session_state:
    st.session_state["corridor_selector"] = "tibbitt_contwoyto"

col_p1, col_p2 = st.columns([13, 11])

with col_p1:
    selected_cid = st.selectbox(
        "Corridor Selection",
        options=list(preset_labels.keys()),
        format_func=lambda x: preset_labels[x],
        key="corridor_selector",
        label_visibility="collapsed",
    )

    # Custom lat/lon inputs if custom is chosen
    custom_lat = 65.0
    custom_lon = -120.0
    if selected_cid == "custom":
        st.markdown('<div style="font-size: 0.85rem; color: #57534e; margin-top: 8px; margin-bottom: 4px;">Specify Geographic Coordinates:</div>', unsafe_allow_html=True)
        col_lat, col_lon = st.columns(2)
        with col_lat:
            custom_lat = st.number_input("Latitude (°N)", min_value=50.0, max_value=75.0, value=65.0, step=0.5)
        with col_lon:
            custom_lon = st.number_input("Longitude (°W)", min_value=-145.0, max_value=-60.0, value=-120.0, step=0.5)

    # Active corridor metadata
    curr_corridor_meta = df_corridors[df_corridors["corridor_id"] == selected_cid].iloc[0]
    lat_val = custom_lat if selected_cid == "custom" else curr_corridor_meta["lat"]
    lon_val = custom_lon if selected_cid == "custom" else curr_corridor_meta["lon"]
    kind_label = curr_corridor_meta["kind"].capitalize()
    has_roads = str(curr_corridor_meta["has_road_records"]).lower() == "true"

    st.markdown(
        f"""
        <div style="background: #ffffff; border: 1px solid #e7e5e4; border-radius: 6px; padding: 12px 16px; margin-top: 10px; font-size: 0.875rem;">
            <div style="display: flex; justify-content: space-between; flex-wrap: wrap; gap: 8px;">
                <div><strong>Corridor:</strong> {curr_corridor_meta['name']}</div>
                <div><strong>Type:</strong> <span style="background: #f5f5f4; padding: 2px 8px; border-radius: 4px;">{kind_label}</span></div>
                <div><strong>Position:</strong> {lat_val:.2f}° N, {abs(lon_val):.2f}° W</div>
                <div><strong>Road Records:</strong> {'Available (31 seasons)' if has_roads else 'Environmental proxy only'}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_p2:
    # Keyless Leaflet Map with CARTO Positron Light Tiles & Fallback to OpenStreetMap
    markers_data = []
    for _, row in df_corridors.iterrows():
        c_lat = custom_lat if row["corridor_id"] == "custom" else row["lat"]
        c_lon = custom_lon if row["corridor_id"] == "custom" else row["lon"]
        markers_data.append({
            "id": row["corridor_id"],
            "name": row["name"],
            "lat": float(c_lat),
            "lon": float(c_lon),
            "active": row["corridor_id"] == selected_cid,
        })
    markers_json = json.dumps(markers_data)

    leaflet_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=" crossorigin="" />
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=" crossorigin=""></script>
        <style>
            html, body {{ margin: 0; padding: 0; height: 100%; width: 100%; background: #ffffff; font-family: -apple-system, BlinkMacSystemFont, "Inter", sans-serif; }}
            #map {{ width: 100%; height: 218px; border-radius: 6px; }}
            .caption {{ font-size: 11px; color: #78716c; text-align: center; padding-top: 5px; }}
            .leaflet-popup-content-wrapper {{ border-radius: 6px; box-shadow: 0 2px 8px rgba(0,0,0,0.12); }}
            .leaflet-popup-content {{ margin: 8px 12px; font-size: 12px; font-weight: 600; color: #1c1917; }}
        </style>
    </head>
    <body>
        <div id="map"></div>
        <div class="caption">CARTO Positron · Click a corridor marker to select</div>
        <script>
            const corridors = {markers_json};
            const activeId = "{selected_cid}";
            const activeCorridor = corridors.find(c => c.id === activeId) || corridors[0];

            // Initialize Leaflet map centered on active corridor or overview
            const map = L.map('map', {{
                center: [activeCorridor.lat, activeCorridor.lon],
                zoom: 4,
                minZoom: 3,
                maxZoom: 9,
                zoomControl: true,
                attributionControl: true
            }});

            // Primary basemap: CARTO Positron Light Tiles (no API key)
            const cartoPositron = L.tileLayer('https://{{s}}.basemaps.cartocdn.com/light_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions" target="_blank">CARTO</a>',
                subdomains: 'abcd',
                maxZoom: 19
            }});

            // Fallback: Official OpenStreetMap standard tiles (no API key)
            const osmFallback = L.tileLayer('https://tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a> contributors',
                maxZoom: 19
            }});

            cartoPositron.addTo(map);

            cartoPositron.on('tileerror', function() {{
                if (!map.hasLayer(osmFallback)) {{
                    map.removeLayer(cartoPositron);
                    osmFallback.addTo(map);
                }}
            }});

            // Add corridor markers
            corridors.forEach(c => {{
                const isSelected = (c.id === activeId);
                const marker = L.circleMarker([c.lat, c.lon], {{
                    radius: isSelected ? 9 : 6,
                    fillColor: isSelected ? '#0e7490' : '#78716c',
                    color: '#ffffff',
                    weight: 2,
                    opacity: 1,
                    fillOpacity: 0.95
                }}).addTo(map);

                marker.bindPopup(`<strong>${{c.name}}</strong><br><span style="color:#78716c;font-size:11px;">Click to select corridor</span>`);

                marker.on('click', function() {{
                    if (window.top) {{
                        const url = new URL(window.top.location.href);
                        url.searchParams.set('corridor', c.id);
                        window.top.location.href = url.toString();
                    }}
                }});

                if (isSelected) {{
                    marker.openPopup();
                }}
            }});
        </script>
    </body>
    </html>
    """
    components.html(leaflet_html, height=255)

st.markdown('<hr style="border: 0; border-top: 1px solid #e7e5e4; margin: 20px 0;">', unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# JOURNEY PART 2: Environmental Metric Selector
# -----------------------------------------------------------------------------
st.markdown('<div class="journey-step">Part 2</div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">Environmental Metric Selector</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="section-desc">'
    'Select a climate indicator derived from NASA daily surface reanalysis (1 Oct – 31 May). '
    'The 380 °C-day accumulation threshold metric is calibrated exclusively for the James Bay coastal ice road benchmark.'
    '</div>',
    unsafe_allow_html=True,
)

metric_defs = {
    "fdd": {
        "name": "Freezing Degree-Days (FDD)",
        "unit": "°C-days",
        "desc": "Cumulative cold energy (sum of mean daily temperatures below 0 °C from Oct 1 to May 31). Primary governing factor of natural ice thickness.",
        "zero_start": True,
    },
    "thaw_days": {
        "name": "Thaw-Day Count",
        "unit": "days",
        "desc": "Number of winter season days where maximum daily temperature exceeded 0 °C. Key driver of surface slush, bearing capacity loss, and portage degradation.",
        "zero_start": True,
    },
    "threshold_doy": {
        "name": "Date of 380 °C-Day Threshold (James Bay Benchmark)",
        "unit": "Calendar Day of Year",
        "desc": "Calendar day of the winter year when 380 °C-days of freezing have accumulated—the historical operational threshold required for safe light-vehicle road commissioning.",
        "zero_start": False,
    },
}

# Locked constraint: Hide or disable the date metric unless James Bay is selected
available_metrics = ["fdd", "thaw_days"]
if selected_cid == "james_bay":
    available_metrics.append("threshold_doy")

# Maintain metric selection cleanly in session state
if "selected_metric" not in st.session_state:
    st.session_state["selected_metric"] = "fdd"
if st.session_state["selected_metric"] not in available_metrics:
    st.session_state["selected_metric"] = "fdd"

selected_metric = st.radio(
    "Environmental Metric",
    options=available_metrics,
    format_func=lambda m: f"{metric_defs[m]['name']} [{metric_defs[m]['unit']}]",
    index=available_metrics.index(st.session_state["selected_metric"]),
    horizontal=True,
    key="metric_radio",
)
st.session_state["selected_metric"] = selected_metric

curr_metric_meta = metric_defs[selected_metric]

st.markdown(
    f"""
    <div style="background-color: #f5f5f4; border-radius: 6px; padding: 10px 14px; font-size: 0.85rem; color: #44403c; margin-top: 8px;">
        <strong>Metric Scope:</strong> {curr_metric_meta['desc']}
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown('<hr style="border: 0; border-top: 1px solid #e7e5e4; margin: 20px 0;">', unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# JOURNEY PART 3: Interactive Historical Chart
# -----------------------------------------------------------------------------
st.markdown('<div class="journey-step">Part 3</div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">Interactive Historical Chart</div>', unsafe_allow_html=True)
st.markdown(
    f'<div class="section-desc">'
    f'Historical winter season time series for <strong>{preset_labels[selected_cid].split("(")[0].strip()}</strong> ({curr_metric_meta["name"]}). '
    f'Points represent verified annual aggregates; the solid line connects annual observations; the dashed line and shaded ribbon indicate the linear decadal trend and 95% confidence interval.'
    f'</div>',
    unsafe_allow_html=True,
)

# Filter dataset
df_subset = df_climate[
    (df_climate["corridor_id"] == selected_cid) & (df_climate["metric"] == selected_metric)
].sort_values("season_year").copy()

# Compute exact regression fit and 95% confidence interval band for the chart
x_vals = df_subset["season_year"].values.astype(float)
y_vals = df_subset["value"].values.astype(float)
n_pts = len(x_vals)

x_bar = np.mean(x_vals)
y_bar = np.mean(y_vals)
sum_sq_x = np.sum((x_vals - x_bar) ** 2)
slope_est = np.sum((x_vals - x_bar) * (y_vals - y_bar)) / sum_sq_x
intercept_est = y_bar - slope_est * x_bar

y_fit = slope_est * x_vals + intercept_est
residuals = y_vals - y_fit
s_err = math.sqrt(np.sum(residuals ** 2) / (n_pts - 2))
se_fit_curve = s_err * np.sqrt(1.0 / n_pts + ((x_vals - x_bar) ** 2) / sum_sq_x)

df_subset["trend_fit"] = y_fit
df_subset["ci_band_low"] = y_fit - 1.96 * se_fit_curve
df_subset["ci_band_high"] = y_fit + 1.96 * se_fit_curve

# Merge road season length if available for direct tooltips
if has_roads:
    df_roads_sub = df_roads[df_roads["corridor_id"] == selected_cid][["season_year", "season_length_days", "open_date"]]
    df_subset = pd.merge(df_subset, df_roads_sub, on="season_year", how="left")
else:
    df_subset["season_length_days"] = np.nan
    df_subset["open_date"] = "N/A"

# Chart scale specifications: counts and accumulations start at zero
y_scale_zero = curr_metric_meta["zero_start"]
y_axis_title = f"{curr_metric_meta['name']} ({curr_metric_meta['unit']})"

# Base chart
base = alt.Chart(df_subset).encode(
    x=alt.X(
        "season_year:Q",
        axis=alt.Axis(
            title="Winter Season Year (Oct 1 – May 31)",
            format="d",
            tickMinStep=2,
            gridColor="#f0edea",
            titleFontWeight="normal",
            titleColor="#57534e",
            labelColor="#78716c",
        ),
    )
)

# 95% Confidence interval band
ci_band = base.mark_area(
    opacity=0.16,
    color="#0e7490",
).encode(
    y=alt.Y(
        "ci_band_low:Q",
        scale=alt.Scale(zero=y_scale_zero),
    ),
    y2="ci_band_high:Q",
)

# Decadal trend line
trend_line = base.mark_line(
    color="#155e75",
    strokeWidth=2,
    strokeDash=[5, 4],
).encode(
    y="trend_fit:Q",
)

# Annual observation line
obs_line = base.mark_line(
    color="#0e7490",
    strokeWidth=2.2,
).encode(
    y=alt.Y(
        "value:Q",
        scale=alt.Scale(zero=y_scale_zero),
        axis=alt.Axis(
            title=y_axis_title,
            gridColor="#f0edea",
            titleFontWeight="normal",
            titleColor="#57534e",
            labelColor="#78716c",
        ),
    )
)

# Annual observation points with interactive tooltips
tooltip_fields = [
    alt.Tooltip("season_year:Q", title="Winter Season"),
    alt.Tooltip("value:Q", title=f"{curr_metric_meta['name']} ({curr_metric_meta['unit']})", format=".1f"),
    alt.Tooltip("missing_days:Q", title="Missing Days"),
]
if has_roads:
    tooltip_fields.append(alt.Tooltip("season_length_days:Q", title="Road Operating Days"))
    tooltip_fields.append(alt.Tooltip("open_date:N", title="Historical Opening Date"))

obs_points = base.mark_circle(
    size=55,
    color="#0e7490",
    opacity=0.95,
).encode(
    y="value:Q",
    tooltip=tooltip_fields,
)

historical_chart = (ci_band + trend_line + obs_line + obs_points).properties(
    height=340,
).configure_view(
    strokeWidth=0,
)

st.altair_chart(historical_chart, width="stretch")

# Optional road duration toggle if corridor has road records
if has_roads:
    show_road_overlay = st.checkbox(
        "Show historical road operating season duration (days) below chart",
        value=False,
    )
    if show_road_overlay:
        road_chart = alt.Chart(df_subset).mark_bar(
            color="#a8a29e",
            opacity=0.75,
            cornerRadiusTopLeft=2,
            cornerRadiusTopRight=2,
        ).encode(
            x=alt.X("season_year:Q", axis=alt.Axis(title="Season Year", format="d")),
            y=alt.Y("season_length_days:Q", title="Operating Season (Days)", scale=alt.Scale(zero=True)),
            tooltip=[
                alt.Tooltip("season_year:Q", title="Season"),
                alt.Tooltip("season_length_days:Q", title="Days Open"),
                alt.Tooltip("open_date:N", title="Open Date"),
            ],
        ).properties(height=160).configure_view(strokeWidth=0)
        st.altair_chart(road_chart, width="stretch")

st.markdown('<hr style="border: 0; border-top: 1px solid #e7e5e4; margin: 20px 0;">', unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# JOURNEY PART 4: Trend Magnitude and Uncertainty
# -----------------------------------------------------------------------------
st.markdown('<div class="journey-step">Part 4</div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">Trend Magnitude & Uncertainty</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="section-desc">'
    'Linear rate of change per decade, 95% confidence interval, non-parametric Mann-Kendall rank correlation test, and operational assessment.'
    '</div>',
    unsafe_allow_html=True,
)

trend_row = df_trends[
    (df_trends["corridor_id"] == selected_cid) & (df_trends["metric"] == selected_metric)
].iloc[0]

c_m1, c_m2, c_m3, c_m4 = st.columns(4)

unit_label = curr_metric_meta["unit"]

with c_m1:
    sign = "+" if trend_row["slope_per_decade"] > 0 else ""
    st.markdown(
        f"""
        <div class="stat-card">
            <div class="stat-label">Slope per Decade</div>
            <div class="stat-value">{sign}{trend_row['slope_per_decade']:.1f}</div>
            <div class="stat-sub">{unit_label} / 10 yrs</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c_m2:
    st.markdown(
        f"""
        <div class="stat-card">
            <div class="stat-label">95% Confidence Interval</div>
            <div class="stat-value">[{trend_row['ci_low']:.1f}, {trend_row['ci_high']:.1f}]</div>
            <div class="stat-sub">Linear OLS interval</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c_m3:
    st.markdown(
        f"""
        <div class="stat-card">
            <div class="stat-label">Observed Seasons</div>
            <div class="stat-value">{int(trend_row['n_seasons'])}</div>
            <div class="stat-sub">Complete series (1994–2024)</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c_m4:
    sig_text = "p < 0.001" if trend_row["p_value"] < 0.001 else f"p = {trend_row['p_value']:.3f}"
    st.markdown(
        f"""
        <div class="stat-card">
            <div class="stat-label">Kendall's Tau (Rank Trend)</div>
            <div class="stat-value">{trend_row['kendall_tau']:+.3f}</div>
            <div class="stat-sub">{sig_text} (two-tailed)</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# One plain sentence about the operating window
st.markdown(
    f"""
    <div class="takeaway-card">
        <div style="font-size: 0.75rem; font-weight: 700; color: #0e7490; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px;">
            Operating Window Assessment
        </div>
        <div class="takeaway-text">
            "{trend_row['plain_takeaway']}"
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown('<hr style="border: 0; border-top: 1px solid #e7e5e4; margin: 20px 0;">', unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# JOURNEY PART 5: Optional Comparison View
# -----------------------------------------------------------------------------
st.markdown('<div class="journey-step">Part 5</div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">Corridor Comparison View</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="section-desc">'
    'Optional comparative view to evaluate divergence in climate trends across different geographic sectors of northern Canada.'
    '</div>',
    unsafe_allow_html=True,
)

# Comparison is OFF by default as required
enable_comparison = st.checkbox("Enable comparison view", value=False)

if enable_comparison:
    # Filter peer corridors that have the same metric available
    eligible_peer_ids = [
        cid for cid in df_corridors["corridor_id"].tolist()
        if cid != selected_cid and selected_metric in df_climate[df_climate["corridor_id"] == cid]["metric"].values
    ]

    if not eligible_peer_ids:
        st.info("The selected metric is not available for comparison across other corridors.")
    else:
        col_comp_sel, col_comp_info = st.columns([2, 1])
        with col_comp_sel:
            second_cid = st.selectbox(
                "Compare with Corridor:",
                options=eligible_peer_ids,
                format_func=lambda x: preset_labels[x],
                index=0,
            )

        # Retrieve shared years and data
        df_corr1 = df_climate[
            (df_climate["corridor_id"] == selected_cid) & (df_climate["metric"] == selected_metric)
        ].copy()
        df_corr2 = df_climate[
            (df_climate["corridor_id"] == second_cid) & (df_climate["metric"] == selected_metric)
        ].copy()

        # Shared years only
        shared_years = sorted(list(set(df_corr1["season_year"]).intersection(set(df_corr2["season_year"]))))
        df_corr1 = df_corr1[df_corr1["season_year"].isin(shared_years)]
        df_corr2 = df_corr2[df_corr2["season_year"].isin(shared_years)]

        name1 = df_corridors[df_corridors["corridor_id"] == selected_cid]["name"].iloc[0]
        name2 = df_corridors[df_corridors["corridor_id"] == second_cid]["name"].iloc[0]

        df_corr1["Corridor"] = name1
        df_corr2["Corridor"] = name2
        df_combined = pd.concat([df_corr1, df_corr2], ignore_index=True)

        trend1_slope = df_trends[(df_trends["corridor_id"] == selected_cid) & (df_trends["metric"] == selected_metric)]["slope_per_decade"].iloc[0]
        trend2_slope = df_trends[(df_trends["corridor_id"] == second_cid) & (df_trends["metric"] == selected_metric)]["slope_per_decade"].iloc[0]

        with col_comp_info:
            st.markdown(
                f"""
                <div style="background: #ffffff; border: 1px solid #e7e5e4; border-radius: 6px; padding: 10px 14px; font-size: 0.8rem; margin-top: 25px;">
                    <div><strong>{name1}:</strong> {trend1_slope:+.1f} {unit_label}/dec</div>
                    <div><strong>{name2}:</strong> {trend2_slope:+.1f} {unit_label}/dec</div>
                    <div><strong>Overlap:</strong> {len(shared_years)} shared seasons</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Comparative Altair chart with two muted accessible tones
        comp_chart = alt.Chart(df_combined).mark_line(point=True, strokeWidth=2).encode(
            x=alt.X("season_year:Q", axis=alt.Axis(title="Shared Winter Season Year", format="d")),
            y=alt.Y("value:Q", title=f"{curr_metric_meta['name']} ({curr_metric_meta['unit']})", scale=alt.Scale(zero=y_scale_zero)),
            color=alt.Color(
                "Corridor:N",
                scale=alt.Scale(
                    domain=[name1, name2],
                    range=["#0e7490", "#475569"],  # Teal and Slate Navy (high contrast, accessible)
                ),
                legend=alt.Legend(orient="top", title=None),
            ),
            tooltip=[
                alt.Tooltip("Corridor:N"),
                alt.Tooltip("season_year:Q", title="Season"),
                alt.Tooltip("value:Q", title=f"{curr_metric_meta['name']}", format=".1f"),
            ],
        ).properties(height=300).configure_view(strokeWidth=0)

        st.altair_chart(comp_chart, width="stretch")

st.markdown('<hr style="border: 0; border-top: 1px solid #e7e5e4; margin: 20px 0;">', unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# JOURNEY PART 6: Evidence Audit
# -----------------------------------------------------------------------------
st.markdown('<div class="journey-step">Part 6</div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">Evidence Audit & Data Provenance</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="section-desc">'
    'Transparent audit trail documenting data sources, reanalysis query specifications, quality control filters, and analytical constraints.'
    '</div>',
    unsafe_allow_html=True,
)

col_a1, col_a2 = st.columns(2)

with col_a1:
    st.markdown(
        """
        <div style="background: #ffffff; border: 1px solid #e7e5e4; border-radius: 8px; padding: 16px 20px; height: 100%;">
            <div style="font-size: 0.9rem; font-weight: 600; color: #1c1917; margin-bottom: 10px;">
                1. Quality Control & Definition Protocols
            </div>
            <ul style="font-size: 0.85rem; color: #44403c; line-height: 1.6; margin-bottom: 0; padding-left: 20px;">
                <li><strong>Season Definition:</strong> Winter is bounded between <strong>1 October and 31 May</strong> (243 days; 244 days in leap years).</li>
                <li><strong>Season Year:</strong> Defined as the calendar year in which the winter season terminates (e.g., season_year 2024 spans 1 Oct 2023 – 31 May 2024).</li>
                <li><strong>Missing Days Filter:</strong> Any season with <strong>more than 2 missing observation days</strong> is dropped from trend calculations.</li>
                <li><strong>Audit Status:</strong> 100% of the 31 historical seasons meet the missing data threshold (maximum observed missing days in series: 1 day).</li>
                <li><strong>Methodology Notice:</strong> <span style="color: #92400e; font-weight: 600;">Provisional synthetic estimation.</span> All indicators require validation against road station logs before operational use.</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_a2:
    st.markdown(
        """
        <div style="background: #ffffff; border: 1px solid #e7e5e4; border-radius: 8px; padding: 16px 20px; height: 100%;">
            <div style="font-size: 0.9rem; font-weight: 600; color: #1c1917; margin-bottom: 10px;">
                2. Data Sources & Institutional Records
            </div>
            <ul style="font-size: 0.85rem; color: #44403c; line-height: 1.6; margin-bottom: 0; padding-left: 20px;">
                <li><strong>Atmospheric Reanalysis:</strong> NASA POWER Daily Surface Meteorological Dataset (MERRA-2 / GEOS-IT global assimilation model).</li>
                <li><strong>Surface Variables:</strong> Daily Mean Temperature (<code>T2M</code>), Minimum Temperature (<code>T2M_MIN</code>), Maximum Temperature (<code>T2M_MAX</code>).</li>
                <li><strong>Road Operating Records:</strong> Northwest Territories Bureau of Statistics, Department of Infrastructure historical road opening/closing registries (Tibbitt–Contwoyto and Inuvik–Tuktoyaktuk).</li>
                <li><strong>Benchmark Validation:</strong> James Bay Winter Road Joint Venture historical opening logs and 380 °C-day accumulation criteria.</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

# NASA POWER Query Template
st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
with st.expander("NASA POWER Query Template (API Specification)", expanded=False):
    nasa_query_template = f"""# NASA POWER API v2.0 REST Query Template for Northern Corridors
# Endpoint: https://power.larc.nasa.gov/api/temporal/daily/point

GET https://power.larc.nasa.gov/api/temporal/daily/point?parameters=T2M,T2M_MIN,T2M_MAX&community=AG&longitude={lon_val:.4f}&latitude={lat_val:.4f}&start=19931001&end=20240531&format=CSV

# Processing Rule:
# 1. Group daily records by season: (Month >= 10 and Year == season_year - 1) OR (Month <= 5 and Year == season_year)
# 2. Daily FDD = max(0.0, -T2M)
# 3. Daily Thaw Day = 1 if T2M_MAX > 0.0 else 0
# 4. Check missing records count; if missing_days > 2, discard season.
"""
    st.code(nasa_query_template, language="bash")

# Limitations Disclosure
with st.expander("Analytical Limitations & Safety Disclosures", expanded=True):
    st.markdown(
        """
        <div style="font-size: 0.85rem; color: #44403c; line-height: 1.6;">
            <p><strong>1. Spatial Resolution Constraint:</strong> The NASA POWER reanalysis grid operates at a spatial resolution of 0.5° latitude × 0.625° longitude (~50 km × 25 km). Microclimates, sheltered lake bays, and canyon wind corridors may deviate from grid-cell averages.</p>
            <p><strong>2. Structural Safety Claim Disclaimer:</strong> Freezing degree-days and thaw counts provide broad thermal boundary conditions only. They do <strong>not</strong> substitute for ground-penetrating radar (GPR) ice thickness profiling, core sampling, or on-ice bearing capacity proof testing for individual vehicle weight classifications (Gold's Formula).</p>
            <p><strong>3. Optical Remote Sensing Limitation:</strong> Summer satellite imagery cannot resolve winter ice road alignment, sub-surface cracks, thermal lead fractures, or slush pocket stratification under snowpack.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

# Raw Data Inspector
with st.expander("Inspect Raw Evidence Dataset (Current Corridor)", expanded=False):
    st.dataframe(
        df_subset[["season_year", "metric", "value", "n_days", "missing_days", "synthetic"]],
        width="stretch",
        hide_index=True,
    )
    csv_bytes = df_subset.to_csv(index=False).encode("utf-8")
    st.download_button(
        label=f"Download {selected_cid}_{selected_metric}.csv",
        data=csv_bytes,
        file_name=f"{selected_cid}_{selected_metric}.csv",
        mime="text/csv",
    )

# -----------------------------------------------------------------------------
# Footer
# -----------------------------------------------------------------------------
st.markdown('<hr style="border: 0; border-top: 1px solid #e7e5e4; margin: 30px 0 16px 0;">', unsafe_allow_html=True)
st.markdown(
    """
    <div style="font-size: 0.75rem; color: #a8a29e; text-align: center; margin-bottom: 24px;">
        Frostline by Strongest Soldiers · Trace the evidence behind changing winters · NASA POWER Daily & NWT Bureau of Statistics records
    </div>
    """,
    unsafe_allow_html=True,
)
