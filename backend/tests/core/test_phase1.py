from decimal import Decimal
import pytest

from backend.app.core.units import parse_value
from backend.app.core.periods import (
    Period,
    parse_period,
    prev_year,
    prev_quarter,
    can_derive_fy,
    derive_fy,
    can_derive_h1,
    derive_h1,
    can_derive_9m,
    derive_9m,
)
from backend.app.core.metrics import match_metric, METRICS

# ==========================================
# Task 1.1: Units tests
# ==========================================
def test_units_acceptance_cases():
    # 1. '₹340 cr == ₹3.4 bn'
    v1 = parse_value("₹340 cr")
    v2 = parse_value("₹3.4 bn")
    assert v1.value == v2.value == Decimal("3400000000")
    assert v1.currency == "INR"
    assert v2.currency == "INR"

    # 2. '(1,234)'
    v3 = parse_value("(1,234)")
    assert v3.value == Decimal("-1234")
    assert v3.is_negative is True
    assert v3.precision == 0

    # 3. '12.5%'
    v4 = parse_value("12.5%")
    assert v4.value == Decimal("12.5")
    assert v4.unit == "percent"
    assert v4.precision == 1

    # 4. '$4.2B'
    v5 = parse_value("$4.2B")
    assert v5.value == Decimal("4200000000")
    assert v5.currency == "USD"
    assert v5.precision == 1

def test_units_additional_scales_and_negatives():
    assert parse_value("€100m").value == Decimal("100000000")
    assert parse_value("€100m").currency == "EUR"
    assert parse_value("-50.2k").value == Decimal("-50200")
    assert parse_value("10 lakh").value == Decimal("1000000")

# ==========================================
# Task 1.2: Periods tests
# ==========================================
def test_periods_parsing():
    # Standard quarters, halves, full years
    assert parse_period("Q3 FY25") == Period(kind="Q", fy=2025, idx=3, fy_end_month=3)
    assert parse_period("Q3 FY2025") == Period(kind="Q", fy=2025, idx=3, fy_end_month=3)
    assert parse_period("H1 FY25") == Period(kind="H", fy=2025, idx=1, fy_end_month=3)
    assert parse_period("9M FY25") == Period(kind="9M", fy=2025, idx=None, fy_end_month=3)
    assert parse_period("FY2025") == Period(kind="FY", fy=2025, idx=None, fy_end_month=3)

    # Year ended with Mar and Dec
    p_mar = parse_period("year ended 31 March 2025")
    assert p_mar == Period(kind="FY", fy=2025, idx=None, fy_end_month=3)

    p_dec = parse_period("year ended 31 December 2024")
    assert p_dec == Period(kind="FY", fy=2024, idx=None, fy_end_month=12)

    # Jul-Sep with Mar year-end vs Dec year-end
    p_jul_sep_mar = parse_period("Jul–Sep 2024", default_fy_end_month=3)
    assert p_jul_sep_mar == Period(kind="Q", fy=2025, idx=2, fy_end_month=3)

    p_jul_sep_dec = parse_period("Jul–Sep 2024", default_fy_end_month=12)
    assert p_jul_sep_dec == Period(kind="Q", fy=2024, idx=3, fy_end_month=12)

def test_periods_navigation_and_algebra():
    p = Period(kind="Q", fy=2025, idx=2, fy_end_month=3)
    assert prev_year(p) == Period(kind="Q", fy=2024, idx=2, fy_end_month=3)
    assert prev_quarter(p) == Period(kind="Q", fy=2025, idx=1, fy_end_month=3)

    p_q1 = Period(kind="Q", fy=2025, idx=1, fy_end_month=3)
    assert prev_quarter(p_q1) == Period(kind="Q", fy=2024, idx=4, fy_end_month=3)

    q1 = Period(kind="Q", fy=2025, idx=1, fy_end_month=3)
    q2 = Period(kind="Q", fy=2025, idx=2, fy_end_month=3)
    q3 = Period(kind="Q", fy=2025, idx=3, fy_end_month=3)
    q4 = Period(kind="Q", fy=2025, idx=4, fy_end_month=3)

    # Derivations
    assert can_derive_h1([q1, q2]) is True
    assert derive_h1([q1, q2]) == Period(kind="H", fy=2025, idx=1, fy_end_month=3)

    assert can_derive_9m([q1, q2, q3]) is True
    assert derive_9m([q1, q2, q3]) == Period(kind="9M", fy=2025, idx=None, fy_end_month=3)

    assert can_derive_fy([q1, q2, q3, q4]) is True
    assert derive_fy([q1, q2, q3, q4]) == Period(kind="FY", fy=2025, idx=None, fy_end_month=3)

# ==========================================
# Task 1.3: Metrics tests
# ==========================================
def test_metrics_matching():
    # Acceptance criteria
    assert match_metric("Net Sales") == "revenue"
    assert match_metric("Income") is None  # Ambiguous label -> unmapped

    # Synonyms and exact matches
    assert match_metric("Turnover") == "revenue"
    assert match_metric("Total income from operations") == "revenue"
    assert match_metric("Cost of goods sold") == "cogs"
    assert match_metric("Operating Profit") == "operating_income"
    assert match_metric("Profit after Tax") == "net_income"
    assert match_metric("Operating costs") == "operating_expenses"

    # Ambiguous rejections
    assert match_metric("Profit") is None
    assert match_metric("Expenses") is None

