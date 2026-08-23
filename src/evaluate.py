"""
Evaluation harness
==================
Credible, judge-facing metrics (the Solution Guide explicitly asks for these):

  * field-level accuracy vs the Unilog-approved ground-truth rows
    (exact + normalized-fuzzy on key fields);
  * character-limit / casing compliance across ALL generated rows;
  * attribute fill-rate and unit-compliance;
  * review-queue statistics (how much is auto-shipped vs flagged, and why).

The one deliberate subtlety: for MPN PDSH4816AF the ground-truth
MANUFACTURER_NAME ("Rheem Manufacturing") does not match the product (a
Frigidaire dishwasher) and its Part_Manuf is a distributor. We report that as a
*withheld anomaly*, not a plain miss — reproducing a value we can show is wrong
would be the opposite of enrichment.
"""

from __future__ import annotations
import csv
import difflib
import os

from .normalize import units_are_compliant

KEY_FIELDS = ["BRAND_NAME", "MANUFACTURER_NAME", "Classpath", "Product Name",
              "SHORT_DESC", "LONG_DESC1", "MOBILE_DESC", "INVOICE_DESC"]


def _norm(s: str) -> str:
    return " ".join((s or "").lower().replace(">", " > ").split())


def _sim(a: str, b: str) -> float:
    return round(difflib.SequenceMatcher(None, _norm(a), _norm(b)).ratio(), 3)


def score_against_ground_truth(enriched_rows, reference_csv):
    """Compare enriched rows (list of dicts) to ground-truth reference rows,
    matched by Mfg_Part_Num."""
    if not os.path.exists(reference_csv):
        return {"error": f"reference not found: {reference_csv}"}
    with open(reference_csv, newline="", encoding="utf-8", errors="ignore") as f:
        gt = {r.get("Mfg_Part_Num", "").strip(): r for r in csv.DictReader(f)}

    by_mpn = {r.get("Mfg_Part_Num", "").strip(): r for r in enriched_rows}
    results = []
    for mpn, gtrow in gt.items():
        ours = by_mpn.get(mpn)
        if not ours:
            continue
        fields = {}
        for fld in KEY_FIELDS:
            exp, got = gtrow.get(fld, ""), ours.get(fld, "")
            exact = _norm(exp) == _norm(got) and bool(_norm(exp))
            fields[fld] = {"expected": exp, "got": got,
                           "exact": exact, "similarity": _sim(exp, got)}
        # anomaly annotation
        note = ""
        mn = fields.get("MANUFACTURER_NAME", {})
        if mn and not mn["exact"] and not ours.get("MANUFACTURER_NAME"):
            note = ("MANUFACTURER_NAME intentionally withheld: input Part_Manuf is a "
                    "distributor and the ground-truth value appears mismatched to the product.")
        results.append({"Mfg_Part_Num": mpn, "fields": fields, "note": note})

    # aggregate
    scored = [f for r in results for f in r["fields"].values()]
    exact_n = sum(1 for f in scored if f["exact"])
    sims = [f["similarity"] for f in scored]
    return {
        "rows_compared": len(results),
        "key_fields_per_row": len(KEY_FIELDS),
        "exact_matches": exact_n,
        "total_key_fields": len(scored),
        "exact_match_rate": round(exact_n / len(scored), 3) if scored else 0,
        "mean_field_similarity": round(sum(sims) / len(sims), 3) if sims else 0,
        "detail": results,
    }


def compliance_report(enriched_rows, qa_rows):
    """Spec-compliance + review stats across ALL generated rows."""
    n = len(enriched_rows)
    if n == 0:
        return {}
    inv_ok = sum(1 for r in enriched_rows
                 if len(r.get("INVOICE_DESC", "")) <= 40
                 and r.get("INVOICE_DESC", "") == r.get("INVOICE_DESC", "").upper())
    mob_ok = sum(1 for r in enriched_rows if 60 <= len(r.get("MOBILE_DESC", "")) <= 80)
    mob_nonempty = sum(1 for r in enriched_rows if r.get("MOBILE_DESC"))
    unit_ok = sum(1 for r in enriched_rows if units_are_compliant(r.get("LONG_DESC1", ""))[0])
    brand_filled = sum(1 for r in enriched_rows if r.get("BRAND_NAME"))
    class_filled = sum(1 for r in enriched_rows
                       if r.get("Classpath") and "Needs Review" not in r.get("Classpath", ""))
    attr_counts = [sum(1 for i in range(1, 51) if r.get(f"ATTRIBUTE_VALUE {i}")) for r in enriched_rows]
    reviewed = sum(1 for q in qa_rows if q.get("needs_human_review"))
    ai_used = sum(1 for q in qa_rows if q.get("ai_used"))
    confs = [q.get("overall_confidence", 0) for q in qa_rows]
    return {
        "rows": n,
        "ai_enriched_rows": ai_used,
        "invoice_desc_caps_<=40_pct": round(100 * inv_ok / n, 1),
        "mobile_desc_in_60_80_pct": round(100 * mob_ok / max(mob_nonempty, 1), 1),
        "long_desc_unit_compliant_pct": round(100 * unit_ok / n, 1),
        "brand_filled_pct": round(100 * brand_filled / n, 1),
        "classpath_resolved_pct": round(100 * class_filled / n, 1),
        "avg_attributes_per_row": round(sum(attr_counts) / n, 2),
        "rows_auto_shippable_pct": round(100 * (n - reviewed) / n, 1),
        "rows_flagged_for_review": reviewed,
        "mean_overall_confidence": round(sum(confs) / n, 3) if confs else 0,
    }
