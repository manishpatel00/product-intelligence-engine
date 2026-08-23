#!/usr/bin/env python3
"""
Unilog Product Intelligence Engine — Streamlit Cloud demo
==========================================================
xAI-inspired design system: near-black canvas, Inter weight 400,
Geist Mono uppercase eyebrows, pill outlines, hairline borders.
"""
import csv
import json
import os
import sys

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
    initial_sidebar_state="expanded",
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
#MainMenu, footer, header,
div[data-testid="stToolbar"],
div[data-testid="stDecoration"],
div[data-testid="stStatusWidget"] {
    display: none !important;
}

.stApp {
    background: var(--canvas) !important;
}

/* Main container */
.stMainBlockContainer,
div[data-testid="stAppViewBlockContainer"] {
    max-width: 1200px;
    padding-top: var(--sp-3xl) !important;
}

/* ═══════════════════════════════════════════════════════════════
   SIDEBAR
   ═══════════════════════════════════════════════════════════════ */
section[data-testid="stSidebar"] {
    background: var(--canvas) !important;
    border-right: 1px solid var(--hairline) !important;
}

section[data-testid="stSidebar"] > div {
    padding-top: var(--sp-3xl) !important;
}

/* Sidebar labels — Geist Mono uppercase */
section[data-testid="stSidebar"] .stSelectbox label,
section[data-testid="stSidebar"] .stTextInput label,
section[data-testid="stSidebar"] .stTextArea label,
section[data-testid="stSidebar"] label {
    font-family: 'JetBrains Mono', 'Geist Mono', monospace !important;
    font-weight: 400 !important;
    font-size: 12px !important;
    text-transform: uppercase !important;
    letter-spacing: 1.4px !important;
    color: var(--body-mid) !important;
}

/* Sidebar inputs */
section[data-testid="stSidebar"] input,
section[data-testid="stSidebar"] textarea,
section[data-testid="stSidebar"] select,
section[data-testid="stSidebar"] div[data-baseweb="select"] {
    background: var(--canvas-soft) !important;
    border: 1px solid var(--hairline) !important;
    border-radius: var(--rounded-sm) !important;
    color: var(--ink) !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 400 !important;
    font-size: 14px !important;
}

section[data-testid="stSidebar"] div[data-baseweb="select"] > div {
    background: var(--canvas-soft) !important;
    border: 1px solid var(--hairline) !important;
    border-radius: var(--rounded-sm) !important;
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
    padding: var(--sp-xs) var(--sp-md) !important;
    letter-spacing: 0 !important;
    transition: border-color 0.2s ease, background 0.2s ease;
}

.stButton > button:hover {
    border-color: rgba(255, 255, 255, 0.5) !important;
    background: rgba(255, 255, 255, 0.04) !important;
    color: var(--ink) !important;
}

/* Primary CTA — the rare filled pill */
.stButton > button[kind="primary"],
section[data-testid="stSidebar"] .stButton > button {
    background: var(--ink) !important;
    color: var(--canvas) !important;
    border: 1px solid var(--ink) !important;
}

section[data-testid="stSidebar"] .stButton > button:hover {
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
    padding: 0 0 var(--sp-3xl) 0;
    border-bottom: 1px solid var(--hairline);
    margin-bottom: var(--sp-2xl);
}

.xhero-sub {
    font-family: 'Inter', sans-serif;
    font-weight: 400;
    font-size: 16px;
    line-height: 24px;
    color: var(--body-mid);
    margin-top: var(--sp-sm);
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
            for r in list(csv.DictReader(f))[:2]:
                presets.append(r)
    except Exception:
        pass
    try:
        with open(samp, newline="", encoding="utf-8") as f:
            for r in list(csv.DictReader(f))[:6]:
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
    val = value if value else '<span style="color:var(--body-mid)">—</span>'
    meta_html = f'<div class="xdesc-meta">{meta}</div>' if meta else ""
    return f"""
    <div class="xdesc">
        <div class="xdesc-label">{label}</div>
        <div class="xdesc-value">{val}</div>
        {meta_html}
    </div>
    """


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
ai_on = llm_client.have_api_key()
pill_class = "xpill xpill-on" if ai_on else "xpill xpill-off"
pill_text = f"Claude AI · {llm_client.DEFAULT_MODEL}" if ai_on else "Deterministic fallback"

st.markdown(f"""
<div class="xhero">
    <div class="eyebrow">Unilog Product Intelligence Engine</div>
    <div class="display-xl">messy row → 252 columns</div>
    <div class="xhero-sub">
        Turn one cryptic distributor row into a complete, standardised, search-ready commerce record.
        AI reasons — deterministic rules enforce the spec.
    </div>
    <div style="margin-top: var(--sp-lg)">
        <span class="{pill_class}">{pill_text}</span>
        <span class="xpill" style="margin-left:8px">Team Codehunt</span>
        <span class="xpill" style="margin-left:8px">UniHack 2026</span>
    </div>
</div>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown('<div class="eyebrow" style="margin-bottom:var(--sp-xl)">Input row</div>', unsafe_allow_html=True)

    preset_options = ["— choose —"] + [
        f"{(p.get('Mfg_Part_Num') or 'row')[:18]} — {(p.get('Part_Desc') or '')[:34]}"
        for p in PRESETS
    ]
    preset_idx = st.selectbox("Sample row", options=range(len(preset_options)),
                              format_func=lambda i: preset_options[i], key="preset")

    default_mpn = default_desc = default_manuf = default_brands = ""
    if preset_idx and preset_idx > 0:
        p = PRESETS[preset_idx - 1]
        default_mpn = p.get("Mfg_Part_Num", "")
        default_desc = p.get("Part_Desc", "")
        default_manuf = p.get("Part_Manuf", "")
        default_brands = " | ".join(filter(None, [
            p.get("E1_Brand", ""), p.get("Unilog_Brand", ""), p.get("DIB_Brand", "")
        ]))

    mpn = st.text_input("MPN", value=default_mpn, placeholder="e.g. PDSH4816AF")
    desc = st.text_area("Part description", value=default_desc,
                        placeholder="e.g. PDSH4816AF Dishwasher SS - Display Only", height=80)
    manuf = st.text_input("Manufacturer", value=default_manuf,
                          placeholder="e.g. Appliance Dealers Cooperative")
    brands = st.text_input("Brand fields", value=default_brands,
                           placeholder="often -- Unbranded --")

    enrich_btn = st.button("Enrich →", use_container_width=True)

    st.markdown("""
    <hr class="divider">
    <div class="body-mute" style="font-size:12px; line-height:1.7">
        Runs the real 9-stage pipeline. Claude classifies &amp; extracts;
        a deterministic gate enforces UOM / fraction / char-limit rules.
        No API key → deterministic fallback, same contract.
    </div>
    """, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if enrich_btn and desc.strip():
    brand_parts = [b.strip() for b in (brands or "").split("|")]
    row = {
        "Mfg_Part_Num": mpn,
        "Part_Desc": desc,
        "Part_Manuf": manuf,
        "E1_Brand": brand_parts[0] if len(brand_parts) > 0 else "",
        "Unilog_Brand": brand_parts[1] if len(brand_parts) > 1 else "",
        "DIB_Brand": brand_parts[2] if len(brand_parts) > 2 else "",
    }

    with st.spinner("Running 9-stage pipeline…"):
        rec, qa = process_row(row)

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
            <div class="xkv-val">{rec.get('BRAND_NAME') or '—'}</div>
            <div class="xkv-key">Manufacturer</div>
            <div class="xkv-val">{rec.get('MANUFACTURER_NAME') or '<span style="color:var(--body-mid)">withheld / flagged</span>'}</div>
            <div class="xkv-key">MPN</div>
            <div class="xkv-val">{rec.get('MANUFACTURER_PART_NUMBER') or '—'}</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="xkv">
            <div class="xkv-key">Classpath</div>
            <div class="xkv-val">{rec.get('Classpath') or '—'}</div>
            <div class="xkv-key">Dept / Class</div>
            <div class="xkv-val">{' › '.join(filter(None, [rec.get('Dept'), rec.get('Class'), rec.get('Fine')])) or '—'}</div>
            <div class="xkv-key">Product</div>
            <div class="xkv-val">{rec.get('Product Name') or '—'}</div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Descriptions ────────────────────────────────────────
    inv = rec.get("INVOICE_DESC", "")
    mob = rec.get("MOBILE_DESC", "")
    st.markdown(f"""
    <div class="xcard">
        <div class="eyebrow">The same product, five formats</div>
        {render_desc("Invoice desc · ≤40 caps", inv, f"{len(inv)}/40 chars" if inv else None)}
        {render_desc("Mobile desc · 60–80", mob, f"{len(mob)} chars" if mob else None)}
        {render_desc("Short desc", rec.get("SHORT_DESC", ""))}
        {render_desc("Long description", rec.get("LONG_DESC1", ""))}
        {render_desc("Marketing", rec.get("MARKETING_DESCRIPTION", ""))}
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
            uom_html = f'<span class="xpill">{uom}</span>' if uom else '<span style="color:var(--body-mid)">—</span>'
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
    engine_label = "Claude AI + rule gate" if qa.get("ai_used") else "deterministic fallback"

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
        flags_html = '<div class="xok" style="margin-top:var(--sp-md)">✓ No blocking issues — auto-shippable.</div>'

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
                               file_name=f"{mpn or 'record'}_enriched.csv",
                               mime="text/csv", use_container_width=True)
        with col_json:
            st.download_button("⬇ JSON", json.dumps(rec, indent=2),
                               file_name=f"{mpn or 'record'}.json",
                               mime="application/json", use_container_width=True)

        grid_html = '<div class="x252">'
        for k, v in rec.items():
            grid_html += f'<div><span class="xc">{k}:</span> {v or ""}</div>'
        grid_html += '</div>'
        st.markdown(grid_html, unsafe_allow_html=True)

elif enrich_btn and not desc.strip():
    st.warning("Enter a Part_Desc to enrich.")

else:
    # ── Landing ─────────────────────────────────────────────
    st.markdown("""
    <div class="xcard">
        <div class="eyebrow">Ready</div>
        <div class="display-sm" style="margin-bottom:var(--sp-md)">
            Pick a sample row or type one, then press Enrich →
        </div>
        <div class="body-md">
            You'll see the five description formats, resolved identity, normalised attributes,
            per-field confidence scores, and the review queue with specific reasons — all from the
            real 9-stage pipeline running live.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Pipeline overview
    st.markdown("""
    <div class="xcard">
        <div class="eyebrow">9-stage pipeline</div>
        <div style="margin-top:var(--sp-md)">
            <div class="xstep">
                <span class="xstep-num xstep-ai">01</span>
                <span class="xstep-text"><span>Ingest & Clean</span> — strip placeholders, trim whitespace</span>
            </div>
            <div class="xstep">
                <span class="xstep-num xstep-ai">02</span>
                <span class="xstep-text"><span>De-Duplicate</span> — collapse repeat SKUs, save LLM spend</span>
            </div>
            <div class="xstep">
                <span class="xstep-num xstep-ai">03</span>
                <span class="xstep-text"><span>AI Classify</span> — Classpath / Dept / Class / Fine taxonomy</span>
            </div>
            <div class="xstep">
                <span class="xstep-num xstep-ai">04</span>
                <span class="xstep-text"><span>AI Extract</span> — attribute triples {label, value, uom}</span>
            </div>
            <div class="xstep">
                <span class="xstep-num xstep-ai">05</span>
                <span class="xstep-text"><span>Enrich</span> — brand / MPN-prefix / manufacturer signals</span>
            </div>
            <hr class="divider" style="margin:var(--sp-sm) 0; margin-left:32px">
            <div class="xstep">
                <span class="xstep-num xstep-det">06</span>
                <span class="xstep-text"><span>Normalize</span> — approved UOM + space; decimals → fractions</span>
            </div>
            <div class="xstep">
                <span class="xstep-num xstep-det">07</span>
                <span class="xstep-text"><span>Build 5 Descriptions</span> — INVOICE ≤40 CAPS, MOBILE, SHORT, LONG, MARKETING</span>
            </div>
            <div class="xstep">
                <span class="xstep-num xstep-det">08</span>
                <span class="xstep-text"><span>Resolve Assets</span> — URLs / images, flagged if unresolved</span>
            </div>
            <div class="xstep">
                <span class="xstep-num xstep-det">09</span>
                <span class="xstep-text"><span>Validation Gate</span> — per-field confidence → auto-ship or review queue</span>
            </div>
        </div>
        <div style="margin-top:var(--sp-xl)">
            <span class="xpill" style="border-color:rgba(160,195,236,0.3); color:var(--accent-breeze)">01–05 AI proposes</span>
            <span class="xpill" style="margin-left:8px; border-color:rgba(55,211,155,0.3); color:var(--good)">06–09 Deterministic rules enforce</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Principle
    st.markdown("""
    <div class="xcard">
        <div class="eyebrow">Principle</div>
        <div class="display-sm" style="color:var(--body)">
            "AI reasons, deterministic rules enforce the spec — so no invented value ever ships."
        </div>
    </div>
    """, unsafe_allow_html=True)
