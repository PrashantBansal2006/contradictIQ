"""
Unit tests for Task 1.4: formulas.py.
Verifies all 7 formulas with >= 3 tests each and typed error handling.
"""
from decimal import Decimal
import pytest

from app.core.formulas import (
    growth_yoy,
    growth_qoq,
    gross_margin,
    operating_margin,
    net_margin,
    expense_ratio,
    opex_ratio,
    DivisionByZeroError,
    UndefinedGrowthBaseError,
    MissingInputError,
)


# ── growth_yoy ────────────────────────────────────────────────────────────────

def test_growth_yoy_positive():
    res = growth_yoy(current=Decimal("125"), previous=Decimal("100"), cur_fact_id="f2", prev_fact_id="f1")
    assert res.value == Decimal("25")
    assert res.unit == "percent"
    assert len(res.steps) == 3
    assert res.input_fact_ids == ["f2", "f1"]


def test_growth_yoy_negative():
    res = growth_yoy(current=Decimal("80"), previous=Decimal("100"))
    assert res.value == Decimal("-20")
    assert res.unit == "percent"


def test_growth_yoy_zero_base_error():
    with pytest.raises(UndefinedGrowthBaseError) as exc_info:
        growth_yoy(current=Decimal("100"), previous=Decimal("0"))
    assert exc_info.value.code == "UNDEFINED_GROWTH_BASE"


def test_growth_yoy_negative_base_error():
    with pytest.raises(UndefinedGrowthBaseError) as exc_info:
        growth_yoy(current=Decimal("100"), previous=Decimal("-50"))
    assert exc_info.value.code == "UNDEFINED_GROWTH_BASE"


# ── growth_qoq ────────────────────────────────────────────────────────────────

def test_growth_qoq_positive():
    res = growth_qoq(current=Decimal("110"), previous=Decimal("100"), cur_fact_id="q2", prev_fact_id="q1")
    assert res.value == Decimal("10")
    assert res.formula_id == "growth_qoq"
    assert res.unit == "percent"


def test_growth_qoq_negative():
    res = growth_qoq(current=Decimal("95"), previous=Decimal("100"))
    assert res.value == Decimal("-5")


def test_growth_qoq_invalid_base_error():
    with pytest.raises(UndefinedGrowthBaseError):
        growth_qoq(current=Decimal("50"), previous=Decimal("0"))


# ── gross_margin ──────────────────────────────────────────────────────────────

def test_gross_margin_with_gross_profit():
    res = gross_margin(revenue=Decimal("1000"), gross_profit=Decimal("400"))
    assert res.value == Decimal("40")
    assert res.formula_id == "gross_margin"


def test_gross_margin_with_cogs_derivation():
    res = gross_margin(revenue=Decimal("1000"), cogs=Decimal("650"))
    assert res.value == Decimal("35")
    assert any("revenue - cogs" in step.expr for step in res.steps)


def test_gross_margin_zero_revenue_error():
    with pytest.raises(DivisionByZeroError) as exc_info:
        gross_margin(revenue=Decimal("0"), gross_profit=Decimal("100"))
    assert exc_info.value.code == "DIVISION_BY_ZERO"


def test_gross_margin_missing_inputs_error():
    with pytest.raises(MissingInputError) as exc_info:
        gross_margin(revenue=Decimal("1000"))
    assert exc_info.value.code == "MISSING_INPUT"


# ── operating_margin ──────────────────────────────────────────────────────────

def test_operating_margin_positive():
    res = operating_margin(operating_income=Decimal("180"), revenue=Decimal("1000"))
    assert res.value == Decimal("18")
    assert res.formula_id == "operating_margin"


def test_operating_margin_loss():
    res = operating_margin(operating_income=Decimal("-50"), revenue=Decimal("1000"))
    assert res.value == Decimal("-5")


def test_operating_margin_zero_revenue_error():
    with pytest.raises(DivisionByZeroError):
        operating_margin(operating_income=Decimal("50"), revenue=Decimal("0"))


# ── net_margin ────────────────────────────────────────────────────────────────

def test_net_margin_positive():
    res = net_margin(net_income=Decimal("84"), revenue=Decimal("1000"))
    assert res.value == Decimal("8.4")
    assert res.formula_id == "net_margin"


def test_net_margin_loss():
    res = net_margin(net_income=Decimal("-25"), revenue=Decimal("500"))
    assert res.value == Decimal("-5")


def test_net_margin_zero_revenue_error():
    with pytest.raises(DivisionByZeroError):
        net_margin(net_income=Decimal("20"), revenue=Decimal("0"))


# ── expense_ratio ─────────────────────────────────────────────────────────────

def test_expense_ratio_standard():
    res = expense_ratio(total_expenses=Decimal("750"), revenue=Decimal("1000"))
    assert res.value == Decimal("75")
    assert res.formula_id == "expense_ratio"


def test_expense_ratio_exceeding_100():
    res = expense_ratio(total_expenses=Decimal("1200"), revenue=Decimal("1000"))
    assert res.value == Decimal("120")


def test_expense_ratio_zero_revenue_error():
    with pytest.raises(DivisionByZeroError):
        expense_ratio(total_expenses=Decimal("500"), revenue=Decimal("0"))


# ── opex_ratio ────────────────────────────────────────────────────────────────

def test_opex_ratio_standard():
    res = opex_ratio(operating_expenses=Decimal("300"), revenue=Decimal("1000"))
    assert res.value == Decimal("30")
    assert res.formula_id == "opex_ratio"


def test_opex_ratio_zero_opex():
    res = opex_ratio(operating_expenses=Decimal("0"), revenue=Decimal("1000"))
    assert res.value == Decimal("0")


def test_opex_ratio_zero_revenue_error():
    with pytest.raises(DivisionByZeroError):
        opex_ratio(operating_expenses=Decimal("200"), revenue=Decimal("0"))

