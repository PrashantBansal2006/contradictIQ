"""
Unit tests for Task 1.6: comparability.py.
Verifies Comparability Gate checks, reason codes, period algebra FY derivation, and disagreement detection.
"""
from decimal import Decimal
import pytest

from app.core.comparability import (
    check_comparability,
    derive_fy_from_quarters,
    REASON_METRIC_MISMATCH,
    REASON_ENTITY_MISMATCH,
    REASON_PERIOD_MISMATCH,
    REASON_NOT_COMPARABLE_PERIOD_KIND,
    REASON_SCOPE_MISMATCH,
    REASON_BASIS_MISMATCH,
    REASON_CURRENCY_MISMATCH,
    REASON_SOURCE_DISAGREEMENT,
)
from app.core.periods import Period


def test_gate_exact_match_passes():
    claim = {
        "metric": "revenue",
        "entity": "Veridian Foods Ltd",
        "period": "FY2025",
        "scope": "consolidated",
        "basis": "reported",
        "currency": "INR",
    }
    fact = {
        "id": "f1",
        "metric": "Revenue from Operations",
        "entity": "Veridian Foods",
        "period": "FY2025",
        "scope": "consolidated",
        "basis": "reported",
        "currency": "INR",
        "value": Decimal("34000000000"),
    }
    res = check_comparability(claim, [fact])
    assert res.passed is True
    assert res.blocked is False
    assert len(res.matched_facts) == 1


def test_gate_metric_mismatch():
    claim = {"metric": "revenue", "period": "FY2025"}
    fact = {"metric": "total_debt", "period": "FY2025"}
    res = check_comparability(claim, [fact])
    assert res.blocked is True
    assert REASON_METRIC_MISMATCH in res.reasons


def test_gate_entity_mismatch():
    claim = {"metric": "revenue", "entity": "Acme Corp", "period": "FY2025"}
    fact = {"metric": "revenue", "entity": "Beta Industries", "period": "FY2025"}
    res = check_comparability(claim, [fact])
    assert res.blocked is True
    assert REASON_ENTITY_MISMATCH in res.reasons


def test_gate_fiscal_year_mismatch():
    claim = {"metric": "revenue", "period": "FY2025"}
    fact = {"metric": "revenue", "period": "FY2024"}
    res = check_comparability(claim, [fact])
    assert res.blocked is True
    assert REASON_PERIOD_MISMATCH in res.reasons


def test_gate_scope_mismatch():
    claim = {"metric": "revenue", "period": "FY2025", "scope": "consolidated"}
    fact = {"metric": "revenue", "period": "FY2025", "scope": "standalone"}
    res = check_comparability(claim, [fact])
    assert res.blocked is True
    assert REASON_SCOPE_MISMATCH in res.reasons


def test_gate_basis_mismatch():
    claim = {"metric": "net_income", "period": "FY2025", "basis": "reported"}
    fact = {"metric": "net_income", "period": "FY2025", "basis": "adjusted"}
    res = check_comparability(claim, [fact])
    assert res.blocked is True
    assert REASON_BASIS_MISMATCH in res.reasons


def test_gate_currency_mismatch():
    claim = {"metric": "revenue", "period": "FY2025", "currency": "USD"}
    fact = {"metric": "revenue", "period": "FY2025", "currency": "INR"}
    res = check_comparability(claim, [fact])
    assert res.blocked is True
    assert REASON_CURRENCY_MISMATCH in res.reasons


def test_quarter_vs_annual_single_quarter_blocked():
    """
    Brownie Acceptance Test B1 trap:
    Comparing a single quarter to annual is blocked unless derivable.
    """
    claim = {"metric": "revenue", "period": "FY2025"}
    q3_fact = {"id": "f_q3", "metric": "revenue", "period": "Q3 FY25", "value": Decimal("9200000000")}

    res = check_comparability(claim, [q3_fact])
    assert res.blocked is True
    assert REASON_NOT_COMPARABLE_PERIOD_KIND in res.reasons


def test_quarter_vs_annual_derivation_all_four_quarters():
    """
    Brownie Acceptance Test B1 resolution:
    If all 4 quarters exist for an additive metric, derive FY total and pass.
    """
    claim = {"metric": "revenue", "period": "FY2025"}
    quarters = [
        {"id": "q1", "metric": "revenue", "period": "Q1 FY25", "value": Decimal("800")},
        {"id": "q2", "metric": "revenue", "period": "Q2 FY25", "value": Decimal("850")},
        {"id": "q3", "metric": "revenue", "period": "Q3 FY25", "value": Decimal("920")},
        {"id": "q4", "metric": "revenue", "period": "Q4 FY25", "value": Decimal("830")},
    ]
    res = check_comparability(claim, quarters)
    assert res.passed is True
    assert res.blocked is False
    assert res.derived is True
    assert res.derived_value == Decimal("3400")
    assert len(res.matched_facts) == 4


def test_quarter_vs_annual_derivation_blocked_for_non_additive_metric():
    """
    Non-additive metrics (like total debt or assets) cannot be derived from quarters.
    """
    claim = {"metric": "total_debt", "period": "FY2025"}
    quarters = [
        {"id": "q1", "metric": "total_debt", "period": "Q1 FY25", "value": Decimal("100")},
        {"id": "q2", "metric": "total_debt", "period": "Q2 FY25", "value": Decimal("100")},
        {"id": "q3", "metric": "total_debt", "period": "Q3 FY25", "value": Decimal("100")},
        {"id": "q4", "metric": "total_debt", "period": "Q4 FY25", "value": Decimal("100")},
    ]
    res = check_comparability(claim, quarters)
    assert res.blocked is True
    assert REASON_NOT_COMPARABLE_PERIOD_KIND in res.reasons


def test_quarter_vs_annual_derivation_blocked_when_incomplete():
    """
    Missing Q4 -> cannot derive FY total.
    """
    claim = {"metric": "revenue", "period": "FY2025"}
    quarters = [
        {"id": "q1", "metric": "revenue", "period": "Q1 FY25", "value": Decimal("800")},
        {"id": "q2", "metric": "revenue", "period": "Q2 FY25", "value": Decimal("850")},
        {"id": "q3", "metric": "revenue", "period": "Q3 FY25", "value": Decimal("920")},
    ]
    res = check_comparability(claim, quarters)
    assert res.blocked is True
    assert REASON_NOT_COMPARABLE_PERIOD_KIND in res.reasons


def test_same_tier_disagreement_detection():
    """
    Two facts from Tier 1 claiming contradictory values for the same metric/period.
    """
    claim = {"metric": "revenue", "period": "FY2025"}
    f1 = {"id": "f1", "metric": "revenue", "period": "FY2025", "value": Decimal("3400"), "source_tier": "T1"}
    f2 = {"id": "f2", "metric": "revenue", "period": "FY2025", "value": Decimal("3550"), "source_tier": "T1"}

    res = check_comparability(claim, [f1, f2])
    assert res.blocked is True
    assert res.same_tier_disagreement is True
    assert REASON_SOURCE_DISAGREEMENT in res.reasons
