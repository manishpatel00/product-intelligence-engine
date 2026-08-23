"""
AI enrichment stage (the reasoning core)
========================================
Turns a cleaned raw row into a structured, spec-aware draft record using Claude
under a forced JSON schema. The system prompt encodes the Unilog written
standard (unit style, decimal->fraction, per-field character limits, the 5
description formulas, controlled-vocabulary discipline) and — critically — an
anti-hallucination rule: only emit a value you can support from the input or
well-known product facts; otherwise leave it blank, lower its confidence, and
add a review reason. "A fluent description of invented values scores zero."

If no API key is present, ``enrich_row`` transparently falls back to a
deterministic pass with the SAME output contract (marked ai_used=False), so the
pipeline always produces output and can be A/B compared field-by-field.
"""

from __future__ import annotations
import re

from . import llm_client
from .lookups import (parse_manufacturer, clean_placeholder, BRAND_MASTER,
                      MPN_PREFIX_BRAND, DISTRIBUTOR_SIGNAL_WORDS)
from .normalize import standardize_units_in_text

# ---------------------------------------------------------------------------
# structured-output schema handed to Claude (forced tool call)
# ---------------------------------------------------------------------------
DRAFT_SCHEMA = {
    "type": "object",
    "properties": {
        "product_type": {"type": "string", "description": "Core item type, e.g. 'Dishwasher', 'Sanding Belt'."},
        "classpath": {"type": "string", "description": "Taxonomy path 'A>B>C' (no spaces around >)."},
        "dept": {"type": "string"},
        "klass": {"type": "string", "description": "The 'Class' level of the taxonomy."},
        "fine": {"type": "string"},
        "brand_name": {"type": "string", "description": "Canonical brand incl. ®/™ if applicable."},
        "manufacturer_name": {"type": "string"},
        "trade_name": {"type": "string"},
        "series": {"type": "string"},
        "unspsc": {"type": "string", "description": "8-digit UNSPSC if confidently known, else ''."},
        "country_of_origin": {"type": "string"},
        "attributes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "label": {"type": "string"},
                    "value": {"type": "string"},
                    "uom": {"type": "string", "description": "Approved UOM abbrev or '' for counts/none."},
                },
                "required": ["label", "value"],
            },
        },
        "item_features": {"type": "array", "items": {"type": "string"}},
        "mobile_desc": {"type": "string", "description": "60-80 chars."},
        "invoice_desc": {"type": "string", "description": "<=40 chars, ALL CAPS."},
        "short_desc": {"type": "string", "description": "Product title = Brand + Series + MPN + Item Type + key attrs."},
        "long_desc": {"type": "string", "description": "Full formula description with dimensions."},
        "retail_desc": {"type": "string"},
        "marketing_description": {"type": "string"},
        "with_note": {"type": "string", "description": "The 'With' feature note, e.g. 'With CleanBoost™'."},
        "standards_approvals": {"type": "string", "description": "Pipe-separated, e.g. 'UL Listed|ENERGY STAR Certified'."},
        "application": {"type": "string"},
        "includes": {"type": "string"},
        "mfr_url": {"type": "string", "description": "Manufacturer's OWN product/support page only (no marketplaces)."},
        "confidence": {
            "type": "object",
            "description": "0..1 confidence keyed by field name (classpath, brand_name, manufacturer_name, attributes, descriptions).",
            "additionalProperties": {"type": "number"},
        },
        "review_reasons": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["product_type", "classpath", "brand_name", "attributes",
                 "short_desc", "long_desc", "confidence"],
}

SYSTEM_PROMPT = """You are Unilog's product-content enrichment engine for industrial distributors.
You convert one cryptic catalogue row into a STANDARDISED, search-ready product record.

NON-NEGOTIABLE RULES (a fluent description made of invented values scores ZERO):
1. ANTI-HALLUCINATION: Emit a value ONLY if it is stated/abbreviated in the input,
   or is a well-established fact about this exact manufacturer part number. If you
   are not sure, leave the field EMPTY, set its confidence < 0.5, and add a
   review_reason. Never invent dimensions, cycles, voltages, materials, UNSPSC,
   or country of origin.
2. UNITS: Use the approved abbreviation with EXACTLY ONE SPACE between number and
   unit: "24 in", "120 V", "15 A", "47 dBA", "50 lb". Never "24in" or "24IN".
   Approved forms include: in, ft, mm, cm, lb, oz, V, A, W, HP, PSI, GPM, dBA,
   Hz, RPM, gal, qt, kW-hr, deg F. Counts use pc/pk/box/case/ea/set/disc/belt.
3. FRACTIONS: Industrial buyers search fractions, not decimals. Convert inch
   decimals to reduced fractions: 0.5 -> "1/2", 0.25 -> "1/4",
   50.25 -> "50-1/4" (whole-<hyphen>-fraction). Keep the unit: "50-1/4 in".
4. DESCRIPTION FORMULAS (the same product, rewritten at five lengths/casings):
   - invoice_desc: <=40 characters, ALL CAPS, densest abbreviations (for a till receipt).
   - mobile_desc : 60-80 characters (Manufacturer/Brand, Item Type, Series, MPN).
   - short_desc  : the Product Title = Brand + Series + MPN + Item Type + a few key attributes.
   - long_desc   : Brand + Item Type + key feature + Series + electricals + mounting +
                   dimensions as "W x D" + special depths + sound level + material,
                   comma-separated, all units in approved form.
   - marketing_description: 1-3 fluent sentences, benefit-oriented, no invented specs.
5. BRAND/MANUFACTURER: Use exact legal casing and ® / ™ symbols when they are part
   of the canonical name (e.g. FRIGIDAIRE®, Whirlpool®, KitchenAid®). If the
   provided Part_Manuf looks like a DISTRIBUTOR/reseller/co-op (not the maker),
   do NOT use it as manufacturer_name — resolve the real manufacturer from the
   brand/MPN, and add a review_reason noting the distributor and any mismatch.
6. ATTRIBUTES: Return a clean list of {label, value, uom}. Labels are Title Case
   nouns (Series, Number of Wash Cycles, Voltage Rating, Amperage Rating,
   Mounting Type, Sound Level, Size, Material, Color, Grit, Length, Width, etc.).
   Put the number in value and the unit in uom (uom empty for counts/none).
7. CONFIDENCE: Provide a 0..1 confidence for classpath, brand_name,
   manufacturer_name, attributes and descriptions. Be honest and calibrated.

Return ONLY via the emit tool. Do not add commentary."""


def _mpn_hint(mpn: str):
    up = (mpn or "").upper()
    for prefix, (brand, series) in MPN_PREFIX_BRAND.items():
        if up.startswith(prefix):
            return brand, series
    return "", ""


def _build_user_prompt(row, manuf_name, manuf_code, is_distributor, brand_hint, series_hint):
    lines = [
        "RAW CATALOGUE ROW",
        f"- Mfg_Part_Num (MPN): {row.get('Mfg_Part_Num','')}",
        f"- Part_Desc: {row.get('Part_Desc','')}",
        f"- E1_Brand: {clean_placeholder(row.get('E1_Brand','')) or '(empty)'}",
        f"- Unilog_Brand: {clean_placeholder(row.get('Unilog_Brand','')) or '(empty)'}",
        f"- DIB_Brand: {clean_placeholder(row.get('DIB_Brand','')) or '(empty)'}",
        f"- Part_Manuf: {row.get('Part_Manuf','')}",
        "",
        "DERIVED HINTS (use only if consistent with the row; verify, don't trust blindly)",
        f"- Parsed manufacturer name: {manuf_name or '(none)'}  code: {manuf_code or '(none)'}",
        f"- Part_Manuf looks like a distributor/reseller: {'YES — do not use as manufacturer' if is_distributor else 'no'}",
    ]
    if brand_hint:
        lines.append(f"- MPN-prefix suggests brand: {brand_hint}"
                     + (f", series: {series_hint}" if series_hint else ""))
    lines += [
        "",
        "TASK: Produce the standardised record via the emit tool, following every rule. "
        "Extract only supported attributes; leave unknowns blank with a low confidence "
        "and a review reason.",
    ]
    return "\n".join(lines)


def enrich_row(row: dict, model: str = None) -> dict:
    """Return the structured draft dict + meta flags. Uses Claude when a key is
    present; deterministic fallback otherwise. Never raises for a single row."""
    mpn = (row.get("Mfg_Part_Num") or "").strip()
    manuf_name, manuf_code, is_distributor = parse_manufacturer(row.get("Part_Manuf", ""))
    brand_hint, series_hint = _mpn_hint(mpn)

    if llm_client.have_api_key():
        try:
            system = SYSTEM_PROMPT
            user = _build_user_prompt(row, manuf_name, manuf_code, is_distributor,
                                      brand_hint, series_hint)
            draft = llm_client.call_structured(
                system=system, user=user, tool_name="emit_product_record",
                input_schema=DRAFT_SCHEMA, model=model, max_tokens=2600, temperature=0.0)
            draft["_ai_used"] = True
            draft["_is_distributor"] = is_distributor
            draft["_manuf_parsed"] = manuf_name
            draft["_manuf_code"] = manuf_code
            return draft
        except llm_client.LLMUnavailable:
            pass
        except Exception as e:  # any API failure -> graceful deterministic fallback
            d = _deterministic_draft(row, mpn, manuf_name, manuf_code, is_distributor,
                                     brand_hint, series_hint)
            d.setdefault("review_reasons", []).append(f"AI call failed, used rule-based fallback: {e}")
            return d

    return _deterministic_draft(row, mpn, manuf_name, manuf_code, is_distributor,
                                brand_hint, series_hint)


# ---------------------------------------------------------------------------
# deterministic fallback  (same contract, lower confidence, ai_used=False)
# ---------------------------------------------------------------------------
_PRODUCT_TYPE_KW = [
    ("dishwasher", "Dishwasher", "Appliances>Kitchen Appliances>Built-In Dishwashers"),
    ("sanding belt", "Sanding Belt", "Abrasives & Grinding>Coated Abrasives>Sanding Belts"),
    ("stikit", "Sanding Disc", "Abrasives & Grinding>Coated Abrasives>Sanding Discs"),
    ("disc", "Sanding Disc", "Abrasives & Grinding>Coated Abrasives>Sanding Discs"),
    ("drill bit", "Drill Bit", "Power Tool Accessories>Drilling>Drill Bits"),
    ("saw blade", "Saw Blade", "Power Tool Accessories>Cutting>Saw Blades"),
    ("coupling", "Coupling", "Plumbing & HVAC>Pipe Fittings>Couplings"),
    ("elbow", "Elbow", "Plumbing & HVAC>Pipe Fittings>Elbows"),
    ("faucet", "Faucet", "Kitchen & Bath>Faucets>Sink Faucets"),
    ("glove", "Glove", "Safety>PPE>Gloves"),
    ("bolt", "Bolt", "Fasteners>Bolts>General"),
]
_DIM_RE = re.compile(
    r"(\d+(?:-\d+/\d+|/\d+|\.\d+)?)\s*(in|inch|inches|\"|ft|mm|cm|v|volt|volts|a|amp|amps|"
    r"w|watt|watts|hp|psi|gpm|lb|lbs|oz|dba|rpm|grit)\b", re.IGNORECASE)


def _deterministic_draft(row, mpn, manuf_name, manuf_code, is_distributor,
                         brand_hint, series_hint):
    from .normalize import standardize_measure
    from .lookups import normalize_uom

    raw_desc = (row.get("Part_Desc") or "").strip()
    body = raw_desc
    if mpn and body.upper().startswith(mpn.upper()):
        body = body[len(mpn):].strip(" -")

    low = raw_desc.lower()
    product_type, classpath = "", "Uncategorized>Needs Review>Needs Review"
    for kw, pt, cp in _PRODUCT_TYPE_KW:
        if kw in low:
            product_type, classpath = pt, cp
            break

    # brand: description token -> known master; else MPN hint; else blank
    brand = ""
    first = body.split(" ")[0].lower().strip(".,-") if body else ""
    if first in BRAND_MASTER:
        brand = BRAND_MASTER[first][0]
    elif brand_hint:
        brand = brand_hint

    attrs = []
    for val, unit in _DIM_RE.findall(raw_desc):
        approved = normalize_uom(unit)
        if approved:
            v, u = standardize_measure(val, unit)
            attrs.append({"label": "Dimension", "value": v, "uom": u})

    manufacturer_name = "" if is_distributor else manuf_name
    parts = [p for p in [brand, series_hint, mpn, product_type] if p]
    short = " ".join(parts) if parts else raw_desc

    reasons = []
    if is_distributor:
        reasons.append(f"Part_Manuf '{manuf_name}' looks like a distributor, not a manufacturer — withheld and flagged.")
    if not product_type:
        reasons.append("Product type/classpath unresolved by rules — needs AI classification or review.")
    if not brand:
        reasons.append("Brand unresolved from input — needs manufacturer-source enrichment.")

    return {
        "product_type": product_type,
        "classpath": classpath,
        "dept": "", "klass": "", "fine": "",
        "brand_name": brand,
        "manufacturer_name": manufacturer_name,
        "trade_name": brand,
        "series": series_hint,
        "unspsc": "", "country_of_origin": "",
        "attributes": attrs,
        "item_features": [],
        "mobile_desc": ", ".join([p for p in [manufacturer_name or brand, product_type, series_hint, mpn] if p]),
        "invoice_desc": (product_type + " " + " ".join(a["value"] + a["uom"] for a in attrs[:3])).upper()[:40].strip(),
        "short_desc": short,
        "long_desc": ", ".join([p for p in [f"{brand} {product_type}".strip(), series_hint] + [f"{a['value']} {a['uom']}".strip() for a in attrs] if p]),
        "retail_desc": short,
        "marketing_description": "",
        "with_note": "", "standards_approvals": "", "application": "", "includes": "",
        "mfr_url": "",
        "confidence": {
            "classpath": 0.7 if product_type else 0.1,
            "brand_name": 0.85 if first in BRAND_MASTER else (0.6 if brand_hint else 0.0),
            "manufacturer_name": 0.0 if is_distributor else (0.5 if manuf_name else 0.0),
            "attributes": 0.6 if attrs else 0.2,
            "descriptions": 0.4 if product_type else 0.15,
        },
        "review_reasons": reasons,
        "_ai_used": False,
        "_is_distributor": is_distributor,
        "_manuf_parsed": manuf_name,
        "_manuf_code": manuf_code,
    }
