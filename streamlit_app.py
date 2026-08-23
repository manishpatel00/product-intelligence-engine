#!/usr/bin/env python3
"""
Unilog Product Intelligence Engine — Streamlit Cloud demo
==========================================================
Drop-in Streamlit frontend for the same 9-stage enrichment pipeline.
Deploy: share.streamlit.io → repo: manishpatel00/product-intelligence-engine
         branch: main → Main file path: streamlit_app.py
"""
import csv
import json
import os
import sys

import streamlit as st

# Ensure src/ is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.pipeline import process_row
from src import llm_client

# ---------------------------------------------------------------------------
# Page config & theme
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Unilog Product Intelligence Engine",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for premium dark look
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Hide Streamlit branding */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

.stApp {
    background: linear-gradient(135deg, #0b0f17 0%, #111826 50%, #0d1220 100%);
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #141b28;
    border-right: 1px solid #26324a;
}

section[data-testid="stSidebar"] .stSelectbox label,
section[data-testid="stSidebar"] .stTextInput label,
section[data-testid="stSidebar"] .stTextArea label {
    color: #8ea0bd !important;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* Metric cards */
div[data-testid="stMetric"] {
    background: #141b28;
    border: 1px solid #26324a;
    border-radius: 12px;
    padding: 16px;
}

/* Custom card style */
.card {
    background: #141b28;
    border: 1px solid #26324a;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 16px;
}

.card-title {
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    color: #8ea0bd;
    margin-bottom: 12px;
    font-weight: 600;
}

/* Description blocks */
.desc-block {
    border-left: 3px solid #4da3ff;
    padding: 10px 14px;
    margin: 8px 0;
    background: #1b2434;
    border-radius: 0 8px 8px 0;
}

.desc-label {
    font-size: 11px;
    color: #8ea0bd;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 4px;
}

.desc-value {
    font-size: 14px;
    color: #e7edf7;
}

.desc-meta {
    font-size: 11px;
    color: #8ea0bd;
    margin-top: 4px;
}

/* Flag / review reason */
.flag {
    background: #2a1414;
    border: 1px solid #5c2626;
    color: #ffc2c2;
    border-radius: 8px;
    padding: 10px 14px;
    margin: 6px 0;
    font-size: 13px;
}

.ok-badge {
    color: #37d39b;
    font-weight: 600;
}

/* Confidence gauge */
.gauge-bg {
    height: 10px;
    border-radius: 6px;
    background: #26324a;
    overflow: hidden;
    margin-top: 4px;
}

.gauge-fill {
    height: 100%;
    border-radius: 6px;
}

/* Pill / badge */
.pill {
    display: inline-block;
    font-size: 11px;
    padding: 2px 8px;
    border-radius: 999px;
    background: #12324a;
    color: #8fd0ff;
}

.badge-on {
    font-size: 12px;
    padding: 4px 12px;
    border-radius: 999px;
    border: 1px solid #1f5c48;
    background: #0f2a22;
    color: #37d39b;
}

.badge-off {
    font-size: 12px;
    padding: 4px 12px;
    border-radius: 999px;
    border: 1px solid #5c4a1f;
    background: #2a220f;
    color: #ffb454;
}

/* KV grid */
.kv-grid {
    display: grid;
    grid-template-columns: 160px 1fr;
    gap: 6px 14px;
}

.kv-key {
    color: #8ea0bd;
    font-size: 13px;
}

.kv-val {
    color: #e7edf7;
    font-size: 13px;
}

/* Header */
.engine-header {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 6px 0 18px 0;
    border-bottom: 1px solid #26324a;
    margin-bottom: 24px;
}

.engine-title {
    font-size: 22px;
    font-weight: 700;
    color: #e7edf7;
    letter-spacing: 0.2px;
}

.engine-subtitle {
    color: #8ea0bd;
    font-size: 12px;
    margin-left: auto;
}

/* Table styling */
.attr-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 13px;
}

.attr-table th {
    text-align: left;
    padding: 8px;
    border-bottom: 1px solid #26324a;
    color: #8ea0bd;
    font-weight: 500;
    font-size: 11px;
    text-transform: uppercase;
}

.attr-table td {
    text-align: left;
    padding: 8px;
    border-bottom: 1px solid #1b2434;
    color: #e7edf7;
}

/* Streamlit overrides */
.stButton > button {
    background: linear-gradient(135deg, #4da3ff, #357abd) !important;
    color: #04121f !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    font-size: 15px !important;
    padding: 12px 24px !important;
    width: 100% !important;
}

.stButton > button:hover {
    background: linear-gradient(135deg, #6bb5ff, #4da3ff) !important;
}

div[data-testid="stExpander"] {
    background: #141b28;
    border: 1px solid #26324a;
    border-radius: 12px;
}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Load preset sample rows
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
# Helper renderers
# ---------------------------------------------------------------------------
def gauge_color(v):
    if v >= 0.75:
        return "#37d39b"
    elif v >= 0.5:
        return "#ffb454"
    return "#ff6b6b"


def render_desc(label, value, meta=None):
    val_display = value if value else '<span style="color:#8ea0bd">(empty)</span>'
    meta_html = f'<div class="desc-meta">{meta}</div>' if meta else ""
    return f"""
    <div class="desc-block">
        <div class="desc-label">{label}</div>
        <div class="desc-value">{val_display}</div>
        {meta_html}
    </div>
    """


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
ai_on = llm_client.have_api_key()
badge_class = "badge-on" if ai_on else "badge-off"
badge_text = ("● Claude AI: " + llm_client.DEFAULT_MODEL) if ai_on else "● Deterministic fallback"

st.markdown(f"""
<div class="engine-header">
    <span style="font-size:28px">⚙️</span>
    <span class="engine-title">Unilog Product Intelligence Engine</span>
    <span class="{badge_class}">{badge_text}</span>
    <span class="engine-subtitle">messy row → 252-column commerce record · confidence-scored · human-in-the-loop</span>
</div>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Sidebar — input form
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 📋 Input Row")

    preset_options = ["— choose —"] + [
        f"{(p.get('Mfg_Part_Num') or 'row')[:18]} — {(p.get('Part_Desc') or '')[:34]}"
        for p in PRESETS
    ]
    preset_idx = st.selectbox("Load a sample row", options=range(len(preset_options)),
                              format_func=lambda i: preset_options[i], key="preset")

    # Pre-fill from preset
    default_mpn = ""
    default_desc = ""
    default_manuf = ""
    default_brands = ""
    if preset_idx and preset_idx > 0:
        p = PRESETS[preset_idx - 1]
        default_mpn = p.get("Mfg_Part_Num", "")
        default_desc = p.get("Part_Desc", "")
        default_manuf = p.get("Part_Manuf", "")
        default_brands = " | ".join(filter(None, [
            p.get("E1_Brand", ""), p.get("Unilog_Brand", ""), p.get("DIB_Brand", "")
        ]))

    mpn = st.text_input("Mfg_Part_Num (MPN)", value=default_mpn, placeholder="e.g. PDSH4816AF")
    desc = st.text_area("Part_Desc (cryptic description)", value=default_desc,
                        placeholder="e.g. PDSH4816AF Dishwasher SS - Display Only")
    manuf = st.text_input("Part_Manuf", value=default_manuf,
                          placeholder="e.g. Appliance Dealers Cooperative (APPDE)")
    brands = st.text_input("E1_Brand / Unilog_Brand / DIB_Brand", value=default_brands,
                           placeholder="often -- Unbranded -- (auto-filtered)")

    enrich_btn = st.button("⚡ Enrich →", use_container_width=True)

    st.markdown("""
    <div style="font-size:12px; color:#8ea0bd; margin-top:12px; line-height:1.6">
        Runs the real 9-stage pipeline. With an API key set, Claude classifies &amp; extracts;
        a deterministic gate then enforces UOM/fraction/char-limit rules and flags
        low-confidence fields.
    </div>
    """, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Main content — enrich and display
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

    with st.spinner("Running 9-stage enrichment pipeline…"):
        rec, qa = process_row(row)

    # --- Identity & Taxonomy ---
    st.markdown('<div class="card"><div class="card-title">Identity & Taxonomy</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div class="kv-grid">
            <div class="kv-key">Brand</div><div class="kv-val"><b>{rec.get('BRAND_NAME') or '—'}</b></div>
            <div class="kv-key">Manufacturer</div><div class="kv-val">{rec.get('MANUFACTURER_NAME') or '<span style="color:#8ea0bd">(withheld/flagged)</span>'}</div>
            <div class="kv-key">MPN</div><div class="kv-val">{rec.get('MANUFACTURER_PART_NUMBER') or '—'}</div>
            <div class="kv-key">Product</div><div class="kv-val">{rec.get('Product Name') or '—'}</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="kv-grid">
            <div class="kv-key">Classpath</div><div class="kv-val">{rec.get('Classpath') or '—'}</div>
            <div class="kv-key">Dept / Class / Fine</div><div class="kv-val">{' › '.join(filter(None, [rec.get('Dept'), rec.get('Class'), rec.get('Fine')])) or '—'}</div>
            <div class="kv-key">MFR URL</div><div class="kv-val">{rec.get('MFR URL') or '—'}</div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # --- Five Descriptions ---
    st.markdown('<div class="card"><div class="card-title">The Same Product, Five Formats</div>', unsafe_allow_html=True)
    inv = rec.get("INVOICE_DESC", "")
    mob = rec.get("MOBILE_DESC", "")
    html_descs = ""
    html_descs += render_desc("Invoice Desc (≤40, CAPS)", inv, f"len {len(inv)}/40" if inv else None)
    html_descs += render_desc("Mobile Desc (60–80)", mob, f"len {len(mob)}" if mob else None)
    html_descs += render_desc("Short Desc / Product Title", rec.get("SHORT_DESC", ""))
    html_descs += render_desc("Long Description", rec.get("LONG_DESC1", ""))
    html_descs += render_desc("Marketing Description", rec.get("MARKETING_DESCRIPTION", ""))
    st.markdown(html_descs, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # --- Attributes ---
    st.markdown('<div class="card"><div class="card-title">Attributes (Normalised · Approved UOM)</div>', unsafe_allow_html=True)
    attr_rows = []
    for i in range(1, 51):
        label = rec.get(f"ATTRIBUTE_LABEL {i}", "")
        if not label:
            continue
        value = rec.get(f"ATTRIBUTE_VALUE {i}", "")
        uom = rec.get(f"ATTRIBUTE_UOM {i}", "")
        attr_rows.append((label, value, uom))

    if attr_rows:
        table_html = '<table class="attr-table"><tr><th>Label</th><th>Value</th><th>UOM</th></tr>'
        for label, value, uom in attr_rows:
            uom_pill = f'<span class="pill">{uom}</span>' if uom else '<span style="color:#8ea0bd">—</span>'
            table_html += f'<tr><td>{label}</td><td><b>{value}</b></td><td>{uom_pill}</td></tr>'
        table_html += '</table>'
        st.markdown(table_html, unsafe_allow_html=True)
    else:
        st.markdown('<span style="color:#8ea0bd">No attributes extracted</span>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # --- Confidence & Review Queue ---
    st.markdown('<div class="card"><div class="card-title">Confidence & Review Queue</div>', unsafe_allow_html=True)

    overall = qa.get("overall_confidence", 0)
    needs_review = qa.get("needs_human_review", False)
    overall_color = gauge_color(overall)

    review_label = '⚑ Routed to human review' if needs_review else '✓ Auto-shippable'
    review_color = '#ffb454' if needs_review else '#37d39b'
    engine_label = 'Claude AI + rule gate' if qa.get("ai_used") else 'deterministic fallback'

    st.markdown(f"""
    <div style="display:flex; gap:20px; align-items:center; margin-bottom:16px">
        <div style="font-size:38px; font-weight:800; color:{overall_color}">{overall}</div>
        <div>
            <div style="color:{review_color}; font-weight:600">{review_label}</div>
            <div style="font-size:12px; color:#8ea0bd">engine: {engine_label} · {qa.get('n_attributes', 0)} attributes</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Field confidence bars
    for field, conf in qa.get("field_confidence", {}).items():
        color = gauge_color(conf)
        pct = int(conf * 100)
        st.markdown(f"""
        <div style="margin:8px 0">
            <div style="display:flex; justify-content:space-between; font-size:12px">
                <span style="color:#8ea0bd">{field}</span>
                <span style="color:#e7edf7">{conf}</span>
            </div>
            <div class="gauge-bg"><div class="gauge-fill" style="width:{pct}%; background:{color}"></div></div>
        </div>
        """, unsafe_allow_html=True)

    # Review reasons
    reasons = qa.get("review_reasons", [])
    if reasons:
        for reason in reasons:
            st.markdown(f'<div class="flag">⚑ {reason}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="ok-badge">✓ No blocking issues — auto-shippable.</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # --- Full 252-column record ---
    filled = sum(1 for v in rec.values() if v)
    with st.expander(f"📄 Full 252-column record · {filled} populated"):
        # Download buttons
        col_csv, col_json = st.columns(2)
        with col_csv:
            csv_data = ",".join(rec.keys()) + "\n" + ",".join(
                f'"{str(v).replace(chr(34), chr(34)+chr(34))}"' if v else '""' for v in rec.values()
            ) + "\n"
            st.download_button("⬇ Download CSV", csv_data,
                               file_name=f"{mpn or 'record'}_enriched.csv",
                               mime="text/csv", use_container_width=True)
        with col_json:
            st.download_button("⬇ Download JSON", json.dumps(rec, indent=2),
                               file_name=f"{mpn or 'record'}.json",
                               mime="application/json", use_container_width=True)

        # Show all columns
        grid_html = '<div style="columns:2; font-size:12px; margin-top:12px">'
        for k, v in rec.items():
            grid_html += f'<div style="break-inside:avoid; padding:2px 0; border-bottom:1px solid #1b2434"><span style="color:#8ea0bd">{k}:</span> {v or ""}</div>'
        grid_html += '</div>'
        st.markdown(grid_html, unsafe_allow_html=True)

elif enrich_btn and not desc.strip():
    st.warning("Please enter a Part_Desc to enrich.")

else:
    # Landing state
    st.markdown("""
    <div class="card">
        <div class="card-title">Output</div>
        <div style="color:#8ea0bd; line-height:1.7">
            Pick a sample row from the sidebar or type one, then press <b>⚡ Enrich →</b>.<br>
            You'll see the five description formats, resolved identity, normalised attributes,
            confidence scores and the review queue — all from the real 9-stage pipeline.<br><br>
            <b>Team Codehunt</b> · UniHack 2026 · Unilog Challenge<br>
            <em>"AI reasons, deterministic rules enforce the spec — so no invented value ever ships."</em>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Architecture overview
    st.markdown("""
    <div class="card">
        <div class="card-title">How It Works — 9-Stage Pipeline</div>
        <div style="color:#8ea0bd; font-size:13px; line-height:1.8">
            <b style="color:#4da3ff">① Ingest & Clean</b> → Strip placeholders ("--Unbranded--" → empty)<br>
            <b style="color:#4da3ff">② De-Duplicate</b> → Collapse repeat SKUs (saves LLM spend)<br>
            <b style="color:#4da3ff">③ AI Classify</b> → Classpath / Dept / Class / Fine<br>
            <b style="color:#4da3ff">④ AI Extract Attributes</b> → {label, value, uom} triples<br>
            <b style="color:#4da3ff">⑤ Enrich</b> → Brand / MPN-prefix / manufacturer signals<br>
            <b style="color:#37d39b">⑥ Normalize</b> → Approved UOM + space; decimals → fractions (1/64 table)<br>
            <b style="color:#37d39b">⑦ Build 5 Descriptions</b> → INVOICE (≤40 CAPS), MOBILE, SHORT, LONG, MARKETING<br>
            <b style="color:#37d39b">⑧ Resolve Assets</b> → URLs / images (flagged if unresolved)<br>
            <b style="color:#37d39b">⑨ Validation Gate</b> → Per-field confidence → AUTO-SHIP or REVIEW QUEUE<br>
            <br>
            <span style="color:#4da3ff">■ Blue = AI proposes</span> &nbsp;&nbsp;
            <span style="color:#37d39b">■ Green = Deterministic rules enforce</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
