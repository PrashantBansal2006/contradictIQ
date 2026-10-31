# ContradictIQ — Brownie Acceptance Tests (B1–B10)

This document tracks the acceptance checklist for the brownie-point features and core validation edge cases defined in `dev/prd (2).md §9` and `dev/tasks.md §5`. These tests are required for demo readiness, auditability, and hackathon evaluation scoring.

---

## Acceptance Checklist Summary

- [ ] **B1: Quarter vs. Annual Handling (Comparability Gate & Derived FY)**
- [ ] **B2: Missing/Malformed Data Graceful Handling (`MISSING_INPUT`)**
- [ ] **B3: Disproved Claim (Material Contradiction with Provenance Trace)**
- [ ] **B4: Source Disagreement (Conflicting Evidence from Equal-Tier Documents)**
- [ ] **B5: Currency Mismatch (Cross-Currency Guard Without FX)**
- [ ] **B6: Grounding Validator (Hallucination & Ungrounded Claim Rejection)**
- [ ] **B7: Access Control & Data Isolation (Owner-Scoped 404)**
- [ ] **B8: Evaluation Harness & Metrics Page (Accuracy, FP Rate, Baseline Comparison)**
- [ ] **B9: Judge Mode (Auditor Read-Only Access via Share Token)**
- [ ] **B10: Claim Versioning & Ledger Auditability (Superseded Findings & Hash Chain)**

---

## Detailed Test Specifications

### B1: Quarter vs. Annual Handling (Comparability Gate & Derived FY)
* **Objective:** Verify that the engine prevents invalid direct comparisons between quarterly and annual metrics, but automatically derives full-year figures when all four quarters are present.
* **Reference:** `prd §9 (B1)`, `architecture §10.1`, `tasks §5.1`
* **Test Case 1 (Direct Mismatch):**
  - **Input Claim:** "Q3 revenue ₹920 cr is inconsistent with annual revenue ₹3,400 cr"
  - **Expected Outcome:** Verdict `Inconclusive`, reason code `NOT_COMPARABLE (quarter vs annual)`. No conflict flag raised; system explains periodicity mismatch.
- [ ] **Checklist Item B1.1:** Direct quarter vs. annual comparison without all quarters returns `Inconclusive: NOT_COMPARABLE`.
* **Test Case 2 (Derived FY Sum):**
  - **Input:** Documents contain Q1 (₹800 cr), Q2 (₹850 cr), Q3 (₹920 cr), Q4 (₹830 cr) revenue.
  - **Expected Outcome:** Verification engine marks metric as `DERIVED` (`Q1 + Q2 + Q3 + Q4 = ₹3,400 cr`). Comparison against annual ₹3,400 cr returns `Consistent`.
  - **Traceability:** Calculation trace stepper lists all four component facts with locators and marks conclusion strength as `Indicative` (due to derived value).
- [ ] **Checklist Item B1.2:** Derived annual sum computes accurately and traces back to component quarters.

---

### B2: Missing/Malformed Data Graceful Handling
* **Objective:** Ensure that missing data or malformed inputs do not crash the system (no unhandled 500s) and produce explicit, typed missing input warnings.
* **Reference:** `prd §9 (B2)`, `architecture §6`, `tasks §5.2`
* **Test Input:** Upload CSV or document with missing Q2 operating expenses; submit an operating margin claim for FY/H1.
* **Expected Outcome:**
  - Finding returns `Inconclusive — MISSING_INPUT: operating_expenses Q2`.
  - Data-quality warnings surfaced in document panel ("Missing period: Q2").
  - Upload of malformed files (empty PDF, renamed `.exe`, corrupt CSV) returns standard error response `{ "error": { "code": "INVALID_FORMAT", "message": "..." } }` with HTTP 400/422.
- [ ] **Checklist Item B2.1:** System returns typed `MISSING_INPUT` with exact missing metric and period name.
- [ ] **Checklist Item B2.2:** Uploading invalid/empty/corrupt files fails gracefully with standard structured error payload.

---

### B3: Disproved Claim (Material Contradiction with Provenance Trace)
* **Objective:** Verify end-to-end detection of a material factual contradiction, triggering the "Disproved" conclusion label under the Strong-Conclusion Guard.
* **Reference:** `prd §9 (B3)`, `architecture §10.2`, `architecture §11`, `tasks §5.3`
* **Test Input:**
  - Document 1 (Press Release): "Revenue grew 25% YoY in FY24."
  - Document 2 (Audited Annual Report): FY23 revenue = ₹1,000 cr, FY24 revenue = ₹1,142 cr (actual growth = 14.2%).
* **Expected Outcome:**
  - Calculated YoY growth: `(1142 - 1000) / 1000 = 14.2%`.
  - Difference exceeds relative tolerance (14.2% vs 25% > tolerance).
  - Verdict: `Conflicting (Severity: Material)`.
  - Strong-Conclusion Guard grants label: **Disproved** (provenance from audited table + locator available).
  - Trace stepper shows: step 1 (extract inputs), step 2 (formula `(v_t - v_prev)/v_prev`), step 3 (comparison vs claim value).
- [ ] **Checklist Item B3.1:** Material discrepancy classified as `Conflicting` with severity `Material`.
- [ ] **Checklist Item B3.2:** Guard assigns `Disproved` label when provenance requirements (table/CSV, locators) are satisfied.
- [ ] **Checklist Item B3.3:** Trace stepper and document passage highlights link directly to source facts.

---

### B4: Source Disagreement (Conflicting Evidence from Equal-Tier Documents)
* **Objective:** Correctly flag ambiguity when two authoritative sources within the same hierarchy tier provide differing figures for the same metric and period.
* **Reference:** `prd §9 (B4)`, `architecture §10.1`, `tasks §5.4`
* **Test Input:** Two statutory filings (e.g. initial filing vs. restated annual report) list different net profit figures for FY24 (₹150 cr vs ₹135 cr).
* **Expected Outcome:**
  - Verdict: `Inconclusive — SOURCE_DISAGREEMENT`.
  - UI highlights both conflicting source passages side-by-side.
  - System refuses to pick a winner without human reviewer confirmation or restatement flag.
- [ ] **Checklist Item B4.1:** Conflicting facts from same-tier documents produce `Inconclusive: SOURCE_DISAGREEMENT`.
- [ ] **Checklist Item B4.2:** Both source passages and locators are exposed in the evidence panel for audit review.

---

### B5: Currency Mismatch (Cross-Currency Guard Without FX)
* **Objective:** Guard against erroneous comparisons between amounts reported in differing currencies without an authenticated FX exchange rate.
* **Reference:** `prd §9 (B5)`, `architecture §10.1`, `architecture §10.2`
* **Test Input:** Claim asserts consistency between ₹3,400 crore and $400 million without an FX rate supplied.
* **Expected Outcome:**
  - Comparability gate triggers currency mismatch check.
  - Verdict: `Inconclusive — CURRENCY_MISMATCH`.
  - System explicitly states that values cannot be verified without a verified exchange rate for the period.
- [ ] **Checklist Item B5.1:** Cross-currency comparison without FX rate is rejected with `CURRENCY_MISMATCH`.

---

### B6: Grounding Validator (Hallucination & Ungrounded Claim Rejection)
* **Objective:** Ensure no AI-extracted claim or fact enters the database unless its text quote and numeric tokens are verified verbatim against source document character offsets.
* **Reference:** `prd §9 (B6)`, `architecture §6`, `tasks §2.9`
* **Test Input:** Inject an LLM extraction output containing a fabricated claim quote or numeric value not present in the document text.
* **Expected Outcome:**
  - Grounding validator executes before database write.
  - Substring search / token check fails.
  - System rejects extraction with error code `UNGROUNDED_EXTRACTION`.
  - No ungrounded claim is persisted to the investigation.
- [ ] **Checklist Item B6.1:** Extracted claims with invalid/missing quotes fail grounding validation.
- [ ] **Checklist Item B6.2:** Rejected claims emit `UNGROUNDED_EXTRACTION` and are excluded from verification.

---

### B7: Access Control & Data Isolation (Owner-Scoped 404)
* **Objective:** Enforce strict tenant/user isolation across all investigation endpoints, preventing information disclosure through URL enumeration.
* **Reference:** `prd §9 (B7)`, `architecture §19`, `tasks §3.3`, `tasks §5.6`
* **Test Input:** User B authenticates with valid credentials and requests `GET /api/investigations/{id}` owned by User A.
* **Expected Outcome:**
  - Backend returns `404 Not Found` (never `403 Forbidden` to avoid confirming the existence of resource ID).
  - No metadata, titles, or document details are leaked in the response body.
  - Automated API test confirms access isolation across all routes (`/documents`, `/claims`, `/findings`, `/ledger`).
- [ ] **Checklist Item B7.1:** Unauthorized access returns strict HTTP 404.
- [ ] **Checklist Item B7.2:** Automated test suite validates owner isolation across all CRUD routes.

---

### B8: Evaluation Harness & Metrics Page
* **Objective:** Demonstrate quantitative verification performance, benchmarked against an LLM-only baseline across a curated test suite.
* **Reference:** `prd §9 (B8)`, `prd §10`, `architecture §14`, `tasks §5.7`, `tasks §5.8`
* **Test Input:** Execute `python scripts/run_eval.py` against `dataset.jsonl` (≥ 60 cases).
* **Expected Outcome:**
  - Overall verdict accuracy ≥ 90%.
  - False-positive rate on `Conflicting` verdict ≤ 3% (critical judging requirement).
  - Recall on true contradictions ≥ 90%.
  - 100% pass rate on trap cases (quarter vs annual, currency mismatch, rounding).
  - Eval page in UI displays confusion matrix, precision/recall per class, and direct comparison table vs LLM-only baseline.
- [ ] **Checklist Item B8.1:** Eval harness executes cleanly and generates structured metrics.
- [ ] **Checklist Item B8.2:** False positive rate on `Conflicting` meets ≤ 3% threshold.
- [ ] **Checklist Item B8.3:** UI Eval page renders confusion matrix and LLM baseline comparison table.

---

### B9: Judge Mode (Auditor Read-Only Access via Share Token)
* **Objective:** Provide a zero-friction, read-only view for judges, auditors, and external stakeholders to verify claims and inspect evidence without account registration.
* **Reference:** `prd §9 (B9)`, `architecture §19`, `tasks §5.6`
* **Test Input:** Generate a share token for an investigation; open the share link in an incognito / unauthenticated browser session.
* **Expected Outcome:**
  - UI enters "Judge Mode" (prominent banner: "Judge Mode — Read Only").
  - Viewer can inspect all documents, facts, claims, calculation traces, and ledger timeline.
  - All mutating controls (upload, edit claim, verify, delete) are hidden or disabled.
  - Any mutating API request using the share token returns HTTP 403 / 401.
- [ ] **Checklist Item B9.1:** Unauthenticated user with share token can view full investigation.
- [ ] **Checklist Item B9.2:** All mutation actions are blocked in both UI and backend API.

---

### B10: Claim Versioning & Ledger Auditability
* **Objective:** Ensure immutable, tamper-evident audit history when claims are edited or re-verified.
* **Reference:** `prd §9 (B10)`, `architecture §5`, `architecture §11`, `tasks §3.9`, `tasks §5.9`, `tasks §5.10`
* **Test Input:** Edit an existing verified claim (e.g. change claimed value or period), then re-run verification.
* **Expected Outcome:**
  - New claim version `v2` is created; `v1` remains preserved.
  - Previous finding associated with `v1` is transitioned to `Superseded`.
  - Ledger service appends `CLAIM_UPDATED` and `VERIFICATION_RUN` events with SHA-256 hash chaining (`prev_event_hash` matches previous entry).
  - UI History tab renders timeline, version diff, and green "Ledger Verified" integrity badge.
  - Tampering test (modifying a ledger row in DB) causes integrity check to return invalid.
- [ ] **Checklist Item B10.1:** Editing a verified claim generates a new version and marks old findings `Superseded`.
- [ ] **Checklist Item B10.2:** Ledger maintains cryptographic hash chain (`prev_hash`).
- [ ] **Checklist Item B10.3:** UI shows version diff and verified ledger integrity badge.

---

## Verification Execution Log

| Test ID | Status | Automated Test Path / Command | Owner | Last Verified | Notes |
|---|---|---|---|---|---|
| B1 | Pending | `pytest backend/tests/core/test_comparability.py -k test_quarter_vs_annual` | A | | |
| B2 | Pending | `pytest backend/tests/core/test_missing_data.py` | B+D | | |
| B3 | Pending | `pytest backend/tests/core/test_verdict.py -k test_disproved_claim` | A+D | | |
| B4 | Pending | `pytest backend/tests/core/test_comparability.py -k test_source_disagreement` | A+D | | |
| B5 | Pending | `pytest backend/tests/core/test_comparability.py -k test_currency_mismatch` | A | | |
| B6 | Pending | `pytest backend/tests/ingest/test_grounding.py` | B | | |
| B7 | Pending | `pytest backend/tests/api/test_auth_isolation.py` | A+D | | |
| B8 | Pending | `python backend/eval/run_eval.py` | D | | |
| B9 | Pending | `pytest backend/tests/api/test_share_tokens.py` | A+C | | |
| B10 | Pending | `pytest backend/tests/services/test_ledger.py` | A+C | | |

