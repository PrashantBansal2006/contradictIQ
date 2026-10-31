"""
Unit tests for Task 1.5: tolerance.py.
Verifies precision-aware tolerance, hedging multipliers, and severity classifications.
"""
from decimal import Decimal
import pytest

from app.core.tolerance import (
    compute_tolerance,
    evaluate_tolerance,
    ToleranceConfig,
)


def test_claim_18_percent_exact_spec_acceptance():
    """
    Spec from tasks.md 1.5:
    '18%' accepts 17.6 and 18.4, rejects 19.2
    """
    # Precision 0 (integer percentage 18)
    # half_ulp = 5 * 10^(-0 - 1) = 0.5
    res_17_6 = evaluate_tolerance(
        computed_value=Decimal("17.6"),
        stated_value=Decimal("18"),
        precision=0,
        is_percent=True,
    )
    assert res_17_6.is_match is True
    assert res_17_6.severity == "Match"
    assert res_17_6.tolerance == Decimal("0.5")

    res_18_4 = evaluate_tolerance(
        computed_value=Decimal("18.4"),
        stated_value=Decimal("18"),
        precision=0,
        is_percent=True,
    )
    assert res_18_4.is_match is True
    assert res_18_4.severity == "Match"

    # 19.2 deviation is 1.2 > 0.5 -> must be rejected
    res_19_2 = evaluate_tolerance(
        computed_value=Decimal("19.2"),
        stated_value=Decimal("18"),
        precision=0,
        is_percent=True,
    )
    assert res_19_2.is_match is False
    # 1.2 is <= 3 * 0.5 = 1.5, so NearMiss
    assert res_19_2.severity == "NearMiss"


def test_severity_material():
    # Deviation > 3 * tolerance
    res_21_0 = evaluate_tolerance(
        computed_value=Decimal("21.0"),
        stated_value=Decimal("18"),
        precision=0,
        is_percent=True,
    )
    assert res_21_0.is_match is False
    assert res_21_0.severity == "Material"


def test_decimal_precision_1():
    # "18.2%" has precision 1 -> half_ulp = 0.05
    tol = compute_tolerance(precision=1, is_percent=True)
    assert tol == Decimal("0.05")

    res_pass = evaluate_tolerance(
        computed_value=Decimal("18.24"),
        stated_value=Decimal("18.2"),
        precision=1,
        is_percent=True,
    )
    assert res_pass.is_match is True

    res_fail = evaluate_tolerance(
        computed_value=Decimal("18.30"),
        stated_value=Decimal("18.2"),
        precision=1,
        is_percent=True,
    )
    assert res_fail.is_match is False


def test_decimal_precision_2():
    # "12.50%" has precision 2 -> half_ulp = 0.005, but min_abs_tol default is 0.01
    cfg = ToleranceConfig(min_abs_tol=Decimal("0.001"))
    tol = compute_tolerance(precision=2, is_percent=True, cfg=cfg)
    assert tol == Decimal("0.005")


def test_hedged_claim_multiplier():
    # Hedged claim ("around 18%") doubles tolerance with default approx_multiplier=2.0
    tol_normal = compute_tolerance(precision=0, is_percent=True, is_hedged=False)
    tol_hedged = compute_tolerance(precision=0, is_percent=True, is_hedged=True)
    assert tol_normal == Decimal("0.5")
    assert tol_hedged == Decimal("1.0")

    # 18.8 fails normal (dev 0.8 > 0.5) but passes hedged (dev 0.8 <= 1.0)
    res_normal = evaluate_tolerance(Decimal("18.8"), Decimal("18"), precision=0, is_hedged=False)
    assert res_normal.is_match is False

    res_hedged = evaluate_tolerance(Decimal("18.8"), Decimal("18"), precision=0, is_hedged=True)
    assert res_hedged.is_match is True


def test_absolute_value_tolerance():
    # Absolute scale (e.g. stated 3,400 crore, scale = 1e7)
    tol = compute_tolerance(
        precision=0,
        is_percent=False,
        scale=Decimal("10000000"),
    )
    # half_ulp = 0.5 * 10,000,000 = 5,000,000
    assert tol == Decimal("5000000")
