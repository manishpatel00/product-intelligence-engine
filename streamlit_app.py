#!/usr/bin/env python3
"""
Unilog Product Intelligence Engine — Streamlit Cloud demo
==========================================================
xAI-inspired design system: near-black canvas, Inter weight 400,
Geist Mono uppercase eyebrows, pill outlines, hairline borders.
"""
import csv
import html
import json
import os
import sys
import textwrap

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.pipeline import process_row
from src import llm_client

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Unilog Product Intelligence Engine",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# xAI-inspired design system CSS
# ---------------------------------------------------------------------------
st.markdown("""
<style>
/* ═══════════════════════════════════════════════════════════════
   FONTS — Inter (display/body substitute for Universal Sans)
          + Geist Mono (uppercase eyebrows, labels, counters)
   ═══════════════════════════════════════════════════════════════ */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Geist+Mono:wght@400&display=swap');
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400&display=swap');

/* ═══════════════════════════════════════════════════════════════
   DESIGN TOKENS
   ═══════════════════════════════════════════════════════════════ */
:root {
    /* Surface */
    --canvas:       #0a0a0a;
    --canvas-soft:  #1a1c20;
    --canvas-card:  #191919;
    --canvas-mid:   #363a3f;
    --hairline:     #212327;

    /* Text */
    --ink:          #ffffff;
    --body:         #dadbdf;
    --body-mid:     #7d8187;

    /* Accent (used sparingly) */
    --accent-sunset:      #ff7a17;
    --accent-sunset-soft: #ffc285;
    --accent-dusk:        #7c3aed;
    --accent-twilight:    #c4b5fd;
    --accent-breeze:      #a0c3ec;

    /* Semantic */
    --good:  #37d39b;
    --warn:  #ffb454;
    --bad:   #ff6b6b;

    /* Shape */
    --rounded-sm:   8px;
    --rounded-pill: 9999px;

    /* Spacing */
    --sp-xs:  4px;
    --sp-sm:  8px;
    --sp-md:  12px;
    --sp-lg:  16px;
    --sp-xl:  24px;
    --sp-2xl: 32px;
    --sp-3xl: 48px;
    --sp-4xl: 64px;
}

/* ═══════════════════════════════════════════════════════════════
   GLOBAL RESET
   ═══════════════════════════════════════════════════════════════ */
html, body, [class*="css"], .stApp,
div[data-testid="stAppViewContainer"],
div[data-testid="stHeader"],
div[data-testid="stToolbar"],
div[data-testid="stDecoration"] {
    font-family: 'Inter', -apple-system, sans-serif !important;
    font-weight: 400 !important;
}

/* Kill Streamlit chrome */
#MainMenu, footer,
div[data-testid="stToolbar"],
div[data-testid="stDecoration"],
div[data-testid="stStatusWidget"] {
    display: none !important;
}

/* Streamlit Header - keep minimal height for toggle if needed */
header[data-testid="stHeader"] {
    background-color: transparent !important;
    background-image: none !important;
    height: 0 !important;
}

.stApp {
    background: var(--canvas) !important;
}

/* Main container - full width */
.stMainBlockContainer,
div[data-testid="stAppViewBlockContainer"] {
    max-width: 100% !important;
    padding: 24px 32px 72px !important;
    margin: 0 auto !important;
    overflow-x: hidden !important;
}

/* ═══════════════════════════════════════════════════════════════
   HIDE SIDEBAR COMPLETELY
   ═══════════════════════════════════════════════════════════════ */
section[data-testid="stSidebar"],
div[data-testid="stSidebarCollapsedControl"],
button[data-testid="stSidebarCollapseButton"],
button[data-testid="collapsedControl"] {
    display: none !important;
    visibility: hidden !important;
    width: 0 !important;
    height: 0 !important;
    opacity: 0 !important;
    pointer-events: none !important;
}

/* ═══════════════════════════════════════════════════════════════
   TOP CONTROL BAR (replaces sidebar)
   ═══════════════════════════════════════════════════════════════ */
.xcontrol-bar {
    display: grid;
    grid-template-columns: 1fr auto;
    gap: var(--sp-xl);
    align-items: end;
    padding: var(--sp-lg) var(--sp-xl);
    background: var(--canvas-card);
    border: 1px solid var(--hairline);
    border-radius: var(--rounded-sm);
    margin-bottom: var(--sp-xl);
}

.xcontrol-left {
    display: grid;
    grid-template-columns: 280px 1fr 1fr 1fr auto;
    gap: var(--sp-md);
    align-items: end;
    width: 100%;
}

.xcontrol-group {
    display: flex;
    flex-direction: column;
    gap: var(--sp-xs);
    min-width: 0;
}

.xcontrol-group label {
    font-family: 'JetBrains Mono', 'Geist Mono', monospace !important;
    font-weight: 400 !important;
    font-size: 11px !important;
    text-transform: uppercase !important;
    letter-spacing: 1.2px !important;
    color: var(--body-mid) !important;
}

.xcontrol-group input,
.xcontrol-group textarea,
.xcontrol-group select,
.xcontrol-group div[data-baseweb="select"] {
    background: var(--canvas-soft) !important;
    border: 1px solid var(--hairline) !important;
    border-radius: var(--rounded-sm) !important;
    color: var(--ink) !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 400 !important;
    font-size: 14px !important;
    padding: var(--sp-xs) var(--sp-md) !important;
    width: 100% !important;
    box-sizing: border-box;
}

.xcontrol-group textarea {
    min-height: 72px !important;
    resize: vertical !important;
}

.xcontrol-group div[data-baseweb="select"] > div {
    background: var(--canvas-soft) !important;
    border: 1px solid var(--hairline) !important;
    border-radius: var(--rounded-sm) !important;
}

.xcontrol-actions {
    display: flex;
    gap: var(--sp-sm);
    align-items: end;
}

.xcontrol-search {
    max-width: 320px;
}

/* ═══════════════════════════════════════════════════════════════
   BUTTONS — pill outline, translucent white border
   ═══════════════════════════════════════════════════════════════ */
.stButton > button {
    background: transparent !important;
    color: var(--ink) !important;
    border: 1px solid rgba(255, 255, 255, 0.25) !important;
    border-radius: var(--rounded-pill) !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 400 !important;
    font-size: 14px !important;
    padding: var(--sp-xs) var(--sp-lg) !important;
    letter-spacing: 0 !important;
    transition: border-color 0.2s ease, background 0.2s ease;
    min-height: 44px !important;
}

.stButton > button:hover {
    border-color: rgba(255, 255, 255, 0.5) !important;
    background: rgba(255, 255, 255, 0.04) !important;
    color: var(--ink) !important;
}

/* Primary CTA — the rare filled pill */
.stButton > button[kind="primary"],
.xcontrol-actions .stButton > button {
    background: var(--ink) !important;
    color: var(--canvas) !important;
    border: 1px solid var(--ink) !important;
}

.xcontrol-actions .stButton > button:hover {
    background: #fafaf7 !important;
}

/* Download buttons */
.stDownloadButton > button {
    background: transparent !important;
    color: var(--ink) !important;
    border: 1px solid rgba(255, 255, 255, 0.25) !important;
    border-radius: var(--rounded-pill) !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 400 !important;
    font-size: 14px !important;
    min-height: 44px !important;
}

.stDownloadButton > button:hover {
    border-color: rgba(255, 255, 255, 0.5) !important;
    background: rgba(255, 255, 255, 0.04) !important;
}

/* ═══════════════════════════════════════════════════════════════
   EXPANDER
   ═══════════════════════════════════════════════════════════════ */
div[data-testid="stExpander"] {
    background: var(--canvas-card) !important;
    border: 1px solid var(--hairline) !important;
    border-radius: var(--rounded-sm) !important;
}

div[data-testid="stExpander"] summary span {
    font-family: 'JetBrains Mono', monospace !important;
    font-weight: 400 !important;
    font-size: 12px !important;
    text-transform: uppercase !important;
    letter-spacing: 1.4px !important;
    color: var(--body-mid) !important;
}

/* ═══════════════════════════════════════════════════════════════
   METRICS — override Streamlit defaults
   ═══════════════════════════════════════════════════════════════ */
div[data-testid="stMetric"] {
    background: var(--canvas-card) !important;
    border: 1px solid var(--hairline) !important;
    border-radius: var(--rounded-sm) !important;
    padding: var(--sp-xl) !important;
}

div[data-testid="stMetric"] label {
    font-family: 'JetBrains Mono', monospace !important;
    font-weight: 400 !important;
    font-size: 12px !important;
    text-transform: uppercase !important;
    letter-spacing: 1.4px !important;
    color: var(--body-mid) !important;
}

div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
    font-family: 'Inter', sans-serif !important;
    font-weight: 400 !important;
    letter-spacing: -1.2px !important;
}

/* ═══════════════════════════════════════════════════════════════
   SPINNER
   ═══════════════════════════════════════════════════════════════ */
.stSpinner > div {
    border-top-color: var(--ink) !important;
}

/* ═══════════════════════════════════════════════════════════════
   WARNING / INFO
   ═══════════════════════════════════════════════════════════════ */
div[data-testid="stAlert"] {
    background: var(--canvas-card) !important;
    border: 1px solid var(--hairline) !important;
    border-radius: var(--rounded-sm) !important;
    color: var(--body) !important;
}

/* ═══════════════════════════════════════════════════════════════
   CUSTOM COMPONENTS
   ═══════════════════════════════════════════════════════════════ */

/* Eyebrow — Geist Mono uppercase tracked */
.eyebrow {
    font-family: 'JetBrains Mono', 'Geist Mono', monospace;
    font-weight: 400;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 1.4px;
    color: var(--body-mid);
    margin-bottom: var(--sp-sm);
}

/* Display headline — Inter 400, negative tracking */
.display-xl {
    font-family: 'Inter', sans-serif;
    font-weight: 400;
    font-size: 48px;
    line-height: 48px;
    letter-spacing: -1.2px;
    color: var(--ink);
    margin: 0 0 var(--sp-lg) 0;
}

.display-md {
    font-family: 'Inter', sans-serif;
    font-weight: 400;
    font-size: 32px;
    line-height: 36px;
    letter-spacing: -0.6px;
    color: var(--ink);
    margin: 0 0 var(--sp-md) 0;
}

.display-sm {
    font-family: 'Inter', sans-serif;
    font-weight: 400;
    font-size: 20px;
    line-height: 28px;
    letter-spacing: 0;
    color: var(--ink);
    margin: 0;
}

/* Body text */
.body-lg {
    font-family: 'Inter', sans-serif;
    font-weight: 400;
    font-size: 18px;
    line-height: 28px;
    color: var(--body);
}

.body-md {
    font-family: 'Inter', sans-serif;
    font-weight: 400;
    font-size: 16px;
    line-height: 24px;
    color: var(--body);
}

.body-sm {
    font-family: 'Inter', sans-serif;
    font-weight: 400;
    font-size: 14px;
    line-height: 20px;
    color: var(--body);
}

.body-mute {
    font-family: 'Inter', sans-serif;
    font-weight: 400;
    font-size: 14px;
    line-height: 20px;
    color: var(--body-mid);
}

/* Card — canvas-card fill, hairline border, 8px radius */
.xcard {
    background: var(--canvas-card);
    border: 1px solid var(--hairline);
    border-radius: var(--rounded-sm);
    padding: var(--sp-xl);
    margin-bottom: var(--sp-lg);
}

/* Divider */
.divider {
    border: none;
    border-top: 1px solid var(--hairline);
    margin: var(--sp-2xl) 0;
}

/* Description block — accent left border */
.xdesc {
    border-left: 2px solid rgba(255, 255, 255, 0.15);
    padding: var(--sp-md) var(--sp-lg);
    margin: var(--sp-sm) 0;
    background: rgba(255, 255, 255, 0.02);
    border-radius: 0 var(--rounded-sm) var(--rounded-sm) 0;
}

.xdesc-label {
    font-family: 'JetBrains Mono', monospace;
    font-weight: 400;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    color: var(--body-mid);
    margin-bottom: 4px;
}

.xdesc-value {
    font-family: 'Inter', sans-serif;
    font-weight: 400;
    font-size: 15px;
    line-height: 22px;
    color: var(--ink);
}

.xdesc-meta {
    font-family: 'JetBrains Mono', monospace;
    font-weight: 400;
    font-size: 11px;
    color: var(--body-mid);
    margin-top: 4px;
}

/* Flag / review reason */
.xflag {
    background: rgba(255, 107, 107, 0.08);
    border: 1px solid rgba(255, 107, 107, 0.2);
    color: #ffc2c2;
    border-radius: var(--rounded-sm);
    padding: var(--sp-md) var(--sp-lg);
    margin: var(--sp-sm) 0;
    font-family: 'Inter', sans-serif;
    font-weight: 400;
    font-size: 13px;
    line-height: 20px;
}

.xok {
    color: var(--good);
    font-family: 'Inter', sans-serif;
    font-weight: 400;
    font-size: 14px;
}

/* Pill badge */
.xpill {
    display: inline-block;
    font-family: 'JetBrains Mono', monospace;
    font-weight: 400;
    font-size: 11px;
    padding: 2px 10px;
    border-radius: var(--rounded-pill);
    border: 1px solid rgba(255, 255, 255, 0.15);
    color: var(--body);
    letter-spacing: 0.5px;
}

.xpill-on {
    border-color: rgba(55, 211, 155, 0.3);
    color: var(--good);
}

.xpill-off {
    border-color: rgba(255, 180, 84, 0.3);
    color: var(--warn);
}

/* Gauge */
.xgauge-bg {
    height: 6px;
    border-radius: 3px;
    background: var(--hairline);
    overflow: hidden;
    margin-top: 6px;
}

.xgauge-fill {
    height: 100%;
    border-radius: 3px;
}

/* KV grid */
.xkv {
    display: grid;
    grid-template-columns: 140px 1fr;
    gap: 8px 16px;
}

.xkv-key {
    font-family: 'JetBrains Mono', monospace;
    font-weight: 400;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: var(--body-mid);
}

.xkv-val {
    font-family: 'Inter', sans-serif;
    font-weight: 400;
    font-size: 14px;
    color: var(--ink);
}

/* Table */
.xtable {
    width: 100%;
    border-collapse: collapse;
}

.xtable th {
    text-align: left;
    padding: 10px 12px;
    border-bottom: 1px solid var(--hairline);
    font-family: 'JetBrains Mono', monospace;
    font-weight: 400;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    color: var(--body-mid);
}

.xtable td {
    text-align: left;
    padding: 10px 12px;
    border-bottom: 1px solid var(--hairline);
    font-family: 'Inter', sans-serif;
    font-weight: 400;
    font-size: 14px;
    color: var(--ink);
}

/* 252-col grid */
.x252 {
    columns: 2;
    font-size: 12px;
    font-family: 'Inter', sans-serif;
    font-weight: 400;
}

.x252 div {
    break-inside: avoid;
    padding: 3px 0;
    border-bottom: 1px solid var(--hairline);
    color: var(--ink);
}

.x252 .xc {
    color: var(--body-mid);
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
}

/* Confidence big number */
.xconf-num {
    font-family: 'Inter', sans-serif;
    font-weight: 400;
    font-size: 48px;
    line-height: 48px;
    letter-spacing: -1.2px;
}

/* Hero header */
.xhero {
    padding: 8px 0 40px;
    border-bottom: 1px solid var(--hairline);
    margin-bottom: 30px;
}

.xutility {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 16px;
    padding-bottom: 24px;
    border-bottom: 1px solid var(--hairline);
    margin-bottom: 34px;
}

.xbrand {
    display: flex;
    align-items: center;
    gap: 10px;
    color: var(--ink);
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    letter-spacing: 1.2px;
    text-transform: uppercase;
}

.xbrand-mark {
    width: 24px;
    height: 24px;
    display: grid;
    place-items: center;
    border: 1px solid rgba(255,255,255,0.6);
    border-radius: 50%;
    color: var(--accent-sunset);
    font-size: 13px;
}

.xutility-meta {
    color: var(--body-mid);
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    letter-spacing: 0.8px;
    text-transform: uppercase;
    text-align: right;
}

.xhero-sub {
    font-family: 'Inter', sans-serif;
    font-weight: 400;
    font-size: 16px;
    line-height: 24px;
    color: var(--body-mid);
    margin-top: var(--sp-sm);
    max-width: 760px;
}

.xhero-row {
    display: grid;
    grid-template-columns: minmax(0, 1fr) 220px;
    gap: 40px;
    align-items: end;
}

.xhero-status {
    border-left: 1px solid var(--hairline);
    padding-left: 20px;
    padding-bottom: 4px;
}

.xhero-status-value {
    color: var(--ink);
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
    letter-spacing: 1px;
    text-transform: uppercase;
    margin-top: 8px;
}

.xmetric-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 1px;
    background: var(--hairline);
    border: 1px solid var(--hairline);
    border-radius: var(--rounded-sm);
    overflow: hidden;
    margin-bottom: var(--sp-lg);
}

.xmetric-cell {
    min-width: 0;
    background: var(--canvas-card);
    padding: 18px 20px;
}

.xmetric-value {
    color: var(--ink);
    font-size: 28px;
    line-height: 32px;
    letter-spacing: -0.8px;
    margin-top: 8px;
}

.xmetric-note {
    color: var(--body-mid);
    font-size: 12px;
    line-height: 18px;
    margin-top: 4px;
}

.xsection-head {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    gap: 16px;
    margin-bottom: 14px.
}

.xsection-head .eyebrow {
    margin-bottom: 0;
}

.xsource-grid {
    display: grid;
    grid-template-columns: 150px minmax(0, 1fr);
    gap: 0;
    border: 1px solid var(--hairline);
    border-radius: var(--rounded-sm);
    overflow: hidden;
    margin-bottom: var(--sp-lg);
}

.xsource-label,
.xsource-value {
    padding: 12px 14px;
    border-bottom: 1px solid var(--hairline);
}

.xsource-label {
    background: rgba(255,255,255,0.025);
    color: var(--body-mid);
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    letter-spacing: 0.8px;
    text-transform: uppercase;
}

.xsource-value {
    min-width: 0;
    color: var(--ink);
    font-size: 14px;
    line-height: 20px;
    overflow-wrap: anywhere;
}

.xsource-label:nth-last-child(2),
.xsource-value:last-child {
    border-bottom: 0;
}

/* Pipeline step */
.xstep {
    display: flex;
    align-items: flex-start;
    gap: var(--sp-md);
    padding: var(--sp-sm) 0;
}

.xstep-num {
    font-family: 'JetBrains Mono', monospace;
    font-weight: 400;
    font-size: 12px;
    color: var(--body-mid);
    min-width: 20px;
}

.xstep-ai { color: var(--accent-breeze); }
.xstep-det { color: var(--good); }

.xstep-text {
    font-family: 'Inter', sans-serif;
    font-weight: 400;
    font-size: 14px;
    color: var(--body);
}

.xstep-text span {
    color: var(--ink);
}

/* Dashboard grid */
.xdash-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: var(--sp-lg);
}

.xdash-grid-3 {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: var(--sp-lg);
}

@media (max-width: 1024px) {
    .xdash-grid,
    .xdash-grid-3 {
        grid-template-columns: 1fr;
    }
}

@media (max-width: 768px) {
    .stMainBlockContainer,
    div[data-testid="stAppViewBlockContainer"] {
        padding: 16px 16px 48px !important;
    }

    .xcontrol-bar {
        grid-template-columns: 1fr;
        gap: var(--sp-lg);
    }

    .xcontrol-left {
        grid-template-columns: 1fr;
        gap: var(--sp-md);
    }

    .xcontrol-search {
        max-width: none;
    }

    .xhero-row {
        display: block;
    }

    .xhero-status {
        border-left: 0;
        border-top: 1px solid var(--hairline);
        margin-top: 24px;
        padding: 16px 0 0;
        padding-left: 0;
    }

    .xmetric-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }

    .xmetric-cell {
        padding: 14px 16px;
    }

    .xhero-sub {
        font-size: 15px;
        line-height: 22px;
    }

    .xcard {
        overflow: hidden;
        padding: var(--sp-md) !important;
    }

    .xtable {
        display: block;
        overflow-x: auto;
        white-space: nowrap;
    }

    .xstep {
        gap: 10px;
    }

    .xstep-text {
        line-height: 20px;
    }

    .stButton > button,
    .stDownloadButton > button {
        min-height: 44px !important;
    }

    div[data-testid="stHorizontalBlock"] {
        gap: 12px !important;
    }

    .display-xl {
        font-size: 48px !important;
        line-height: 48px !important;
        letter-spacing: -1.2px !important;
    }

    .xkv {
        grid-template-columns: 1fr;
        gap: 4px;
        margin-bottom: var(--sp-lg);
    }
    .xkv-key {
        margin-top: var(--sp-sm);
    }

    .x252 {
        columns: 1;
    }

    div[data-testid="stMetric"] {
        padding: var(--sp-md) !important;
    }

    .xsource-grid {
        grid-template-columns: 1fr;
    }

    .xsource-label {
        padding-bottom: 4px;
        border-bottom: 0;
    }

    .xsource-value {
        padding-top: 0;
    }
}

@media (min-width: 769px) {
    .display-xl {
        font-size: 72px;
        line-height: 72px;
        letter-spacing: -1.8px;
    }
}

@media (max-width: 420px) {
    .display-xl {
        font-size: 40px !important;
        line-height: 42px !important;
    }

    .xmetric-value {
        font-size: 24px;
    }
}

/* Pipeline visualization component */
.xpipeline {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: var(--sp-sm);
}

.pipe-stage {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: var(--sp-md) var(--sp-xl);
    background: var(--canvas-card);
    border: 1px solid var(--hairline);
    border-radius: var(--rounded-sm);
    width: 100%;
    max-width: 720px;
    text-align: center;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.pipe-stage:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(0,0,0,0.3);
    border-color: rgba(255,255,255,0.1);
}

.pipe-input .pipe-icon { color: var(--accent-sunset); }
.pipe-output .pipe-icon { color: var(--good); }

.pipe-icon {
    font-size: 20px;
    margin-bottom: var(--sp-xs);
    line-height: 1;
}

.pipe-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
    font-weight: 400;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    color: var(--ink);
    margin-bottom: var(--sp-xs);
}

.pipe-meta {
    font-family: 'Inter', sans-serif;
    font-size: 13px;
    color: var(--body-mid);
    line-height: 1.5;
}

.pipe-connector {
    color: var(--hairline);
    font-size: 18px;
    line-height: 1;
    margin: var(--sp-xs) 0;
    animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 0.4; }
    50% { opacity: 1; }
}

.pipe-group {
    width: 100%;
    max-width: 720px;
    background: var(--canvas-card);
    border: 1px solid var(--hairline);
    border-radius: var(--rounded-sm);
    padding: var(--sp-lg) var(--sp-xl);
    position: relative;
}

.pipe-ai {
    border-left: 3px solid var(--accent-breeze);
}

.pipe-det {
    border-left: 3px solid var(--good);
}

.pipe-group-header {
    display: flex;
    align-items: center;
    gap: var(--sp-md);
    margin-bottom: var(--sp-lg);
    padding-bottom: var(--sp-md);
    border-bottom: 1px solid var(--hairline);
}

.pipe-group-badge {
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    font-weight: 400;
    text-transform: uppercase;
    letter-spacing: 1px;
    padding: 2px 8px;
    border-radius: var(--rounded-pill);
    background: rgba(255,255,255,0.05);
}

.pipe-ai .pipe-group-badge {
    color: var(--accent-breeze);
    border: 1px solid rgba(160,195,236,0.3);
}

.pipe-det .pipe-group-badge {
    color: var(--good);
    border: 1px solid rgba(55,211,155,0.3);
}

.pipe-group-title {
    font-family: 'Inter', sans-serif;
    font-size: 14px;
    color: var(--body-mid);
}

.pipe-stages {
    display: flex;
    flex-wrap: wrap;
    align-items: stretch;
    gap: var(--sp-sm);
    justify-content: center;
}

.pipe-step {
    flex: 1;
    min-width: 140px;
    max-width: 180px;
    background: var(--canvas-soft);
    border: 1px solid var(--hairline);
    border-radius: var(--rounded-sm);
    padding: var(--sp-md);
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    transition: all 0.2s ease;
    position: relative;
}

.pipe-step:hover {
    border-color: rgba(255,255,255,0.15);
    background: rgba(255,255,255,0.02);
}

.pipe-ai .pipe-step { border-top: 2px solid var(--accent-breeze); }
.pipe-det .pipe-step { border-top: 2px solid var(--good); }

.pipe-step-num {
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    font-weight: 400;
    color: var(--body-mid);
    margin-bottom: var(--sp-xs);
}

.pipe-ai .pipe-step-num { color: var(--accent-breeze); }
.pipe-det .pipe-step-num { color: var(--good); }

.pipe-step-name {
    font-family: 'Inter', sans-serif;
    font-size: 13px;
    font-weight: 400;
    color: var(--ink);
    margin-bottom: var(--sp-xs);
    line-height: 1.3;
}

.pipe-step-desc {
    font-family: 'Inter', sans-serif;
    font-size: 11px;
    color: var(--body-mid);
    line-height: 1.4;
}

.pipe-arrow {
    color: var(--hairline);
    font-size: 18px;
    line-height: 1;
    display: flex;
    align-items: center;
    height: 100%;
    min-height: 80px;
}

.pipe-legend {
    justify-content: center;
}

@media (max-width: 768px) {
    .pipe-stages {
        flex-direction: column;
        align-items: stretch;
    }

    .pipe-step {
        max-width: none;
        min-width: 0;
    }

    .pipe-arrow {
        display: none;
    }

    .pipe-step::after {
        content: "→";
        position: absolute;
        right: var(--sp-md);
        top: 50%;
        transform: translateY(-50%);
        color: var(--hairline);
        font-size: 16px;
    }

    .pipe-step:last-child::after {
        display: none;
    }
}

@media (max-width: 420px) {
    .pipe-stage {
        padding: var(--sp-md) var(--sp-md);
    }

    .pipe-group {
        padding: var(--sp-md);
    }

    .pipe-group-header {
        flex-direction: column;
        align-items: flex-start;
        gap: var(--sp-xs);
    }
}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Presets
# ---------------------------------------------------------------------------
@st.cache_data
def load_presets():
    presets = []
    root = os.path.dirname(os.path.abspath(__file__))
    gt = os.path.join(root, "data", "ground_truth_input.csv")
    samp = os.path.join(root, "data", "input_sample_1000.csv")
    try:
        with open(gt, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                presets.append(r)
    except Exception:
        pass
    try:
        with open(samp, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                presets.append(r)
    except Exception:
        pass
    return presets


PRESETS = load_presets()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def gauge_color(v):
    if v >= 0.75:
        return "var(--good)"
    elif v >= 0.5:
        return "var(--warn)"
    return "var(--bad)"


def render_desc(label, value, meta=None):
    val = value if value else '<span style="color:var(--body-mid)">-</span>'
    meta_html = f'<div class="xdesc-meta">{meta}</div>' if meta else ""
    return f"""
    <div class="xdesc">
        <div class="xdesc-label">{label}</div>
        <div class="xdesc-value">{val}</div>
        {meta_html}
    </div>
    """


def render_source_row(row):
    fields = (
        ("MPN", row.get("Mfg_Part_Num", "")),
        ("Description", row.get("Part_Desc", "")),
        ("E1 brand", row.get("E1_Brand", "")),
        ("Unilog brand", row.get("Unilog_Brand", "")),
        ("DIB brand", row.get("DIB_Brand", "")),
        ("Manufacturer", row.get("Part_Manuf", "")),
    )
    return "".join(
        f'<div class="xsource-label">{html.escape(label)}</div>'
        f'<div class="xsource-value">{html.escape(value) or "-"}</div>'
        for label, value in fields
    )


# ---------------------------------------------------------------------------
# Session state init
# ---------------------------------------------------------------------------
if "preset_idx" not in st.session_state:
    st.session_state.preset_idx = 0
if "search_query" not in st.session_state:
    st.session_state.search_query = ""
if "mpn" not in st.session_state:
    st.session_state.mpn = ""
if "desc" not in st.session_state:
    st.session_state.desc = ""
if "manuf" not in st.session_state:
    st.session_state.manuf = ""
if "brands" not in st.session_state:
    st.session_state.brands = ""
if "enrich_clicked" not in st.session_state:
    st.session_state.enrich_clicked = False
if "selected_row" not in st.session_state:
    st.session_state.selected_row = None
if "rec" not in st.session_state:
    st.session_state.rec = None
if "qa" not in st.session_state:
    st.session_state.qa = None


# ---------------------------------------------------------------------------
# Header / Hero
# ---------------------------------------------------------------------------
ai_on = llm_client.have_api_key()
pill_class = "xpill xpill-on" if ai_on else "xpill xpill-off"
pill_text = f"Claude AI · {llm_client.DEFAULT_MODEL}" if ai_on else "Deterministic fallback"

st.markdown(f"""
<div class="xutility">
    <div class="xbrand">
        <span class="xbrand-mark">U</span>
        <span>Unilog / Product Intelligence</span>
    </div>
    <div class="xutility-meta">Delivery format · 252 fields · 9-stage pipeline</div>
</div>
<div class="xhero">
    <div class="xhero-row">
        <div>
            <div class="eyebrow">Product Intelligence Engine</div>
            <div class="display-xl">Messy distributor rows → clean commerce records</div>
            <div class="xhero-sub">
                Drop in a cryptic SKU line. Get back a complete, search-ready product record -
                classified, attributed, described in five formats, and validated against 252 standard fields.
                AI proposes. Deterministic rules enforce. Nothing invented ships.
            </div>
        </div>
        <div class="xhero-status">
            <div class="eyebrow">Engine status</div>
            <div class="xhero-status-value">{pill_text}</div>
        </div>
    </div>
    <div style="margin-top: var(--sp-lg)">
        <span class="xpill" style="margin-left:8px">Team Codehunt</span>
        <span class="xpill" style="margin-left:8px">UniHack 2026</span>
    </div>
</div>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Top Control Bar (replaces sidebar)
# ---------------------------------------------------------------------------
search_query = st.session_state.search_query
normalized_query = search_query.strip().casefold()
if normalized_query:
    visible_indices = [
        i for i, row in enumerate(PRESETS)
        if normalized_query in " ".join(row.values()).casefold()
    ]
else:
    visible_indices = list(range(min(12, len(PRESETS))))

preset_options = ["- choose a sample row -"] + [
    f"{(PRESETS[i].get('Mfg_Part_Num') or 'row')[:28]} - "
    f"{(PRESETS[i].get('Part_Desc') or '')[:48]}"
    for i in visible_indices
]

# Build the control bar using columns
col_search, col_preset, col_mpn, col_desc, col_manuf, col_brands, col_action = st.columns(
    [1.2, 1.8, 1.2, 2.5, 1.2, 1.5, 1],
    gap="medium"
)

with col_search:
    st.markdown('<div class="xcontrol-group xcontrol-search">', unsafe_allow_html=True)
    st.markdown('<label>Search catalog</label>', unsafe_allow_html=True)
    new_search = st.text_input("Search catalog", 
                                value=search_query,
                                placeholder="MPN or description…",
                                label_visibility="collapsed",
                                key="search_input")
    if new_search != search_query:
        st.session_state.search_query = new_search
        st.session_state.preset_idx = 0
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

with col_preset:
    st.markdown('<div class="xcontrol-group">', unsafe_allow_html=True)
    st.markdown('<label>Sample row</label>', unsafe_allow_html=True)
    new_preset = st.selectbox("Sample row",
                               options=range(len(preset_options)),
                               format_func=lambda i: preset_options[i],
                               label_visibility="collapsed",
                               key="preset_select")
    if new_preset != st.session_state.preset_idx:
        st.session_state.preset_idx = new_preset
        if new_preset > 0:
            p = PRESETS[visible_indices[new_preset - 1]]
            st.session_state.mpn = p.get("Mfg_Part_Num", "")
            st.session_state.desc = p.get("Part_Desc", "")
            st.session_state.manuf = p.get("Part_Manuf", "")
            st.session_state.brands = " | ".join(filter(None, [
                p.get("E1_Brand", ""), p.get("Unilog_Brand", ""), p.get("DIB_Brand", "")
            ]))
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

with col_mpn:
    st.markdown('<div class="xcontrol-group">', unsafe_allow_html=True)
    st.markdown('<label>MPN</label>', unsafe_allow_html=True)
    st.session_state.mpn = st.text_input("MPN",
                                          value=st.session_state.mpn,
                                          placeholder="PDSH4816AF",
                                          label_visibility="collapsed")
    st.markdown('</div>', unsafe_allow_html=True)

with col_desc:
    st.markdown('<div class="xcontrol-group">', unsafe_allow_html=True)
    st.markdown('<label>Part description</label>', unsafe_allow_html=True)
    st.session_state.desc = st.text_area("Part description",
                                          value=st.session_state.desc,
                                          placeholder="Dishwasher SS - Display Only…",
                                          label_visibility="collapsed",
                                          height=72)
    st.markdown('</div>', unsafe_allow_html=True)

with col_manuf:
    st.markdown('<div class="xcontrol-group">', unsafe_allow_html=True)
    st.markdown('<label>Manufacturer</label>', unsafe_allow_html=True)
    st.session_state.manuf = st.text_input("Manufacturer",
                                            value=st.session_state.manuf,
                                            placeholder="Appliance Dealers…",
                                            label_visibility="collapsed")
    st.markdown('</div>', unsafe_allow_html=True)

with col_brands:
    st.markdown('<div class="xcontrol-group">', unsafe_allow_html=True)
    st.markdown('<label>Brand fields</label>', unsafe_allow_html=True)
    st.session_state.brands = st.text_input("Brand fields",
                                             value=st.session_state.brands,
                                             placeholder="Unbranded | …",
                                             label_visibility="collapsed")
    st.markdown('</div>', unsafe_allow_html=True)

with col_action:
    st.markdown('<div class="xcontrol-group xcontrol-actions">', unsafe_allow_html=True)
    st.markdown('<label style="visibility:hidden">Action</label>', unsafe_allow_html=True)
    enrich_btn = st.button("Enrich →", use_container_width=True, type="primary")
    if enrich_btn:
        st.session_state.enrich_clicked = True
    st.markdown('</div>', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Load selected row
# ---------------------------------------------------------------------------
if st.session_state.preset_idx and st.session_state.preset_idx > 0:
    st.session_state.selected_row = PRESETS[visible_indices[st.session_state.preset_idx - 1]]
else:
    st.session_state.selected_row = None


# ---------------------------------------------------------------------------
# Main Dashboard
# ---------------------------------------------------------------------------
if st.session_state.selected_row:
    st.markdown(f"""
    <div class="xsection-head">
        <div class="eyebrow">Source row · 6 fields</div>
        <div class="body-mute">Selected from catalog</div>
    </div>
    <div class="xsource-grid">{render_source_row(st.session_state.selected_row)}</div>
    """, unsafe_allow_html=True)

if st.session_state.enrich_clicked and st.session_state.desc.strip():
    brand_parts = [b.strip() for b in (st.session_state.brands or "").split("|")]
    row = {
        "Mfg_Part_Num": st.session_state.mpn,
        "Part_Desc": st.session_state.desc,
        "Part_Manuf": st.session_state.manuf,
        "E1_Brand": brand_parts[0] if len(brand_parts) > 0 else "",
        "Unilog_Brand": brand_parts[1] if len(brand_parts) > 1 else "",
        "DIB_Brand": brand_parts[2] if len(brand_parts) > 2 else "",
    }

    with st.spinner("Running 9-stage pipeline…"):
        rec, qa = process_row(row)

    st.session_state.rec = rec
    st.session_state.qa = qa
    st.session_state.enrich_clicked = False

elif st.session_state.enrich_clicked and not st.session_state.desc.strip():
    st.warning("Enter a Part Description to enrich.")
    st.session_state.enrich_clicked = False


# Render results if available
if st.session_state.rec and st.session_state.qa:
    rec = st.session_state.rec
    qa = st.session_state.qa

    # ── Identity & Taxonomy ──────────────────────────────────
    st.markdown("""
    <div class="xcard">
        <div class="eyebrow">Identity & Taxonomy</div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div class="xkv">
            <div class="xkv-key">Brand</div>
            <div class="xkv-val">{rec.get('BRAND_NAME') or '-'}</div>
            <div class="xkv-key">Manufacturer</div>
            <div class="xkv-val">{rec.get('MANUFACTURER_NAME') or '<span style="color:var(--body-mid)">withheld / flagged</span>'}</div>
            <div class="xkv-key">MPN</div>
            <div class="xkv-val">{rec.get('MANUFACTURER_PART_NUMBER') or '-'}</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        dept_class = ' > '.join(filter(None, [rec.get('Dept'), rec.get('Class'), rec.get('Fine')]))
        st.markdown(f"""
        <div class="xkv">
            <div class="xkv-key">Classpath</div>
            <div class="xkv-val">{rec.get('Classpath') or '-'}</div>
            <div class="xkv-key">Dept / Class</div>
            <div class="xkv-val">{dept_class or '-'}</div>
            <div class="xkv-key">Product</div>
            <div class="xkv-val">{rec.get('Product Name') or '-'}</div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Descriptions ────────────────────────────────────────
    inv = rec.get("INVOICE_DESC", "")
    mob = rec.get("MOBILE_DESC", "")
    st.markdown(f"""
    <div class="xcard">
        <div class="eyebrow">Five description formats from one source</div>
        {render_desc("Invoice desc · ≤40 CAPS", inv, f"{len(inv)}/40 chars" if inv else None)}
        {render_desc("Mobile desc · 60–80 chars", mob, f"{len(mob)} chars" if mob else None)}
        {render_desc("Short description", rec.get("SHORT_DESC", ""))}
        {render_desc("Long description", rec.get("LONG_DESC1", ""))}
        {render_desc("Marketing copy", rec.get("MARKETING_DESCRIPTION", ""))}
    </div>
    """, unsafe_allow_html=True)

    # ── Attributes ──────────────────────────────────────────
    attr_rows = []
    for i in range(1, 51):
        label = rec.get(f"ATTRIBUTE_LABEL {i}", "")
        if not label:
            continue
        value = rec.get(f"ATTRIBUTE_VALUE {i}", "")
        uom = rec.get(f"ATTRIBUTE_UOM {i}", "")
        attr_rows.append((label, value, uom))

    table_html = ""
    if attr_rows:
        table_html = '<table class="xtable"><tr><th>Label</th><th>Value</th><th>UOM</th></tr>'
        for label, value, uom in attr_rows:
            uom_html = f'<span class="xpill">{uom}</span>' if uom else '<span style="color:var(--body-mid)">-</span>'
            table_html += f'<tr><td>{label}</td><td>{value}</td><td>{uom_html}</td></tr>'
        table_html += '</table>'
    else:
        table_html = '<div class="body-mute">No attributes extracted</div>'

    st.markdown(f"""
    <div class="xcard">
        <div class="eyebrow">Attributes · normalised · approved UOM</div>
        {table_html}
    </div>
    """, unsafe_allow_html=True)

    # ── Confidence & Review ─────────────────────────────────
    overall = qa.get("overall_confidence", 0)
    needs_review = qa.get("needs_human_review", False)
    overall_color = gauge_color(overall)
    engine_label = "Claude AI + rule gate" if qa.get("ai_used") else "Deterministic fallback"

    review_html = ""
    if needs_review:
        review_html = '<span style="color:var(--warn)">⚑ Routed to human review</span>'
    else:
        review_html = '<span class="xok">✓ Auto-shippable</span>'

    # Field confidence gauges
    fc_html = ""
    for field, conf in qa.get("field_confidence", {}).items():
        color = gauge_color(conf)
        pct = int(conf * 100)
        fc_html += f"""
        <div style="margin:10px 0">
            <div style="display:flex; justify-content:space-between; align-items:center">
                <span class="xkv-key" style="text-transform:none; letter-spacing:0">{field}</span>
                <span style="font-family:'JetBrains Mono',monospace; font-size:12px; color:var(--body)">{conf}</span>
            </div>
            <div class="xgauge-bg"><div class="xgauge-fill" style="width:{pct}%; background:{color}"></div></div>
        </div>
        """

    # Review reasons
    reasons = qa.get("review_reasons", [])
    flags_html = ""
    if reasons:
        for reason in reasons:
            flags_html += f'<div class="xflag">⚑ {reason}</div>'
    else:
        flags_html = '<div class="xok" style="margin-top:var(--sp-md)">✓ No blocking issues - auto-shippable.</div>'

    st.markdown(f"""
    <div class="xcard">
        <div class="eyebrow">Confidence & review queue</div>
        <div style="display:flex; gap:24px; align-items:center; margin-bottom:var(--sp-xl)">
            <div class="xconf-num" style="color:{overall_color}">{overall}</div>
            <div>
                <div>{review_html}</div>
                <div class="body-mute" style="font-size:12px; margin-top:4px">
                    <span class="xpill" style="font-size:10px">{engine_label}</span>
                    <span style="margin-left:8px">{qa.get('n_attributes', 0)} attributes</span>
                </div>
            </div>
        </div>
        {fc_html}
        <hr class="divider" style="margin:var(--sp-lg) 0">
        {flags_html}
    </div>
    """, unsafe_allow_html=True)

    # ── Full 252-column record ──────────────────────────────
    filled = sum(1 for v in rec.values() if v)
    with st.expander(f"Full 252-column record · {filled} populated"):
        col_csv, col_json, _ = st.columns([1, 1, 2])
        with col_csv:
            csv_data = ",".join(rec.keys()) + "\n" + ",".join(
                f'"{str(v).replace(chr(34), chr(34)+chr(34))}"' if v else '""' for v in rec.values()
            ) + "\n"
            st.download_button("⬇ CSV", csv_data,
                               file_name=f"{st.session_state.mpn or 'record'}_enriched.csv",
                               mime="text/csv", use_container_width=True)
        with col_json:
            st.download_button("⬇ JSON", json.dumps(rec, indent=2),
                               file_name=f"{st.session_state.mpn or 'record'}.json",
                               mime="application/json", use_container_width=True)

        grid_html = '<div class="x252">'
        for k, v in rec.items():
            grid_html += f'<div><span class="xc">{k}:</span> {v or ""}</div>'
        grid_html += '</div>'
        st.markdown(grid_html, unsafe_allow_html=True)


# ── Landing state (no row selected, no enrich) ──────────────────
elif not st.session_state.rec:
    st.markdown(textwrap.dedent("""
    <div class="xsection-head">
        <div class="eyebrow">Workspace ready</div>
        <div class="body-mute">Pick a sample or type a row, then hit Enrich</div>
    </div>
    <div class="xmetric-grid">
        <div class="xmetric-cell">
            <div class="eyebrow">Input</div>
            <div class="xmetric-value">1 row</div>
            <div class="xmetric-note">messy distributor data</div>
        </div>
        <div class="xmetric-cell">
            <div class="eyebrow">Output</div>
            <div class="xmetric-value">252</div>
            <div class="xmetric-note">standardised fields</div>
        </div>
        <div class="xmetric-cell">
            <div class="eyebrow">Pipeline</div>
            <div class="xmetric-value">09</div>
            <div class="xmetric-note">auditable stages</div>
        </div>
        <div class="xmetric-cell">
            <div class="eyebrow">Quality gate</div>
            <div class="xmetric-value">100%</div>
            <div class="xmetric-note">rules enforce the spec</div>
        </div>
    </div>
    """), unsafe_allow_html=True)

    st.markdown(textwrap.dedent("""
    <div class="xcard">
        <div class="eyebrow">How it works</div>
        <div class="display-sm" style="margin-bottom:var(--sp-md); color:var(--body)">
            Paste a messy SKU line. Get a complete commerce record back.
        </div>
        <div class="body-md" style="margin-bottom:var(--sp-lg)">
            The engine runs a real 9-stage pipeline: ingest -> deduplicate -> AI classify -> AI extract ->
            enrich -> normalize (UOM/fractions) -> build 5 descriptions -> resolve assets -> validation gate.
            Per-field confidence scores. Explicit review reasons. Deterministic rules gate every AI output.
        </div>
    </div>
    """), unsafe_allow_html=True)

# Pipeline overview - Professional component
    st.markdown(textwrap.dedent("""
    <div class="xcard">
        <div class="eyebrow">9-stage pipeline architecture</div>
        <div class="xpipeline" style="margin-top:var(--sp-lg);">
            <div class="pipe-stage pipe-input">
                <div class="pipe-icon">◈</div>
                <div class="pipe-label">MESSY DISTRIBUTOR ROW</div>
                <div class="pipe-meta">MPN · telegraphic desc · empty brands</div>
            </div>
            <div class="pipe-connector">▼</div>

            <div class="pipe-group pipe-ai">
                <div class="pipe-group-header">
                    <span class="pipe-group-badge">AI PROPOSES</span>
                    <span class="pipe-group-title">Stages 01-05 · LLM reasoning</span>
                </div>
                <div class="pipe-stages">
                    <div class="pipe-step" data-step="01">
                        <div class="pipe-step-num">01</div>
                        <div class="pipe-step-name">Ingest & Clean</div>
                        <div class="pipe-step-desc">Strip placeholders, trim whitespace, normalize encoding</div>
                    </div>
                    <div class="pipe-arrow">→</div>
                    <div class="pipe-step" data-step="02">
                        <div class="pipe-step-num">02</div>
                        <div class="pipe-step-name">De-Duplicate</div>
                        <div class="pipe-step-desc">Collapse repeat SKUs, hash-based dedup, save LLM spend</div>
                    </div>
                    <div class="pipe-arrow">→</div>
                    <div class="pipe-step" data-step="03">
                        <div class="pipe-step-num">03</div>
                        <div class="pipe-step-name">AI Classify</div>
                        <div class="pipe-step-desc">Classpath / Dept / Class / Fine taxonomy via Claude</div>
                    </div>
                    <div class="pipe-arrow">→</div>
                    <div class="pipe-step" data-step="04">
                        <div class="pipe-step-num">04</div>
                        <div class="pipe-step-name">AI Extract</div>
                        <div class="pipe-step-desc">Attribute triples {label, value, UOM} from description</div>
                    </div>
                    <div class="pipe-arrow">→</div>
                    <div class="pipe-step" data-step="05">
                        <div class="pipe-step-num">05</div>
                        <div class="pipe-step-name">Enrich</div>
                        <div class="pipe-step-desc">Brand resolution, MPN-prefix signals, manufacturer lookup</div>
                    </div>
                </div>
            </div>
            <div class="pipe-connector">▼</div>

            <div class="pipe-group pipe-det">
                <div class="pipe-group-header">
                    <span class="pipe-group-badge">DETERMINISTIC ENFORCE</span>
                    <span class="pipe-group-title">Stages 06-09 · Pure rules, auditable</span>
                </div>
                <div class="pipe-stages">
                    <div class="pipe-step" data-step="06">
                        <div class="pipe-step-num">06</div>
                        <div class="pipe-step-name">Normalize</div>
                        <div class="pipe-step-desc">Approved UOM + space; decimals to fractions; case rules</div>
                    </div>
                    <div class="pipe-arrow">→</div>
                    <div class="pipe-step" data-step="07">
                        <div class="pipe-step-num">07</div>
                        <div class="pipe-step-name">Build 5 Descriptions</div>
                        <div class="pipe-step-desc">INVOICE <=40 CAPS · MOBILE 60-80 · SHORT · LONG · MARKETING</div>
                    </div>
                    <div class="pipe-arrow">→</div>
                    <div class="pipe-step" data-step="08">
                        <div class="pipe-step-num">08</div>
                        <div class="pipe-step-name">Resolve Assets</div>
                        <div class="pipe-step-desc">MFR URLs / images; flag unresolved for review queue</div>
                    </div>
                    <div class="pipe-arrow">→</div>
                    <div class="pipe-step" data-step="09">
                        <div class="pipe-step-num">09</div>
                        <div class="pipe-step-name">Validation Gate</div>
                        <div class="pipe-step-desc">Per-field confidence to auto-ship or human review with reasons</div>
                    </div>
                </div>
            </div>
            <div class="pipe-connector">▼</div>

            <div class="pipe-stage pipe-output">
                <div class="pipe-icon">⬡</div>
                <div class="pipe-label">CLEAN COMMERCE RECORD</div>
                <div class="pipe-meta">252 fields · 5 descriptions · normalized attrs · confidence · review queue</div>
            </div>
        </div>
        <div class="pipe-legend" style="margin-top:var(--sp-xl); display:flex; gap:var(--sp-md); flex-wrap:wrap; align-items:center;">
            <span class="xpill" style="border-color:rgba(160,195,236,0.4); color:var(--accent-breeze); background:rgba(160,195,236,0.08);">
                <span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:var(--accent-breeze);margin-right:6px;"></span>01-05 AI proposes
            </span>
            <span class="xpill" style="border-color:rgba(55,211,155,0.4); color:var(--good); background:rgba(55,211,155,0.08);">
                <span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:var(--good);margin-right:6px;"></span>06-09 Deterministic rules enforce
            </span>
            <span class="xpill" style="border-color:rgba(255,180,84,0.4); color:var(--warn); background:rgba(255,180,84,0.08);">
                <span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:var(--warn);margin-right:6px;"></span>Human review gate
            </span>
        </div>
    </div>
    """), unsafe_allow_html=True)

    # Principle
    st.markdown(textwrap.dedent("""
    <div class="xcard">
        <div class="eyebrow">Principle</div>
        <div class="display-sm" style="color:var(--body)">
            "AI reasons, deterministic rules enforce the spec - so no invented value ever ships."
        </div>
    </div>
    """), unsafe_allow_html=True)