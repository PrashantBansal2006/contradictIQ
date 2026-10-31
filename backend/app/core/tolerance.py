"""
tolerance.py — Precision-aware tolerance calculation and severity classification.

Pure Python, deterministic, no I/O.
Per architecture §10.3 and tasks.md §1.5.
"""
from dataclasses import dataclass
from decimal import Decimal
from typing import Literal


@dataclass(frozen=True)
class ToleranceConfig:
    approx_multiplier: Decimal = Decimal("2.0")
    min_abs_tol: Decimal = Decimal("0.01")


@dataclass(frozen=True)
class ToleranceResult:
    is_match: bool
    deviation: Decimal
    tolerance: Decimal
    severity: Literal["Match", "NearMiss", "Material"]


def _to_decimal(val: Decimal | int | float | str) -> Decimal:
    if isinstance(val, Decimal):
        return val
    return Decimal(str(val))


def compute_tolerance(
    precision: int = 0,
    is_percent: bool = True,
    is_hedged: bool = False,
    scale: Decimal | int | float | str = Decimal("1"),
    cfg: ToleranceConfig | None = None,
) -> Decimal:
    """
    Calculate precision-aware tolerance:
      half_ulp = 5 * 10^(-precision - 1)
        - "18%"   (precision 0) -> 0.5
        - "18.2%" (precision 1) -> 0.05
      approx = cfg.approx_multiplier if is_hedged else 1.0
      percent claims: max(half_ulp * approx, cfg.min_abs_tol)
      absolute claims: max(half_ulp * scale * approx, cfg.min_abs_tol)
    """
    if cfg is None:
        cfg = ToleranceConfig()

    scale_d = _to_decimal(scale)
    half_ulp = Decimal("5") * (Decimal("10") ** -(precision + 1))
    approx = cfg.approx_multiplier if is_hedged else Decimal("1.0")

    if is_percent:
        return max(half_ulp * approx, cfg.min_abs_tol)
    else:
        return max(half_ulp * scale_d * approx, cfg.min_abs_tol)


def evaluate_tolerance(
    computed_value: Decimal | int | float | str,
    stated_value: Decimal | int | float | str,
    precision: int = 0,
    is_percent: bool = True,
    is_hedged: bool = False,
    scale: Decimal | int | float | str = Decimal("1"),
    cfg: ToleranceConfig | None = None,
) -> ToleranceResult:
    """
    Compare computed value against stated value within precision-aware tolerance.
    Severity rules:
      - dev <= tol: Match (Consistent)
      - tol < dev <= 3 * tol: NearMiss (Conflicting)
      - dev > 3 * tol: Material (Conflicting)
    """
    computed_d = _to_decimal(computed_value)
    stated_d = _to_decimal(stated_value)

    tol = compute_tolerance(
        precision=precision,
        is_percent=is_percent,
        is_hedged=is_hedged,
        scale=scale,
        cfg=cfg,
    )

    dev = abs(computed_d - stated_d)

    if dev <= tol:
        return ToleranceResult(
            is_match=True,
            deviation=dev,
            tolerance=tol,
            severity="Match",
        )
    elif dev <= Decimal("3") * tol:
        return ToleranceResult(
            is_match=False,
            deviation=dev,
            tolerance=tol,
            severity="NearMiss",
        )
    else:
        return ToleranceResult(
            is_match=False,
            deviation=dev,
            tolerance=tol,
            severity="Material",
        )
