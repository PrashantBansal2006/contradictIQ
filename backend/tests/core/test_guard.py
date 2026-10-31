"""Tests for Strong-Conclusion Guard in guard.py (Task 1.8).

Tests:
- Confirmed: Consistent + Match + clean provenance + clean doc
- Disproved: Conflicting + Material + clean provenance + clean doc
- Indicative: Capped due to NearMiss severity
- Indicative: Capped due to unconfirmed LLM/regex extraction
- Indicative: Capped due to missing document locator
- Indicative: Capped due to derived value across periods
- Indicative: Capped due to open document quality warnings
- Insufficient: Inconclusive from missing input, comparability, or low confidence
- Verification of explicit cap_reasons output
"""

from decimal import Decimal
import pytest

from app.core.guard import (
    ConclusionStrength,
    GuardResult,
    apply_guard,
    has_valid_locator,
)
from app.core.verdict import (
    Severity,
    VerdictOutcome,
    VerdictType,
)


class TestStrongConclusionGuard:
    # -----------------------------------------------------------------------
    # Confirmed Label Tests
    # -----------------------------------------------------------------------

    def test_guard_confirmed_success(self):
        fact = {
            "id": "fact_rev_25",
            "document_id": "doc_annual_25",
            "method": "table",
            "confirmed": True,
            "locator": {"page": 42, "table_id": "tbl_income", "row": 1, "col": 2},
        }
        outcome = VerdictOutcome(
            verdict=VerdictType.CONSISTENT,
            severity=Severity.MATCH,
            calc_value=Decimal("3400"),
            claim_value=Decimal("3400"),
            input_facts=[fact],
            derived=False,
            gate_clean=True,
        )

        res = apply_guard(outcome)
        assert res.strength == ConclusionStrength.CONFIRMED
        assert res.is_capped is False
        assert len(res.cap_reasons) == 0

    # -----------------------------------------------------------------------
    # Disproved Label Tests
    # -----------------------------------------------------------------------

    def test_guard_disproved_success(self):
        f1 = {
            "id": "fact_1",
            "document_id": "doc_1",
            "method": "table",
            "locator": {"page": 10, "bbox": [10.0, 20.0, 100.0, 50.0]},
        }
        f2 = {
            "id": "fact_2",
            "document_id": "doc_2",
            "method": "csv",
            "locator": {"row": 5, "col": 3},
        }
        outcome = VerdictOutcome(
            verdict=VerdictType.CONFLICTING,
            severity=Severity.MATERIAL,
            calc_value=Decimal("14.2"),
            claim_value=Decimal("25.0"),
            deviation=Decimal("10.8"),
            input_facts=[f1, f2],
            derived=False,
            gate_clean=True,
        )

        res = apply_guard(outcome)
        assert res.strength == ConclusionStrength.DISPROVED
        assert res.is_capped is False
        assert len(res.cap_reasons) == 0

    # -----------------------------------------------------------------------
    # Indicative Label & Cap Reason Tests
    # -----------------------------------------------------------------------

    def test_guard_capped_to_indicative_by_near_miss(self):
        f = {
            "id": "fact_1",
            "method": "table",
            "locator": {"page": 1},
        }
        outcome = VerdictOutcome(
            verdict=VerdictType.CONFLICTING,
            severity=Severity.NEAR_MISS,
            calc_value=Decimal("18.2"),
            claim_value=Decimal("18.0"),
            deviation=Decimal("0.2"),
            input_facts=[f],
            derived=False,
            gate_clean=True,
        )

        res = apply_guard(outcome)
        assert res.strength == ConclusionStrength.INDICATIVE
        assert res.is_capped is True
        assert any("NearMiss" in r for r in res.cap_reasons)

    def test_guard_capped_by_unconfirmed_llm_method(self):
        f = {
            "id": "fact_ai_1",
            "method": "llm",
            "confirmed": False,
            "locator": {"page": 5, "char_span": [100, 150]},
        }
        outcome = VerdictOutcome(
            verdict=VerdictType.CONSISTENT,
            severity=Severity.MATCH,
            calc_value=Decimal("100"),
            claim_value=Decimal("100"),
            input_facts=[f],
            derived=False,
            gate_clean=True,
        )

        res = apply_guard(outcome)
        assert res.strength == ConclusionStrength.INDICATIVE
        assert res.is_capped is True
        assert any("probabilistic 'llm'" in r for r in res.cap_reasons)

    def test_guard_capped_by_unconfirmed_regex_method(self):
        f = {
            "id": "fact_regex_1",
            "method": "regex",
            "confirmed": False,
            "locator": {"page": 2, "quote": "revenue grew 20%"},
        }
        outcome = VerdictOutcome(
            verdict=VerdictType.CONFLICTING,
            severity=Severity.MATERIAL,
            calc_value=Decimal("10"),
            claim_value=Decimal("20"),
            input_facts=[f],
            derived=False,
            gate_clean=True,
        )

        res = apply_guard(outcome)
        assert res.strength == ConclusionStrength.INDICATIVE
        assert res.is_capped is True
        assert any("probabilistic 'regex'" in r for r in res.cap_reasons)

    def test_guard_capped_by_missing_locator(self):
        f = {
            "id": "fact_no_loc",
            "method": "table",
            "confirmed": True,
            "locator": {},  # Empty locator
        }
        outcome = VerdictOutcome(
            verdict=VerdictType.CONSISTENT,
            severity=Severity.MATCH,
            calc_value=Decimal("50"),
            claim_value=Decimal("50"),
            input_facts=[f],
            derived=False,
            gate_clean=True,
        )

        res = apply_guard(outcome)
        assert res.strength == ConclusionStrength.INDICATIVE
        assert res.is_capped is True
        assert any("lacks document physical locator" in r for r in res.cap_reasons)

    def test_guard_capped_by_derived_facts(self):
        f = {
            "id": "fact_derived_fy",
            "method": "table",
            "confirmed": True,
            "locator": {"page": 10},
        }
        outcome = VerdictOutcome(
            verdict=VerdictType.CONSISTENT,
            severity=Severity.MATCH,
            calc_value=Decimal("400"),
            claim_value=Decimal("400"),
            input_facts=[f],
            derived=True,  # Derived across quarters
            gate_clean=True,
        )

        res = apply_guard(outcome)
        assert res.strength == ConclusionStrength.INDICATIVE
        assert res.is_capped is True
        assert any("derived algebraically" in r for r in res.cap_reasons)

    def test_guard_capped_by_document_quality_warnings(self):
        f = {
            "id": "fact_warned",
            "document_id": "doc_suspect_pdf",
            "method": "table",
            "confirmed": True,
            "locator": {"page": 15},
        }
        outcome = VerdictOutcome(
            verdict=VerdictType.CONFLICTING,
            severity=Severity.MATERIAL,
            calc_value=Decimal("100"),
            claim_value=Decimal("200"),
            input_facts=[f],
            derived=False,
            gate_clean=True,
        )

        doc_warnings = {
            "doc_suspect_pdf": ["SUM_MISMATCH", "UNPARSEABLE_ROW_CELL"],
        }
        res = apply_guard(outcome, document_warnings=doc_warnings)
        assert res.strength == ConclusionStrength.INDICATIVE
        assert res.is_capped is True
        assert any("open data quality issues" in r for r in res.cap_reasons)

    # -----------------------------------------------------------------------
    # Insufficient Evidence Label Tests
    # -----------------------------------------------------------------------

    def test_guard_insufficient_for_inconclusive_verdicts(self):
        inconclusive_cases = [
            ("MISSING_INPUT", ["Required Q4 fact not found"]),
            ("NOT_COMPARABLE", ["Currency mismatch: INR vs USD"]),
            ("SOURCE_DISAGREEMENT", ["Conflicting figures in same-tier documents"]),
            ("LOW_CONFIDENCE_EXTRACTION", ["Confidence 0.50 below threshold"]),
            ("UNDEFINED_GROWTH_BASE", ["Base period was negative"]),
            ("ZERO_CHANGE", ["Direction delta is zero"]),
        ]

        for code, reasons in inconclusive_cases:
            outcome = VerdictOutcome(
                verdict=VerdictType.INCONCLUSIVE,
                reason_code=code,
                reasons=reasons,
                rule_triggered="R2",
            )
            res = apply_guard(outcome)
            assert res.strength == ConclusionStrength.INSUFFICIENT
            assert res.is_capped is True
            assert any(code in r for r in res.cap_reasons)

    # -----------------------------------------------------------------------
    # Provenance Locator Validator Helper Test
    # -----------------------------------------------------------------------

    def test_has_valid_locator(self):
        assert has_valid_locator({"locator": {"page": 1}}) is True
        assert has_valid_locator({"locator": {"bbox": [0, 0, 10, 10]}}) is True
        assert has_valid_locator({"locator": {"table_id": "tbl_1"}}) is True
        assert has_valid_locator({"locator": {"row": 1, "col": 2}}) is True
        assert has_valid_locator({"locator": {"char_span": [10, 20]}}) is True
        assert has_valid_locator({"locator": {"quote": "Veridian revenue"}}) is True
        assert has_valid_locator({"locator": {}}) is False
        assert has_valid_locator({}) is False
