#!/usr/bin/env python3
"""
Unilog Product Intelligence Engine — batch runner
=================================================
Reads a raw catalogue CSV and produces the full 252-column Delivery Format
output plus a QA/review report, a duplicate report and an evaluation summary.

Examples
--------
  python3 run.py                                  # 1000-row sample, all rows
  python3 run.py --limit 25                        # quick slice
  python3 run.py --input data/my.csv --workers 8   # your data, 8 parallel calls
  UNILOG_MODEL=claude-haiku-4-5-20251001 python3 run.py --limit 200

With ANTHROPIC_API_KEY set, the AI path runs; without it, the engine falls back
to a deterministic pass (still produces valid output, marked ai_used=False).
"""

from __future__ import annotations
import argparse
import csv
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.schema import DELIVERY_HEADERS
from src.pipeline import process_row, find_duplicates
from src import llm_client
from src.evaluate import score_against_ground_truth, compliance_report
from src.xlsx_writer import write_xlsx

HERE = os.path.dirname(os.path.abspath(__file__))


def load_rows(path, limit=None):
    with open(path, newline="", encoding="utf-8", errors="ignore") as f:
        rows = list(csv.DictReader(f))
    return rows[:limit] if limit else rows


def write_csv(path, headers, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=headers, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default=os.path.join(HERE, "data", "input_sample_1000.csv"))
    ap.add_argument("--outdir", default=os.path.join(HERE, "outputs"))
    ap.add_argument("--reference", default=os.path.join(HERE, "data", "expected_output_reference.csv"))
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--model", default=None)
    args = ap.parse_args()

    os.makedirs(args.outdir, exist_ok=True)
    rows = load_rows(args.input, args.limit)
    ai_on = llm_client.have_api_key()
    print(f"[i] loaded {len(rows)} rows from {os.path.relpath(args.input, HERE)}")
    print(f"[i] AI path: {'ON (' + (args.model or llm_client.DEFAULT_MODEL) + ')' if ai_on else 'OFF — deterministic fallback (set ANTHROPIC_API_KEY to enable Claude)'}")

    # stage 2 — duplicates
    dups = find_duplicates(rows)
    print(f"[i] duplicate groups: {len(dups)}")

    # stages 1,3-9 — enrich (parallel I/O when AI is on)
    t0 = time.time()
    enriched = [None] * len(rows)
    qa = [None] * len(rows)
    done = 0

    def work(i_row):
        i, row = i_row
        return i, process_row(row, model=args.model)

    workers = args.workers if ai_on else 1
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(work, (i, r)) for i, r in enumerate(rows)]
        for fut in as_completed(futs):
            i, (rec, qarow) = fut.result()
            enriched[i], qa[i] = rec, qarow
            done += 1
            if done % 25 == 0 or done == len(rows):
                print(f"    enriched {done}/{len(rows)}  ({time.time()-t0:.1f}s)")

    # ---- write outputs -----------------------------------------------------
    out_csv = os.path.join(args.outdir, "enriched_output.csv")
    write_csv(out_csv, DELIVERY_HEADERS, enriched)

    # same 252-column data as a downloadable workbook (pure-stdlib OOXML)
    out_xlsx = os.path.join(args.outdir, "enriched_output.xlsx")
    write_xlsx(out_xlsx, DELIVERY_HEADERS, enriched)

    qa_csv = os.path.join(args.outdir, "qa_review_report.csv")
    with open(qa_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Mfg_Part_Num", "ai_used", "overall_confidence", "needs_human_review",
                    "distributor_detected", "n_attributes", "review_reasons"])
        for q in qa:
            w.writerow([q["Mfg_Part_Num"], q["ai_used"], q["overall_confidence"],
                        q["needs_human_review"], q["distributor_detected"],
                        q["n_attributes"], " | ".join(q["review_reasons"])])

    with open(os.path.join(args.outdir, "duplicate_report.json"), "w") as f:
        json.dump({"duplicate_groups": dups, "n_groups": len(dups)}, f, indent=2)

    # ---- evaluation --------------------------------------------------------
    gt = score_against_ground_truth(enriched, args.reference)
    comp = compliance_report(enriched, qa)
    summary = {
        "input": os.path.relpath(args.input, HERE),
        "rows": len(rows),
        "ai_path": ai_on,
        "model": (args.model or llm_client.DEFAULT_MODEL) if ai_on else None,
        "elapsed_sec": round(time.time() - t0, 1),
        "duplicate_groups": len(dups),
        "ground_truth_scoring": gt,
        "compliance": comp,
    }
    with open(os.path.join(args.outdir, "evaluation_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)

    # ---- console recap -----------------------------------------------------
    print("\n=== EVALUATION SUMMARY ===")
    if "exact_match_rate" in gt:
        print(f"Ground-truth key-field exact match : {gt['exact_matches']}/{gt['total_key_fields']} "
              f"({gt['exact_match_rate']*100:.0f}%), mean similarity {gt['mean_field_similarity']}")
    for k, v in comp.items():
        print(f"  {k}: {v}")
    print(f"\nOutputs written to {os.path.relpath(args.outdir, HERE)}/:")
    print("  enriched_output.csv  enriched_output.xlsx  qa_review_report.csv  duplicate_report.json  evaluation_summary.json")


if __name__ == "__main__":
    main()
