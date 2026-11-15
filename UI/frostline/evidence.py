"""The Frostline Evidence Engine.

For one investigation (location, variable, window) it assembles a structured assessment of what the evidence
is and how far it can be trusted. Six evidence layers are kept apart:

    A observations, B derived indicators, C statistical inference, D external corroboration,
    E limitations, F unanswered questions

and seven quality dimensions are judged separately, each with a plain state and the specific, source-derived
reasons for it. There is deliberately no overall score: a single number would hide which part of the
evidence is weak. Every reason is generated from the analysis objects and the approved data files.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from . import analysis as an
from . import fmt
from .registry import SOURCES, VARIABLES

# dimension states: a small fixed vocabulary, never a number
STRONG = "Meets the standard"
CAUTION = "Use with caution"
LIMITED = "Material limitation"
NOT_ASSESSED = "Not assessed"
NOT_APPLICABLE = "Not applicable"

STATE_TONE = {STRONG: "good", CAUTION: "warn", LIMITED: "alert", NOT_ASSESSED: "muted", NOT_APPLICABLE: "muted"}


@dataclass(frozen=True)
class Dimension:
    key: str
    title: str
    state: str
    summary: str
    reasons: tuple
    sources: tuple = ()

    @property
    def tone(self) -> str:
        return STATE_TONE[self.state]


@dataclass(frozen=True)
class Layer:
    key: str
    title: str
    question: str
    items: tuple


@dataclass(frozen=True)
class EvidenceReport:
    location_id: str
    variable_id: str
    first: int
    last: int
    headline: str
    suitability: str
    dimensions: tuple
    layers: tuple
    files: tuple = ()

    def dimension(self, key: str) -> Dimension:
        return next(d for d in self.dimensions if d.key == key)

    def layer(self, key: str) -> Layer:
        return next(l for l in self.layers if l.key == key)


def _completeness(ds, loc, var, f) -> Dimension:
    if var.kind == "road":
        c = an.road_status_counts(ds, loc.id, f.first, f.last)
        other = ", ".join(f"{v} {k.replace('_', ' ')}" for k, v in c["other"].items()) or "none excluded"
        reasons = [f"{c['verified']} of {c['total']} winters in {fmt.period(f.first, f.last)} have a verified opening and closing date ({other}).",
                   "Only verified rows carry dates. Flagged or missing winters are left empty, never estimated."]
        if f.n < an.MIN_SEASONS:
            return Dimension("completeness", "Temporal completeness", LIMITED, f"{f.n} verified winters: below the minimum of {an.MIN_SEASONS}.", tuple(reasons), ("road_operations_all_routes.csv",))
        state = STRONG if c["verified"] == c["total"] else CAUTION
        return Dimension("completeness", "Temporal completeness", state, f"{c['verified']} of {c['total']} winters verified.", tuple(reasons), ("road_operations_all_routes.csv",))
    reasons = [f"{f.n} of {f.n_expected} winters in {fmt.period(f.first, f.last)} have a value for this variable."]
    cov = an.coverage(ds, loc.id, f.first, f.last)
    srcs = ["season_metrics_extended.csv"]
    if cov:
        reasons.append(f"Daily NASA record for this location: {cov['complete']} of {cov['winters']} winters complete, {cov['missing_days']} missing days "
                       f"across {fmt.count(cov['days'])} expected days.")
        srcs.append("climate_annual.csv")
    else:
        reasons.append("Day-level coverage is audited in this app only for the two documented case-study locations.")
    reasons.append("A winter with any missing day would be excluded, not filled.")
    if f.n < an.MIN_SEASONS:
        return Dimension("completeness", "Temporal completeness", LIMITED, f"{f.n} winters selected: below the minimum of {an.MIN_SEASONS}.", tuple(reasons), tuple(srcs))
    state = STRONG if (f.n == f.n_expected and (cov is None or cov["missing_days"] == 0)) else CAUTION
    return Dimension("completeness", "Temporal completeness", state, f"{f.n} of {f.n_expected} winters complete.", tuple(reasons), tuple(srcs))


def _provenance(ds, loc, var, f) -> Dimension:
    src = SOURCES[var.source_id]
    if var.kind == "road":
        reasons = [f"Source: {src.citation}",
                   "Dates were read from the published workbook and checked for calendar consistency; rows that fail the checks are excluded, not corrected.",
                   "This is a primary government record of operations."]
        return Dimension("provenance", "Source provenance", STRONG, "Primary government record, publicly citable.", tuple(reasons), ("road_operations_all_routes.csv",))
    reasons = [f"Source: {src.name}, parameter {var.power_parameter}. {src.note}",
               "Downloaded 2026-11-14 through the POWER daily API; the file headers do not state a service version, which limits exact re-citation.",
               "Results are reproducible from the cached source files; a live re-download has not been compared."]
    elig = "NASA POWER is not on the challenge's listed Resources. A cross-extraction through NASA Giovanni has " + (
        "been ingested for the Dettah / Yellowknife grid cell (MERRA-2 M2TMNXSLV T2M, monthly, 1980 to 2025) and is shown in the Giovanni record view and under Methods and sources; "
        "it is monthly reanalysis and never feeds the daily metrics." if ds.giovanni else "not been obtained.")
    reasons.append(elig)
    return Dimension("provenance", "Source provenance", CAUTION, f"Documented NASA product ({src.kind}), with version and eligibility caveats.", tuple(reasons), ("canonical_facts.json",))


def _representativeness(ds, loc, var, f) -> Dimension:
    if var.kind == "road":
        if loc.id == "dettah_bay":
            return Dimension("spatial", "Spatial representativeness", STRONG, "The record describes this specific short crossing.",
                             ("The record is for the Dettah Ice Road itself, a single crossing of about 6.5 km.",
                              "Opening is to light vehicles first, so the opening date is not full-capacity status."), ())
        if loc.id == "aklavik_delta":
            return Dimension("spatial", "Spatial representativeness", CAUTION, "Which road segment the dates describe is not settled.",
                             ("The road is reported as 112 to 117 km long and the segment described by the record dates is ambiguous.",
                              "One opening date cannot describe conditions along the whole route."), ())
        return Dimension("spatial", "Spatial representativeness", CAUTION, "Route identity is limited to the workbook name.",
                         ("For supplementary routes the identity is the workbook route name only.",), ())
    grid = var.spatial_resolution
    if loc.id == "dettah_bay":
        return Dimension("spatial", "Spatial representativeness", CAUTION, "One large grid cell stands in for a 6.5 km crossing.",
                         (f"Values are averages over a {grid}.",
                          "The crossing, Yellowknife, Dettah and the airport station all sit inside the same cell, which also covers open lake and surrounding shield.",
                          "A grid-cell value is not the temperature on the ice surface or along the road."), ("corridors.csv",))
    if loc.id == "aklavik_delta":
        return Dimension("spatial", "Spatial representativeness", LIMITED, "Representativeness of the sampled cell is unverified.",
                         (f"Values are averages over a {grid}.",
                          "The sampling point is a straight-line midpoint; the road follows delta channels and may lie outside this cell for much of its length.",
                          "Whether this cell represents the road has not been verified."), ("corridors.csv",))
    return Dimension("spatial", "Spatial representativeness", LIMITED, "Approximate, team-chosen sampling point.",
                     (f"Values are averages over a {grid}.", "The sampling point is approximate and was not verified as lying on the route."), ("corridor_panel.csv",))


def _ground_agreement(ds, loc, var, f) -> Dimension:
    b = ds.facts["bias"]
    if var.kind == "road":
        return Dimension("ground", "Ground-observation agreement", NOT_APPLICABLE, "This is the primary record; no second operational record is in the data.",
                         ("No independent record of opening and closing dates is held in the app data.",
                          "Published reports were used to spot-check route identity and some dates (documented in docs/ROUTE_IDENTITY.md)."), ())
    if not var.is_temperature:
        return Dimension("ground", "Ground-observation agreement", NOT_ASSESSED, "No station comparison exists for this variable.",
                         ("The station check in this project covers air temperature and freezing degree-days only.",), ())
    if loc.id == "dettah_bay":
        s = an.station_fdd(ds)
        reasons = [f"Against the ECCC Yellowknife A station ({fmt.count(b['paired_days'])} paired days), NASA is {fmt.num(b['overall_oct_dec'], 2, True)} °C in Oct to Dec "
                   f"and {fmt.num(b['overall_jan_mar'], 2, True)} °C in Jan to Mar.",
                   f"NASA mean Oct to Dec freezing degree-days are {fmt.num(s.nasa_mean, 0)} against {fmt.num(s.station_mean, 0)} at the station "
                   f"({fmt.num(s.pct_over, 1, True)}%) on {s.n_complete} winters complete in both series.",
                   f"Year-to-year variation is tracked (correlation {fmt.num(s.pearson_r, 2)}), which does not make the absolute values agree.",
                   "The cause of the cold bias is not established, and no bias correction is applied."]
        return Dimension("ground", "Ground-observation agreement", LIMITED, "Absolute values disagree materially with the station; year-to-year variation agrees.",
                         tuple(reasons), ("bias_by_month.csv", "station_fdd_by_season.csv", "canonical_facts.json"))
    if loc.id == "aklavik_delta":
        st = ds["station_summary_aklavik_inuvik"]
        lo, hi = float(st.bias_octmar_c.max()), float(st.bias_octmar_c.min())
        reasons = [f"Against {len(st)} ECCC station records at Aklavik and Inuvik, NASA is {fmt.num(hi, 1, True)} to {fmt.num(lo, 1, True)} °C in Oct to Mar.",
                   "The stations sit at the two ends of the road, not at the sampling point.",
                   "The bias is smaller than at Yellowknife but still cold; absolute values are not local conditions."]
        return Dimension("ground", "Ground-observation agreement", CAUTION, "Colder than nearby stations by about 1 to 2 °C in the cold season.",
                         tuple(reasons), ("station_summary_aklavik_inuvik.csv",))
    return Dimension("ground", "Ground-observation agreement", NOT_ASSESSED, "No station comparison was made for this corridor.",
                     ("Station checks exist only for the Dettah and Aklavik cells.",), ())


def _precision(ds, loc, var, f) -> Dimension:
    d = var.slope_decimals
    if f.status == "too_few_points":
        return Dimension("precision", "Statistical precision", LIMITED, "Too few winters for any estimate.", (f.sentence,), ())
    if not f.estimated:
        return Dimension("precision", "Statistical precision", NOT_ASSESSED, "No trend can be estimated from this series.", (f.sentence, var.trend_note or "The values barely vary from winter to winter."), ())
    ts_excl = f.ci_low > 0 or f.ci_high < 0
    bb_excl = f.bb_low > 0 or f.bb_high < 0
    reasons = [f"Theil-Sen slope {fmt.num(f.slope, d, True)} {var.unit_per_decade}; 95% interval {fmt.interval(f.ci_low, f.ci_high, d)}; "
               f"block-bootstrap interval {fmt.interval(f.bb_low, f.bb_high, d)}; n = {f.n} winters.",
               f"Mann-Kendall p = {fmt.pval(f.p)} (unadjusted)."]
    if f.autocorr_flag:
        reasons.append(f"Residual lag-1 autocorrelation is {fmt.num(f.lag1, 2, True)} (above 0.3 in size), so the p-value may be optimistic.")
    else:
        reasons.append(f"Residual lag-1 autocorrelation is {fmt.num(f.lag1, 2, True)}; the serial-correlation flag is not raised.")
    if ts_excl and bb_excl:
        state, summary = STRONG, "Both intervals exclude zero."
    elif ts_excl or bb_excl:
        state, summary = CAUTION, "Only one of the two intervals excludes zero."
        reasons.append("The Theil-Sen and block-bootstrap intervals disagree about zero; the estimate is fragile.")
    else:
        state, summary = CAUTION, "The interval spans zero: the direction of change is not resolved."
        reasons.append("An interval that spans zero is not evidence of no change; the record may simply be too short.")
    if f.n < 24:
        reasons.append(f"{f.n} winters is a short record for a trend.")
    return Dimension("precision", "Statistical precision", state, summary, tuple(reasons), (f.stored_source,) if f.stored_source else ())


def _exploratory(ds, loc, var, f) -> Dimension:
    reasons = ["No hypothesis in this project was registered before the data were examined, so every result is exploratory."]
    if f.window_kind == "fixed" and f.q is not None:
        fam = an.FAMILY_LABEL.get(f.q_family, f.q_family)
        reasons.append(f"Multiplicity: Benjamini-Hochberg q = {fmt.pval(f.q)} within {fam}. Tests in a family are not independent, so q is indicative.")
    elif f.estimated:
        reasons.append("This window was chosen by the user, so the p-value is unadjusted and no q is reported. Changing the window changes the question.")
    if loc.id == "dettah_bay" and var.kind == "road":
        reasons.append("Dettah was selected after its road-date trend had been seen, so this result is selection-biased; the all-route family is the adjustment.")
    if not loc.is_primary_pair:
        reasons.append("Supplementary corridor with an approximate sampling point.")
    state = CAUTION if (f.state == an.SUPPORTED) else LIMITED if f.estimated else NOT_ASSESSED
    summary = {an.SUPPORTED: "Exploratory, but it survives correction in its declared family.",
               an.UNRESOLVED: "Exploratory and not supported after correction.",
               an.EXPLORATORY: "Exploratory, user-selected window, unadjusted."}.get(f.state, "No inference to qualify.")
    return Dimension("exploratory", "Exploratory status", state, summary, tuple(reasons), ("hypothesis_families.csv",))


def _alignment(ds, loc, var, f) -> Dimension:
    if var.kind == "road":
        return Dimension("alignment", "Temporal alignment with road operations", STRONG, "Each date is assigned to its own winter by a fixed rule.",
                         ("An opening or closing date in Oct to Dec belongs to the winter that started that year; Jan to Sep belongs to the winter that started the previous October.",
                          "Day numbers count from Oct 1, so the same calendar date is one day later after Feb 28 in leap-year winters (at most 1 day)."), ("road_seasons.csv",))
    if not loc.is_primary_pair:
        return Dimension("alignment", "Temporal alignment with road operations", NOT_ASSESSED, "No alignment audit exists for this corridor.",
                         ("The audit of predictor windows against road dates covers the two documented case studies only.",), ())
    ov = an.window_overlap(ds, loc.id)
    if var.column.endswith("octdec") or "octdec" in var.column:
        if ov:
            return Dimension("alignment", "Temporal alignment with road operations", LIMITED,
                             f"The Oct to Dec window overlaps the opening date in {ov['n_overlap']} of {ov['n_winters']} winters.",
                             (f"In {ov['n_overlap']} of {ov['n_winters']} winters the road opened on or before Dec 31, so this seasonal value includes days after the opening.",
                              "It can describe the winter in retrospect. It cannot be read as information that was available before the road opened.",
                              "Associations with road dates in this app use shorter windows that end before the earliest opening on record."), ("leakage_audit.csv",))
    if "mar15" in var.column:
        la = ds["leakage_audit"]
        r = la[(la.location_id == loc.id) & (la.outcome == "closing_date") & la.predictor_window.str.startswith("Mar 15 - Apr 15")]
        if len(r):
            k, n = int(r.iloc[0].n_winters_window_reaches_outcome), int(r.iloc[0].n_winters)
            state = LIMITED if k else CAUTION
            return Dimension("alignment", "Temporal alignment with road operations", state,
                             f"The Mar 15 to Apr 15 window overlaps the closing date in {k} of {n} winters.",
                             (f"In {k} of {n} winters the road closed inside this window.", "Use it to describe the late season, not as information available before closing."), ("leakage_audit.csv",))
    return Dimension("alignment", "Temporal alignment with road operations", CAUTION, "A retrospective seasonal summary.",
                     ("This value summarises a part of the winter that includes days after the road opened.",
                      "It describes the season after the fact and carries no predictive meaning for road dates."), ("leakage_audit.csv",))


def _layers(ds, loc, var, f, dims) -> tuple:
    src = SOURCES[var.source_id]
    d = var.slope_decimals
    if var.kind == "road":
        obs = (f"Opening and closing dates of the {loc.road_name}, one pair per winter, as published in {src.name}.",
               f"{f.n} verified winters in {fmt.period(f.first, f.last)}.")
        derived = (f"{var.label}: {var.definition}",)
    else:
        obs = (f"{src.name}: daily {var.power_parameter} for the grid cell containing {loc.short if loc.mapped else loc.name}. {src.kind.capitalize()} output, not a ground measurement.",
               f"{f.n} winters in {fmt.period(f.first, f.last)}.")
        derived = (f"{var.label}: {var.definition}", "One value per winter; a winter with a missing day would have no value.")
    if f.estimated:
        inference = [an.plain_language(ds, f), f"Block-bootstrap 95% interval {fmt.interval(f.bb_low, f.bb_high, d)}; Mann-Kendall p = {fmt.pval(f.p)} (unadjusted)."]
        if f.q is not None:
            inference.append(f"q = {fmt.pval(f.q)} within {an.FAMILY_LABEL.get(f.q_family, f.q_family)}.")
        else:
            inference.append("User-selected window: exploratory, not adjusted for multiple testing; no q is reported.")
        inference.append(f.sentence)
    else:
        inference = [f.sentence]
    ground = dims["ground"]
    corro = list(ground.reasons[:3])
    if var.kind == "environmental" and loc.is_primary_pair:
        a = an.associations(ds, loc.id)
        if len(a):
            corro.append(f"Leak-free climate predictors against {loc.short} road dates: {len(a)} associations, "
                         + ("all with intervals that include zero." if an.all_ci_include_zero(a) else "not all intervals include zero."))
    if var.kind == "road" and loc.is_primary_pair:
        env = an.trend(ds, loc.id, "fdd_octdec", 2001, 2024)
        corro.append(f"NASA Oct to Dec freezing degree-days for the same cell (winters {fmt.period(2001, 2024)}): "
                     f"{fmt.num(env.slope, 0, True)} °C-days per decade, 95% interval {fmt.interval(env.ci_low, env.ci_high, 0)}. {env.sentence}")
    limits = list(var.limitations)
    if loc.caution:
        limits.append(loc.caution)
    limits.append("Nothing here is a statement of cause, a road-safety statement or a prediction.")
    limits.append("No statistician has signed off on these methods; the analysis is exploratory.")
    return (
        Layer("observations", "A. Observations", "What was actually measured or modelled?", obs),
        Layer("derived", "B. Derived indicators", "What was calculated from those observations?", derived),
        Layer("inference", "C. Statistical inference", "What was estimated, and with what uncertainty?", tuple(inference)),
        Layer("corroboration", "D. External corroboration", "Do independent measurements support or contradict it?", tuple(corro)),
        Layer("limitations", "E. Limitations", "What can this evidence not establish?", tuple(limits)),
        Layer("questions", "F. Unanswered questions", "What evidence would strengthen the investigation?", tuple(_questions(ds, loc, var, f))),
    )


def _questions(ds, loc, var, f) -> list:
    q = []
    if var.kind == "environmental":
        q.append("What produces the cold-season difference between the NASA reanalysis and the station? The cause is not established.")
        q.append("Would a longer NASA record (winters before 2001/02) change the estimate? The record was not extended, to keep the cached sources verifiable.")
        if not ds.giovanni:
            q.append("Does an extraction of MERRA-2 through NASA Giovanni reproduce the POWER series at this cell? That check has not been run.")
    if var.kind == "road" or loc.is_primary_pair:
        q.append("What do local ice-thickness and snow measurements show for these winters? None are in this dataset.")
        q.append("How did construction timing, equipment and operating rules change over the record? Operational history is not recorded here.")
    if loc.id == "aklavik_delta":
        q.append("Which road segment do the Aklavik record dates describe, and does the sampled grid cell represent it?")
    if loc.id == "dettah_bay" and var.kind == "road":
        q.append("Is the later-opening estimate robust to the earliest winters? Dropping the first five winters of 2001 to 2024 leaves an interval that touches zero.")
    if not f.estimated:
        q.append("Would a station-based or higher-resolution series make this indicator estimable?")
    q.append("Has an independent statistician reviewed the methods? Sign-off is pending.")
    return q


def _headline(ds, loc, var, f) -> str:
    where = loc.short if loc.mapped else loc.name
    if f.state == an.SUPPORTED:
        return (f"The record supports a change in {var.phrase} at {where} over {fmt.period(f.first, f.last)} "
                f"({fmt.num(f.slope, var.slope_decimals, True)} {var.unit_per_decade}, {f.direction}). It is exploratory and does not show what produced the change.")
    if f.state == an.UNRESOLVED:
        return f"For {var.phrase} at {where} over {fmt.period(f.first, f.last)}, a change is not statistically resolved. That is not proof of no change."
    if f.state == an.EXPLORATORY:
        return f"A user-selected window for {var.phrase} at {where}: descriptive and unadjusted, not a supported finding."
    if f.state == an.INSUFFICIENT:
        return f"Too few winters are selected to estimate a trend in {var.phrase} at {where}."
    return f"A trend in {var.phrase} at {where} cannot be estimated from this series."


def _suitability(loc, var, f, dims) -> str:
    """What the assembled evidence is and is not suitable for, chosen from the dimension states."""
    limited = [d.title.lower() for d in dims.values() if d.state == LIMITED]
    if var.kind == "road":
        s = "Suitable for describing how recorded operating dates changed. Not suitable for inferring ice conditions, road safety or the reason for any change."
    elif var.is_temperature:
        s = ("Suitable for year-to-year variation and for trends read with their intervals. Not suitable as absolute local temperature, "
             "as an ice or safety indicator, or as a predictor of road dates.")
    else:
        s = "Suitable for an exploratory look at year-to-year variation in a model-based or satellite-derived estimate. Not verified against ground observations here."
    if limited:
        s += " Material limitations: " + ", ".join(limited) + "."
    return s


def assess(ds, location_id: str, variable_id: str, first: int, last: int) -> EvidenceReport:
    loc, var = an.locations(ds)[location_id], VARIABLES[variable_id]
    f = an.trend(ds, location_id, variable_id, first, last)
    order = [_completeness, _provenance, _representativeness, _ground_agreement, _precision, _exploratory, _alignment]
    dims = {}
    for fn in order:
        d = fn(ds, loc, var, f)
        dims[d.key] = d
    layers = _layers(ds, loc, var, f, dims)
    files = sorted({s for d in dims.values() for s in d.sources if s} | {an.get_series(ds, location_id, variable_id).source_file})
    return EvidenceReport(location_id, variable_id, int(first), int(last), _headline(ds, loc, var, f), _suitability(loc, var, f, dims),
                          tuple(dims.values()), layers, tuple(files))


def corridor_conclusion(ds, location_id: str) -> list:
    """Evidence conclusion for a documented corridor, assembled sentence by sentence from computed results."""
    loc = an.locations(ds)[location_id]
    out = []
    op_full = an.trend(ds, location_id, "open_day", 1993, 2024)
    op_nasa = an.trend(ds, location_id, "open_day", 2001, 2024)
    env = an.trend(ds, location_id, "fdd_octdec", 2001, 2024)
    word = {an.SUPPORTED: "supports", an.UNRESOLVED: "does not resolve"}[op_full.state]
    out.append(f"The government record {word} a change in the {loc.short} opening date over {fmt.period(1993, 2024)}: "
               f"{fmt.num(op_full.slope, 1, True)} days per decade ({op_full.direction}), 95% interval {fmt.interval(op_full.ci_low, op_full.ci_high, 1)}, "
               f"q = {fmt.pval(op_full.q)} across {op_full.q_family_n} route-level tests.")
    if op_nasa.state != an.SUPPORTED:
        out.append(f"Over the shorter {fmt.period(2001, 2024)} window the estimate is {fmt.num(op_nasa.slope, 1, True)} days per decade "
                   f"(interval {fmt.interval(op_nasa.ci_low, op_nasa.ci_high, 1)}) and is not supported after correction (q = {fmt.pval(op_nasa.q)}), so the result is sensitive to the period.")
    out.append(f"The NASA reanalysis freezing accumulation for the same cell shows {fmt.num(env.slope, 0, True)} °C-days per decade "
               f"(interval {fmt.interval(env.ci_low, env.ci_high, 0)}) over {fmt.period(2001, 2024)}: not statistically distinguishable from no change, which is not proof of no change.")
    a = an.associations(ds, location_id)
    if len(a):
        out.append(f"{len(a)} leak-free associations between NASA climate predictors and {loc.short} road dates were tested; "
                   + ("every interval includes zero." if an.all_ci_include_zero(a) else "not every interval includes zero."))
    if location_id == "dettah_bay":
        b = ds.facts["bias"]
        out.append(f"Station observations disagree materially with the reanalysis in absolute terms (NASA freezing degree-days {fmt.num(b['fdd_pct_over'], 1, True)}% "
                   f"against Yellowknife A), while tracking its year-to-year variation.")
    else:
        out.append("The road's alignment, the segment the dates describe and the representativeness of the sampled grid cell are unverified.")
    out.append("The evidence does not show what produced the change in operating dates. Local ice, snow and operational records would be needed to investigate that.")
    return out
