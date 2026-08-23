#!/usr/bin/env python3
"""
Web-demo core test (no socket bind — the sandbox forbids it).
=============================================================
Exercises the pure request handlers render_index() and handle_enrich() exactly
as the socket transport calls them, so the live prototype is proven correct
without opening a port. Run: python3 tests/test_server_core.py
"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import server


def check(name, cond, extra=""):
    print(("  ok  " if cond else " FAIL ") + name + (f"  {extra}" if extra else ""))
    if not cond:
        raise SystemExit(1)


def main():
    print("=== live-prototype core (render_index + handle_enrich) ===")

    # --- GET / ---------------------------------------------------------------
    html = server.render_index()
    check("index renders HTML", "<title>Unilog Product Intelligence Engine" in html)
    check("index injects presets JSON", "const PRE = [" in html or "const PRE = []" in html)
    check("index shows AI badge", "badge" in html)
    check("no unfilled template tokens", "%PRESETS%" not in html and "%AI_LABEL%" not in html
          and "%PRESETS_JSON%" not in html and "%AI_CLASS%" not in html)

    # --- POST /api/enrich : a distributor + placeholder-brand row ------------
    body = json.dumps({"row": {
        "Mfg_Part_Num": "PDSH4816AF",
        "Part_Desc": "PDSH4816AF Dishwasher SS - Display Only",
        "Part_Manuf": "Appliance Dealers Cooperative (APPDE)",
        "E1_Brand": "-- Unbranded --",
    }})
    code, out = server.handle_enrich(body)
    check("enrich returns 200", code == 200, f"code={code}")
    data = json.loads(out)
    check("response has record", "record" in data)
    check("response has qa", "qa" in data)
    rec, qa = data["record"], data["qa"]
    check("record has exactly 252 columns", len(rec) == 252, f"got {len(rec)}")
    check("MPN passed through", rec["Mfg_Part_Num"] == "PDSH4816AF")
    check("INVOICE_DESC within 40 & caps",
          len(rec["INVOICE_DESC"]) <= 40 and rec["INVOICE_DESC"] == rec["INVOICE_DESC"].upper(),
          repr(rec["INVOICE_DESC"]))
    check("qa has overall_confidence", isinstance(qa["overall_confidence"], (int, float)))
    check("qa has review queue list", isinstance(qa["review_reasons"], list))
    check("qa is JSON-serialisable", json.dumps(qa) is not None)
    print(f"    -> INVOICE_DESC={rec['INVOICE_DESC']!r}  brand={rec['BRAND_NAME']!r}  "
          f"conf={qa['overall_confidence']}  review={qa['needs_human_review']}")

    # --- malformed body must not crash the handler ---------------------------
    code, out = server.handle_enrich("this is not json")
    check("bad JSON handled gracefully (500 + error)", code == 500 and "error" in json.loads(out))

    # --- empty row still yields a valid 252-col record -----------------------
    code, out = server.handle_enrich(json.dumps({"row": {}}))
    check("empty row -> 200 with 252-col record",
          code == 200 and len(json.loads(out)["record"]) == 252)

    print("\nALL CORE CHECKS PASSED — the live prototype logic is verified.")


if __name__ == "__main__":
    main()
