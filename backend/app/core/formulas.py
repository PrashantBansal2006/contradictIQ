"""
formulas.py — Pure deterministic financial formulas with execution traces.

Pure Python, no I/O, no floats (Decimals only).
Per architecture §9 and tasks.md §1.4.
"""
from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP, getcontext
from typing import Any

# Ensure standard high precision for financial intermediate steps
getcontext().prec = 28


class FormulaError(Exception):
    """Base error for financial formula calculations."""
    code: str = "FORMULA_ERROR"

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class DivisionByZeroError(FormulaError):
    """Raised when dividing by zero."""
    code: str = "DIVISION_BY_ZERO"


class UndefinedGrowthBaseError(FormulaError):
    """Raised when base value for growth calculation is non-positive or zero."""
    code: str = "UNDEFINED_GROWTH_BASE"


class MissingInputError(FormulaError):
    """Raised when an expected input fact is missing."""
    code: str = "MISSING_INPUT"


@dataclass(frozen=True)
class Step:
    label: str
    expr: str
    values: dict[str, str]
    result: Decimal


@dataclass(frozen=True)
class CalcResult:
    formula_id: str
    value: Decimal
    unit: str
    steps: list[Step]
    input_fact_ids: list[str]
    derived: bool = False


def _to_decimal(val: Decimal | int | float | str) -> Decimal:
    if isinstance(val, Decimal):
        return val
    return Decimal(str(val))


def growth_yoy(
    current: Decimal | int | float | str,
    previous: Decimal | int | float | str,
    cur_fact_id: str = "cur",
    prev_fact_id: str = "prev",
) -> CalcResult:
    """
    Calculate year-over-year growth rate: ((current - previous) / previous) * 100.
    Raises UndefinedGrowthBaseError if previous <= 0.
    """
    cur_d = _to_decimal(current)
    prev_d = _to_decimal(previous)

    if prev_d <= Decimal("0"):
        raise UndefinedGrowthBaseError(
            f"Base period value is {prev_d}; YoY growth is undefined for non-positive bases.",
            details={"current": str(cur_d), "previous": str(prev_d)},
        )

    diff = cur_d - prev_d
    step1 = Step(
        label="Calculate absolute difference",
        expr="current - previous",
        values={"current": str(cur_d), "previous": str(prev_d)},
        result=diff,
    )

    growth_frac = diff / prev_d
    step2 = Step(
        label="Calculate growth ratio",
        expr="difference / previous",
        values={"difference": str(diff), "previous": str(prev_d)},
        result=growth_frac,
    )

    growth_pct = growth_frac * Decimal("100")
    step3 = Step(
        label="Convert to percentage",
        expr="growth_ratio * 100",
        values={"growth_ratio": str(growth_frac)},
        result=growth_pct,
    )

    return CalcResult(
        formula_id="growth_yoy",
        value=growth_pct,
        unit="percent",
        steps=[step1, step2, step3],
        input_fact_ids=[cur_fact_id, prev_fact_id],
    )


def growth_qoq(
    current: Decimal | int | float | str,
    previous: Decimal | int | float | str,
    cur_fact_id: str = "cur",
    prev_fact_id: str = "prev",
) -> CalcResult:
    """
    Calculate quarter-over-quarter growth rate: ((current - previous) / previous) * 100.
    Raises UndefinedGrowthBaseError if previous <= 0.
    """
    cur_d = _to_decimal(current)
    prev_d = _to_decimal(previous)

    if prev_d <= Decimal("0"):
        raise UndefinedGrowthBaseError(
            f"Base quarter value is {prev_d}; QoQ growth is undefined for non-positive bases.",
            details={"current": str(cur_d), "previous": str(prev_d)},
        )

    diff = cur_d - prev_d
    step1 = Step(
        label="Calculate QoQ difference",
        expr="current - previous",
        values={"current": str(cur_d), "previous": str(prev_d)},
        result=diff,
    )

    growth_frac = diff / prev_d
    step2 = Step(
        label="Calculate QoQ ratio",
        expr="difference / previous",
        values={"difference": str(diff), "previous": str(prev_d)},
        result=growth_frac,
    )

    growth_pct = growth_frac * Decimal("100")
    step3 = Step(
        label="Convert to percentage",
        expr="growth_ratio * 100",
        values={"growth_ratio": str(growth_frac)},
        result=growth_pct,
    )

    return CalcResult(
        formula_id="growth_qoq",
        value=growth_pct,
        unit="percent",
        steps=[step1, step2, step3],
        input_fact_ids=[cur_fact_id, prev_fact_id],
    )


def gross_margin(
    revenue: Decimal | int | float | str,
    cogs: Decimal | int | float | str | None = None,
    gross_profit: Decimal | int | float | str | None = None,
    rev_fact_id: str = "rev",
    other_fact_id: str = "other",
) -> CalcResult:
    """
    Calculate gross margin percentage: (gross_profit / revenue) * 100.
    gross_profit can either be provided directly or derived from (revenue - cogs).
    Raises DivisionByZeroError if revenue == 0.
    """
    rev_d = _to_decimal(revenue)
    if rev_d == Decimal("0"):
        raise DivisionByZeroError("Revenue is zero; gross margin is undefined.")

    steps: list[Step] = []
    input_ids = [rev_fact_id]

    if gross_profit is not None:
        gp_d = _to_decimal(gross_profit)
        input_ids.append(other_fact_id)
        steps.append(
            Step(
                label="Gross profit provided",
                expr="gross_profit",
                values={"gross_profit": str(gp_d)},
                result=gp_d,
            )
        )
    elif cogs is not None:
        cogs_d = _to_decimal(cogs)
        input_ids.append(other_fact_id)
        gp_d = rev_d - cogs_d
        steps.append(
            Step(
                label="Derive gross profit",
                expr="revenue - cogs",
                values={"revenue": str(rev_d), "cogs": str(cogs_d)},
                result=gp_d,
            )
        )
    else:
        raise MissingInputError("Either cogs or gross_profit must be provided for gross margin.")

    margin_frac = gp_d / rev_d
    steps.append(
        Step(
            label="Calculate gross margin ratio",
            expr="gross_profit / revenue",
            values={"gross_profit": str(gp_d), "revenue": str(rev_d)},
            result=margin_frac,
        )
    )

    margin_pct = margin_frac * Decimal("100")
    steps.append(
        Step(
            label="Convert to percentage",
            expr="gross_margin_ratio * 100",
            values={"gross_margin_ratio": str(margin_frac)},
            result=margin_pct,
        )
    )

    return CalcResult(
        formula_id="gross_margin",
        value=margin_pct,
        unit="percent",
        steps=steps,
        input_fact_ids=input_ids,
    )


def operating_margin(
    operating_income: Decimal | int | float | str,
    revenue: Decimal | int | float | str,
    op_fact_id: str = "op_inc",
    rev_fact_id: str = "rev",
) -> CalcResult:
    """
    Calculate operating margin percentage: (operating_income / revenue) * 100.
    Raises DivisionByZeroError if revenue == 0.
    """
    op_d = _to_decimal(operating_income)
    rev_d = _to_decimal(revenue)

    if rev_d == Decimal("0"):
        raise DivisionByZeroError("Revenue is zero; operating margin is undefined.")

    ratio = op_d / rev_d
    step1 = Step(
        label="Calculate operating margin ratio",
        expr="operating_income / revenue",
        values={"operating_income": str(op_d), "revenue": str(rev_d)},
        result=ratio,
    )

    pct = ratio * Decimal("100")
    step2 = Step(
        label="Convert to percentage",
        expr="operating_ratio * 100",
        values={"operating_ratio": str(ratio)},
        result=pct,
    )

    return CalcResult(
        formula_id="operating_margin",
        value=pct,
        unit="percent",
        steps=[step1, step2],
        input_fact_ids=[op_fact_id, rev_fact_id],
    )


def net_margin(
    net_income: Decimal | int | float | str,
    revenue: Decimal | int | float | str,
    ni_fact_id: str = "net_inc",
    rev_fact_id: str = "rev",
) -> CalcResult:
    """
    Calculate net margin percentage: (net_income / revenue) * 100.
    Raises DivisionByZeroError if revenue == 0.
    """
    ni_d = _to_decimal(net_income)
    rev_d = _to_decimal(revenue)

    if rev_d == Decimal("0"):
        raise DivisionByZeroError("Revenue is zero; net margin is undefined.")

    ratio = ni_d / rev_d
    step1 = Step(
        label="Calculate net margin ratio",
        expr="net_income / revenue",
        values={"net_income": str(ni_d), "revenue": str(rev_d)},
        result=ratio,
    )

    pct = ratio * Decimal("100")
    step2 = Step(
        label="Convert to percentage",
        expr="net_ratio * 100",
        values={"net_ratio": str(ratio)},
        result=pct,
    )

    return CalcResult(
        formula_id="net_margin",
        value=pct,
        unit="percent",
        steps=[step1, step2],
        input_fact_ids=[ni_fact_id, rev_fact_id],
    )


def expense_ratio(
    total_expenses: Decimal | int | float | str,
    revenue: Decimal | int | float | str,
    exp_fact_id: str = "tot_exp",
    rev_fact_id: str = "rev",
) -> CalcResult:
    """
    Calculate expense ratio percentage: (total_expenses / revenue) * 100.
    Raises DivisionByZeroError if revenue == 0.
    """
    exp_d = _to_decimal(total_expenses)
    rev_d = _to_decimal(revenue)

    if rev_d == Decimal("0"):
        raise DivisionByZeroError("Revenue is zero; expense ratio is undefined.")

    ratio = exp_d / rev_d
    step1 = Step(
        label="Calculate expense ratio",
        expr="total_expenses / revenue",
        values={"total_expenses": str(exp_d), "revenue": str(rev_d)},
        result=ratio,
    )

    pct = ratio * Decimal("100")
    step2 = Step(
        label="Convert to percentage",
        expr="expense_ratio * 100",
        values={"expense_ratio": str(ratio)},
        result=pct,
    )

    return CalcResult(
        formula_id="expense_ratio",
        value=pct,
        unit="percent",
        steps=[step1, step2],
        input_fact_ids=[exp_fact_id, rev_fact_id],
    )


def opex_ratio(
    operating_expenses: Decimal | int | float | str,
    revenue: Decimal | int | float | str,
    opex_fact_id: str = "opex",
    rev_fact_id: str = "rev",
) -> CalcResult:
    """
    Calculate operating expense ratio percentage: (operating_expenses / revenue) * 100.
    Raises DivisionByZeroError if revenue == 0.
    """
    opex_d = _to_decimal(operating_expenses)
    rev_d = _to_decimal(revenue)

    if rev_d == Decimal("0"):
        raise DivisionByZeroError("Revenue is zero; opex ratio is undefined.")

    ratio = opex_d / rev_d
    step1 = Step(
        label="Calculate opex ratio",
        expr="operating_expenses / revenue",
        values={"operating_expenses": str(opex_d), "revenue": str(rev_d)},
        result=ratio,
    )

    pct = ratio * Decimal("100")
    step2 = Step(
        label="Convert to percentage",
        expr="opex_ratio * 100",
        values={"opex_ratio": str(ratio)},
        result=pct,
    )

    return CalcResult(
        formula_id="opex_ratio",
        value=pct,
        unit="percent",
        steps=[step1, step2],
        input_fact_ids=[opex_fact_id, rev_fact_id],
    )
