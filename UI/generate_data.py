"""Generate synthetic test data for NorthLink following the locked schema.
"""
import math
import numpy as np
import pandas as pd

np.random.seed(42)

# 1. Corridors
corridors_data = [
    {
        "corridor_id": "tibbitt_contwoyto",
        "name": "Tibbitt–Contwoyto Winter Road",
        "kind": "verified",
        "lat": 64.0,
        "lon": -113.0,
        "has_road_records": "true",
    },
    {
        "corridor_id": "inuvik_tuk",
        "name": "Inuvik–Tuktoyaktuk Ice Road",
        "kind": "verified",
        "lat": 69.0,
        "lon": -133.5,
        "has_road_records": "true",
    },
    {
        "corridor_id": "james_bay",
        "name": "James Bay Winter Road",
        "kind": "benchmark",
        "lat": 53.0,
        "lon": -81.0,
        "has_road_records": "false",
    },
    {
        "corridor_id": "custom",
        "name": "Custom Corridor",
        "kind": "custom",
        "lat": 65.0,
        "lon": -120.0,
        "has_road_records": "false",
    },
]
df_corridors = pd.DataFrame(corridors_data)
df_corridors.to_csv("data/corridors.csv", index=False)
print("Wrote data/corridors.csv")

# 2. Climate Annual
years = list(range(1994, 2025))  # 1994-2024 (31 seasons)

# Configuration for corridors and metrics
configs = {
    "tibbitt_contwoyto": {
        "fdd": {"base": 3720.0, "slope_per_year": -16.2, "noise_std": 140.0, "round": 1},
        "thaw_days": {"base": 18.0, "slope_per_year": 0.46, "noise_std": 3.2, "round": 0, "min": 5},
    },
    "inuvik_tuk": {
        "fdd": {"base": 4680.0, "slope_per_year": -21.5, "noise_std": 170.0, "round": 1},
        "thaw_days": {"base": 9.0, "slope_per_year": 0.35, "noise_std": 2.5, "round": 0, "min": 2},
    },
    "james_bay": {
        "fdd": {"base": 1980.0, "slope_per_year": -13.4, "noise_std": 120.0, "round": 1},
        "thaw_days": {"base": 36.0, "slope_per_year": 0.62, "noise_std": 4.5, "round": 0, "min": 15},
        "threshold_doy": {"base": 6.0, "slope_per_year": 0.38, "noise_std": 3.0, "round": 0, "min": 1},
    },
    "custom": {
        "fdd": {"base": 3520.0, "slope_per_year": -14.8, "noise_std": 150.0, "round": 1},
        "thaw_days": {"base": 20.0, "slope_per_year": 0.42, "noise_std": 3.5, "round": 0, "min": 6},
    },
}

climate_rows = []
for cid, metrics in configs.items():
    for metric_name, cfg in metrics.items():
        base = cfg["base"]
        slope = cfg["slope_per_year"]
        noise_std = cfg["noise_std"]
        rnd = cfg["round"]
        min_val = cfg.get("min", 0.0)

        for i, year in enumerate(years):
            val = base + slope * i + np.random.normal(0, noise_std)
            if val < min_val:
                val = min_val
            val = round(val, rnd) if rnd > 0 else int(round(val))

            is_leap = (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0))
            n_days = 244 if is_leap else 243
            missing_days = 1 if (year % 7 == 0) else 0

            climate_rows.append({
                "corridor_id": cid,
                "season_year": year,
                "metric": metric_name,
                "value": val,
                "n_days": n_days,
                "missing_days": missing_days,
                "synthetic": "true",
            })

df_climate = pd.DataFrame(climate_rows)
df_climate.to_csv("data/climate_annual.csv", index=False)
print("Wrote data/climate_annual.csv")

# 3. Road Seasons
# Tibbitt–Contwoyto and Inuvik–Tuktoyaktuk have road_seasons.
road_rows = []
# Tibbitt-Contwoyto
for i, year in enumerate(years):
    # Open date around Jan 25 to Feb 10, trending later
    open_day_of_jan = int(round(25 + 0.35 * i + np.random.normal(0, 3.5)))
    if open_day_of_jan < 15:
        open_day_of_jan = 15
    if open_day_of_jan > 31:
        # overflows into February
        feb_day = open_day_of_jan - 31
        open_date = f"{year}-02-{feb_day:02d}"
    else:
        open_date = f"{year}-01-{open_day_of_jan:02d}"
    
    # Season length: around 65 days in 1994, declining to ~45 days
    season_len = int(round(65 - 0.65 * i + np.random.normal(0, 4.5)))
    season_len = max(28, season_len)

    road_rows.append({
        "corridor_id": "tibbitt_contwoyto",
        "season_year": year,
        "open_date": open_date,
        "season_length_days": season_len,
        "synthetic": "true",
    })

# Inuvik-Tuktoyaktuk
for i, year in enumerate(years):
    # Historical winter ice road across Mackenzie Delta to Tuktoyaktuk
    open_day_of_dec = int(round(20 + 0.25 * i + np.random.normal(0, 4.0)))
    open_date = f"{year - 1}-12-{min(31, max(10, open_day_of_dec)):02d}"
    season_len = int(round(135 - 0.70 * i + np.random.normal(0, 6.0)))
    season_len = max(90, season_len)

    road_rows.append({
        "corridor_id": "inuvik_tuk",
        "season_year": year,
        "open_date": open_date,
        "season_length_days": season_len,
        "synthetic": "true",
    })

df_roads = pd.DataFrame(road_rows)
df_roads.to_csv("data/road_seasons.csv", index=False)
print("Wrote data/road_seasons.csv")

# 4. Trends
# Calculate exact statistics from df_climate to guarantee consistency
def kendall_tau(x, y):
    n = len(x)
    concordant = 0
    discordant = 0
    for i in range(n):
        for j in range(i + 1, n):
            dx = x[j] - x[i]
            dy = y[j] - y[i]
            prod = dx * dy
            if prod > 0:
                concordant += 1
            elif prod < 0:
                discordant += 1
    total = n * (n - 1) / 2
    tau = (concordant - discordant) / total if total > 0 else 0.0
    # Approx p-value
    var_tau = (4 * n + 10) / (9 * n * (n - 1))
    z = tau / math.sqrt(var_tau) if var_tau > 0 else 0
    p_val = 2 * (1 - 0.5 * (1 + math.erf(abs(z) / math.sqrt(2))))
    return tau, p_val

takeaways = {
    ("tibbitt_contwoyto", "fdd"): "Winter freezing degree-days declined by ~160 °C-days per decade, shortening the thick-ice payload window by an estimated 5 to 7 days.",
    ("tibbitt_contwoyto", "thaw_days"): "Mid-winter thaw events increased by ~4.5 days per decade, heightening rutting risks and requiring earlier road closures.",
    ("inuvik_tuk", "fdd"): "High-latitude freezing accumulation fell by ~210 °C-days per decade, pushing ice road commissioning into late December.",
    ("inuvik_tuk", "thaw_days"): "Spring thaw occurrences increased by ~3.5 days per decade, accelerating spring river crossing deterioration.",
    ("james_bay", "fdd"): "Subarctic coastal degree-days decreased by ~130 °C-days per decade, narrowing the operating safety margin for heavy freight.",
    ("james_bay", "thaw_days"): "Thaw days rose by ~6.0 days per decade, creating repeated freeze-thaw cycles on coastal overland portages.",
    ("james_bay", "threshold_doy"): "The 380 °C-day freezing accumulation threshold shifted ~3.8 days later per decade, delaying initial vehicle traffic.",
    ("custom", "fdd"): "Freezing degree-days decreased by ~150 °C-days per decade across the custom corridor coordinates.",
    ("custom", "thaw_days"): "Thaw day occurrences increased by ~4.2 days per decade, indicating warming winter trends.",
}

trends_rows = []
for cid, metrics in configs.items():
    for metric_name in metrics.keys():
        subset = df_climate[(df_climate["corridor_id"] == cid) & (df_climate["metric"] == metric_name)].sort_values("season_year")
        x = subset["season_year"].values.astype(float)
        y = subset["value"].values.astype(float)
        n = len(x)

        # OLS regression
        x_mean = np.mean(x)
        y_mean = np.mean(y)
        slope = np.sum((x - x_mean) * (y - y_mean)) / np.sum((x - x_mean) ** 2)
        intercept = y_mean - slope * x_mean

        y_pred = slope * x + intercept
        residuals = y - y_pred
        s_err = math.sqrt(np.sum(residuals ** 2) / (n - 2))
        se_slope = s_err / math.sqrt(np.sum((x - x_mean) ** 2))

        slope_per_decade = round(float(slope * 10), 1)
        ci_half = 1.96 * se_slope * 10
        ci_low = round(float(slope_per_decade - ci_half), 1)
        ci_high = round(float(slope_per_decade + ci_half), 1)

        tau, p_val = kendall_tau(x, y)

        plain_takeaway = takeaways.get((cid, metric_name), f"Metric trend shows {slope_per_decade} per decade across {n} seasons.")

        trends_rows.append({
            "corridor_id": cid,
            "metric": metric_name,
            "slope_per_decade": slope_per_decade,
            "ci_low": ci_low,
            "ci_high": ci_high,
            "n_seasons": n,
            "kendall_tau": round(float(tau), 3),
            "p_value": round(float(p_val), 4),
            "plain_takeaway": plain_takeaway,
            "synthetic": "true",
        })

df_trends = pd.DataFrame(trends_rows)
df_trends.to_csv("data/trends.csv", index=False)
print("Wrote data/trends.csv")
