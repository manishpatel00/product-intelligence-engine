"""
Pipeline orchestrator
=====================
Runs the 9 auditable stages the Solution Guide describes and assembles the
exact 252-column Unilog Delivery Format record:

  1 ingest & clean placeholders   2 de-duplicate   3 AI classify
  4 AI attribute extraction        5 (manufacturer-source enrichment hook)
  6 deterministic normalization    7 description building (spec-enforced)
  8 asset resolution (flagged)     9 validation gate + confidence + review queue

The AI stage *proposes*; stages 6-9 *enforce* the written standard and decide
what is trustworthy enough to ship. Every uncertain field is routed to a review
queue with a specific reason instead of being silently guessed.
"""

from __future__ import annotations
import re

from .schema import blank_record, MAX_ATTRIBUTES
from .ai_enrich import enrich_row
from .normalize import (standardize_units_in_text, standardize_measure,
                        enforce_limit, collapse_ws, units_are_compliant,
                        compress_units_in_text)
from .lookups import clean_placeholder, normalize_uom

# ---------------------------------------------------------------------------
# stage 2 — de-duplication
# ---------------------------------------------------------------------------
def normalize_for_dedup(desc: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (desc or "").lower())


def find_duplicates(rows):
    groups = {}
    for i, r in enumerate(rows):
        key = normalize_for_dedup(r.get("Part_Desc", ""))
        groups.setdefault(key, []).append(r.get("Mfg_Part_Num", "") or f"row{i}")
    return {k: v for k, v in groups.items() if len(v) > 1}


# ---------------------------------------------------------------------------
# stage 6/7 — enforce spec on the AI draft and build the description variants
# ---------------------------------------------------------------------------
_DIM_DEDICATED = {  # attribute label (lower) -> (value col, uom col)
    "length": ("LENGTH", "LENGTH_UOM"),
    "height": ("HEIGHT", "HEIGHT_UOM"),
    "width": ("WIDTH", "WIDTH_UOM"),
    "weight": ("WEIGHT", "WEIGHT_UOM"),
    "volume": ("VOLUME", "VOLUME_UOM"),
}


def _clean_attributes(attributes):
    """Normalize each attribute's unit+value; drop empties; dedupe by label."""
    out, seen = [], set()
    for a in attributes or []:
        label = collapse_ws(str(a.get("label", ""))).strip()
        value = collapse_ws(str(a.get("value", ""))).strip()
        uom_raw = collapse_ws(str(a.get("uom", ""))).strip()
        if not label or not value:
            continue
        key = label.lower()
        if key in seen:
            continue
        seen.add(key)
        approved_uom = normalize_uom(uom_raw) if uom_raw else ""
        # if value itself carries a unit ("24 in"), standardize the whole string
        if not approved_uom and re.search(r"\d", value):
            value = standardize_units_in_text(value)
        elif approved_uom:
            v2, u2 = standardize_measure(value, uom_raw)
            value, approved_uom = v2, u2
        out.append({"label": label, "value": value, "uom": approved_uom or (uom_raw if not uom_raw.isalpha() else uom_raw if uom_raw else "")})
    return out


def build_record(row: dict, draft: dict) -> tuple[dict, dict]:
    rec = blank_record()

    # ---- pass-through raw input (never mutate the source of truth) ---------
    rec["Mfg_Part_Num"] = row.get("Mfg_Part_Num", "")
    rec["Part_Desc"] = row.get("Part_Desc", "")
    rec["E1_Brand"] = row.get("E1_Brand", "")
    rec["Unilog_Brand"] = row.get("Unilog_Brand", "")
    rec["DIB_Brand"] = row.get("DIB_Brand", "")
    rec["Part_Manuf"] = row.get("Part_Manuf", "")
    rec["MANUFACTURER_PART_NUMBER"] = row.get("Mfg_Part_Num", "")

    # ---- identity / taxonomy ----------------------------------------------
    is_distributor = draft.get("_is_distributor", False)
    brand = collapse_ws(draft.get("brand_name", ""))
    manuf = collapse_ws(draft.get("manufacturer_name", ""))
    # If the model merely echoed the distributor string as the manufacturer,
    # drop it — a distributor is never a legitimate MANUFACTURER_NAME. But if the
    # model resolved a real maker from the brand/MPN, KEEP it and let the review
    # queue carry the distributor/mismatch flag (fill the field correctly AND
    # surface the anomaly, rather than blanking a value we can defend).
    parsed_dist = collapse_ws(draft.get("_manuf_parsed", "")).lower()
    if manuf and parsed_dist and manuf.lower() == parsed_dist:
        manuf = ""
    rec["BRAND_NAME"] = brand
    rec["MANUFACTURER_NAME"] = manuf
    rec["TRADE_NAME"] = collapse_ws(draft.get("trade_name", "")) or brand
    classpath = collapse_ws(draft.get("classpath", "")).replace(" > ", ">")
    rec["Classpath"] = classpath
    dept = draft.get("dept", ""); klass = draft.get("klass", ""); fine = draft.get("fine", "")
    if not (dept or klass or fine) and ">" in classpath:
        seg = [s.strip() for s in classpath.split(">")]
        dept = dept or (seg[0] if len(seg) > 0 else "")
        klass = klass or (seg[1] if len(seg) > 1 else "")
        fine = fine or (seg[2] if len(seg) > 2 else "")
    rec["Dept"], rec["Class"], rec["Fine"] = dept, klass, fine
    rec["Product Name"] = collapse_ws(draft.get("product_type", ""))
    rec["MFR URL"] = collapse_ws(draft.get("mfr_url", ""))
    rec["UNSPSC"] = collapse_ws(draft.get("unspsc", ""))
    rec["Country Of Origin"] = collapse_ws(draft.get("country_of_origin", ""))

    # ---- attributes (normalized) + dedicated dimension columns ------------
    attrs = _clean_attributes(draft.get("attributes"))
    for idx, a in enumerate(attrs[:MAX_ATTRIBUTES], start=1):
        rec[f"ATTRIBUTE_LABEL {idx}"] = a["label"]
        rec[f"ATTRIBUTE_VALUE {idx}"] = a["value"]
        rec[f"ATTRIBUTE_UOM {idx}"] = a["uom"]
        col = _DIM_DEDICATED.get(a["label"].lower())
        if col:
            rec[col[0]] = a["value"]
            rec[col[1]] = a["uom"]

    # ---- descriptions: take AI text, enforce units + limits ----------------
    def norm(t):
        return standardize_units_in_text(collapse_ws(t or ""))

    rec["MOBILE_DESC"] = enforce_limit(norm(draft.get("mobile_desc", "")), 80)
    # INVOICE_DESC is the compressed till-receipt form: glue approved unit
    # abbreviations to save characters within the 40-char CAPS budget.
    rec["INVOICE_DESC"] = enforce_limit(compress_units_in_text(collapse_ws(draft.get("invoice_desc", ""))), 40, upper=True)
    rec["SHORT_DESC"] = norm(draft.get("short_desc", ""))
    rec["LONG_DESC1"] = norm(draft.get("long_desc", ""))
    rec["RETAIL_DESC"] = norm(draft.get("retail_desc", "")) or rec["SHORT_DESC"]
    rec["MARKETING_DESCRIPTION"] = norm(draft.get("marketing_description", ""))

    # ---- feature bullets ---------------------------------------------------
    feats = [collapse_ws(f) for f in (draft.get("item_features") or []) if collapse_ws(f)]
    for i, f in enumerate(feats[:20], start=1):
        rec[f"ITEM_FEATURES_{i}"] = f

    rec["With"] = collapse_ws(draft.get("with_note", ""))
    rec["Standard/Approvals"] = collapse_ws(draft.get("standards_approvals", ""))
    rec["Application"] = collapse_ws(draft.get("application", ""))
    rec["Includes"] = collapse_ws(draft.get("includes", ""))

    # ---- stage 9: validation gate + confidence + review queue --------------
    qa = _validate_and_score(row, rec, draft, attrs, is_distributor)
    return rec, qa


# ---------------------------------------------------------------------------
# stage 9 — deterministic validation + confidence + review reasons
# ---------------------------------------------------------------------------
def _validate_and_score(row, rec, draft, attrs, is_distributor):
    conf = dict(draft.get("confidence", {}) or {})
    reasons = list(draft.get("review_reasons", []) or [])
    checks = {}

    # character-limit compliance
    inv_ok = len(rec["INVOICE_DESC"]) <= 40 and rec["INVOICE_DESC"] == rec["INVOICE_DESC"].upper()
    mob_len = len(rec["MOBILE_DESC"])
    mob_ok = 40 <= mob_len <= 80  # target 60-80; accept >=40 as non-fatal
    checks["invoice_desc_<=40_caps"] = inv_ok
    checks["mobile_desc_len"] = mob_len
    if not inv_ok:
        reasons.append("INVOICE_DESC exceeds 40 chars or not all-caps.")
    if mob_len and mob_len < 60:
        reasons.append(f"MOBILE_DESC is {mob_len} chars (target 60-80).")

    # unit compliance across the key long text
    ok_units, offenders = units_are_compliant(rec["LONG_DESC1"])
    checks["long_desc_units_ok"] = ok_units
    if not ok_units:
        reasons.append(f"Non-standard unit spacing/abbrev in LONG_DESC1: {offenders[:3]}")

    # emptiness checks on must-have fields
    if not rec["BRAND_NAME"]:
        reasons.append("BRAND_NAME empty — needs manufacturer-source enrichment.")
    if not rec["Classpath"] or "Needs Review" in rec["Classpath"]:
        reasons.append("Classpath unresolved — needs classification review.")
    if not attrs:
        reasons.append("No attributes extracted — description too sparse or needs enrichment.")

    # anomaly: manufacturer/brand or distributor mismatch
    if is_distributor:
        parsed = draft.get("_manuf_parsed", "")
        if rec["MANUFACTURER_NAME"]:
            reasons.append(f"ANOMALY: input Part_Manuf '{parsed}' is a distributor/reseller; "
                           f"MANUFACTURER_NAME resolved from brand as '{rec['MANUFACTURER_NAME']}' — verify.")
            conf["manufacturer_name"] = min(float(conf.get("manufacturer_name", 0.5)), 0.55)
        else:
            reasons.append(f"ANOMALY: Part_Manuf '{parsed}' is a distributor/reseller and no "
                           "manufacturer could be resolved from the brand — withheld pending review.")
            conf["manufacturer_name"] = 0.0

    # overall confidence = mean of the calibrated field confidences
    keys = ["classpath", "brand_name", "manufacturer_name", "attributes", "descriptions"]
    vals = [float(conf.get(k, 0.0)) for k in keys]
    overall = round(sum(vals) / len(vals), 3) if vals else 0.0

    needs_review = (overall < 0.6) or is_distributor or (not inv_ok) or (not rec["BRAND_NAME"])

    # de-dup reasons, keep order
    seen, uniq = set(), []
    for r in reasons:
        if r not in seen:
            seen.add(r); uniq.append(r)

    return {
        "Mfg_Part_Num": rec["Mfg_Part_Num"],
        "ai_used": bool(draft.get("_ai_used")),
        "overall_confidence": overall,
        "needs_human_review": needs_review,
        "field_confidence": {k: round(float(conf.get(k, 0.0)), 3) for k in keys},
        "distributor_detected": is_distributor,
        "n_attributes": len(attrs),
        "checks": checks,
        "review_reasons": uniq,
    }


# ---------------------------------------------------------------------------
# top-level per-row entry point
# ---------------------------------------------------------------------------
def process_row(row: dict, model: str = None):
    draft = enrich_row(row, model=model)
    return build_record(row, draft)
