# Unilog Product Intelligence Engine

**UniHack 2026 · Unilog challenge — "AI-Powered Product Intelligence for Industrial Commerce"**

> Turn one cryptic distributor row — a part number, a telegraphic description, and mostly-empty
> brand fields — into the complete, standardized, search-ready **252-column Unilog Delivery Format**
> record. **AI reasons; deterministic rules enforce the spec — so no invented value ever ships.**

---

## The problem

Industrial distributors hand over rows that look like this:

| Mfg_Part_Num | Part_Desc | E1_Brand | Unilog_Brand | DIB_Brand | Part_Manuf |
|---|---|---|---|---|---|
| `PDSH4816AF` | `PDSH4816AF Dishwasher SS - Display Only` | `-- Unbranded --` | `-- No Unilog Brand --` | `-- No DIB Brand --` | `Appliance Dealers Cooperative (APPDE)` |

Measured on Unilog's real **1,000-row sample**:

- **80%** of rows arrive with **no usable brand** (placeholder text).
- **9%** name a **distributor / buying co-op in the "manufacturer" field** — not the actual maker.
- Descriptions are **telegraphic** and full of trade abbreviations (`SS`, `Display Only`).

Each of these must become a full **252-column** record: correct taxonomy, extracted attributes,
five standardized descriptions, resolved brand/manufacturer, assets, and a trust score — a **42×
field expansion**. And the hard part isn't fluency, it's **trust**: the Solution Guide is blunt that
*"a fluent description made of invented values scores zero."* **We treat a guess as worse than a blank.**

## The idea: a hybrid engine

Most tools let an LLM *write the whole record* — fluent, confident, and often quietly wrong. We
invert control:

```
        Claude PROPOSES  ────►  Deterministic rules DISPOSE  ────►  ships  or  REVIEW QUEUE
   (forced JSON tool-call)      (pure Python: vocab, units,        (per-field
    every value + confidence     fractions, char limits, casing)    confidence + reason)
```

The LLM never writes a final field. It proposes values under a **forced JSON schema**; a pure,
rule-based layer then validates every one against controlled vocabularies and the written standard
**before it ships**. What can't be verified is **flagged, not fabricated**.

## The 9-stage pipeline

```
 RAW ROW (6 cols)
   │
   ▼ [1] INGEST & CLEAN     strip placeholders ("-- Unbranded --" → empty)
   ▼ [2] DE-DUPLICATE       collapse repeat SKUs (saves LLM spend)
   ├───────────── AI PROPOSES (Claude, forced JSON) ─────────────┐
   ▼ [3] CLASSIFY           → Classpath / Dept / Class / Fine     │
   ▼ [4] EXTRACT ATTRIBUTES → {label, value, uom}[]               │
   ▼ [5] ENRICH             from brand / MPN-prefix signals       │
   ├──────────── DETERMINISTIC RULES ENFORCE (pure Python) ───────┤
   ▼ [6] NORMALIZE          units → approved abbrev + space; decimals → fractions
   ▼ [7] BUILD 5 DESCRIPTIONS  at spec lengths / casings
   ▼ [8] RESOLVE ASSETS     URLs / images (flagged if unresolved)
   ▼ [9] VALIDATION GATE    per-field confidence → PASS or REVIEW QUEUE
   │
   ├──►  252-COLUMN RECORD  (auto-ship)
   └──►  HUMAN REVIEW QUEUE (specific reason per flagged field)
```

## Quickstart — zero setup

Pure Python **standard library only**. No `pip install`. No build step.

```bash
cd product-intelligence-engine
python3 run.py                 # enrich the full 1,000-row sample, write outputs/
```

Enable the Claude reasoning path by setting a key (optional — it degrades gracefully without one):

```bash
export ANTHROPIC_API_KEY=sk-ant-...
export UNILOG_MODEL=claude-sonnet-5      # optional; Haiku for cheaper volume
python3 run.py --limit 50
```

Outputs land in `outputs/`:

| File | What it is |
|---|---|
| `enriched_output.csv` | the **252-column** Delivery Format records (the deliverable) |
| `enriched_output.xlsx` | the same 252-column records as a workbook (pure-stdlib OOXML — values kept as text so part numbers keep leading zeros) |
| `qa_review_report.csv` | per-row confidence, review flag, and **specific reasons** |
| `duplicate_report.json` | duplicate SKU groups found before enrichment |
| `evaluation_summary.json` | ground-truth scoring + batch compliance metrics |

## Live prototype (web demo)

```bash
python3 app/server.py          # then open http://localhost:8000
```

Paste or pick a raw row and watch it explode into the 252-field record: the five description
formats, resolved identity/taxonomy, normalized attributes with approved UOMs, a per-field
**confidence gauge**, and the **review queue** with reasons. A badge shows whether the Claude path
or the deterministic fallback is active. (Set `ANTHROPIC_API_KEY` before launching for the AI path.)

## Accuracy & trust — how a wrong value is prevented from shipping

- **Rule-based validation gate.** Units, fractions, casing, and character limits are enforced by
  pure code — not another LLM — so hallucinations can't pass. `24in` → `24 in`; `120VOLTS` → `120 V`;
  inch decimals convert to the fractions buyers actually search via an **exact 1/64 table**
  (`50.25 in` → `50-1/4 in`).
- **Anti-hallucination prompt contract.** Claude must leave a field blank and lower its confidence
  rather than invent a value.
- **Per-field confidence (0–1)** across classpath, brand, manufacturer, attributes, descriptions.
- **Human-in-the-loop review queue.** Low-confidence fields route to review **with a specific,
  human-readable reason** — never silently guessed.
- **Anomaly detection.** Distributor-as-manufacturer and brand/product mismatches are caught and
  withheld. For `PDSH4816AF`, the "manufacturer" is a distributor co-op and the supplied brand
  mismatches the product — so the engine **withholds `MANUFACTURER_NAME` and flags exactly why**,
  instead of propagating a wrong value.

### Five descriptions, one product (each enforced to spec)

| Field | Rule | Example (PDSH4816AF, AI path) |
|---|---|---|
| `INVOICE_DESC` | ≤ 40 chars, ALL CAPS, compressed units | `DISHWASHER LEG 5 SST 120V 15A 50-1/4IN` (38) |
| `MOBILE_DESC` | 60–80 chars | `FRIGIDAIRE Dishwasher, Professional Series, PDSH4816AF, Leg Mount` |
| `SHORT_DESC` | title / listing line | `FRIGIDAIRE® Professional Series … Dishwasher …` |
| `LONG_DESC1` | full attribute formula | `FRIGIDAIRE® Dishwasher … 24 in W … 50-1/4 in Depth …` |
| `MARKETING_DESCRIPTION` | benefit-led prose | `A quiet, efficient built-in dishwasher …` |

## Results

Two honest numbers, because this repo can run in two modes:

**1. Deterministic floor (no API key — what `python3 run.py` produces here):**
1,000 rows in **~0.2 s**. **100%** `INVOICE_DESC` ≤40/CAPS compliance and **100%** unit-format
compliance **by construction**, on every row. Enrichment depth is intentionally low on this path
(brand/attributes need the reasoning step), so **993/1,000 rows are flagged for review rather than
guessed** — the anti-hallucination principle made visible.

**2. AI path, validated end-to-end (`tests/test_ai_path_mock.py`):**
Because the sandbox can't reach the live API, this test stubs *only* the network call with realistic
Claude drafts and runs the **real** pipeline (enrich → build → validate → score) against Unilog's
ground truth. Result: **8/16 key fields exact, 0.872 mean field similarity**, `INVOICE_DESC` for the
flagship row **exact**, and decimal→fraction / UOM enforcement proven firing on live-shaped model
output. Set a real key and `run.py` takes the same path on the full dataset.

## Scalability

- **Zero-dependency** pure-Python stdlib calling Claude over HTTPS — **runs anywhere**, no install.
- **Graceful degradation:** no key / API error → deterministic pass, same output contract, `ai_used=False`. **Never hard-fails.**
- **De-dup before spend:** repeat SKUs collapse before any model call.
- **Bounded, tiered cost:** one structured call per *unique* SKU; swap `claude-haiku-4-5` for volume.
- **Parallel & cacheable:** `ThreadPoolExecutor` over rows; every stage is idempotent and reprocessable.
- **Data-driven:** brand / UOM / taxonomy are lookups — drop in the real UniCat master, no code change.

## Repo layout

```
product-intelligence-engine/
├── run.py                     # batch runner → outputs/
├── app/server.py              # live web demo (stdlib http.server)
├── src/
│   ├── schema.py              # the 252 static headers (exact, immutable)
│   ├── lookups.py             # UOM map · 1/64 fraction table · brand master · distributor signals
│   ├── normalize.py           # deterministic spec-enforcement (the trust gate)
│   ├── llm_client.py          # zero-dep Claude client (urllib, forced tool-use, retries)
│   ├── ai_enrich.py           # the reasoning core: schema + anti-hallucination prompt
│   ├── pipeline.py            # 9-stage orchestrator → 252-col record + QA
│   └── evaluate.py            # ground-truth scoring + compliance report
├── tests/
│   ├── test_ai_path_mock.py   # AI path e2e (network stubbed) + ground-truth scoring
│   └── test_server_core.py    # web-demo request core
├── data/                      # input sample + ground-truth reference
├── docs/                      # deck content · video script · solution overview
└── outputs/                   # generated artifacts
```

## Tests

```bash
python3 tests/test_ai_path_mock.py     # AI path end-to-end (stubbed network) + scoring
python3 tests/test_server_core.py      # live-demo request core (render + enrich + error handling)
```

## Configuration

| Env var | Default | Purpose |
|---|---|---|
| `ANTHROPIC_API_KEY` | *(unset)* | enables the Claude reasoning path; unset → deterministic fallback |
| `UNILOG_MODEL` | `claude-sonnet-5` | model id (`claude-haiku-4-5-20251001` for cheaper volume) |
| `ANTHROPIC_BASE_URL` | Anthropic API | override for a gateway/proxy |
| `PORT` / `HOST` | `8000` / `0.0.0.0` | web-demo bind |

## Submission artifacts

- **Solution overview (≤2056 chars):** [`docs/SOLUTION_OVERVIEW.txt`](docs/SOLUTION_OVERVIEW.txt)
- **Slide-by-slide deck content:** [`docs/DECK_CONTENT.md`](docs/DECK_CONTENT.md)
- **Demo video script (3–4 min):** [`docs/VIDEO_SCRIPT.md`](docs/VIDEO_SCRIPT.md)
- **Architecture deep-dive:** [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)

## License

See [`LICENSE`](LICENSE).
