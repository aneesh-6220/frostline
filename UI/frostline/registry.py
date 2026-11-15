"""Registries: study locations, scientific variables, guiding questions and sources.

Everything the interface offers is declared here, so a new verified location or variable is added by
extending a registry and the data files, not by rewriting views (docs/EXTENDING_FROSTLINE.md).

Descriptive text follows docs/ROUTE_IDENTITY.md, docs/GEOGRAPHIC_SCOPE.md and docs/SCIENTIFIC_METHODS.md,
including their verification status. Numbers are never typed here; they come from the data files.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

# ------------------------------------------------------------------ sources
@dataclass(frozen=True)
class Source:
    id: str
    name: str
    kind: str          # reanalysis | satellite-derived | government record | station observation
    citation: str
    url: str
    resolution: str
    note: str = ""


POWER_ACK = ("The data was obtained from National Aeronautics and Space Administration (NASA) Langley Research Center's "
             "Prediction Of Worldwide Energy Resources (POWER) project funded through the NASA Earth Science Division.")

SOURCES = {
    "power": Source(
        "power", "NASA POWER daily (MERRA-2 meteorology)", "reanalysis",
        "NASA Langley Research Center (LaRC) Prediction Of Worldwide Energy Resources (POWER) Project, daily API. "
        "Accessed 2026-11-14; data end 2025-06-30. The downloaded file headers do not state a service version.",
        "https://power.larc.nasa.gov/",
        "Daily values for a 0.5 x 0.625 degree MERRA-2 grid cell",
        "Model reanalysis, not a station observation. POWER meteorology is derived from MERRA-2, so the two are not independent."),
    "power_ceres": Source(
        "power_ceres", "NASA POWER daily (CERES SYN1deg radiation)", "satellite-derived",
        "NASA LaRC POWER Project, daily API, parameters ALLSKY_SFC_SW_DWN and ALLSKY_SFC_LW_DWN (CERES SYN1deg). Accessed 2026-11-14.",
        "https://power.larc.nasa.gov/",
        "Daily values on a 1 x 1 degree grid",
        "Satellite-derived surface irradiance, distributed through POWER."),
    "merra2": Source(
        "merra2", "MERRA-2 reanalysis", "reanalysis",
        "Gelaro, R., McCarty, W., Suarez, M. J., et al. (2017). The Modern-Era Retrospective Analysis for Research and Applications, "
        "Version 2 (MERRA-2). Journal of Climate 30, 5419-5454. https://doi.org/10.1175/JCLI-D-16-0758.1",
        "https://doi.org/10.1175/JCLI-D-16-0758.1", "0.5 x 0.625 degree grid",
        "The reanalysis named in the POWER file headers (for example 'MERRA-2 Temperature at 2 Meters')."),
    "nwt_t108": Source(
        "nwt_t108", "NWT Bureau of Statistics, Table 108", "government record",
        "NWT Bureau of Statistics, Table 108, Winter Road Opening and Closing Dates, 1993/94 to 2024/25 "
        "(data from the Government of the Northwest Territories, Department of Infrastructure).",
        "https://www.statsnwt.ca/en/node/1073", "One opening and one closing date per route and winter",
        "A record of operations, not a measurement of ice. Temporary closures are not recorded."),
    "eccc": Source(
        "eccc", "Environment and Climate Change Canada station records", "station observation",
        "Environment and Climate Change Canada, Historical Climate Data, daily station data "
        "(Yellowknife A station IDs 1706 and 51058; Aklavik A 1623 and 52962; Inuvik 41883, 51477, 1669, 31470).",
        "https://climate.weather.gc.ca/", "Daily observations at a single station",
        "The only independent ground check in this project."),
}

LITERATURE = [
    "Hori, Y., Gough, W. A., Butler, K., Tsuji, L. J. S. (2017). Trends in the seasonal length and opening dates of a winter road in the western "
    "James Bay region, Ontario, Canada. Theoretical and Applied Climatology 129, 1309-1320. https://doi.org/10.1007/s00704-016-1855-1",
    "Hori, Y., Cheng, V. Y. S., Gough, W. A., Jien, J. Y., Tsuji, L. J. S. (2018). Implications of projected climate change on winter road systems "
    "in Ontario's Far North, Canada. Climatic Change 148(1), 109-122. https://doi.org/10.1007/s10584-018-2178-2",
    "Hori, Y., Gough, W. A., Tam, B., Tsuji, L. J. S. (2018). Community vulnerability to changes in the winter road viability and longevity in the "
    "western James Bay region of Ontario's Far North. Regional Environmental Change 18(6), 1753-1763. https://doi.org/10.1007/s10113-018-1310-1",
    "Song, J., Sparrow, S., Wallom, D. (2026). The impact of climate change on a large industrial winter road operation in Northern Canada. "
    "Cold Regions Science and Technology 248, 104952. https://doi.org/10.1016/j.coldregions.2026.104952",
    "Mullan, D. J., Barr, I. D., Flood, R. P., Galloway, J. M., Newton, A. M. W., Swindles, G. T. (2021). Examining the viability of the world's "
    "busiest winter road to climate change using a process-based lake model. Bulletin of the American Meteorological Society 102(7), E1464-E1480. "
    "https://doi.org/10.1175/BAMS-D-20-0168.1",
    "Transportation Association of Canada (2018), conference paper 'Winter roads and climate adaptation'. "
    "https://tac-atc.ca/wp-content/uploads/barrettep_winter_roads_and_climate_adaptation.pdf",
    "ClimateData.ca, Winter Ice Roads in Northern Ontario. https://climatedata.ca/?p=15894",
]

SOFTWARE = ["Python", "Streamlit", "Plotly", "pandas", "NumPy", "SciPy", "PyDeck (deck.gl)", "CARTO basemap tiles with OpenStreetMap data (optional map background)"]

# ---------------------------------------------------------------- locations
MERRA2_DLAT, MERRA2_DLON = 0.5, 0.625


def merra2_cell(lat: float, lon: float) -> dict:
    """MERRA-2 grid cell containing a point, calculated from the grid definition
    (cell centres at -90 + 0.5 j degrees latitude and -180 + 0.625 i degrees longitude)."""
    j = int(math.floor((lat + 90 + MERRA2_DLAT / 2) / MERRA2_DLAT))
    i = int(math.floor((lon + 180 + MERRA2_DLON / 2) / MERRA2_DLON))
    clat, clon = -90 + MERRA2_DLAT * j, -180 + MERRA2_DLON * i
    return dict(lat_index=j, lon_index=i, center_lat=clat, center_lon=clon,
                south=clat - MERRA2_DLAT / 2, north=clat + MERRA2_DLAT / 2, west=clon - MERRA2_DLON / 2, east=clon + MERRA2_DLON / 2)


@dataclass(frozen=True)
class Fact:
    label: str
    text: str
    status: str  # VERIFIED | SECONDARY | CALCULATED | UNVERIFIED | UNRESOLVED


@dataclass(frozen=True)
class Location:
    id: str
    name: str
    short: str
    role: str                 # primary | comparison | supplementary
    road_id: str
    road_name: str
    road_kind: str            # ice_road | winter_road | ice_crossing | mining_road
    lat: float | None = None
    lon: float | None = None
    mapped: bool = False
    region: str = ""
    sampling_point: str = ""
    setting: str = ""
    access: str = ""
    station: str = ""
    cell_elevation_m: float | None = None
    facts: tuple = ()
    caution: str = ""

    @property
    def is_primary_pair(self) -> bool:
        return self.role in ("primary", "comparison")

    @property
    def cell(self) -> dict | None:
        return merra2_cell(self.lat, self.lon) if self.mapped else None


ROAD_KIND_LABEL = {"ice_road": "Ice road", "winter_road": "Winter road", "ice_crossing": "Ice crossing", "mining_road": "Private mining winter road"}

# Text for the two documented case studies. Source and status: docs/ROUTE_IDENTITY.md.
_CASE_TEXT = {
    "dettah_bay": dict(
        short="Dettah",
        region="Yellowknife Bay, Great Slave Lake, Northwest Territories",
        sampling_point="Calculated midpoint of the two ends of the crossing. It is a point on or near the crossing, not a measurement site.",
        setting="A seasonal ice road about 6.5 km long across Yellowknife Bay, between Yellowknife and Dettah. A single short lake crossing.",
        access="An all-season road of about 27 km through the Ingraham Trail connects the same places all year. The ice road is a shorter "
               "seasonal route that saves roughly 15 to 20 minutes; it is not the community's only road connection.",
        station="ECCC Yellowknife A, about 6.3 km from the sampling point and inside the same NASA grid cell.",
        cell_elevation_m=204.71,
        caution="Dettah was chosen as the primary case after its road-date trend had been seen, so its road-date results are selection-biased. "
                "The all-route family of 51 tests is the adjustment.",
        facts=(
            Fact("Official record name", "Dettah Ice Road, sheet 'Ice Roads', NWT Table 108; 32 winters with no missing or flagged rows.", "VERIFIED"),
            Fact("What it is", "A 6.5 km seasonal ice road across Yellowknife Bay (north arm of Great Slave Lake).", "SECONDARY"),
            Fact("Year-round alternative", "A 27 km all-season road through the Ingraham Trail connects the same places.", "SECONDARY"),
            Fact("Meaning of 'open'", "Opening is to light vehicles (under 5,000 kg) first; heavier loads follow later. Temporary closures are not recorded.", "SECONDARY"),
            Fact("Sampling point", "62.43 N, 114.34 W, our calculated midpoint of the two ends.", "CALCULATED"),
            Fact("NASA grid cell", "Dettah, Yellowknife, the midpoint and the ECCC station all fall in one MERRA-2 0.5 x 0.625 degree cell.", "CALCULATED"),
            Fact("Date check", "Workbook dates agree with published reports for the winters checked. One opening date differs by a day from a press report (2024-01-28 in the workbook); the workbook value is kept.", "SECONDARY"),
        ),
    ),
    "aklavik_delta": dict(
        short="Aklavik",
        region="Mackenzie Delta, Northwest Territories",
        sampling_point="Straight-line midpoint between Aklavik and Inuvik. The road follows delta channels, so the point may lie off the alignment.",
        setting="A seasonal ice road between Aklavik and Inuvik through channels of the Mackenzie Delta. Its length is reported as 112 to 117 km "
                "and the exact alignment and segment described by the record are ambiguous.",
        access="No all-season road alternative to Aklavik is documented in this project's sources (still to be confirmed against "
               "territorial route definitions). That is a different transportation context from Dettah, where a year-round road exists.",
        station="ECCC Aklavik A (west end) and Inuvik stations (east end). No station sits at the sampling point.",
        cell_elevation_m=50.26,
        caution="Road identity, segment and the representativeness of the sampled grid cell are unverified. Treat Aklavik as a different setting, "
                "never as a repeat of the Dettah case.",
        facts=(
            Fact("Official record name", "Aklavik Ice Road, sheet 'Ice Roads', NWT Table 108; 32 winters with no missing or flagged rows.", "VERIFIED"),
            Fact("What it is", "The seasonal ice road between Aklavik and Inuvik through delta channels.", "SECONDARY"),
            Fact("Length and segment", "Reported as 112, 116 and 117 km by different sources; which segment the record dates describe is not settled.", "UNRESOLVED"),
            Fact("Sampling point", "68.29 N, 134.37 W, the straight-line midpoint of Aklavik and Inuvik.", "CALCULATED"),
            Fact("Grid-cell representativeness", "Whether one grid cell represents a road of more than 100 km is not verified.", "UNVERIFIED"),
            Fact("Meaning of 'open'", "Opened by the territorial department once construction is complete. Mid-season closures are not recorded.", "SECONDARY"),
        ),
    ),
}


def build_locations(ds) -> dict:
    """Locations offered by the app, from the approved data files. The 'custom' row has no data and is never offered."""
    corr = ds["corridors"]
    ops = ds["road_operations_all_routes"]
    road_names = ops.drop_duplicates("road_id").set_index("road_id").road_name.to_dict()
    out = {}
    facts_loc = {l["location_id"]: l for l in ds.facts["locations"]}
    for _, r in corr.iterrows():
        cid = str(r.corridor_id)
        if cid == "custom" or not bool(r.has_road_records) or cid not in facts_loc or cid not in _CASE_TEXT:
            continue
        f, t = facts_loc[cid], _CASE_TEXT[cid]
        out[cid] = Location(id=cid, name=str(r["name"]), short=t["short"], role=f["role"], road_id=f["road_id"],
                            road_name=road_names.get(f["road_id"], f["road_id"]), road_kind="ice_road", lat=float(r.lat), lon=float(r.lon),
                            mapped=True, region=t["region"], sampling_point=t["sampling_point"], setting=t["setting"], access=t["access"],
                            station=t["station"], cell_elevation_m=t["cell_elevation_m"], facts=t["facts"], caution=t["caution"])
    for _, r in ds["corridor_panel"].iterrows():
        lid = str(r.location_id)
        if lid in out:
            continue
        rn = road_names.get(str(r.road_id), str(r.road_id))
        out[lid] = Location(id=lid, name=rn, short=rn.replace(" Winter Road", "").replace(" Ice Crossing", "").replace(" Ice Road", ""),
                            role="supplementary", road_id=str(r.road_id), road_name=rn, road_kind=str(r.road_kind), mapped=False,
                            caution="Supplementary corridor. Approximate team-chosen sampling point; identity limited to the workbook route name. "
                                    "Its coordinates are not part of the approved app data, so it is not drawn on the map.")
    return out


def primary_locations(locations: dict) -> list:
    return [l for l in locations.values() if l.is_primary_pair]


# ---------------------------------------------------------------- variables
@dataclass(frozen=True)
class Variable:
    id: str
    label: str
    short: str
    kind: str                 # environmental | road
    tier: str                 # core | exploratory
    unit: str
    definition: str
    why: str
    source_id: str
    power_parameter: str
    temporal_resolution: str
    spatial_resolution: str
    table: str                # data file holding the per-winter values
    column: str
    valid_first: int
    valid_last: int
    locations: str            # 'primary' or 'all'
    fixed_windows: tuple      # windows that carry a multiplicity-adjusted q
    is_temperature: bool = False
    decimals: int = 2
    slope_decimals: int = 2
    up_word: str = "higher"
    down_word: str = "lower"
    quality: str = ""
    limitations: tuple = ()
    methods: tuple = ("Theil-Sen slope per decade", "Mann-Kendall test with tie correction", "moving-block bootstrap interval")
    trend_note: str = ""
    slope_unit: str = ""

    @property
    def phrase(self) -> str:
        """The short label for use inside a sentence."""
        s = self.short
        return s if s[:3] in ("Oct", "Jan", "Mar") else s[0].lower() + s[1:]

    @property
    def unit_per_decade(self) -> str:
        return f"{self.slope_unit or self.unit} per decade"


_ENV_Q = "A winter enters a trend only with complete daily coverage; at least 15 winters are required for any estimate."
_REANALYSIS_LIMITS = (
    "Reanalysis value for a 0.5 x 0.625 degree grid cell, not a measurement at the road.",
    "Colder than the nearby station in the cold season; absolute values are not local conditions.",
    "24 winters is a short record; natural variability can resemble a trend.",
)
_GRID = "0.5 x 0.625 degree MERRA-2 grid cell (roughly 55 km north to south and 25 to 32 km east to west at these latitudes)"
_ROAD_LIMITS = (
    "A government record of operations, not a measurement of ice thickness or road condition.",
    "Opening and closing reflect construction, ice surveys, snow, maintenance and administrative decisions as well as weather.",
    "Temporary closures are not recorded.",
)

VARIABLES = {v.id: v for v in [
    Variable("mean_octdec_c", "Early-winter mean air temperature (Oct to Dec)", "Oct-Dec mean temperature", "environmental", "core", "°C",
             "Mean of the daily 2 m air temperature from Oct 1 to Dec 31 of each winter.",
             "Early-winter temperature sets how quickly lakes and rivers begin to freeze.",
             "power", "T2M", "Daily values, one seasonal mean per winter", _GRID, "season_metrics_extended", "mean_octdec_c", 2001, 2024, "all",
             ((2001, 2024),), True, 2, 2, "warmer", "colder", _ENV_Q, _REANALYSIS_LIMITS),
    Variable("mean_janmar_c", "Midwinter mean air temperature (Jan to Mar)", "Jan-Mar mean temperature", "environmental", "core", "°C",
             "Mean of the daily 2 m air temperature from Jan 1 to Mar 31 of each winter.",
             "Midwinter temperature describes the coldest part of the season, when ice roads are in use.",
             "power", "T2M", "Daily values, one seasonal mean per winter", _GRID, "season_metrics_extended", "mean_janmar_c", 2001, 2024, "all",
             ((2001, 2024),), True, 2, 2, "warmer", "colder", _ENV_Q, _REANALYSIS_LIMITS),
    Variable("fdd_octdec", "Early-winter freezing degree-days (Oct to Dec)", "Oct-Dec freezing degree-days", "environmental", "core", "°C-days",
             "Sum over Oct 1 to Dec 31 of the degrees below 0 °C of each daily mean temperature: sum of max(0, -T).",
             "Freezing degree-days accumulate cold over the freeze-up season, the standard index of freezing accumulation in winter-road studies.",
             "power", "T2M", "Daily values, one seasonal total per winter", _GRID, "season_metrics_extended", "fdd_octdec", 2001, 2024, "all",
             ((2001, 2024),), True, 0, 0, "more freezing accumulation", "less freezing accumulation", _ENV_Q,
             _REANALYSIS_LIMITS + ("At the Yellowknife cell the NASA total is well above the station total; use it for year-to-year variation, not absolute cold.",)),
    Variable("tmax_mean_mar15_apr15_c", "Late-season mean daily maximum temperature (Mar 15 to Apr 15)", "Mar 15-Apr 15 mean daily max", "environmental", "core", "°C",
             "Mean of the daily maximum 2 m air temperature from Mar 15 to Apr 15.",
             "Daytime warmth late in the season is when ice roads approach closing.",
             "power", "T2M_MAX", "Daily values, one window mean per winter", _GRID, "season_metrics_extended", "tmax_mean_mar15_apr15_c", 2001, 2024, "all",
             ((2001, 2024),), True, 2, 2, "warmer", "colder", _ENV_Q, _REANALYSIS_LIMITS),
    Variable("thaw_days_janmar", "Midwinter above-freezing days (Jan to Mar)", "Jan-Mar above-freezing days", "environmental", "core", "days",
             "Number of days from Jan 1 to Mar 31 whose daily mean temperature is above 0 °C.",
             "Midwinter thaw events matter for ice and snow surfaces, so their frequency is a natural question.",
             "power", "T2M", "Daily values, one count per winter", _GRID, "climate_annual", "thaw_days", 2001, 2024, "primary",
             (), True, 0, 1, "more", "fewer", _ENV_Q,
             ("The NASA series records almost no above-freezing midwinter days, so a trend cannot be estimated.",
              "The reanalysis runs cold and under-detects thaw relative to the station; zero NASA thaw days does not mean no thaw."),
             trend_note="Counts are shown per winter. No trend is estimated when one value fills at least 75% of winters."),
    Variable("skin_temp_mean_octdec_c", "Early-winter mean surface skin temperature (Oct to Dec)", "Oct-Dec skin temperature", "environmental", "exploratory", "°C",
             "Mean of the daily Earth skin temperature from Oct 1 to Dec 31.", "The surface itself, not the air above it, is where ice forms.",
             "power", "TS", "Daily values, one seasonal mean per winter", _GRID, "season_metrics_extended", "skin_temp_mean_octdec_c", 2001, 2024, "all",
             ((2001, 2024),), True, 2, 2, "warmer", "colder", _ENV_Q, _REANALYSIS_LIMITS[:1] + ("No station comparison is available for this variable.",) + _REANALYSIS_LIMITS[2:]),
    Variable("precip_octdec_mm", "Early-winter precipitation total (Oct to Dec)", "Oct-Dec precipitation", "environmental", "exploratory", "mm",
             "Sum of daily corrected precipitation from Oct 1 to Dec 31.", "Early snow insulates new ice and slows its growth, so precipitation is a candidate influence.",
             "power", "PRECTOTCORR", "Daily values, one seasonal total per winter", _GRID, "season_metrics_extended", "precip_octdec_mm", 2001, 2024, "all",
             ((2001, 2024),), False, 1, 1, "wetter", "drier", _ENV_Q, ("Reanalysis precipitation for a grid cell; it does not separate rain from snow.", "No station comparison is shown for this variable.", "24 winters is a short record.")),
    Variable("wind_mean_octdec_ms", "Early-winter mean wind speed at 10 m (Oct to Dec)", "Oct-Dec wind speed", "environmental", "exploratory", "m/s",
             "Mean of the daily 10 m wind speed from Oct 1 to Dec 31.", "Wind affects heat loss from open water and how snow is redistributed over ice.",
             "power", "WS10M", "Daily values, one seasonal mean per winter", _GRID, "season_metrics_extended", "wind_mean_octdec_ms", 2001, 2024, "all",
             ((2001, 2024),), False, 2, 2, "windier", "calmer", _ENV_Q, ("Reanalysis value for a grid cell.", "No station comparison is shown for this variable.", "24 winters is a short record.")),
    Variable("rh_mean_octdec_pct", "Early-winter mean relative humidity at 2 m (Oct to Dec)", "Oct-Dec relative humidity", "environmental", "exploratory", "%",
             "Mean of the daily 2 m relative humidity from Oct 1 to Dec 31.", "Humidity is part of the surface energy balance during freeze-up.",
             "power", "RH2M", "Daily values, one seasonal mean per winter", _GRID, "season_metrics_extended", "rh_mean_octdec_pct", 2001, 2024, "all",
             ((2001, 2024),), False, 1, 2, "more humid", "drier", _ENV_Q, ("Reanalysis value for a grid cell.", "No station comparison is shown for this variable.", "24 winters is a short record.")),
    Variable("lw_down_mean_octdec", "Early-winter downward longwave radiation (Oct to Dec)", "Oct-Dec downward longwave", "environmental", "exploratory", "W/m²",
             "Mean of the daily all-sky surface downward longwave irradiance from Oct 1 to Dec 31.", "Downward longwave radiation from clouds and air slows surface cooling.",
             "power_ceres", "ALLSKY_SFC_LW_DWN", "Daily values, one seasonal mean per winter", "1 x 1 degree CERES SYN1deg grid", "season_metrics_extended", "lw_down_mean_octdec", 2001, 2024, "all",
             ((2001, 2024),), False, 1, 2, "more", "less", _ENV_Q, ("Satellite-derived estimate on a 1 degree grid.", "No ground comparison is shown for this variable.", "24 winters is a short record.")),
    Variable("sw_down_mean_mar15_apr15", "Late-season downward shortwave radiation (Mar 15 to Apr 15)", "Mar 15-Apr 15 downward shortwave", "environmental", "exploratory", "W/m²",
             "Mean of the daily all-sky surface downward shortwave irradiance from Mar 15 to Apr 15.", "Returning sunlight contributes to melt late in the season.",
             "power_ceres", "ALLSKY_SFC_SW_DWN", "Daily values, one window mean per winter", "1 x 1 degree CERES SYN1deg grid", "season_metrics_extended", "sw_down_mean_mar15_apr15", 2001, 2024, "all",
             ((2001, 2024),), False, 1, 2, "more", "less", _ENV_Q, ("Satellite-derived estimate on a 1 degree grid.", "No ground comparison is shown for this variable.", "24 winters is a short record.")),
    Variable("lw_down_mean_mar15_apr15", "Late-season downward longwave radiation (Mar 15 to Apr 15)", "Mar 15-Apr 15 downward longwave", "environmental", "exploratory", "W/m²",
             "Mean of the daily all-sky surface downward longwave irradiance from Mar 15 to Apr 15.", "Published work on a large NWT winter road uses downward thermal radiation as an indicator for closing dates.",
             "power_ceres", "ALLSKY_SFC_LW_DWN", "Daily values, one window mean per winter", "1 x 1 degree CERES SYN1deg grid", "season_metrics_extended", "lw_down_mean_mar15_apr15", 2001, 2024, "all",
             ((2001, 2024),), False, 1, 2, "more", "less", _ENV_Q, ("Satellite-derived estimate on a 1 degree grid.", "No ground comparison is shown for this variable.", "24 winters is a short record.")),
    Variable("open_day", "Road opening day", "Opening day", "road", "core", "days since Oct 1",
             "Recorded opening date of the road, counted in days since Oct 1 of the winter. A higher number is a later opening.",
             "The opening date is the recorded start of public traffic each winter.",
             "nwt_t108", "", "One date per winter", "One route", "road_operations_all_routes", "open_day", 1993, 2024, "all",
             ((1993, 2024), (2001, 2024)), False, 0, 1, "later", "earlier",
             "Only rows whose dates pass the record checks (status 'verified') are used.", _ROAD_LIMITS, slope_unit="days"),
    Variable("close_day", "Road closing day", "Closing day", "road", "core", "days since Oct 1",
             "Recorded final closing date of the road, counted in days since Oct 1 of the winter. A higher number is a later closing.",
             "The closing date is the recorded end of the operating season.",
             "nwt_t108", "", "One date per winter", "One route", "road_operations_all_routes", "close_day", 1993, 2024, "all",
             ((1993, 2024), (2001, 2024)), False, 0, 1, "later", "earlier",
             "Only rows whose dates pass the record checks (status 'verified') are used.", _ROAD_LIMITS, slope_unit="days"),
    Variable("open_to_close_days", "Opening-to-closing interval", "Open-to-close interval", "road", "core", "days",
             "Days from the recorded opening date to the recorded closing date.",
             "The interval between first opening and final closing bounds the operating season. It is not usable days.",
             "nwt_t108", "", "One interval per winter", "One route", "road_operations_all_routes", "open_to_close_days", 1993, 2024, "all",
             ((1993, 2024), (2001, 2024)), False, 0, 1, "longer", "shorter",
             "Only rows whose dates pass the record checks (status 'verified') are used.",
             _ROAD_LIMITS + ("The interval is not usable days: opening is to light vehicles first and temporary closures are not recorded.",)),
]}


def variables_for(location, tier: str | None = None, kind: str | None = None) -> list:
    out = []
    for v in VARIABLES.values():
        if v.locations == "primary" and not location.is_primary_pair:
            continue
        if tier and v.tier != tier:
            continue
        if kind and v.kind != kind:
            continue
        out.append(v)
    return out


# ---------------------------------------------------------------- questions
@dataclass(frozen=True)
class Question:
    id: str
    text: str
    blurb: str
    variables: tuple          # recommended variable ids, in order
    reasons: dict = field(default_factory=dict)
    next_view: str = "detective"
    next_label: str = "Open in the Trend Detective"


QUESTIONS = {q.id: q for q in [
    Question("early_winter", "Are early winters becoming warmer?",
             "Look at the season when lakes and rivers freeze over.",
             ("mean_octdec_c", "fdd_octdec"),
             {"mean_octdec_c": "The direct answer: the average Oct to Dec air temperature of each winter.",
              "fdd_octdec": "A second view of the same season that weights colder days more heavily."}),
    Question("freezing", "Is freezing accumulation changing?",
             "Track how much cold builds up before midwinter.",
             ("fdd_octdec", "mean_octdec_c"),
             {"fdd_octdec": "Freezing degree-days are the standard measure of accumulated cold in winter-road research.",
              "mean_octdec_c": "The seasonal mean over the same months, for comparison with the accumulation."}),
    Question("thaw", "Are midwinter thaw conditions changing?",
             "Count the days that rise above freezing in the coldest months.",
             ("thaw_days_janmar", "mean_janmar_c"),
             {"thaw_days_janmar": "The direct count of above-freezing days. In this dataset it is almost always zero, which is itself the finding.",
              "mean_janmar_c": "The midwinter mean temperature can still be analysed when thaw days are too rare to trend."}),
    Question("regions", "Do patterns differ between northern locations?",
             "Compare the same variable at two places over the same winters.",
             ("mean_octdec_c", "fdd_octdec", "mean_janmar_c"),
             {"mean_octdec_c": "Compared on matched winters with a test on the difference between the two series.",
              "fdd_octdec": "Compared on matched winters with a test on the difference between the two series.",
              "mean_janmar_c": "Compared on matched winters with a test on the difference between the two series."},
             next_view="compare", next_label="Open the regional comparison"),
    Question("roads", "How do environmental observations compare with road-opening records?",
             "Set NASA data beside the government record of opening and closing dates.",
             ("open_day", "fdd_octdec", "open_to_close_days"),
             {"open_day": "The recorded opening date each winter, from the territorial government.",
              "fdd_octdec": "The freezing accumulation of the same winters, shown beside the record as an association, not a cause.",
              "open_to_close_days": "The span from first opening to final closing. It is not usable days."},
             next_view="corridor", next_label="Open the corridor investigation"),
]}

DEFAULT_LOCATION = "dettah_bay"
DEFAULT_VARIABLE = "fdd_octdec"
