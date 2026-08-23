#!/usr/bin/env python3
"""
End-to-end test of the AI code path with the network call STUBBED.
==================================================================
We cannot hit the live API in CI, so we replace only ``llm_client.call_structured``
with a function that returns a realistic Claude draft for the two ground-truth
MPNs, then run the *real* pipeline (enrich_row -> build_record -> validation ->
scoring). This proves the assembly, unit/fraction enforcement, description
handling, anomaly flagging and ground-truth scoring all work — independent of a
live key. Run: ``python3 tests/test_ai_path_mock.py``
"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import llm_client
from src.pipeline import process_row
from src.evaluate import score_against_ground_truth

# realistic drafts (what Claude returns under our schema), decimals ON PURPOSE
# (50.25, 24.25) so we prove decimal->fraction enforcement fires.
DRAFTS = {
 "PDSH4816AF": {
   "product_type":"Dishwasher",
   "classpath":"Appliances & Consumer Electronics>Kitchen Appliances>Built-In Dishwashers",
   "dept":"Appliances","klass":"Large Appliances","fine":"Dishwashers",
   "brand_name":"FRIGIDAIRE®","manufacturer_name":"Frigidaire","trade_name":"FRIGIDAIRE®",
   "series":"Professional Series","unspsc":"52141505","country_of_origin":"",
   "attributes":[
     {"label":"Series","value":"Professional Series","uom":""},
     {"label":"Number of Wash Cycles","value":"5","uom":""},
     {"label":"Voltage Rating","value":"120","uom":"volts"},
     {"label":"Amperage Rating","value":"15","uom":"amps"},
     {"label":"Mounting Type","value":"Leg","uom":""},
     {"label":"Depth With Door Open","value":"50.25","uom":"in"},
     {"label":"Width","value":"24","uom":"in"},
     {"label":"Sound Level","value":"47","uom":"dba"},
     {"label":"Material","value":"Stainless Steel","uom":""},
   ],
   "item_features":["5 wash cycles","CleanBoost technology","Stainless steel tub"],
   "mobile_desc":"FRIGIDAIRE Dishwasher, Professional Series, PDSH4816AF, Leg Mount",
   "invoice_desc":"DISHWASHER LEG 5 SST 120VOLTS 15AMPS 50.25IN",
   "short_desc":"FRIGIDAIRE® Professional Series PDSH4816AF Dishwasher With CleanBoost, Leg Mounting, 5-Wash Cycle, Stainless Steel",
   "long_desc":"FRIGIDAIRE® Dishwasher With CleanBoost, Professional Series, 5 Wash Cycles, 120volts, 15amps, Leg Mounting, 24in W x 24.25in D, 50.25in Depth With Door Open, 47 dba Sound Level, Stainless Steel",
   "retail_desc":"Professional Series Dishwasher, Leg Mounting, 5-Wash Cycle, Stainless Steel",
   "marketing_description":"A quiet, efficient built-in dishwasher with a stainless steel tub and five wash cycles for everyday cleaning power.",
   "with_note":"With CleanBoost","standards_approvals":"UL Listed|ENERGY STAR Certified|NSF Certified",
   "application":"","includes":"","mfr_url":"https://www.frigidaire.com/en/p/owner-center/product-support/PDSH4816AF",
   "confidence":{"classpath":0.95,"brand_name":0.93,"manufacturer_name":0.8,"attributes":0.85,"descriptions":0.9},
   "review_reasons":[],
 },
 "WDTS7024RZ": {
   "product_type":"Dishwasher",
   "classpath":"Appliances & Consumer Electronics>Kitchen Appliances>Built-In Dishwashers",
   "dept":"Appliances","klass":"Large Appliances","fine":"Dishwashers",
   "brand_name":"Whirlpool®","manufacturer_name":"Whirlpool Corporation","trade_name":"Whirlpool®",
   "series":"Eco Series","unspsc":"52141505","country_of_origin":"",
   "attributes":[
     {"label":"Series","value":"Eco Series","uom":""},
     {"label":"Voltage Rating","value":"120","uom":"V"},
     {"label":"Amperage Rating","value":"10","uom":"A"},
     {"label":"Mounting Type","value":"Built-in","uom":""},
     {"label":"Sound Level","value":"41","uom":"dBA"},
     {"label":"Material","value":"Stainless Steel","uom":""},
   ],
   "item_features":["3rd rack with extra wash action","Adjustable 2nd Rack","Leak Detection System"],
   "mobile_desc":"Whirlpool Dishwasher, Eco Series, WDTS7024RZ, Built-in Mounting",
   "invoice_desc":"DISHWASHER BLTLN SST 120V 10A 41DBA",
   "short_desc":"Whirlpool® Eco Series WDTS7024RZ Dishwasher, Built-in Mounting, Stainless Steel",
   "long_desc":"Whirlpool® Dishwasher, Eco Series, 120 V, 10 A, Built-in Mounting, 41 dBA Sound Level, Stainless Steel",
   "retail_desc":"Eco Series Dishwasher, Built-in Mounting, Stainless Steel",
   "marketing_description":"Load more and run less with a quiet, large-capacity dishwasher featuring a dedicated 3rd rack.",
   "with_note":"With Washing 3rd Rack","standards_approvals":"UL Listed|ENERGY STAR Certified",
   "application":"","includes":"","mfr_url":"https://www.whirlpool.com/",
   "confidence":{"classpath":0.95,"brand_name":0.92,"manufacturer_name":0.9,"attributes":0.8,"descriptions":0.9},
   "review_reasons":[],
 },
}

def fake_call_structured(system, user, tool_name, input_schema, **kw):
    for mpn, draft in DRAFTS.items():
        if mpn in user:
            return dict(draft)
    raise RuntimeError("no mock draft for this row")

def main():
    os.environ["ANTHROPIC_API_KEY"] = "test-stub-key"   # enable AI path
    llm_client.call_structured = fake_call_structured     # stub the network

    import csv
    rows = list(csv.DictReader(open(os.path.join(os.path.dirname(__file__), "..", "data", "ground_truth_input.csv"))))
    enriched, qa = [], []
    for r in rows:
        rec, q = process_row(r)
        enriched.append(rec); qa.append(q)

    ref = os.path.join(os.path.dirname(__file__), "..", "data", "expected_output_reference.csv")
    score = score_against_ground_truth(enriched, ref)

    print("=== AI-path e2e (stubbed network) — ground-truth scoring ===")
    print(f"exact key-field matches: {score['exact_matches']}/{score['total_key_fields']} "
          f"({score['exact_match_rate']*100:.0f}%)  mean similarity: {score['mean_field_similarity']}")
    for row in score["detail"]:
        print(f"\nMPN {row['Mfg_Part_Num']}:")
        for fld, d in row["fields"].items():
            mark = "EXACT" if d["exact"] else f"sim={d['similarity']}"
            print(f"  {fld:18s} {mark}")
            if not d["exact"]:
                print(f"      exp: {d['expected'][:90]}")
                print(f"      got: {d['got'][:90]}")
        if row["note"]:
            print(f"  NOTE: {row['note']}")

    print("\n=== spec enforcement proof (decimals -> fractions, units) ===")
    r0 = enriched[0]
    print("  LONG_DESC1:", r0["LONG_DESC1"])
    print("  INVOICE_DESC:", repr(r0["INVOICE_DESC"]), f"(len {len(r0['INVOICE_DESC'])}, caps={r0['INVOICE_DESC'].isupper()})")
    print("  Depth attr value:", [ (r0[f'ATTRIBUTE_LABEL {i}'], r0[f'ATTRIBUTE_VALUE {i}'], r0[f'ATTRIBUTE_UOM {i}']) for i in range(1,11) if r0.get(f'ATTRIBUTE_LABEL {i}') ][:9])
    print("\n=== QA / review ===")
    for q in qa:
        print(f"  {q['Mfg_Part_Num']}: conf={q['overall_confidence']} review={q['needs_human_review']} distributor={q['distributor_detected']}")
        for rr in q["review_reasons"]:
            print(f"      - {rr}")

if __name__ == "__main__":
    main()
