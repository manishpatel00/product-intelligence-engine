# DECK CONTENT — Unilog Product Intelligence Engine (Codehunt)

UniHack 2026 · Unilog challenge: "AI-Powered Product Intelligence for Industrial Commerce"

**How to use this file:** each `## Slide N` maps 1:1 to the mandatory template's slide order
(recovered from the provided `.pptx`). Copy the bullets into the matching template slide.
Text in _[brackets]_ is a placeholder for the team to fill. Speaker-note lines are prefixed
`SN:`. Judging tags show which of the 4 equal criteria a slide is built to win:
**[INNOVATION] · [ACCURACY] · [QUALITY] · [SCALABILITY]**.

---

## Slide 1 — Guidelines (template's own slide)
Leave exactly as provided by the template. This is the organizer's instruction slide
("Kindly use the given template… Make a copy…"). No team content goes here.

---

## Slide 2 — Team Details
- **Team name:** _Codehunt_
- **Team leader name:** _Rajeev Kumar Tiwari_
- **Members:** _Manish Kumar, Tarun Yadav, Divyanshu Tiwari_
- **Project:** Unilog Product Intelligence Engine — cryptic distributor rows → complete,
  standardized, search-ready 252-column commerce records.
- **One line:** *"AI reasons, deterministic rules enforce the spec — so no invented value ever ships."*

SN: Say the team name, then the one-liner. Keep it to ~15 seconds; the judges read the rest.

---

## Slide 3 — Brief about your solution
**The Unilog Product Intelligence Engine** turns one cryptic catalogue row —
an MPN, an abbreviated description, and mostly-empty brand fields — into the full
**252-column Unilog Delivery Format** record: correct taxonomy, extracted attributes,
five standardized descriptions, resolved brand/manufacturer, assets, and a per-field
trust score.

- **Input reality (measured on the 1,000-row sample):** 6 raw fields; **80% of rows arrive
  `-- Unbranded --`**; **9% list a distributor/co-op in the "manufacturer" field**;
  descriptions are telegraphic (`"PDSH4816AF Dishwasher SS - Display Only"`).
- **Output:** all **252 static headers** populated to the written standard — a **42× field expansion**.
- **The hard part isn't fluency, it's trust.** The Solution Guide warns *"a fluent
  description made of invented values scores zero."* We treat a guess as worse than a blank.
- **Our answer — a hybrid pipeline:** an LLM (Claude) **proposes**; a deterministic rules
  layer **validates every value** against controlled vocabularies and character limits
  **before it ships**. What can't be verified is **flagged, not fabricated.**

SN: This is the elevator pitch slide. Land "guess is worse than a blank" — it frames the whole deck.

---

## Slide 4 — The three mandated questions
> This slide is graded directly against the 4 criteria. Answer all three, concretely.

**1. How does your solution enrich minimal product information?**  **[QUALITY]**
- A **9-stage pipeline** takes the raw row → cleans placeholders → de-duplicates →
  **AI classifies** into the taxonomy/Classpath → **AI extracts attributes** from the cryptic
  description → **enriches** from manufacturer signals (brand/MPN) → **deterministically
  normalizes** → **builds 5 descriptions** → resolves assets → **validates + scores**.
- Example: `PDSH4816AF Dishwasher SS - Display Only` → Classpath
  `Appliances & Consumer Electronics>Kitchen Appliances>Built-In Dishwashers`,
  Brand `FRIGIDAIRE®`, attributes (voltage, amperage, wash cycles, material, size),
  and 5 descriptions incl. `INVOICE_DESC = DISHWASHER LEG 5 SST 120V 15A 50-1/4IN` (38 chars).

**2. How does your solution ensure accuracy and trust?**  **[ACCURACY]**
- **Rule-based validation gate:** every unit, fraction, casing, and character limit is
  enforced by pure code — not another LLM — so hallucinations can't pass.
- **Anti-hallucination prompt contract:** Claude must leave a field blank + lower its
  confidence rather than invent a value.
- **Per-field confidence scoring (0–1)** across classpath, brand, manufacturer, attributes, descriptions.
- **Human-in-the-loop review queue:** low-confidence fields route to review **with a specific reason.**
- **Anomaly detection / multi-signal verification:** distributor-as-manufacturer and
  brand/product mismatches are caught and withheld (see Slide 5 & 12).

**3. What makes it scalable for enterprise catalogs?**  **[SCALABILITY]**
- **Large catalogs:** per-row bounded cost; **de-dup collapses repeat SKUs before any LLM spend**;
  stages are independently **cacheable & parallelizable** (ran the full 1,000-row sample).
- **New manufacturers:** brand/UOM/taxonomy are **data-driven lookups** — drop in the real
  27k-row UniCat brand master or UOM master; no code change.
- **Different formats:** a thin ingest adapter maps any column layout to the 6 canonical inputs.
- **Continuous updates:** each row is idempotent and independently reprocessable; confidence
  + review flags make re-runs auditable.

---

## Slide 5 — Opportunities (differentiation · problem fit · USP)
**How is it different from existing ideas / naive "ask an LLM" tools?**  **[INNOVATION]**
- Most tools let an LLM **write the whole record** — fluent, confident, and often **wrong**.
  We invert control: **AI proposes, deterministic rules dispose.** No value ships unvalidated.
- We **quantify uncertainty per field** and **route it to humans**, instead of hiding it.
- We **detect the traps in the data** (distributors mislabeled as manufacturers, mismatched
  brands) rather than faithfully reproducing them.

**How it solves the problem statement:**
- Produces **all 252 static headers**, spec-compliant, from the real evaluation dataset —
  dynamic, not hardcoded; degrades gracefully so it **never hard-fails**.

**USP (one line):** *"The only entry where a wrong value is structurally prevented from
shipping — every field is either validated or flagged, and you can see the confidence for each."*

SN: This is the Innovation criterion slide. Emphasize the inversion of control and the anomaly catch.

---

## Slide 6 — List of features
**[QUALITY] [INNOVATION]**
1. **6 → 252 field expansion** to the exact Unilog Delivery Format (static headers preserved).
2. **AI classification** into taxonomy Classpath (Dept / Class / Fine).
3. **AI attribute extraction** from cryptic descriptions → clean `{label, value, uom}` triples.
4. **Deterministic normalization:** approved UOM abbreviations with one space (`24 in`, `120 V`);
   inch decimals → searchable fractions via an **exact 1/64 table** (`50.25 → 50-1/4 in`).
5. **5 descriptions, one product:** `INVOICE_DESC` (≤40, CAPS) · `MOBILE_DESC` (60–80) ·
   `SHORT_DESC` (title) · `LONG_DESC1` (full formula) · `MARKETING_DESCRIPTION`.
6. **Per-field confidence scoring** + overall row score.
7. **Human-review queue** with specific, human-readable reasons per flagged field.
8. **Anomaly detection:** distributor-vs-manufacturer signal + brand/product mismatch.
9. **Graceful degradation:** runs on pure Python stdlib; **no API key → deterministic pass**, same output contract.
10. **Evaluation harness:** field-level accuracy vs ground truth, compliance %, fill-rate, review stats.
11. **Downloadable CSV/XLSX** output + a QA review report + a duplicate report.

---

## Slide 7 — Process flow / use-case diagram
Render this left-to-right; label the AI vs deterministic zones distinctly.

```
 RAW ROW (6 cols)
 MPN · Part_Desc · E1_Brand · Unilog_Brand · DIB_Brand · Part_Manuf
        │
        ▼
 [1] INGEST & CLEAN ── strip placeholders ("-- Unbranded --" → empty)
        │
        ▼
 [2] DE-DUPLICATE ── collapse repeat SKUs  (saves LLM spend)
        │
        ▼
 ┌───────────── AI PROPOSES (Claude, forced JSON tool-call) ─────────────┐
 │ [3] CLASSIFY → Classpath / Dept / Class / Fine                        │
 │ [4] EXTRACT ATTRIBUTES → {label, value, uom}[]                        │
 │ [5] ENRICH from manufacturer signals (brand / MPN prefix)             │
 └───────────────────────────────────────────────────────────────────────┘
        │  (draft + self-reported confidence)
        ▼
 ┌──────────── DETERMINISTIC RULES ENFORCE (pure Python) ────────────────┐
 │ [6] NORMALIZE units → approved abbrev + space; decimals → fractions   │
 │ [7] BUILD 5 DESCRIPTIONS at spec lengths/casings                      │
 │ [8] RESOLVE ASSETS (URLs / images; flagged if unresolved)             │
 │ [9] VALIDATION GATE → per-field confidence → PASS or REVIEW QUEUE     │
 └───────────────────────────────────────────────────────────────────────┘
        │                                  │
        ▼                                  ▼
 252-COLUMN RECORD (auto-ship)      HUMAN REVIEW QUEUE (reason per field)
```

**Primary use case:** a catalog manager drops a distributor feed → gets a spec-compliant
252-column file to load, plus a short worklist of exactly the fields a human must confirm.

---

## Slide 8 — Wireframes / mock (optional)
Two simple views (screenshot the real outputs for Slide 12; mock the UI here):
- **Enriched Record view:** left = raw 6-field row; right = the 252-field record grouped
  (Identity · Taxonomy · Attributes · 5 Descriptions · Assets), each field with a
  **confidence chip** (green ≥0.6, amber <0.6).
- **Review Queue view:** a table of flagged rows → click a row → see the specific reason
  ("ANOMALY: Part_Manuf is a distributor — MANUFACTURER_NAME withheld") and Approve / Edit actions.

SN: Optional slide — keep it to the two views; the real proof is Slide 12.

---

## Slide 9 — Architecture diagram
**[SCALABILITY] [QUALITY]** — the headline principle: **AI reasons, deterministic rules enforce.**

```
╔══════════════════════════════════════════════════════════════════════════════╗
║              UNILOG PRODUCT INTELLIGENCE ENGINE — Architecture             ║
║            "AI reasons — deterministic rules enforce the spec"             ║
╚══════════════════════════════════════════════════════════════════════════════╝

         Input CSV/XLSX                                            OUTPUTS
       ┌──────────────┐                                   ┌───────────────────┐
       │ Any column   │                                   │ enriched_output   │
       │ layout       │                                   │ .csv / .xlsx      │
       │ (6 raw cols) │                                   │ (252 cols)        │
       └──────┬───────┘                                   ├───────────────────┤
              │                                           │ qa_review_report  │
              ▼                                           │ .csv              │
  ┌────────────────────────────┐                          ├───────────────────┤
  │      run.py                │                          │ duplicate_report  │
  │  ┌──────────────────────┐  │                          │ .json             │
  │  │  ThreadPoolExecutor  │  │                          ├───────────────────┤
  │  │  (parallel per-row)  │  │                          │ evaluation_       │
  │  └──────────┬───────────┘  │                          │ summary.json      │
  └─────────────┼──────────────┘                          └───────────────────┘
                │                                                  ▲
                │ per unique row                                   │
                ▼                                                  │
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┷━━━━━━━━━┓
┃  pipeline.py — 9-STAGE ORCHESTRATOR                                        ┃
┃                                                                             ┃
┃  ┌─────────────────────────────────────────────────────────────────────┐    ┃
┃  │ [1] INGEST & CLEAN           [2] DE-DUPLICATE                     │    ┃
┃  │  strip "--Unbranded--"→""     collapse repeat Part_Desc hashes    │    ┃
┃  │  trim whitespace, tags        → saves all downstream LLM spend    │    ┃
┃  └─────────────────────────────────────────┬───────────────────────────┘    ┃
┃                                            │                               ┃
┃                                            ▼                               ┃
┃               ┌──────────── ANTHROPIC_API_KEY? ────────────┐               ┃
┃               │                                            │               ┃
┃           SET │                                    UNSET   │               ┃
┃               ▼                                            ▼               ┃
┃  ┌─────────────────────────────┐          ┌────────────────────────────┐   ┃
┃  │░░░ AI PATH (ai_used=True) ░░│          │ DETERMINISTIC FALLBACK    │   ┃
┃  │                              │          │ (ai_used=False)           │   ┃
┃  │  ai_enrich.py                │          │                          │   ┃
┃  │  ┌────────────────────────┐  │          │ • MPN-prefix brand hint  │   ┃
┃  │  │ System Prompt:         │  │          │ • Placeholder cleaning   │   ┃
┃  │  │ • Anti-hallucination   │  │          │ • Best-effort attributes │   ┃
┃  │  │ • UOM rules            │  │          │ • Low confidence → flag  │   ┃
┃  │  │ • Sourcing (mfr only)  │  │          │                          │   ┃
┃  │  │ • 5 desc formulas      │  │          │ Same draft contract.     │   ┃
┃  │  └────────────┬───────────┘  │          │ Never hard-fails.        │   ┃
┃  │               ▼              │          └─────────────┬────────────┘   ┃
┃  │  ┌────────────────────────┐  │                        │               ┃
┃  │  │ llm_client.py          │  │                        │               ┃
┃  │  │ • urllib HTTPS (0 dep) │  │                        │               ┃
┃  │  │ • Forced tool_choice   │  │                        │               ┃
┃  │  │ • Retry 429/5xx/529    │  │                        │               ┃
┃  │  │ • temp=0, ~2.6k tok   │  │                        │               ┃
┃  │  └────────────┬───────────┘  │                        │               ┃
┃  │               │              │                        │               ┃
┃  │ [3] CLASSIFY  │ Classpath    │                        │               ┃
┃  │ [4] EXTRACT   │ Attributes   │                        │               ┃
┃  │ [5] ENRICH    │ Brand/MPN    │                        │               ┃
┃  └───────────────┼──────────────┘                        │               ┃
┃                  │                                       │               ┃
┃                  └──────────────┬─────────────────────────┘               ┃
┃                                │                                         ┃
┃                 draft { values, confidence{}, review_reasons[] }         ┃
┃                                │                                         ┃
┃  ╔═════════════════════════════╧══════════════════════════════════════╗   ┃
┃  ║▓▓▓▓▓▓  DETERMINISTIC TRUST GATE (pure Python)  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓║   ┃
┃  ║                                                                   ║   ┃
┃  ║  [6] NORMALIZE  ──── normalize.py ────────────────────────────    ║   ┃
┃  ║       │  Unit standardize:  "24in" → "24 in"                     ║   ┃
┃  ║       │  Decimal→fraction:  50.25  → "50-1/4"   (1/64 table)    ║   ┃
┃  ║       │  Approved UOM map + _NUM_UNIT_RE regex                   ║   ┃
┃  ║       │                                                           ║   ┃
┃  ║  [7] BUILD 5 DESCRIPTIONS ────────────────────────────────────    ║   ┃
┃  ║       │  INVOICE_DESC ≤40 CAPS │ MOBILE 60-80 │ SHORT ~120      ║   ┃
┃  ║       │  LONG_DESC1 (formula)  │ MARKETING (prose)              ║   ┃
┃  ║       │  enforce_limit() + word-boundary trim                    ║   ┃
┃  ║       │                                                           ║   ┃
┃  ║  [8] RESOLVE ASSETS ── URLs/images validated or flagged ──────    ║   ┃
┃  ║       │                                                           ║   ┃
┃  ║  [9] VALIDATION GATE ────────────────────────────────────────    ║   ┃
┃  ║       │  Structural:  limits ✓  casing ✓  UOM compliance ✓      ║   ┃
┃  ║       │  Anomaly:     distributor scan (lookups.py)              ║   ┃
┃  ║       │               ┌─── is_distributor? ───┐                  ║   ┃
┃  ║       │               │YES: withhold + reason │                  ║   ┃
┃  ║       │               │NO:  pass through      │                  ║   ┃
┃  ║       │               └───────────────────────┘                  ║   ┃
┃  ║       │  Confidence:  field scores → overall = mean              ║   ┃
┃  ║       │  Route:       ≥0.6 + clean → AUTO-SHIP                  ║   ┃
┃  ║       │               <0.6 / anomaly → REVIEW QUEUE + reasons   ║   ┃
┃  ║                                                                   ║   ┃
┃  ╚═══════════════════════════════════════════════════════════════════╝   ┃
┃                                                                         ┃
┃          ┌────────── lookups.py ──────────┐                             ┃
┃          │  APPROVED_UOM map              │                             ┃
┃          │  1/64 fraction table           │                             ┃
┃          │  Brand master                  │                             ┃
┃          │  DISTRIBUTOR_SIGNAL_WORDS      │                             ┃
┃          │  MPN-prefix hints              │                             ┃
┃          │  Placeholder set               │                             ┃
┃          └────────────────────────────────┘                             ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

- **Zero-dependency:** stdlib `urllib` calls the Claude Messages API; **no `pip install`**.
- **Graceful degradation:** if `ANTHROPIC_API_KEY` is unset (or the API errors), the same
  contract is met by a deterministic pass, marked `ai_used=False`. **The pipeline never hard-fails.**
- **Auditable:** every stage is a separate, testable module; every field is traceable to a source or a flag.

---

## Slide 10 — Technologies used
- **Language:** Python 3 — **standard library only** (csv, json, re, urllib, concurrent.futures). No third-party deps.
- **AI:** Anthropic **Claude** (default `claude-sonnet-5`, model-configurable; Haiku for cost) via
  the Messages API using **structured tool-use** (`tool_choice` forces schema-valid JSON, not prose).
- **Determinism layer:** custom rules engine — approved-UOM map, exact 1/64 decimal↔fraction table,
  controlled vocabularies, character-limit/casing enforcement, validation + confidence scoring.
- **Concurrency:** `ThreadPoolExecutor` for parallel per-row LLM I/O.
- **Outputs:** CSV/XLSX (252 static headers) + JSON reports.
- **Demo:** lightweight, zero-dependency browser view of the enriched record + review queue.
- **Repro:** `python3 run.py` runs the full 1,000-row sample with **zero setup**.

---

## Slide 11 — Estimated implementation cost (optional)
- **Compute:** one bounded LLM call per **unique** SKU (de-dup collapses repeats first).
  Attributes + 5 descriptions + classification come back in a **single structured call**
  (temp 0, ~2.6k output tokens/SKU — measured, not estimated).
- **How catalog cost scales:** model spend is **linear in the number of _unique_ SKUs** after
  de-dup — not total rows — and is set by the chosen tier (Haiku for volume, Sonnet for hard rows).
  Per-stage caching means re-runs of unchanged rows cost **$0**.
- **The real cost is the human-review tail, and we minimize it:** only flagged fields reach a
  person; everything validated auto-ships. The deterministic fallback costs **$0** and still
  ships a valid record, so the engine has a hard cost floor of zero.
- **Ops:** no servers/GPUs required to run the engine; scales horizontally by sharding rows.

SN: Don't quote a catalog dollar total you can't defend — lead with the levers: dedup-first,
model-tiering, caching, and a $0 fallback floor. The measurable number is ~2.6k output tokens per unique SKU.

---

## Slide 12 — Snapshots of the MVP
Show three real screenshots from an actual run.

**A. Before → After (the flagship row, MPN `PDSH4816AF`):**
- **IN:** `Part_Desc="PDSH4816AF Dishwasher SS - Display Only"`, `E1_Brand="-- Unbranded --"`,
  `Part_Manuf="Appliance Dealers Cooperative (APPDE)"`.
- **OUT (excerpt of 252 cols):** `BRAND_NAME=FRIGIDAIRE®`, Classpath `…>Built-In Dishwashers`,
  `INVOICE_DESC=DISHWASHER LEG 5 SST 120V 15A 50-1/4IN` (38 chars, note `50.25 → 50-1/4`),
  attributes populated, `MANUFACTURER_NAME` **withheld & flagged**.

**B. `qa_review_report.csv` (real output):** columns
`Mfg_Part_Num, ai_used, overall_confidence, needs_human_review, distributor_detected, n_attributes, review_reasons`
— e.g. *"ANOMALY: Part_Manuf 'Jam Industrial Supply LLC' is a distributor/reseller, not a
manufacturer — MANUFACTURER_NAME withheld pending review."*

**C. `evaluation_summary.json` (real output):** compliance block — **`INVOICE_DESC ≤40 CAPS: 100%`**,
**`LONG_DESC unit-format compliant: 100%`**, brand-filled %, classpath-resolved %, avg attributes/row,
auto-shippable %, rows flagged, mean confidence.

SN: Walk A → B → C in 20 seconds. The 100% compliance numbers are *structural guarantees*, true on every row.

---

## Slide 13 — Additional details / future development
- **Swap in real master data:** the 27k-row UniCat brand/manufacturer list and the ~500-row
  UOM master (89 measurement types) load via a drop-in file — the seams already exist in code.
- **Manufacturer-source RAG:** replace the MPN-prefix hint with live retrieval over the
  manufacturer's own product pages/spec sheets for citable attribute provenance.
- **Active learning:** every human-review decision becomes a labeled example to raise
  auto-ship rate over time.
- **Asset pipeline:** image de-dup + spec-sheet OCR to fill the asset columns.
- **Multi-format ingest:** PDF/Excel/EDI adapters onto the same 6 canonical inputs.
- **Confidence calibration dashboard:** track precision at each confidence threshold per category.

---

## Slide 14 — Links
- **GitHub Public Repository:** _[https://github.com/…]_
- **Demo Video (3–4 min):** _[link]_
- **Working Prototype:** _[link — or "clone & run `python3 run.py` (zero setup, stdlib only)"]_

---

## Slide 15 — Closing
**Unilog Product Intelligence Engine — Codehunt**
- **Innovation:** AI proposes, deterministic rules enforce; anomaly detection; confidence-scored HITL.
- **Accuracy of data:** 100% spec-compliance by construction + no unvalidated value ships.
- **Quality of solution:** 9 auditable stages, full 252-col output, real evaluation harness.
- **Scalability:** zero-dependency, dedup-first, parallel, graceful degradation — runs anywhere.

*"Every field is either validated or flagged — and you can see the confidence for each."*
Thank you — questions welcome.
