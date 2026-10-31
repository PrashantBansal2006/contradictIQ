# ContradictIQ — Product Requirements Document (PRD)

**Problem Statement:** PS 04 — Financial Intelligence & Evidence Investigation Platform
**Event:** Nexaura Prompt Battle (BSA, MNNIT) — 6-hour hackathon, 31 Oct 2026
**Version:** 1.0 | **Status:** Build-ready

---

## 1. One-line pitch

> **ContradictIQ is an evidence-first investigation workspace where AI *reads* financial documents but only deterministic code *judges* claims — every verdict is a traceable calculation linked to the exact passage or table cell it came from, and the system refuses to conclude when evidence is incomplete or not comparable.**

Core design rule (repeat this in the demo): **"The LLM proposes. The code disposes."**

---

## 2. Problem & why existing approaches fail

Financial researchers cross-check reports, spreadsheets and news articles. Typical failure modes:

| Failure mode | Real example | What naive tools do |
|---|---|---|
| Period confusion | Claim "revenue ₹920 cr" vs annual report "₹3,400 cr" | LLM flags a "contradiction" (false positive) |
| Scale/unit confusion | "₹3.4 bn" vs "₹340 crore" | Treated as different numbers |
| Rounding | "grew 18%" vs computed 17.6% | Flagged conflicting |
| Adjusted vs reported | "Adjusted EBITDA" vs "EBITDA" | Compared as equals |
| Restatements | Original vs restated figures | Silently picks one |
| Hallucinated explanation | LLM says "margin fell" with no calculation | Unverifiable |
| No audit trail | Conclusion changes, no one knows why | Lost history |

ContradictIQ is designed around **precision of contradiction detection** (low false-positive rate) and **traceability**, which are the two things the problem statement explicitly rewards.

---

## 3. Users

| Persona | Need | Key screens |
|---|---|---|
| **Researcher (primary)** | Verify claims in a report/news piece against filings | Workspace, Claims table, Verification detail |
| **Reviewer** | Challenge and sign off on findings | Comments, assignments, version history |
| **Judge / Auditor (read-only)** | Inspect whole investigation history | Judge Mode (read-only share link), Ledger timeline |

---

## 4. Product principles

1. **LLM proposes, code disposes.** AI may extract and explain; verdicts come from a deterministic rule engine.
2. **No evidence, no verdict.** Missing/incomparable evidence ⇒ `Inconclusive`, never a guess.
3. **Comparability before comparison.** Period, scope, currency, scale and accounting basis are checked *before* any number is compared.
4. **Every number has a receipt.** Each fact links to document → page → passage/cell → bbox.
5. **History is append-only.** Nothing is silently overwritten; the ledger is hash-chained.
6. **Fail gracefully.** Malformed data produces explained warnings, not crashes.
7. **Works without an LLM.** A rule-based extractor fallback guarantees the demo never dies on API failure.

---

## 5. Scope

### 5.1 In scope (MUST — maps to PS Basic Functionalities)

| PS Basic requirement | Our module | FR IDs |
|---|---|---|
| Investigation Management | Investigations CRUD + archive + status | FR-1.x |
| Document Upload (PDF/CSV, validation, metadata) | Upload & validation service | FR-2.x |
| Document Workspace | Docs list + viewer + extracted info panel | FR-3.x |
| Claim Management | Manual + AI-extracted claims | FR-4.x |
| Financial Verification (deterministic) | Metric registry + calc engine | FR-5.x |
| Evidence Comparison (Consistent/Conflicting/Inconclusive) | Comparability gate + verdict engine | FR-6.x |
| Evidence Linking | Evidence links + calc trace | FR-7.x |
| Investigation Dashboard | Dashboard | FR-8.x |
| Database storage | SQLite (SQLAlchemy) | NFR |

### 5.2 Advanced (SHOULD — maps to PS Advanced Functionalities)

| PS Advanced requirement | Our feature | FR IDs |
|---|---|---|
| Revisit saved investigations | Persisted state + ledger replay | FR-9.x |
| AI-assisted extraction | LLM structured extraction w/ grounding validation | FR-10.x |
| Highlight supporting passages | PDF/text viewer with bbox highlights | FR-11.x |
| Side-by-side comparison | Compare docs / periods view | FR-12.x |
| Comments, reviewers, collaboration | Comments, assignees, share | FR-13.x |
| Version history | Claim/conclusion versions + diff | FR-14.x |
| Downloadable report | HTML + Markdown (+ PDF via print) | FR-15.x |
| Evidence graph | Interactive graph (React Flow) | FR-16.x |
| Multi-agent (retrieval, numeric verification, criticism) | Retriever / Verifier / Skeptic | FR-17.x |
| Background jobs w/ status | Job queue + SSE progress | FR-18.x |

### 5.3 Brownie points — all mapped (see Section 9 for acceptance tests)

| Brownie point | Our answer |
|---|---|
| Quarterly vs annual not treated as contradiction | **Comparability Gate** + period algebra (Q1–Q4 → FY derivation) |
| Missing / malformed / inconsistent data handled gracefully | Validation pipeline, data-quality flags, `Inconclusive` reasons |
| Example where initial claim is disproved by documents | Seeded demo: "Revenue grew 25%" → computed 14.2% |
| Traceable calculations, not only AI explanations | Calculation Trace (formula, inputs, source refs, step values) |
| Prevent strong conclusions on incomplete/incomparable evidence | **Strong-Conclusion Guard** |
| Access control for private investigations & documents | Owner-scoped queries, JWT, role checks, signed read-only share tokens |
| Measure correctness + false-positive rate on labelled dataset | **In-app Eval page + CLI**, 60+ labelled cases, LLM-only baseline comparison |
| Judges inspect complete history | **Judge Mode** + hash-chained ledger timeline |

### 5.4 Out of scope

- OCR for scanned PDFs (flag as unsupported with clear message; stretch only)
- XBRL / SEC EDGAR live ingestion
- Multi-tenant org management, SSO
- Real-time multi-cursor collaboration

---

## 6. Glossary (shared vocabulary — use these exact words in UI and code)

| Term | Definition |
|---|---|
| **Investigation** | A container: title, description, status, documents, claims, findings, ledger |
| **Document** | Uploaded PDF/CSV with metadata, parsed pages/tables, and *source tier* |
| **Source tier** | Authority rank: `T1 audited annual/regulatory filing` > `T2 quarterly filing/results` > `T3 company press release` > `T4 news/third-party` |
| **Fact** | A normalized number extracted from a doc: `metric, value, unit, scale, currency, period, scope, basis, confidence, locator` |
| **Claim** | A statement under test, e.g. "Revenue grew 25% YoY in FY25". Structured as `metric, claim_type, value, period, scope, source_ref` |
| **Period** | Structured: `type (Q/H1/9M/FY/TTM), fiscal_year, quarter, start, end` |
| **Comparability Gate** | Checks that claim and evidence are about the same thing |
| **Calculation** | Deterministic formula execution with a step-by-step trace |
| **Verdict** | `Consistent` / `Conflicting` / `Inconclusive` (+ reason codes, severity) |
| **Finding** | Verdict + evidence links + calc trace + narrative + conclusion strength |
| **Ledger** | Append-only, hash-chained event log of everything that happened |

---

## 7. Functional requirements

Priority: **P0** = must ship, **P1** = should, **P2** = stretch.

### FR-1 Investigation management
| ID | Requirement | Pri | Acceptance criteria |
|---|---|---|---|
| FR-1.1 | Create investigation (title, description, status) | P0 | Appears in list; persisted after restart |
| FR-1.2 | View/edit title, description, status (`Open`, `In Review`, `Concluded`) | P0 | Edit writes ledger event |
| FR-1.3 | Archive / unarchive (soft delete) | P0 | Archived hidden by default, filterable |
| FR-1.4 | Private by default; only owner (and invited reviewers) access | P0 | Other user gets 404 on direct URL |

### FR-2 Document upload & validation
| ID | Requirement | Pri | Acceptance criteria |
|---|---|---|---|
| FR-2.1 | Upload PDF or CSV | P0 | Accepted types only; others rejected with message |
| FR-2.2 | Validate: magic bytes (not just extension), size ≤ 20 MB, PDF ≤ 200 pages, CSV ≤ 100k rows | P0 | Each violation returns a specific error code |
| FR-2.3 | Metadata: filename, size, SHA-256, page count, uploader, upload time, source tier (user-selectable), doc date, company, reporting entity | P0 | Visible in doc list; duplicate hash warns |
| FR-2.4 | Encrypted/corrupt/scanned PDF detected | P0 | Status `Failed` with human-readable reason; investigation unaffected |
| FR-2.5 | CSV schema sniffing: detect header row, delimiter, period columns, scale hints ("in crores") | P0 | Wide (periods as columns) and long (period as rows) layouts both handled |

### FR-3 Document workspace
| ID | Requirement | Pri | Acceptance criteria |
|---|---|---|---|
| FR-3.1 | List documents with processing status badge | P0 | `Queued → Parsing → Extracting → Ready / Failed` |
| FR-3.2 | Document detail: page text, extracted tables, extracted facts | P0 | Fact click jumps to its location |
| FR-3.3 | Data-quality panel (missing periods, unit ambiguity, duplicates, parse warnings) | P1 | Each warning has a code and explanation |

### FR-4 Claim management
| ID | Requirement | Pri | Acceptance criteria |
|---|---|---|---|
| FR-4.1 | Create claim manually via form: metric, claim type, value, period, entity, source ref | P0 | Validated against metric registry |
| FR-4.2 | Free-text claim → structured via parser (rule-based first, LLM assist) | P1 | Shows parsed structure for user confirmation |
| FR-4.3 | AI-extract claims from a document | P1 | Each extracted claim has verbatim quote + page; quote must exist in text (grounding check) |
| FR-4.4 | Claim states: `Draft → Extracted (needs confirmation) → Confirmed → Verified → Archived` | P0 | Only Confirmed claims are verified by default |
| FR-4.5 | Edit claim creates a new version (never overwrites) | P1 | Version list with diff |
| FR-4.6 | Supported claim types: `ABSOLUTE`, `GROWTH_YOY`, `GROWTH_QOQ`, `MARGIN`, `RATIO`, `DIRECTION` | P0 | Each has a registered formula |

### FR-5 Financial verification (deterministic)
| ID | Requirement | Pri | Acceptance criteria |
|---|---|---|---|
| FR-5.1 | Metric registry: revenue, cost of goods sold, gross profit, operating expenses, operating income, EBITDA, net income, total expenses | P0 | Synonym mapping (e.g., "Turnover", "Net Sales", "Total income from operations") |
| FR-5.2 | Derived metrics: revenue growth (YoY/QoQ), gross/operating/net margin, expense ratio, opex ratio | P0 | Formulas are pure functions with unit tests |
| FR-5.3 | Unit normalization: units, thousands, lakh, million, crore, billion; currency symbols | P0 | `₹340 cr == ₹3.4 bn` verified in tests |
| FR-5.4 | Period algebra: Q1+Q2+Q3+Q4 = FY; H1 = Q1+Q2; 9M = Q1+Q2+Q3 | P0 | Derived values labelled `DERIVED` with component trace |
| FR-5.5 | Calculation trace stored per verification: formula id, input fact ids, intermediate values, result, rounding | P0 | Rendered as step-by-step panel in UI |
| FR-5.6 | Tolerance based on **claim precision** (rounding-aware) | P0 | "18%" matches 17.6% and 18.4%; does not match 19.2% |

### FR-6 Evidence comparison
| ID | Requirement | Pri | Acceptance criteria |
|---|---|---|---|
| FR-6.1 | Comparability Gate checks: metric, period, period type, scope (consolidated/standalone/segment), currency, scale, basis (reported/adjusted), restated flag | P0 | Failure ⇒ `Inconclusive/NOT_COMPARABLE(<reason>)`, **never Conflicting** |
| FR-6.2 | Verdict engine (ordered rules in architecture §10) | P0 | Deterministic; same input ⇒ same output |
| FR-6.3 | Deviation severity: `Match`, `NearMiss` (probable rounding/restatement), `Material` | P1 | Shown beside verdict |
| FR-6.4 | Supporting vs opposing evidence list per claim | P0 | Each evidence item has stance: `supports/opposes/neutral/not_comparable` |
| FR-6.5 | Source disagreement handling: tier precedence; same-tier disagreement ⇒ `Inconclusive/SOURCE_DISAGREEMENT` with both shown | P1 | Demo case included |
| FR-6.6 | **Strong-Conclusion Guard**: the label "Disproved"/"Confirmed" requires deterministic inputs + traceable refs + no open warnings | P0 | Otherwise capped at "Indicative" or "Insufficient evidence" |

### FR-7 Evidence linking
| ID | Requirement | Pri | Acceptance criteria |
|---|---|---|---|
| FR-7.1 | Every finding links to: document, page, passage/table cell, reporting period, calculation id | P0 | Click opens viewer at highlighted location |
| FR-7.2 | Broken-link prevention: facts cannot be deleted while referenced (archive instead) | P1 | Attempt returns explanatory error |

### FR-8 Dashboard
| ID | Requirement | Pri | Acceptance criteria |
|---|---|---|---|
| FR-8.1 | Cards: documents (by status), claims (by state), findings (Consistent / Conflicting / Inconclusive), unresolved claims | P0 | Live counts |
| FR-8.2 | Investigation status + last activity | P0 | |
| FR-8.3 | Unresolved queue with reason codes ("Missing Q2 expense data") | P0 | Each row has a suggested next action |
| FR-8.4 | Data-quality summary | P1 | |

### FR-9 – FR-18 (Advanced)
| ID | Requirement | Pri |
|---|---|---|
| FR-9.1 | Revisit investigation: ledger timeline + "state as of event N" view | P1 |
| FR-10.1 | LLM extraction of claims, metrics, periods with JSON schema + grounding validation | P1 |
| FR-10.2 | Provider abstraction (Gemini / Groq / OpenAI-compatible / Ollama / Anthropic) + rule-based fallback | P0 |
| FR-11.1 | Highlight passages in viewer using stored bbox / char offsets | P1 |
| FR-12.1 | Side-by-side: two documents or two periods with aligned metrics | P1 |
| FR-13.1 | Comments on claims/findings; assign reviewer; reviewer approve/challenge | P1 |
| FR-14.1 | Version history for claims & conclusions with diff | P1 |
| FR-15.1 | Report: summary, findings, evidence refs, calc traces, unresolved items, methodology; HTML + MD download | P1 |
| FR-16.1 | Evidence graph: nodes (Claim, Metric, Fact, Document, Calculation, Conclusion), edges (extracted_from, computed_from, supports, opposes) | P1 |
| FR-17.1 | Agents: **Retriever** (finds candidate evidence), **Numeric Verifier** (calls calc tools only), **Skeptic** (looks for reasons the verdict could be wrong; may downgrade, never upgrade) | P2 |
| FR-18.1 | Background jobs for parsing/extraction/verification with progress (SSE) | P1 |

---

## 8. Non-functional requirements

| Area | Requirement |
|---|---|
| Performance | 20-page PDF parsed + facts extracted ≤ 30 s (no LLM) / ≤ 90 s (with LLM); verification of a claim ≤ 200 ms |
| Determinism | Verification engine has **no I/O, no randomness, no LLM calls**; 100% unit-tested |
| Reliability | LLM failure → fallback extractor + visible "AI unavailable" badge; app never white-screens |
| Security | JWT auth, owner-scoped queries, upload hardening, prompt-injection containment (document text is data), signed share tokens |
| Observability | Structured logs per job; ledger events for all state changes |
| Reproducibility | `docker compose up` or `make dev`; seed script creates demo data in < 10 s |
| Accessibility/UX | Keyboard navigable tables, color + icon + text for verdict (not color alone) |

---

## 9. Acceptance tests mapped to brownie points (demo-able)

| # | Test | Expected |
|---|---|---|
| B1 | Claim "Q3 revenue ₹920 cr is inconsistent with annual ₹3,400 cr" | `Inconclusive — NOT_COMPARABLE (quarter vs annual)`; if all 4 quarters exist → `DERIVED` FY = sum, then compare → `Consistent` |
| B2 | Upload CSV with missing Q2 expenses | Margin claim → `Inconclusive — MISSING_INPUT: operating_expenses Q2` |
| B3 | Press release "revenue grew 25% YoY"; filings show 14.2% | `Conflicting (Material)`, "Disproved" label allowed, trace shown |
| B4 | Two docs same tier disagree on net profit | `Inconclusive — SOURCE_DISAGREEMENT`, both highlighted |
| B5 | Value in "₹ crore" vs "$ million" without FX | `Inconclusive — CURRENCY_MISMATCH`, no verdict |
| B6 | LLM-extracted claim whose quote isn't in the document | Rejected automatically with `UNGROUNDED_EXTRACTION` |
| B7 | User B opens User A's investigation URL | 404; no data leak; test automated |
| B8 | Eval page | Shows accuracy, per-class precision/recall, **false-positive rate on Conflicting**, confusion matrix, LLM-only baseline comparison |
| B9 | Judge Mode link | Read-only; can open ledger, claims, versions, traces; cannot mutate |
| B10 | Edit a claim after verification | New version created; old finding marked `Superseded`; ledger shows both |

---

## 10. Success metrics (what we will *show*, not just claim)

| Metric | Target on our labelled set (≥ 60 cases) |
|---|---|
| Overall verdict accuracy | ≥ 90% |
| **False-positive rate on `Conflicting`** (flagged conflict but truth ≠ conflict) | ≤ 3% |
| Recall on true contradictions | ≥ 90% |
| Trap-case pass rate (quarter-vs-annual, scale, rounding, adjusted-vs-reported) | 100% |
| Traceability coverage (findings with ≥1 source ref + calc trace) | 100% |
| Ungrounded AI extractions reaching the verdict stage | 0 |

Baseline comparison: run the same cases through an **LLM-only judge** and show our pipeline's lower false-positive rate. This is the strongest single slide in the demo.

---

## 11. Demo dataset & scenario (fictional — no copyright issues)

**Company:** *Veridian Foods Ltd* (FY2025, ₹ crore). Generated by `scripts/generate_demo_data.py`.

| File | Tier | Content |
|---|---|---|
| `veridian_q1..q4_fy25.csv` (or one wide CSV) | T2 | Quarterly P&L; **Q2 expenses missing in a variant file** |
| `veridian_annual_report_fy25.pdf` | T1 | Annual P&L table, MD&A narrative, restated-prior-year note |
| `veridian_press_release_q4.pdf` | T3 | Claims: "Revenue grew 25%", "Net margin doubled" |
| `veridian_news_article.pdf` | T4 | Claims: "₹920 crore revenue shows collapse vs ₹3,400 crore" (trap) |
| `veridian_annual_report_restated.pdf` | T1 | Restated FY24 numbers (source disagreement) |

**Story arc for the 5-minute demo:**
1. Create investigation "Veridian press claims vs filings".
2. Upload docs → jobs run, status updates live.
3. AI extracts 6 claims; grounding check rejects 1 hallucinated claim (show it!).
4. Verify: 1 Consistent, 1 Conflicting (disproved), 1 trap → Inconclusive/derived-consistent, 1 missing data, 1 source disagreement.
5. Open the disproved finding → trace → highlighted passage in PDF → evidence graph.
6. Edit the claim → version history → ledger → hash verify.
7. Eval page: our FP rate vs LLM-only baseline.
8. Export report. Open Judge Mode link.

---

## 12. Differentiators (what judges won't see elsewhere)

1. **Comparability Gate** — explicit, explainable gate with reason codes.
2. **Indian-context unit algebra** (lakh/crore) alongside million/billion.
3. **Quote-grounding validator** for all AI extractions.
4. **Skeptic agent can only downgrade** — safety-by-design.
5. **Hash-chained ledger + Judge Mode** — tamper-evident audit.
6. **Built-in evaluation harness with LLM-only baseline** — evidence, not claims.
7. **Strong-Conclusion Guard** — the product tells you *how much* it is allowed to conclude.

---

## 13. Risks & mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| PDF table extraction is messy | Wrong facts | Deterministic CSV path for demo; PDF tables via pdfplumber + confidence + human confirm; never auto-verify low confidence |
| LLM API rate limit / outage | Demo failure | Provider abstraction, response cache keyed by (prompt hash), rule-based fallback, pre-warmed cache for demo docs |
| Scope creep in 6 h | Unfinished basics | Phase gates in `tasks.md`; cut-lines defined; basics complete by T+3:15 |
| Hallucinated numbers | Credibility | Grounding validator + number-in-trace checker for narratives |
| Frontend time sink | Ugly/slow UI | Component kit (shadcn/ui) + design.md owner decides; build screens in priority order |

---

## 13b. Assumptions

- Judges value correctness, traceability and false-positive control over raw feature count.
- A fictional-but-realistic dataset is acceptable if also labelled and reproducible; optionally add one real public filing as a bonus.
- Single-node SQLite is acceptable for a hackathon; architecture notes the Postgres path.
