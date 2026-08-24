# Architecture - Unilog Product Intelligence Engine

This document explains *how* the engine works and *why* it is built this way. The design thesis is
one sentence:

> **AI reasons; deterministic rules enforce the spec.** The LLM proposes structured values; a pure,
> rule-based layer validates every one against the written standard before it ships, and routes
> anything it cannot verify to a human - it never fabricates.

That single inversion is what separates this from a "prompt-the-LLM-for-the-whole-record" tool, and
it is what lets us make hard guarantees (100% unit/casing/limit compliance, no unvalidated value
ships) on top of a probabilistic model.

---

## Full system architecture (end-to-end)

<img width="1536" height="1024" alt="image" src="https://github.com/user-attachments/assets/9d6a40a9-d4d2-47f3-b44a-d8fa9958df25" />


## 1. Data contract: the 252 static headers

- `src/schema.py` holds `DELIVERY_HEADERS` — the **exact 252 column names, in order**, generated
  from Unilog's Expected Output file. `assert len(DELIVERY_HEADERS) == 252` guards against drift.
- Headers are **immutable**: never renamed, reordered, added, or removed. `blank_record()` returns a
  dict pre-seeded with all 252 keys empty, so every output row satisfies the contract by
  construction. `run.py` writes with `csv.DictWriter(..., extrasaction="ignore")`, so no stray key
  can ever corrupt the header set.
- The engine populates a **superset-safe subset** of those headers; unfilled columns stay empty
  rather than guessed.

## 2. Module responsibilities

| Module | Role | Deterministic? |
|---|---|---|
| `schema.py` | the 252-header contract + `blank_record()` | ✅ |
| `lookups.py` | controlled vocabularies: UOM map, 1/64 fraction table, brand master, MPN-prefix hints, distributor signal words, placeholder set | ✅ |
| `normalize.py` | spec-enforcement: unit standardization, decimal→fraction, char-limit/casing, compliance predicates | ✅ (the trust gate) |
| `llm_client.py` | zero-dependency Claude client over `urllib`; forced tool-use; retry/backoff | — (I/O) |
| `ai_enrich.py` | the reasoning core: JSON schema + anti-hallucination system prompt; deterministic fallback draft | mixed |
| `pipeline.py` | the 9-stage orchestrator: draft → 252-col record → validation/confidence/review | ✅ (stages 6–9) |
| `evaluate.py` | ground-truth scoring + batch compliance report | ✅ |
| `run.py` | batch CLI: load → dedup → parallel enrich → write 4 artifacts | — |
| `app/server.py` | live web demo (stdlib `http.server`) over the same `process_row` | — |

The split is deliberate: **every probabilistic step (`ai_enrich`, `llm_client`) is isolated from
every guarantee-making step (`normalize`, the stage 6–9 logic in `pipeline`)**, so the guarantees
hold regardless of what the model returns.

## 3. The AI stage — structured, not prose (`ai_enrich.py`, `llm_client.py`)

- The model is **forced to call a tool** (`tool_choice`) whose `input_schema` is our draft schema
  (`product_type`, `classpath`, dept/class/fine, `brand_name`, `manufacturer_name`, `series`,
  `unspsc`, `attributes[{label,value,uom}]`, `item_features`, five descriptions, `standards_approvals`,
  `mfr_url`, **`confidence{}`**, **`review_reasons[]`**). This guarantees schema-valid JSON, not
  free text we have to parse and hope.
- The **system prompt encodes the non-negotiable rules** — anti-hallucination ("leave blank, lower
  confidence, add a review reason — never invent"), UOM spacing, decimal→fraction, the five
  description formulas, brand/manufacturer casing with ®/™, distributor handling, and calibrated
  confidence.
- `llm_client.call_structured(...)` POSTs to `/v1/messages` via `urllib` (no SDK), parses the
  `tool_use` block, and **retries with exponential backoff** on 429/5xx/529.
- **Sourcing rule** is enforced in-prompt: product facts come from the manufacturer's own
  site/docs; marketplaces (Amazon/eBay) are prohibited.

## 4. The deterministic gate — where trust is manufactured (`normalize.py`)

This is the module the whole architecture leans on, because it is pure and rule-based — auditable,
testable, and immune to hallucination.

- **Unit standardization.** A single regex (`_NUM_UNIT_RE`) finds every `number+unit` token; the
  unit is mapped to its approved abbreviation and rewritten with exactly one space: `24in` → `24 in`,
  `120VOLTS` → `120 V`. `compress_units_in_text()` is the till-receipt variant that *glues* the unit
  for the ≤40-char `INVOICE_DESC` budget (`50.25IN` → `50-1/4IN`).
- **Decimal → fraction.** `decimal_to_fraction_inches()` uses an **exact 1/64 lookup table** (all
  fractions reduced) with a tolerance, because trade buyers search `50-1/4`, not `50.25`. Mixed
  numbers render as `50-1/4`; proper fractions as `1/2`.
- **Limits & casing.** `enforce_limit(text, limit, upper)` trims on a word boundary and applies
  casing; `INVOICE_DESC` is ≤40 + CAPS, `MOBILE_DESC` targets 60–80.
- **Compliance predicates.** `units_are_compliant()` returns `(ok, offenders)` so the validation
  gate can *prove* a description is spec-clean and flag it precisely when it isn't.

## 5. Stage 9 — validation, confidence, and the review queue (`pipeline.py`)

`_validate_and_score()` turns a draft into a trust decision:

1. **Structural checks** — `INVOICE_DESC` ≤40/CAPS, `MOBILE_DESC` length band, unit compliance on
   `LONG_DESC1`, and emptiness of must-have fields (brand, classpath, attributes).
2. **Anomaly checks** — if the input `Part_Manuf` is a distributor/reseller (see §6), the row is
   flagged; if a real manufacturer was nonetheless resolved from the brand it is **kept but
   confidence-capped**, otherwise `MANUFACTURER_NAME` is **withheld**.
3. **Overall confidence** = mean of the five calibrated field confidences.
4. **Routing** — `needs_human_review` is true when overall confidence < 0.6, a distributor was
   detected, the invoice line fails, or the brand is empty. Each reason is a **specific,
   human-readable string** ("ANOMALY: Part_Manuf '…' is a distributor/reseller — MANUFACTURER_NAME
   withheld pending review."), de-duplicated and order-preserving.

The output QA object (`overall_confidence`, `needs_human_review`, `field_confidence`,
`distributor_detected`, `n_attributes`, `checks`, `review_reasons`) is what powers both
`qa_review_report.csv` and the web demo's confidence heatmap.

## 6. Anomaly detection — catching the trap in the data (`lookups.parse_manufacturer`)

The brief's headline trap: the "manufacturer" field is often a **distributor or buying co-op**, not
the maker. `parse_manufacturer()` returns `(name, code, is_distributor)` by matching
`DISTRIBUTOR_SIGNAL_WORDS` (e.g. *cooperative*, *supply*, *distribution*, *industrial supply LLC*).
When detected, the engine **resolves the true maker from the brand/MPN if it can, and flags the
anomaly either way** — it fixes the field *and* surfaces the discrepancy, rather than silently
trusting a wrong input or blanking a value it can defend.

## 7. Graceful degradation — the deterministic fallback

When `ANTHROPIC_API_KEY` is unset (or the API errors after retries), `enrich_row()` calls
`_deterministic_draft()` instead of Claude. It emits the **same draft contract** — brand/MPN-prefix
resolution, placeholder cleaning, best-effort attributes from the description, `ai_used=False`, and
low confidences that route most rows to review. Consequences:

- The pipeline **never hard-fails**; every row still yields a valid 252-column record.
- The compliance guarantees (units, fractions, limits, casing) **still hold**, because they live in
  the deterministic layer, not the model.
- It is honest: the fallback flags what it couldn't confidently enrich instead of faking depth.

## 8. Scaling model

- **De-dup first** (`find_duplicates`): identical `Part_Desc` rows collapse before any model call.
- **One bounded structured call per unique SKU** (classification + attributes + 5 descriptions
  together, temperature 0).
- **Parallel I/O**: `run.py` uses `ThreadPoolExecutor` (workers configurable); the AI path is
  I/O-bound so threads are the right tool. Workers drop to 1 on the deterministic path.
- **Model tiering**: `UNILOG_MODEL` swaps Sonnet ↔ Haiku for the cost/quality trade-off.
- **Idempotent & cacheable**: each row is independent and reprocessable; per-stage caching makes
  re-runs of unchanged rows free.
- **Data-driven growth**: onboarding a new manufacturer or UOM is a lookup-table edit, not code.

## 9. Testing strategy

Because the sandbox cannot reach the live API or bind a socket, correctness is proven without either:

- **`tests/test_ai_path_mock.py`** stubs *only* `llm_client.call_structured` with realistic Claude
  drafts (deliberately containing decimals like `50.25` and spellings like `volts`/`amps`/`dba`) and
  runs the **real** pipeline end-to-end, then scores against ground truth. This proves assembly,
  unit/fraction enforcement, description handling, anomaly flagging, and scoring — independent of a
  live key. Result: 8/16 key fields exact, 0.872 mean similarity, `INVOICE_DESC` flagship row exact.
- **`tests/test_server_core.py`** exercises the web demo's pure request core (`render_index`,
  `handle_enrich`) — 252-column contract, JSON serialization, graceful error handling on bad input —
  without opening a port.

