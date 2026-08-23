# DEMO VIDEO SCRIPT — Unilog Product Intelligence Engine ([TEAM NAME])

**Target length:** 3 min 30 sec · **Format:** screen recording + voiceover.
**Golden thread:** one messy 6-field row (`PDSH4816AF`) → a full, trustworthy 252-column record,
with confidence scores and a human-review flag.

**Recording assets to have open (all real, in the repo):**
`data/input_sample_1000.csv` · a terminal at `product-intelligence-engine/` ·
`outputs/enriched_output.csv` · `outputs/qa_review_report.csv` · `outputs/evaluation_summary.json`
(optionally the browser record-view for the pretty shots). Use a spreadsheet or the web view so
the 252 columns are legible on screen.

Legend — **SCENE:** what's on screen · **VO:** what you say.

---

### 0:00–0:18 — The problem (hook)
**SCENE:** Full-screen the raw input row in the spreadsheet, cursor highlighting each cell:
`PDSH4816AF | "PDSH4816AF Dishwasher SS - Display Only" | -- Unbranded -- | -- No Unilog Brand -- | -- No DIB Brand -- | Appliance Dealers Cooperative (APPDE)`.
**VO:** "This is what industrial distributors actually hand you: a part number, a cryptic
half-sentence, and brand fields that just say *Unbranded*. On Unilog's real sample, **80% of
rows arrive with no brand**, and **9% name a distributor where the manufacturer should be**.
Unilog needs this to become a complete, search-ready, 252-column product record."

---

### 0:18–0:38 — The trap, and our principle
**SCENE:** Title card: **"AI reasons. Deterministic rules enforce the spec."** Below it, small text:
*"A fluent description made of invented values scores zero." — Solution Guide.*
**VO:** "The easy move is to let an AI just *write* the whole record. It'll sound great — and quietly
invent voltages and dimensions that don't exist. The guide is blunt: invented values score zero. So
we built a **hybrid engine**. Claude *proposes* every value; a deterministic rules layer *validates*
each one against controlled vocabularies and character limits **before it ships**. A guess is treated
as worse than a blank."

---

### 0:38–0:52 — One command, full run
**SCENE:** Terminal. Type and run: `python3 run.py`. Show the live log scrolling —
`loaded 1000 rows`, `AI path: ON (claude-sonnet-5)`, `duplicate groups: …`, `enriched 1000/1000`,
then `=== EVALUATION SUMMARY ===`.
**VO:** "One command, no setup — it's pure Python standard library, no pip install. It runs the full
thousand-row sample end to end, in parallel, and writes the 252-column output, a QA review report,
and an evaluation summary."

---

### 0:52–1:45 — The explosion: 6 fields → 252
**SCENE:** Open `enriched_output.csv` (spreadsheet or web record-view), filter to `Mfg_Part_Num = PDSH4816AF`.
Slowly scroll the record, pausing on each group. Use call-out boxes as each appears:
- **Taxonomy:** `Classpath = Appliances & Consumer Electronics>Kitchen Appliances>Built-In Dishwashers`
- **Brand:** `BRAND_NAME = FRIGIDAIRE®`
- **Attributes:** voltage / amperage / wash cycles / material / size as `{label, value, uom}`
- **The 5 descriptions**, stacked:
  - `INVOICE_DESC = DISHWASHER LEG 5 SST 120V 15A 50-1/4IN`  ← call-out: **38 chars, ALL CAPS**
  - `MOBILE_DESC` (60–80 chars) · `SHORT_DESC` (title) · `LONG_DESC1` (full) · `MARKETING_DESCRIPTION`
**VO:** "Watch six fields explode into two hundred and fifty-two. The engine classifies it into the
dishwasher taxonomy, resolves the real brand — Frigidaire — and extracts the attributes hidden in
that cryptic string. Then it writes the **same product five different ways**, each to spec: a
forty-character all-caps invoice line, a sixty-to-eighty-character mobile title, a full long
description, and marketing copy."
**SCENE (zoom):** Highlight `50-1/4IN` inside INVOICE_DESC; briefly show a spec sheet value `50.25`.
**VO:** "And look closely — the source spec says fifty-point-two-five inches, but the record says
**fifty and one-quarter**. Industrial buyers search fractions, not decimals, so an exact
one-sixty-fourth table converts every measurement. Units are normalized too — approved abbreviation,
single space. That's the deterministic layer doing its job."

---

### 1:45–2:35 — Trust: confidence + the anomaly catch
**SCENE:** Open `qa_review_report.csv`. Show the header row, then the `PDSH4816AF` row; expand the
`review_reasons` cell so it's readable.
**VO:** "Now the part that makes this trustworthy. Every field carries a confidence score, and this
row is flagged for human review — not silently guessed."
**SCENE (call-out on the reason text):** highlight
`distributor_detected = True` and the reason:
*"ANOMALY: Part_Manuf 'Appliance Dealers Cooperative' is a distributor/reseller, not a manufacturer —
MANUFACTURER_NAME withheld pending review."*
**VO:** "The engine noticed that the so-called manufacturer — *Appliance Dealers Cooperative* — is
actually a distributor co-op. On top of that, the reference data lists the maker as *Rheem
Manufacturing* — a water-heater company — on a *Frigidaire dishwasher*. That's a real
brand-to-product mismatch. Instead of propagating a wrong value, the engine **withholds it and tells
a human exactly why.** This is the anomaly the guide says to catch — not reproduce."
**SCENE:** Scroll to show other flagged rows with distributor reasons (e.g. *Jam Industrial Supply LLC*),
so it's clearly systematic, not a one-off.
**VO:** "And it's systematic — every distributor-as-manufacturer row across the sample gets the same
treatment, with its own reason."

---

### 2:35–3:00 — Accuracy, compliance & scale
**SCENE:** Open `evaluation_summary.json`; highlight the `compliance` block and the ground-truth scoring block.
**VO:** "We don't just claim accuracy, we measure it. The harness scores every field against Unilog's
ground-truth rows, and reports compliance across the whole batch. Character-limit and casing
compliance, and approved-unit formatting, are **one hundred percent — by construction**, because the
rules layer guarantees them on every row. It also reports attribute fill-rate, brand and classpath
coverage, and exactly how many rows were auto-shipped versus flagged."
**SCENE:** Quick cut to a diagram or bullet overlay: `de-dup → bounded per-row cost → parallel → cacheable`.
**VO:** "It scales the way an enterprise catalog needs: de-duplication collapses repeat SKUs before we
ever pay for a model call, cost per row is bounded, and every stage is parallel and cacheable."

---

### 3:00–3:18 — Runs anywhere (graceful degradation)
**SCENE:** Terminal. Run `unset ANTHROPIC_API_KEY; python3 run.py --limit 15`. Show the log line
`AI path: OFF — deterministic fallback` and that it still writes a valid 252-column file.
**VO:** "And if there's no API key, or the network's down? It doesn't crash. It falls back to a
deterministic pass with the exact same output contract — still a valid, spec-compliant record. It
runs anywhere."

---

### 3:18–3:30 — Close
**SCENE:** Closing card — **"Unilog Product Intelligence Engine · [TEAM NAME]"** with four tags:
*Innovation · Accuracy · Quality · Scalability*, plus the GitHub / demo links.
**VO:** "The Unilog Product Intelligence Engine: AI reasons, deterministic rules enforce the spec, and
every field is either validated or flagged. No invented value ever ships. Thanks for watching."

---

**Editing notes**
- Keep cursor movement slow on the 252-column scroll (0:52–1:45) — that reveal is the emotional peak; let it breathe.
- Pre-stage the AI-path run so the on-camera `python3 run.py` shows realistic timing; if recording offline, narrate over the deterministic run and show a pre-captured AI-path `evaluation_summary.json`.
- Hard-cut between the 6-field input and the 252-field output to sell the "explosion".
- Total VO word budget ≈ 470–500 words for a comfortable 3:30 pace.
