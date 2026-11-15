"""Methods and sources: methodology, provenance, citations, NASA resource status, AI-use disclosure and how to extend Frostline."""
import pandas as pd
import streamlit as st

from .. import APP_VERSION, METHOD_ID
from .. import analysis as an
from .. import fmt, ui
from ..data import code_version
from ..registry import LITERATURE, POWER_ACK, SOFTWARE, SOURCES
from .questions import catalogue


def giovanni_panel(ds) -> bool:
    """Shown only when a real Giovanni extraction has been ingested. Returns whether it was shown."""
    if not ds.giovanni:
        return False
    tr, chk = ds.giovanni["giovanni_monthly_t2m_trends.csv"], ds.giovanni["giovanni_vs_power_check.csv"]
    ui.html("<div class='fl-eyebrow'>MERRA-2 monthly temperature through NASA Giovanni</div>"
            "<div class='fl-sub'>Monthly mean 2 m air temperature (collection M2TMNXSLV, variable T2M) extracted through Giovanni for the same grid cells. "
            "POWER and Giovanni share the MERRA-2 source, so this is a consistency check on access routes, not an independent observation. "
            "Monthly means are used for seasonal mean-temperature trends only, never for freezing degree-days or thaw counts.</div>")
    st.dataframe(pd.DataFrame({"Location": tr.location_id, "Seasonal mean": tr.metric.map({"octdec_mean_c": "Oct to Dec", "janmar_mean_c": "Jan to Mar"}).fillna(tr.metric), "n": tr.n,
                               "Slope (°C per decade)": [fmt.num(v, 2, True) for v in tr.slope_per_decade], "95% interval": [fmt.interval(a, b, 2) for a, b in zip(tr.ci95_low, tr.ci95_high)],
                               "p (unadjusted)": [fmt.pval(p) for p in tr.mk_p], "Status": tr.status}), hide_index=True)
    st.dataframe(pd.DataFrame({"Location": chk.location_id, "Months compared": chk.n_months, "Mean difference, Giovanni minus POWER (°C)": chk.mean_diff_giovanni_minus_power_c,
                               "Largest absolute difference (°C)": chk.max_abs_diff_c, "Correlation": chk.pearson_r}), hide_index=True)
    ui.bias_caveat(ds)
    return True


def render(ds):
    ui.page_header("Methods and sources", "How Frostline works, and what it rests on",
                   "Everything needed to inspect the investigation without a presenter: methods, data provenance, citations, the status of open requirements and the limits of the work.")
    tabs = st.tabs(["Methods", "Data and citations", "NASA resource status", "AI-use disclosure", "Limits and review", "Extending Frostline"])

    with tabs[0]:
        ui.html(ui.kv_table([
            ("Winter definition", ds.facts["periods"]["winter_label_rule"]),
            ("Trend estimator", "Theil-Sen slope against the winter start year, reported per decade, with its 95% interval"),
            ("Significance test", "Mann-Kendall with tie correction, two-sided. The p-value is always labelled unadjusted"),
            ("Dependence-aware interval", "Moving-block bootstrap of residuals: blocks of ceil(n^(1/3)) winters, 2000 resamples, fixed seed 20261114"),
            ("Serial correlation", "Lag-1 autocorrelation of the residuals; above 0.3 in size raises a flag (a warning, not a correction)"),
            ("Completeness", "A winter enters a trend only with complete daily coverage. At least 15 winters are required. Missing days are never filled"),
            ("Degenerate series", "No slope or p-value when one value fills at least 75% of winters (midwinter above-freezing days)"),
            ("Multiple testing", "Benjamini-Hochberg q within five declared families, Holm across the two main families. q is shown only for the fixed windows of those families"),
            ("Regional comparison", "Trend of the difference series on matched winters; one small and one large p-value do not imply different slopes"),
            ("Associations", "Spearman rank correlation with a block-bootstrap interval, only for predictor windows that end before the earliest recorded outcome"),
            ("Bias handling", "No bias correction is applied to any reported result"),
            ("Method identifier", METHOD_ID)]))
        ui.html("<div class='fl-src'>Authoritative specification: docs/SCIENTIFIC_METHODS.md. Implementation: the metrics, statistics and recompute modules in the repository's scripts folder. "
                "The application contains no statistical method of its own.</div>")
        with st.expander("Variable catalogue"):
            st.dataframe(catalogue(ds), hide_index=True, height=380)

    with tabs[1]:
        p = ds.facts["periods"]
        s = ds.facts["status_counts"]
        ui.html(ui.kv_table([
            ("NASA daily data", f"{p['nasa_daily_first']} to {p['nasa_daily_last']}; {p['trend_winters_n']} winters ({fmt.period(p['trend_winters_first'], p['trend_winters_last'])}); "
                                f"{p['missing_nasa_days_in_trend_seasons']} missing days in the trend seasons"),
            ("Road record", f"Winters {fmt.period(p['road_record_first'], p['road_record_last'])}; {s['total_rows']} route-winter rows across {s['routes']} routes: "
                            + ", ".join(f"{v} {k.replace('_', ' ')}" for k, v in sorted(s['counts'].items()))),
            ("Station validation", f"{fmt.count(ds.facts['bias']['paired_days'])} paired days against ECCC Yellowknife A; Aklavik and Inuvik stations for the delta cell"),
            ("App data", f"{len(ds.file_hashes)} approved files in UI/data_real, digest {ds.digest}. The app reads nothing else and downloads nothing")]))
        for src in SOURCES.values():
            ui.html(f"<div class='fl-layer'><b>{ui.esc(src.name)}</b><div class='q'>{ui.esc(src.kind)} · {ui.esc(src.resolution)}</div><ul><li>{ui.esc(src.citation)}</li><li>{ui.esc(src.note)}</li>"
                    f"<li><a href='{src.url}' target='_blank' rel='noopener noreferrer'>{ui.esc(src.url)}</a></li></ul></div>")
        ui.html(f"<div class='fl-note'><b style='color:#E8EEF7'>POWER acknowledgement.</b> {ui.esc(POWER_ACK)}</div>")
        with st.expander("Context literature"):
            ui.html("<div class='fl-layer'><ul>" + "".join(f"<li>{ui.esc(x)}</li>" for x in LITERATURE) + "</ul></div>")
            ui.html("<div class='fl-src'>Used for context and for what Frostline does not claim. Frostline does not replicate these studies and does not apply the James Bay freezing threshold reported in them.</div>")
        with st.expander("Software"):
            ui.html("<div class='fl-sub'>" + ui.esc(", ".join(SOFTWARE)) + ".</div>")
        with st.expander("File hashes (sha256)"):
            st.dataframe(pd.DataFrame({"File": list(ds.file_hashes), "sha256": list(ds.file_hashes.values())}), hide_index=True)

    with tabs[2]:
        ui.html("<div class='fl-eyebrow'>NASA data use and the listed-resource requirement</div>")
        if giovanni_panel(ds):
            ui.note("A Giovanni extraction is present in the app data and is shown above. Whether it satisfies the Global Award resource requirement is for the team and organizers to confirm.")
        else:
            ui.caveat("Frostline's NASA data come from NASA POWER, whose meteorology is the MERRA-2 reanalysis. POWER is not on the challenge's listed Resources (NASA Giovanni and AppEEARS are). "
                      "A cross-extraction of MERRA-2 monthly temperature through Giovanni is prepared and has not been obtained. Meaningful use of a listed NASA resource is therefore not demonstrated in this release.",
                      "Status: not demonstrated")
            ui.html(ui.kv_table([
                ("What is used", "NASA POWER daily data: T2M, T2M_MAX, TS, PRECTOTCORR, WS10M, RH2M (MERRA-2) and surface irradiance (CERES SYN1deg)"),
                ("What the challenge names", "MERRA-2 is named in the challenge background as a suitable model; POWER distributes MERRA-2 variables"),
                ("What is ready", "A strict ingest path for a Giovanni MERRA-2 monthly T2M extraction (collection M2TMNXSLV). A panel appears here automatically once real files are ingested"),
                ("What it would add", "A consistency check that POWER equals the MERRA-2 product at the same cell, and seasonal mean-temperature trends from a listed resource. Not an independent observation"),
                ("What it would never do", "Monthly means are never used to compute freezing degree-days or thaw counts")]))
        ui.html("<div class='fl-src'>Details and the manual extraction steps: docs/CHALLENGE_ELIGIBILITY.md.</div>")

    with tabs[3]:
        ui.html("<div class='fl-eyebrow'>How AI was used</div>")
        ui.html("<div class='fl-layer'><ul>"
                "<li>The data pipeline, the statistical scripts, the documentation and this application were written with substantial AI assistance (Claude by Anthropic, including Claude Code), directed and reviewed by the team.</li>"
                "<li>AI output is not treated as evidence. Every number on screen is produced by scripts from public data and checked by automated tests; none is written by a language model.</li>"
                "<li>Interpretation sentences are fixed templates selected by the computed statistical status. No generative model runs inside the app, and no observation is sent to one.</li>"
                "<li>No AI-generated imagery is used anywhere in the product.</li>"
                "<li>The methods have not been signed off by an independent statistician. Until that happens, all results are labelled exploratory.</li>"
                "</ul></div>")

    with tabs[4]:
        ui.html("<div class='fl-eyebrow'>What Frostline does not do</div><div class='fl-layer'><ul>"
                "<li>It does not measure ice thickness, assess road safety, recommend routes or predict opening dates.</li>"
                "<li>It does not show what produced any change in road dates. Associations are labelled as associations.</li>"
                "<li>It does not present NASA grid-cell values as local observations, and it applies no bias correction.</li>"
                "<li>It does not offer an arbitrary custom location: no data exist for one.</li></ul></div>")
        ui.html("<div class='fl-eyebrow'>Known limitations</div><div class='fl-layer'><ul>"
                "<li>24 winters of NASA data and 32 winters of road records are short records; natural variability can resemble a trend.</li>"
                "<li>One reanalysis grid cell is not the whole road, and the cold-season bias against the station has no established cause.</li>"
                "<li>The Aklavik alignment, segment and grid-cell representativeness are unverified.</li>"
                "<li>Four road-record rows fail date checks and are excluded, not corrected. Temporary closures are not recorded.</li>"
                "<li>The NASA record was not extended before winter 2001/02. Results are reproducible from cached sources; a live re-download was not compared.</li>"
                "<li>Dettah was selected after its trend had been seen; no hypothesis was registered in advance.</li></ul></div>")
        ui.html("<div class='fl-eyebrow'>Review status</div>")
        ui.html(ui.kv_table([("Statistical sign-off", "Pending. No independent reviewer has signed off on the methods"),
                             ("NASA listed-resource requirement", "Not demonstrated" if not ds.giovanni else "Giovanni extraction ingested; confirmation pending"),
                             ("Stakeholder validation", "None. No community adoption, interviews or endorsements are claimed"),
                             ("Automated checks", "Scientific and application test suites; deterministic regeneration of every derived file")]))

    with tabs[5]:
        ui.html("<div class='fl-eyebrow'>Research architecture</div>"
                "<div class='fl-sub'>Locations, variables and questions are entries in registries; findings and evidence reports are typed objects. A new verified location or variable "
                "is added through the data pipeline and a registry entry, and then every view, the Evidence Engine and the Evidence Brief work for it without new statistical code.</div>")
        locs = an.locations(ds)
        st.dataframe(pd.DataFrame([{"Location": l.name, "Identifier": l.id, "Role": l.role, "Road record": l.road_id, "On the map": "yes" if l.mapped else "no (approximate point)"} for l in locs.values()]), hide_index=True)
        ui.html(ui.kv_table([
            ("To add a location", "Add its verified coordinates and per-winter values through scripts/regenerate_all.py, then add its context to the location registry"),
            ("To add a variable", "Add its per-winter column to the data files and one entry to the variable registry with definition, units, source and limitations"),
            ("Quality gates", "Complete daily coverage, documented provenance, validated units and at least 15 winters before any trend is shown"),
            ("Live NASA downloads", "Not offered. The app makes no network request for data, so results cannot change under a presenter and remain reproducible"),
            ("Guide", "docs/EXTENDING_FROSTLINE.md")]))
        ui.html(f"<div class='fl-src'>Frostline {APP_VERSION} · code {ui.esc(code_version())} · app data digest {ds.digest}</div>")
