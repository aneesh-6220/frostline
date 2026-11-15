"""Shared Streamlit layer: design system, the shared investigation state, and components used by every view.

One investigation state (location, variable, analysis window, guiding question) lives in st.session_state.
Every view reads it through current(), and every statistic on screen is derived from it through
analysis.trend(), so a change of selection re-derives every number, interval and sentence.

Presentation only: this module styles and lays out values computed elsewhere. The design tokens below
are mirrored in .streamlit/config.toml (native widgets and tables) and charts.py (figures).
"""
from __future__ import annotations

import html as _html
import os
from dataclasses import dataclass

import streamlit as st

from . import APP_NAME, TAGLINE, TEAM_NAME
from . import analysis as an
from . import brief as brief_mod
from . import evidence as ev
from . import fmt
from .registry import DEFAULT_LOCATION, DEFAULT_VARIABLE, QUESTIONS, SOURCES, VARIABLES, primary_locations, variables_for

PAGES: dict = {}   # view key -> st.Page, filled by the entrypoint on every run
ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")

STATE_TONE = {an.SUPPORTED: "good", an.UNRESOLVED: "neutral", an.EXPLORATORY: "warn", an.INSUFFICIENT: "muted", an.UNAVAILABLE: "muted"}

# ------------------------------------------------------------------ design tokens
# Surfaces step up in lightness; ink steps down. Every text token passes WCAG AA (4.5:1) on --surface.
# --frost is the single accent: focus, the active place in navigation and primary actions, nothing else.
# Status hues are reserved for evidence states and always ship with a text label.
CSS = """
<style>
:root{
--bg:#F5F5F7;--bg-side:#FBFBFD;--surface:#FFFFFF;--surface-2:#F5F5F7;--surface-3:#E8E8ED;
--line:#E5E5EA;--line-soft:#EFEFF2;--line-strong:#D2D2D7;
--ink:#1D1D1F;--ink-2:#424245;--ink-3:#6E6E73;
--frost:#0071E3;--frost-ink:#FFFFFF;--frost-tint:rgba(0,113,227,.08);
--good:#248A3D;--warn:#B25000;--alert:#D70015;--muted:#8E8E93;
--r-sm:8px;--r:12px;--r-lg:18px;
--shadow:0 1px 2px rgba(0,0,0,.04),0 4px 16px rgba(0,0,0,.04);
--s1:4px;--s2:8px;--s3:12px;--s4:16px;--s5:24px;--s6:32px;--s7:48px;
--ease:cubic-bezier(.2,.7,.2,1);--fast:120ms;--med:200ms;
--sans:-apple-system,BlinkMacSystemFont,'SF Pro Text',Inter,'Segoe UI',sans-serif;
--mono:ui-monospace,'SF Mono',Menlo,Consolas,monospace;
--tabbar-h:64px;
}

/* ---------- base ---------- */
html,body{-webkit-font-smoothing:antialiased;-moz-osx-font-smoothing:grayscale;text-rendering:optimizeLegibility}
.stApp{background:var(--bg)}
.fl-metric .v,.fl-finding .big,.fl-steps li::before{font-variant-numeric:tabular-nums}
.fl-finding .big small{font-variant-numeric:normal}
[data-testid="stMainBlockContainer"],.block-container{max-width:1240px;padding:calc(var(--s7) + var(--s5)) var(--s6) var(--s7)}
h1,h2,h3,h4{letter-spacing:-.022em;color:var(--ink)}
.stApp,.stApp p,.stApp li{font-family:var(--sans)}
a{color:var(--frost);text-underline-offset:2px}
::selection{background:rgba(0,113,227,.18)}
:focus-visible{outline:2px solid var(--frost)!important;outline-offset:2px!important;border-radius:var(--r-sm)}
.stMarkdown p{margin-bottom:0}
hr{border-color:var(--line)}

/* ---------- header and top navigation ---------- */
[data-testid="stHeader"]{background:rgba(251,251,253,.82);-webkit-backdrop-filter:saturate(180%) blur(20px);backdrop-filter:saturate(180%) blur(20px);border-bottom:1px solid var(--line);height:56px}
[data-testid="stToolbar"]{height:56px}
[data-testid="stTopNav"]{gap:2px}
[data-testid="stTopNav"] [data-testid="stIconMaterial"]{display:none}
[data-testid="stTopNavLink"]{position:relative;height:56px;padding:0 12px;border-radius:0;background:transparent!important;transition:color var(--fast) var(--ease)}
[data-testid="stTopNavLink"] p{font-size:13.5px;font-weight:400;color:var(--ink-2);letter-spacing:-.003em;transition:color var(--fast) var(--ease)}
[data-testid="stTopNavLink"]:hover p{color:var(--ink)}
[data-testid="stTopNavLink"][aria-current="page"] p{color:var(--ink)}
[data-testid="stTopNavLink"]::after{content:"";position:absolute;left:12px;right:12px;bottom:-1px;height:2px;border-radius:2px;background:var(--frost);transform:scaleX(0);transition:transform var(--med) var(--ease)}
[data-testid="stTopNavLink"][aria-current="page"]::after{transform:scaleX(1)}
[data-testid="stLogo"]{height:22px}

/* ---------- sidebar: the investigation console ---------- */
[data-testid="stSidebar"]{background:var(--bg-side);border-right:1px solid var(--line)}
[data-testid="stSidebar"] [data-testid="stSidebarUserContent"]{padding-top:var(--s2)}
[data-testid="stSidebarNav"] a span{font-size:14px}
.fl-side-team{font-size:12px;color:var(--ink-3);margin:-2px 0 var(--s5);line-height:1.5}
.fl-side-team b{color:var(--ink-2);font-weight:500}
.fl-side-h{font-size:13px;font-weight:600;color:var(--ink);letter-spacing:-.01em;margin:0 0 var(--s3)}
.fl-side-status{margin-top:var(--s4);padding:var(--s3) var(--s4);border:0;border-radius:var(--r);background:var(--surface-2)}
.fl-side-status .meta{font-size:12px;color:var(--ink-2);line-height:1.55;margin-top:var(--s2)}
.fl-side-digest{font-size:11.5px;color:var(--ink-3);line-height:1.6;margin-top:var(--s5)}
.fl-side-digest code{font-family:var(--mono);font-size:11px;color:var(--ink-2);background:none;padding:0}

/* ---------- native controls ---------- */
[data-testid="stWidgetLabel"] p{font-size:12.5px!important;font-weight:500;color:var(--ink-2)}
[data-testid="stTooltipIcon"] svg{opacity:.55}
[data-baseweb="select"]>div{min-height:40px;background:var(--surface);border-color:var(--line);transition:border-color var(--fast) var(--ease)}
[data-baseweb="select"]>div:hover{border-color:var(--line-strong)}
[data-baseweb="popover"] ul{background:var(--surface-2)}
[data-baseweb="popover"] li{font-size:14px}
button[data-testid^="stBaseButton"]{min-height:40px;padding:0 var(--s4);font-weight:500;letter-spacing:-.003em;
  transition:background-color var(--fast) var(--ease),border-color var(--fast) var(--ease),color var(--fast) var(--ease),transform var(--fast) var(--ease)}
button[data-testid^="stBaseButton"] p{font-size:14px;font-weight:500}
button[data-testid^="stBaseButton"]:active:not(:disabled){transform:translateY(1px)}
button[data-testid="stBaseButton-primary"]{background:var(--frost);border-color:var(--frost);color:var(--frost-ink);border-radius:980px}
button[data-testid="stBaseButton-primary"] p,button[data-testid="stBaseButton-primary"] span{color:var(--frost-ink)}
button[data-testid="stBaseButton-primary"]:hover{background:#0077ED;border-color:#0077ED;color:var(--frost-ink)}
button[data-testid="stBaseButton-secondary"]{background:var(--surface);border-color:var(--line-strong);border-radius:980px;color:var(--frost)}
button[data-testid="stBaseButton-secondary"] p{color:var(--frost)}
button[data-testid="stBaseButton-secondary"]:hover{background:var(--frost-tint);border-color:var(--frost);color:var(--frost)}
button[data-testid^="stBaseButton"]:disabled{opacity:.42}
[data-testid="stSidebar"] button[data-testid^="stBaseButton"]{min-height:36px}
[data-testid="stSidebar"] button[data-testid^="stBaseButton"] p{font-size:13px}
[data-testid="stSlider"] [data-testid="stSliderTickBarMin"],[data-testid="stSlider"] [data-testid="stSliderTickBarMax"]{font-size:12px;color:var(--ink-3)}
[data-testid="stSliderThumbValue"]{font-size:12px;font-family:var(--sans)}

/* tabs: an underline indicator, not pills */
.stTabs [data-baseweb="tab-list"]{gap:28px!important;overflow-x:auto;scrollbar-width:none}
.stTabs [data-baseweb="tab-list"]::-webkit-scrollbar{display:none}
.stTabs [data-baseweb="tab"]{height:44px;padding:0;background:transparent;white-space:nowrap}
.stTabs [data-baseweb="tab"] p{font-size:13.5px;font-weight:500;color:var(--ink-3);transition:color var(--fast) var(--ease)}
.stTabs [data-baseweb="tab"]:hover p,.stTabs [aria-selected="true"] p{color:var(--ink)}
.stTabs [data-baseweb="tab-highlight"]{background:var(--frost);height:2px;transition:left var(--med) var(--ease),width var(--med) var(--ease)}
.stTabs [data-baseweb="tab-border"]{background:var(--line);height:1px}
.stTabs [data-baseweb="tab-panel"]{padding-top:var(--s5)}

[data-testid="stExpander"] details{border:1px solid var(--line);border-radius:var(--r-lg);background:var(--surface);box-shadow:var(--shadow)}
[data-testid="stExpander"] summary{padding:var(--s3) var(--s4)}
[data-testid="stExpander"] summary p{font-size:14px;font-weight:500}
[data-testid="stExpander"] summary:hover p{color:var(--ink)}
[data-testid="stDataFrame"]{border-radius:var(--r);overflow:hidden}
[data-testid="stPlotlyChart"]{min-height:0}
[data-testid="stAlert"]{border-radius:var(--r)}
[data-testid="stButtonGroup"] button{min-height:36px}
[data-testid="stRadio"] label p{font-size:14px}
[data-testid="stVerticalBlockBorderWrapper"]{border-color:var(--line)}
[data-testid="stIFrame"]{border-radius:var(--r-lg);background:#fff}

/* ---------- type ---------- */
.fl-page{margin:0 0 var(--s5)}
.fl-kicker{display:flex;align-items:center;gap:var(--s2);font-size:14px;font-weight:600;color:var(--frost);margin:0 0 var(--s2)}
.fl-kicker i{display:none}
.fl-title{font-size:34px;line-height:1.12;font-weight:700;letter-spacing:-.03em;color:var(--ink);margin:0 0 var(--s2)}
.fl-lede{color:var(--ink-3);font-size:17px;line-height:1.5;max-width:68ch;margin:0}
.fl-section{display:flex;align-items:baseline;justify-content:space-between;gap:var(--s3);margin:var(--s6) 0 var(--s3)}
.fl-section h3{font-size:21px;line-height:1.25;font-weight:600;letter-spacing:-.02em;margin:0;padding:0}
.fl-section span{font-size:12.5px;color:var(--ink-3)}
.fl-label{font-size:12px;font-weight:500;color:var(--ink-3);letter-spacing:.005em}
.fl-sub{color:var(--ink-2);font-size:14px;line-height:1.6;max-width:80ch}
.fl-src{color:var(--ink-3);font-size:12px;line-height:1.55;margin-top:var(--s2)}
.fl-src code,.fl-mono{font-family:var(--mono);font-size:11.5px;color:var(--ink-2);background:none;padding:0}
.fl-plain{font-size:14px;line-height:1.6;color:var(--ink-2);margin-top:var(--s4)}
.fl-plain b{color:var(--ink);font-weight:600}
.fl-gap{height:var(--s4)}

/* ---------- hero (Observatory) ---------- */
.fl-hero{padding:var(--s2) 0 var(--s4)}
.fl-hero h1{font-size:56px;line-height:1.05;font-weight:700;letter-spacing:-.038em;margin:var(--s3) 0 var(--s4);max-width:13ch;padding:0}
.fl-hero p{font-size:19px;line-height:1.47;color:var(--ink-3);max-width:40ch;margin:0}

/* ---------- badge (evidence state) ---------- */
.fl-chip{display:inline-flex;align-items:center;gap:6px;height:24px;padding:0 10px;border-radius:980px;font-size:12.5px;font-weight:500;line-height:1;
  border:0;color:var(--ink-2);background:var(--surface-2);white-space:nowrap}
.fl-chip i{width:6px;height:6px;border-radius:50%;background:var(--muted);flex:none}
.fl-chip.good i{background:var(--good)}.fl-chip.warn i{background:var(--warn)}.fl-chip.alert i{background:var(--alert)}.fl-chip.neutral i{background:var(--ink-2)}
.fl-chip.good{background:rgba(52,199,89,.12);color:#1F7A35}.fl-chip.warn{background:rgba(255,149,0,.12);color:#9A4500}.fl-chip.alert{background:rgba(255,59,48,.10);color:#B8000F}

/* ---------- panel: one bordered surface; the base of results and charts ---------- */
.fl-panel{border:0;border-radius:var(--r-lg);background:var(--surface);box-shadow:var(--shadow);padding:var(--s5)}
.fl-panel-head{display:flex;align-items:center;justify-content:space-between;gap:var(--s3);flex-wrap:wrap}
.fl-panel-title{font-size:15px;font-weight:600;color:var(--ink);letter-spacing:-.01em;margin-top:2px}
[class*="st-key-fl_frame"]{border:0;border-radius:var(--r-lg);background:var(--surface);box-shadow:var(--shadow);padding:var(--s5) var(--s5) var(--s4)}

.fl-place{margin-top:var(--s3)}
.fl-place-name{font-size:18px;font-weight:600;letter-spacing:-.015em;color:var(--ink);margin:var(--s1) 0 2px}
.fl-place-region{font-size:13px;color:var(--ink-2);margin-bottom:var(--s2)}

.fl-matched{display:flex;flex-direction:column;gap:2px;padding-bottom:6px}
.fl-matched b{font-size:15px;font-weight:600;color:var(--ink);font-variant-numeric:tabular-nums}

/* result */
.fl-finding{border:0;border-radius:var(--r-lg);background:var(--surface);box-shadow:var(--shadow);padding:var(--s5);margin:0 0 var(--s4)}
.fl-finding .big{display:flex;align-items:baseline;flex-wrap:wrap;column-gap:var(--s2);font-size:40px;font-weight:600;letter-spacing:-.035em;color:var(--ink);line-height:1.1;margin:var(--s4) 0 var(--s1)}
.fl-finding .big small{font-size:13.5px;font-weight:500;letter-spacing:0;color:var(--ink-2);line-height:1.4}
.fl-finding p{color:var(--ink);font-size:14px;line-height:1.6;margin:var(--s3) 0 0}
.fl-finding p.dim{color:var(--ink-2);font-size:13px;margin-top:var(--s2)}
.fl-finding .big + p.dim{margin-top:0}
.fl-finding .fl-src{border-top:1px solid var(--line-soft);margin-top:var(--s4);padding-top:var(--s3)}
.fl-finding .lead{font-size:15.5px;line-height:1.55}

/* callouts */
.fl-caveat,.fl-note{display:flex;gap:var(--s3);align-items:flex-start;border-radius:var(--r);padding:var(--s3) var(--s4);font-size:13.5px;line-height:1.6;margin:var(--s3) 0}
.fl-caveat svg,.fl-note svg{flex:none;margin-top:3px}
.fl-caveat{background:rgba(255,149,0,.08);border:0;color:var(--ink)}
.fl-caveat svg{color:var(--warn)}
.fl-caveat b{color:var(--warn);font-weight:600}
.fl-note{background:var(--surface-2);border:0;color:var(--ink-2)}
.fl-note svg{color:var(--ink-3)}
.fl-note b{color:var(--ink);font-weight:600}

/* key-value list */
.fl-kv{width:100%;border-collapse:collapse;font-size:13.5px;border:0;margin:0!important}
.fl-kv tr{border:0;background:transparent!important}
.fl-kv td{padding:10px 0;border:0;border-bottom:1px solid var(--line-soft);vertical-align:top;color:var(--ink);line-height:1.55}
.fl-kv tr:last-child td{border-bottom:0}
.fl-kv td:first-child{color:var(--ink-3);width:38%;padding-right:var(--s4);font-weight:500}

/* ruled grid: cells share hairlines instead of floating as separate cards */
.fl-grid{display:grid;grid-template-columns:repeat(var(--cols,4),minmax(0,1fr));gap:0;background:var(--surface);border:0;box-shadow:var(--shadow);border-radius:var(--r-lg);overflow:hidden;margin:0 0 var(--s4)}
.fl-grid>div{padding:var(--s5);min-width:0;box-shadow:1px 0 0 var(--line),0 1px 0 var(--line)}   /* hairlines; the outer ones are clipped */
.fl-metric .k{font-size:13px;font-weight:600;color:var(--ink-2);margin-bottom:var(--s3)}
.fl-metric .v{font-size:34px;font-weight:600;letter-spacing:-.035em;color:var(--ink);line-height:1.1}
.fl-metric .u{font-size:13px;color:var(--ink-2);margin-top:2px}
.fl-metric .d{font-size:13px;color:var(--ink-2);line-height:1.55;margin-top:var(--s3)}
.fl-metric .s{font-size:11.5px;color:var(--ink-3);margin-top:var(--s3)}
.fl-dimcell .h{display:flex;justify-content:space-between;align-items:flex-start;gap:var(--s2);margin-bottom:var(--s2)}
.fl-dimcell .h b{font-size:14px;font-weight:600;color:var(--ink);letter-spacing:-.006em;line-height:1.4}
.fl-dimcell .s{color:var(--ink);font-size:13.5px;line-height:1.55;margin-bottom:var(--s2)}
.fl-dimcell ul{margin:0;padding-left:16px}.fl-dimcell li{color:var(--ink-2);font-size:12.5px;line-height:1.55;margin-bottom:2px}
.fl-dimcell .fl-src{margin-top:var(--s3)}

/* plain card (used sparingly: one location, one variable) */
.fl-card{border:0;box-shadow:var(--shadow);border-radius:var(--r-lg);background:var(--surface);padding:var(--s5);height:100%}
.fl-card .k{font-size:12px;font-weight:500;color:var(--ink-3);margin-bottom:var(--s2)}
.fl-card h4{font-size:15px;font-weight:600;color:var(--ink);margin:0 0 var(--s2);padding:0;letter-spacing:-.01em}
.fl-card p{color:var(--ink-2);font-size:13.5px;line-height:1.6;margin:0}
.fl-card p + p{margin-top:var(--s2)}

.fl-rec{display:flex;flex-direction:column;margin-bottom:var(--s2);min-height:236px}
.fl-rec p.fit{color:var(--ink)}
.fl-rec .fl-src{margin-top:auto;padding-top:var(--s3)}
/* question picker: a selectable list instead of bare radio dots */
.st-key-fl_qpick [role="radiogroup"]{gap:0;border:0;box-shadow:var(--shadow);border-radius:var(--r-lg);overflow:hidden;width:100%}
.st-key-fl_qpick [role="radiogroup"]>div{border-top:1px solid var(--line);background:var(--surface);transition:background-color var(--fast) var(--ease)}
.st-key-fl_qpick [role="radiogroup"]>div:first-child{border-top:0}
.st-key-fl_qpick [role="radiogroup"]>div:hover{background:var(--surface-2)}
.st-key-fl_qpick [role="radiogroup"]>div[data-selected="true"]{background:var(--frost-tint)}
.st-key-fl_qpick [data-testid="stRadioOption"]{display:flex;align-items:center;width:100%;min-height:46px;margin:0;padding:10px var(--s4);cursor:pointer}
.st-key-fl_qpick [role="radiogroup"]>div[data-selected="true"] p{color:var(--ink);font-weight:500}
.st-key-fl_qpick [role="radiogroup"] p{font-size:14px;color:var(--ink-2)}

/* entry rows (Observatory) */
.fl-rows{border:0;box-shadow:var(--shadow);border-radius:var(--r-lg);overflow:hidden}
.fl-rows>div{display:grid;grid-template-columns:28px 1fr;gap:var(--s3);padding:var(--s4) var(--s5);background:var(--surface);border-top:1px solid var(--line-soft)}
.fl-rows>div:first-child{border-top:0}
.fl-rows .n{font-family:var(--sans);font-size:15px;font-weight:600;color:var(--frost);padding-top:1px}
.fl-rows .k{font-size:12px;color:var(--ink-3);margin-bottom:2px}
.fl-rows h4{font-size:15px;font-weight:600;margin:0 0 var(--s1);padding:0;color:var(--ink);letter-spacing:-.01em}
.fl-rows p{font-size:13.5px;line-height:1.6;color:var(--ink-2);margin:0}

/* stepper */
.fl-steps{display:flex;flex-wrap:wrap;gap:var(--s2) var(--s4);list-style:none;margin:var(--s3) 0 0;padding:0;counter-reset:s}
.fl-steps li{display:flex;align-items:center;gap:var(--s2);font-size:13px;color:var(--ink-3);margin:0;padding:0;counter-increment:s}
.fl-steps li::before{content:counter(s);display:inline-grid;place-items:center;width:22px;height:22px;border-radius:50%;border:0;background:var(--surface-3);font-size:11px;font-weight:600;color:var(--ink-3);font-family:var(--sans)}
.fl-steps li.done{color:var(--ink-2)}
.fl-steps li.done::before{background:var(--surface-3);color:var(--ink-2);border-color:var(--line-strong)}
.fl-steps li.on{color:var(--ink);font-weight:500}
.fl-steps li.on::before{background:var(--frost);border-color:var(--frost);color:var(--frost-ink)}
.fl-progress{height:2px;background:var(--line);border-radius:2px;overflow:hidden;margin:var(--s4) 0 0}
.fl-progress i{display:block;height:100%;background:var(--frost);transition:width var(--med) var(--ease)}

/* evidence layers */
.fl-layer{padding:0;margin:0 0 var(--s5)}
.fl-layer b{color:var(--ink);font-size:14px;font-weight:600;letter-spacing:-.006em}
.fl-layer .q{color:var(--ink-3);font-size:12.5px;margin:2px 0 var(--s2)}
.fl-layer li{color:var(--ink-2);font-size:13.5px;line-height:1.6;margin-bottom:2px}
.fl-layer ul{margin:0;padding-left:16px}

/* footer */
.fl-foot{display:flex;flex-wrap:wrap;gap:var(--s2) var(--s5);justify-content:space-between;color:var(--ink-3);font-size:12px;line-height:1.6;border-top:1px solid var(--line-soft);margin-top:var(--s7);padding-top:var(--s4)}
.fl-foot p{max-width:96ch;margin:0}
.fl-foot b{color:var(--ink-2);font-weight:500}

/* ---------- mobile tab bar (phones only) ---------- */
.st-key-fl_tabbar{display:none}

/* ---------- motion: content settles in once, on navigation ---------- */
@keyframes fl-in{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:none}}
.fl-page,.fl-hero{animation:fl-in var(--med) var(--ease) both}
@media (prefers-reduced-motion:reduce){*,*::before,*::after{animation:none!important;transition:none!important}}

/* ---------- responsive ---------- */
@media (max-width:1100px){
  .fl-grid{--cols:2!important}
  [data-testid="stMainBlockContainer"],.block-container{padding-left:var(--s5);padding-right:var(--s5)}
}
@media (max-width:767px){
  [data-testid="stMainBlockContainer"],.block-container{padding:calc(56px + var(--s5)) var(--s4) calc(var(--tabbar-h) + var(--s6) + env(safe-area-inset-bottom))}
  .fl-hero h1{font-size:32px;max-width:none}
  .fl-hero p{font-size:15px}
  .fl-title{font-size:23px}
  .fl-finding .big{font-size:30px}
  .fl-grid>div,.fl-panel,.fl-finding,.fl-card{padding:var(--s4)}
  .fl-rows>div{padding:var(--s4)}
  .fl-metric .v{font-size:24px}
  .fl-section{margin-top:var(--s5);flex-direction:column;align-items:flex-start;gap:2px}
  .fl-rec{min-height:0}
  .fl-kv tr,.fl-kv td{display:block;width:100%!important}
  .fl-kv td:first-child{padding:var(--s3) 0 0;border-bottom:0;font-size:12px}
  .fl-kv td:last-child{padding-top:2px}
  button[data-testid^="stBaseButton"]{min-height:44px}
  [data-baseweb="select"]>div{min-height:44px}
  .stTabs [data-baseweb="tab"]{height:44px}
  /* bottom tab bar: the five most used destinations; everything else stays in the menu */
  .st-key-fl_tabbar{display:flex!important;position:fixed;left:0;right:0;bottom:0;z-index:999990;flex-wrap:nowrap!important;gap:0!important;
    justify-content:space-around;align-items:stretch;background:rgba(251,251,253,.92);-webkit-backdrop-filter:blur(20px);backdrop-filter:blur(20px);border-top:1px solid var(--line);box-shadow:none;
    padding:0 var(--s1) env(safe-area-inset-bottom);height:calc(var(--tabbar-h) + env(safe-area-inset-bottom))}
  .st-key-fl_tabbar>div{flex:1 1 0;min-width:0;width:auto!important}
  .st-key-fl_tabbar [data-testid="stPageLink"]{height:100%}
  .st-key-fl_tabbar a{display:flex!important;flex-direction:column;align-items:center;justify-content:center;gap:3px;height:var(--tabbar-h);min-width:44px;
    padding:0!important;margin:0;border-radius:0;background:transparent!important}
  .st-key-fl_tabbar a span{margin:0!important}
  .st-key-fl_tabbar a [data-testid="stIconMaterial"]{font-size:22px;color:var(--ink-3)}
  .st-key-fl_tabbar a p{font-size:11px!important;font-weight:500;color:var(--ink-3);white-space:nowrap}
  .st-key-fl_tabbar [class*="st-key-fl_tab_on"] a [data-testid="stIconMaterial"],.st-key-fl_tabbar [class*="st-key-fl_tab_on"] a p{color:var(--frost)}
}
@media (max-width:480px){
  .fl-grid{--cols:1!important}
  .fl-hero h1{font-size:30px}
  .fl-finding .big{font-size:28px}
}
</style>
"""

ICON = {
    # one stroke family: 16px grid, 1.5px stroke, round caps
    "info": "<svg width='16' height='16' viewBox='0 0 16 16' fill='none' aria-hidden='true'><circle cx='8' cy='8' r='6.25' stroke='currentColor' stroke-width='1.5'/><path d='M8 7.2v3.6M8 5.2v.1' stroke='currentColor' stroke-width='1.5' stroke-linecap='round'/></svg>",
    "alert": "<svg width='16' height='16' viewBox='0 0 16 16' fill='none' aria-hidden='true'><path d='M8 2.2 14.3 13.3H1.7z' stroke='currentColor' stroke-width='1.5' stroke-linejoin='round'/><path d='M8 6.6v3M8 11.4v.1' stroke='currentColor' stroke-width='1.5' stroke-linecap='round'/></svg>",
}


def esc(s) -> str:
    return _html.escape(str(s), quote=False)


def html(body: str) -> None:
    st.markdown(body, unsafe_allow_html=True)


def inject_theme() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def brand() -> None:
    """The Frostline mark in the header and the sidebar (an original SVG; no third-party logo)."""
    st.logo(os.path.join(ASSETS, "wordmark.svg"), icon_image=os.path.join(ASSETS, "mark.svg"), size="medium")


# ------------------------------------------------------------------ state
@dataclass(frozen=True)
class Investigation:
    location_id: str
    variable_id: str
    first: int
    last: int
    question_id: str | None

    @property
    def variable(self):
        return VARIABLES[self.variable_id]


def init_state(ds) -> None:
    ss = st.session_state
    locs = an.locations(ds)
    if ss.get("loc") not in locs or not locs[ss["loc"]].is_primary_pair:
        ss["loc"] = DEFAULT_LOCATION
    if ss.get("var") not in VARIABLES:
        ss["var"] = DEFAULT_VARIABLE
    lo, hi = an.available_range(ds, ss["loc"], ss["var"])
    if not (isinstance(ss.get("first"), int) and isinstance(ss.get("last"), int) and lo <= ss["first"] <= ss["last"] <= hi):
        ss["first"], ss["last"] = lo, hi
    ss.setdefault("question", None)
    ss.setdefault("demo_step", 0)


def set_investigation(ds, location_id: str | None = None, variable_id: str | None = None, window: tuple | None = None, question_id: str | None = "__keep__") -> None:
    """Change the shared investigation. A new location or variable resets the window to that record's full range."""
    ss = st.session_state
    if location_id:
        ss["loc"] = location_id
    if variable_id:
        ss["var"] = variable_id
    lo, hi = an.available_range(ds, ss["loc"], ss["var"])
    if window:
        ss["first"], ss["last"] = max(lo, int(window[0])), min(hi, int(window[1]))
    elif location_id or variable_id:
        ss["first"], ss["last"] = lo, hi
    if question_id != "__keep__":
        ss["question"] = question_id


def current() -> Investigation:
    ss = st.session_state
    return Investigation(ss["loc"], ss["var"], int(ss["first"]), int(ss["last"]), ss.get("question"))


def goto(view: str) -> None:
    st.switch_page(PAGES[view])


# ---------------------------------------------------------------- console
def _var_label(vid: str) -> str:
    v = VARIABLES[vid]
    return v.short + (" (exploratory)" if v.tier == "exploratory" else "")


def _on_loc(ds):
    set_investigation(ds, location_id=st.session_state["w_loc"])


def _on_var(ds):
    set_investigation(ds, variable_id=st.session_state["w_var"])


def _on_period(ds):
    ss = st.session_state
    value = ss.get("w_period")
    if isinstance(value, (tuple, list)) and len(value) == 2:
        set_investigation(ds, window=(min(value), max(value)))
        ss["_w_period_canon"] = (ss["loc"], ss["var"], ss["first"], ss["last"])


def _on_preset(ds, window):
    set_investigation(ds, window=window)


def console(ds, where=None) -> Investigation:
    """The shared investigation controls. Rendered in the sidebar on every view."""
    box = where or st.sidebar
    ss = st.session_state
    locs = an.locations(ds)
    prim = [l.id for l in primary_locations(locs)]
    with box:
        html(f"<div class='fl-side-team'><b>by {TEAM_NAME}</b><br>{TAGLINE}</div><div class='fl-side-h'>Current investigation</div>")
        ss["w_loc"] = ss["loc"]
        st.selectbox("Location", prim, format_func=lambda i: locs[i].road_name, key="w_loc", on_change=_on_loc, args=(ds,),
                     help="The two documented case studies. Statistics, charts and the Evidence Brief all follow this choice.")
        if VARIABLES[ss["var"]].tier == "exploratory":
            ss["show_exploratory"] = True
        ss.setdefault("show_exploratory", False)
        opts = [v.id for v in variables_for(locs[ss["loc"]]) if v.tier == "core" or ss["show_exploratory"]]
        ss["w_var"] = ss["var"]
        st.selectbox("Variable", opts, format_func=_var_label, key="w_var", on_change=_on_var, args=(ds,),
                     help="NASA environmental variables and the government road record. Exploratory variables have no station check.")
        st.toggle("Include exploratory NASA variables", key="show_exploratory", disabled=VARIABLES[ss["var"]].tier == "exploratory",
                  help="Skin temperature, precipitation, wind, humidity and surface radiation. They have no station check and are offered for exploration only.")
        lo, hi = an.available_range(ds, ss["loc"], ss["var"])
        years = list(range(lo, hi + 1))
        # the slider keeps one key (so it keeps keyboard focus); a change made elsewhere (a preset, a new variable) is pushed into it
        canon = (ss["loc"], ss["var"], ss["first"], ss["last"])
        if "w_period" in ss and ss.get("_w_period_canon") != canon:
            ss["w_period"] = (ss["first"], ss["last"])
        ss["_w_period_canon"] = canon
        st.select_slider("Analysis period (winters)", options=years, value=(ss["first"], ss["last"]), format_func=fmt.winter, key="w_period", on_change=_on_period, args=(ds,),
                         help="Winter y runs Oct 1 of y to Mar 31 of y+1. Changing the period recomputes every statistic.")
        var = VARIABLES[ss["var"]]
        if len(var.fixed_windows) > 1 or (ss["first"], ss["last"]) not in var.fixed_windows:
            for w in var.fixed_windows or ((lo, hi),):
                st.button("Approved window: " + fmt.period(*w), key=f"preset_{w[0]}_{w[1]}", on_click=_on_preset, args=(ds, w), width="stretch",
                          type="primary" if (ss["first"], ss["last"]) == w else "secondary", help="A fixed window whose result carries a multiplicity-adjusted q.")
        inv = current()
        f = an.trend(ds, inv.location_id, inv.variable_id, inv.first, inv.last)
        fixed = an.is_fixed_window(inv.variable_id, inv.first, inv.last)
        html(f"<div class='fl-side-status'>{chip(f.state_label, STATE_TONE[f.state])}"
             f"<div class='meta'>{fmt.period(inv.first, inv.last)} · n = {f.n} winters · "
             f"{'approved fixed window' if fixed else 'user-selected window: exploratory, not adjusted for multiple testing'}</div></div>")
        html(f"<div class='fl-side-digest'>Data digest <code>{ds.digest}</code> · case-study values come from the approved files in UI/data_real; only exploratory map points use live NASA POWER requests</div>")
    return inv


# -------------------------------------------------------------- components
def chip(label: str, tone: str = "neutral") -> str:
    return f"<span class='fl-chip {tone}'><i></i>{esc(label)}</span>"


def kicker(text: str) -> str:
    return f"<div class='fl-kicker'><i></i>{esc(text)}</div>"


def page_header(eyebrow: str, title: str, lede: str = "") -> None:
    html(f"<header class='fl-page'>{kicker(eyebrow) if eyebrow else ''}<div class='fl-title' role='heading' aria-level='1'>{esc(title)}</div>"
         + (f"<p class='fl-lede'>{esc(lede)}</p>" if lede else "") + "</header>")


def section(title: str, aside: str = "") -> None:
    """A section heading inside a view."""
    html(f"<div class='fl-section'><h3>{esc(title)}</h3>" + (f"<span>{esc(aside)}</span>" if aside else "") + "</div>")


def caption(text: str, top: bool = False) -> None:
    style = " style='margin-top:0'" if top else ""
    html(f"<div class='fl-src'{style}>{esc(text)}</div>")


def caveat(text: str, label: str = "Caveat") -> None:
    html(f"<div class='fl-caveat' role='note'>{ICON['alert']}<div><b>{esc(label)}.</b> {esc(text)}</div></div>")


def note(text: str, label: str = "") -> None:
    html(f"<div class='fl-note' role='note'>{ICON['info']}<div>" + (f"<b>{esc(label)}.</b> " if label else "") + f"{esc(text)}</div></div>")


def plain_language(ds, f) -> None:
    """The plain-language reading of a finding, shown under its chart."""
    note(f"{an.plain_language(ds, f)} {f.sentence}", "In plain language")


def bias_caveat(ds) -> None:
    """The required caveat beside every NASA temperature figure (text from canonical_facts.json)."""
    caveat(ds.facts["bias_caveat"] + " Absolute NASA values are not local conditions.", "Reanalysis caveat")


def provenance_line(ds, var, loc) -> str:
    src = SOURCES[var.source_id]
    if var.kind == "road":
        return f"Source: {src.name} (government record of operations) · {loc.road_name}"
    return f"Source: {src.name}, parameter {var.power_parameter} · {src.kind}, {var.spatial_resolution}"


def kv_table(rows) -> str:
    return "<table class='fl-kv'>" + "".join(f"<tr><td>{esc(k)}</td><td>{esc(v)}</td></tr>" for k, v in rows) + "</table>"


def _head(label: str, badge: str = "") -> str:
    return f"<div class='fl-panel-head'><span class='fl-label'>{esc(label)}</span>{badge}</div>"


def finding_card(ds, f: an.Finding, title: str | None = None, show_table: bool = True) -> None:
    """One result with everything the contract requires beside it: n, period, units, intervals, p, q, status and provenance."""
    var, loc = VARIABLES[f.variable_id], an.locations(ds)[f.location_id]
    tone = STATE_TONE[f.state]
    d = var.slope_decimals
    head = _head(title or var.short + " · " + loc.short, chip(f.state_label, tone))
    if f.estimated:
        big = (f"<div class='big'>{fmt.num(f.slope, d, True)}<small>{esc(var.unit_per_decade)} · {esc(f.direction)}</small></div>"
               f"<p class='dim'>95% interval {fmt.interval(f.ci_low, f.ci_high, d)} · n = {f.n} winters · {fmt.period(f.first, f.last)}</p>")
    else:
        big = f"<div class='big'>Not estimated</div><p class='dim'>n = {f.n} winters · {fmt.period(f.first, f.last)}</p>"
    body = f"<p>{esc(f.sentence)}</p>" + "".join(f"<p class='dim'>{esc(s)}</p>" for s in f.extra_sentences)
    html(f"<section class='fl-finding {tone}'>{head}{big}{body}<div class='fl-src'>{esc(provenance_line(ds, var, loc))}</div></section>")
    if show_table:
        with st.expander("Full statistical record", expanded=True):
            html(kv_table(brief_mod.stat_rows(ds, f)))
    if var.is_temperature:
        bias_caveat(ds)


def result_panel(label: str, badge: str, value: str = "", unit: str = "", meta: str = "", paragraphs=(), dim=(), source: str = "", tone: str = "neutral", lead: bool = False) -> None:
    """A result-shaped panel for values that are not a single trend Finding (a comparison, an association, a conclusion)."""
    big = f"<div class='big'>{esc(value)}" + (f"<small>{esc(unit)}</small>" if unit else "") + "</div>" if value else ""
    meta_html = f"<p class='dim'>{esc(meta)}</p>" if meta else ""
    body = "".join(f"<p class='{'lead' if lead and i == 0 else ''}'>{esc(p)}</p>" for i, p in enumerate(paragraphs)) + "".join(f"<p class='dim'>{esc(p)}</p>" for p in dim)
    html(f"<section class='fl-finding {tone}'>{_head(label, badge)}{big}{meta_html}{body}" + (f"<div class='fl-src'>{esc(source)}</div>" if source else "") + "</section>")


def dimension_cards(report: ev.EvidenceReport, columns: int = 2) -> None:
    cells = []
    for d in report.dimensions:
        cells.append(f"<div class='fl-dimcell'><div class='h'><b>{esc(d.title)}</b>{chip(d.state, d.tone)}</div><div class='s'>{esc(d.summary)}</div><ul>"
                     + "".join(f"<li>{esc(r)}</li>" for r in d.reasons) + "</ul>"
                     + (f"<div class='fl-src'>From: {esc(', '.join(d.sources))}</div>" if d.sources else "") + "</div>")
    html(f"<div class='fl-grid' style='--cols:{columns}'>" + "".join(cells) + "</div>")


def layer_blocks(report: ev.EvidenceReport, keys=None) -> None:
    for layer in report.layers:
        if keys and layer.key not in keys:
            continue
        html(f"<div class='fl-layer'><b>{esc(layer.title)}</b><div class='q'>{esc(layer.question)}</div><ul>" + "".join(f"<li>{esc(i)}</li>" for i in layer.items) + "</ul></div>")


def steps(labels, active: int | None = None) -> None:
    parts = []
    for i, lab in enumerate(labels):
        cls = "on" if active == i else "done" if (active is not None and i < active) else ""
        parts.append(f"<li class='{cls}'" + (" aria-current='step'" if active == i else "") + f">{esc(lab)}</li>")
    bar = f"<div class='fl-progress' aria-hidden='true'><i style='width:{(active + 1) / len(labels) * 100:.1f}%'></i></div>" if active is not None else ""
    html("<ol class='fl-steps'>" + "".join(parts) + "</ol>" + bar)


def card(kicker_text: str, title: str, text: str) -> str:
    return f"<div class='fl-card'><div class='k'>{esc(kicker_text)}</div><h4>{esc(title)}</h4><p>{esc(text)}</p></div>"


def _metric_cell(kicker_text: str, value: str, unit: str, sub: str, source: str) -> str:
    return (f"<div class='fl-metric'><div class='k'>{esc(kicker_text)}</div><div class='v'>{esc(value)}</div><div class='u'>{esc(unit)}</div>"
            f"<div class='d'>{esc(sub)}</div><div class='s'>{esc(source)}</div></div>")


def stat_card(kicker_text: str, value: str, unit: str, sub: str, source: str) -> str:
    """A single metric on its own surface."""
    return f"<div class='fl-grid' style='--cols:1'>{_metric_cell(kicker_text, value, unit, sub, source)}</div>"


def metrics(items) -> None:
    """A row of metrics in one ruled strip. items: (kicker, value, unit, description, source)."""
    items = list(items)
    html(f"<div class='fl-grid' style='--cols:{len(items)}'>" + "".join(_metric_cell(*i) for i in items) + "</div>")


def footer() -> None:
    html(f"<footer class='fl-foot'><p><b>{APP_NAME} by {TEAM_NAME}</b> · NASA Space Apps Challenge 2026, Be An Earth System Trend Detective! · "
         "An exploratory scientific investigation tool. It does not assess road safety, measure ice or predict opening dates, and it makes no statement of cause. "
         "Built with AI assistance; see Methods and sources for the disclosure. NASA does not endorse this project.</p></footer>")


# phones: the investigation path (place, trend, evidence, export); every other view stays in the top navigation menu
TABBAR = [("observatory", "Home", ":material/home:"), ("atlas", "Map", ":material/map:"), ("detective", "Trends", ":material/show_chart:"),
          ("evidence", "Evidence", ":material/fact_check:"), ("brief", "Brief", ":material/description:")]


def tabbar(active_key: str | None) -> None:
    """Bottom tab bar for phones (hidden by CSS above 767px). Same pages as the top navigation, so the session state is kept."""
    with st.container(key="fl_tabbar", horizontal=True, gap=None):
        for key, label, icon in TABBAR:
            if key in PAGES:
                with st.container(key=f"fl_tab_on_{key}" if key == active_key else f"fl_tab_{key}"):
                    st.page_link(PAGES[key], label=label, icon=icon)


def plot(fig, key: str) -> None:
    from .charts import CONFIG

    st.plotly_chart(fig, key=key, config=CONFIG, theme=None)


def brief_downloads(ds, inv: Investigation, key: str = "brief") -> brief_mod.Brief:
    b = brief_mod.build(ds, inv.location_id, inv.variable_id, inv.first, inv.last, inv.question_id)
    c1, c2, c3 = st.columns(3)
    c1.download_button("Download Evidence Brief (HTML)", b.html, file_name=b.filename_stem + ".html", mime="text/html", type="primary", key=f"{key}_html", width="stretch", on_click="ignore")
    c2.download_button("Download data (CSV)", b.csv, file_name=b.filename_stem + ".csv", mime="text/csv", key=f"{key}_csv", width="stretch", on_click="ignore")
    c3.download_button("Download analysis record (JSON)", b.json, file_name=b.filename_stem + ".json", mime="application/json", key=f"{key}_json", width="stretch", on_click="ignore")
    return b
