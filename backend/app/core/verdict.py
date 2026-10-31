"""Deterministic Verdict Engine (Architecture §10.2, §10.3 — Task 1.7).

Ordered rules R1 through R6:
R1: Parseability check (UNPARSEABLE_CLAIM)
R2: Missing inputs check (MISSING_INPUT)
R3: Comparability gate check (NOT_COMPARABLE, PERIOD_MISMATCH, etc.)
R4: Source disagreement check among same-tier facts (SOURCE_DISAGREEMENT)
R5: Confidence threshold gate (LOW_CONFIDENCE_EXTRACTION)
R6: Compute formula, precision-aware tolerance, and determine verdict + severity (Match/NearMiss/Material)
"""

from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence, Union


class VerdictType(str, Enum):
    CONSISTENT = "Consistent"
    CONFLICTING = "Conflicting"
    INCONCLUSIVE = "Inconclusive"


class Severity(str, Enum):
    MATCH = "Match"
    NEAR_MISS = "NearMiss"
    MATERIAL = "Material"


@dataclass(frozen=True)
class DecisionConfig:
    min_conf: float = 0.8
    approx_multiplier: float = 2.0
    min_abs_tol: Decimal = Decimal("0.1")
    require_exact_entity: bool = True


@dataclass
class ToleranceResult:
    half_ulp: Decimal
    approx_multiplier: float
    min_abs_tol: Decimal
    effective_tol: Decimal


@dataclass
class CalculationTraceStep:
    label: str
    expr: str
    values: Dict[str, Any]
    result: str


@dataclass
class VerdictOutcome:
    verdict: VerdictType
    severity: Optional[Severity] = None
    reason_code: Optional[str] = None
    reasons: List[str] = field(default_factory=list)
    calc_value: Optional[Decimal] = None
    claim_value: Optional[Decimal] = None
    deviation: Optional[Decimal] = None
    tolerance: Optional[ToleranceResult] = None
    calc_steps: List[CalculationTraceStep] = field(default_factory=list)
    input_facts: List[Any] = field(default_factory=list)
    derived: bool = False
    gate_clean: bool = True
    rule_triggered: str = "R6"


# ---------------------------------------------------------------------------
# Helpers for Claim and Fact attribute extraction (supports dict or object)
# ---------------------------------------------------------------------------

def _get_val(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _to_decimal(val: Any) -> Optional[Decimal]:
    if val is None:
        return None
    if isinstance(val, Decimal):
        return val
    try:
        # Strip common formatting like commas or percentage signs
        s = str(val).replace(",", "").replace("%", "").strip()
        # Strip parentheses for negative numbers e.g. (1234) -> -1234
        if s.startswith("(") and s.endswith(")"):
            s = f"-{s[1:-1]}"
        return Decimal(s)
    except (InvalidOperation, ValueError):
        return None


# ---------------------------------------------------------------------------
# Tolerance computation (§10.3)
# ---------------------------------------------------------------------------

def compute_tolerance(
    precision: int,
    hedged: bool,
    cfg: DecisionConfig,
    unit: str = "percent"
) -> ToleranceResult:
    """Computes precision-aware tolerance based on half-ULP.
    
    e.g. 18% (precision=0) -> half_ulp = 0.5
         18.2% (precision=1) -> half_ulp = 0.05
    """
    prec = max(0, int(precision))
    half_ulp = Decimal("5") * (Decimal("10") ** -(prec + 1))
    approx_mult = cfg.approx_multiplier if hedged else 1.0
    scaled = half_ulp * Decimal(str(approx_mult))
    effective = max(scaled, cfg.min_abs_tol)
    return ToleranceResult(
        half_ulp=half_ulp,
        approx_multiplier=approx_mult,
        min_abs_tol=cfg.min_abs_tol,
        effective_tol=effective,
    )


# ---------------------------------------------------------------------------
# Comparability Gate Checks (§10.1)
# ---------------------------------------------------------------------------

def check_comparability(claim: Any, facts: Sequence[Any], is_compound: bool = False) -> Dict[str, Any]:
    """Evaluates comparability between claim and evidence facts."""
    reasons: List[str] = []
    reason_codes: List[str] = []

    claim_metric = (_get_val(claim, "metric") or "").strip().lower()
    claim_entity = (_get_val(claim, "entity") or "").strip().lower()
    claim_scope = (_get_val(claim, "scope") or "consolidated").strip().lower()
    claim_basis = (_get_val(claim, "basis") or "reported").strip().lower()
    claim_currency = (_get_val(claim, "currency") or "").strip().upper()
    claim_period = _get_val(claim, "period")

    for idx, fact in enumerate(facts):
        f_metric = (_get_val(fact, "metric") or "").strip().lower()
        if not is_compound and f_metric and claim_metric and f_metric != claim_metric:
            reasons.append(f"Metric mismatch: claim '{claim_metric}' vs fact '{f_metric}'")
            if "METRIC_MISMATCH" not in reason_codes:
                reason_codes.append("METRIC_MISMATCH")

        f_entity = (_get_val(fact, "entity") or "").strip().lower()
        if f_entity and claim_entity and f_entity != claim_entity:
            reasons.append(f"Entity mismatch: claim '{claim_entity}' vs fact '{f_entity}'")
            if "ENTITY_MISMATCH" not in reason_codes:
                reason_codes.append("ENTITY_MISMATCH")

        f_scope = (_get_val(fact, "scope") or "consolidated").strip().lower()
        if f_scope != claim_scope:
            reasons.append(f"Scope mismatch: claim '{claim_scope}' vs fact '{f_scope}'")
            if "SCOPE_MISMATCH" not in reason_codes:
                reason_codes.append("SCOPE_MISMATCH")

        f_basis = (_get_val(fact, "basis") or "reported").strip().lower()
        if f_basis != claim_basis:
            reasons.append(f"Accounting basis mismatch: claim '{claim_basis}' vs fact '{f_basis}'")
            if "BASIS_MISMATCH" not in reason_codes:
                reason_codes.append("BASIS_MISMATCH")

        f_curr = (_get_val(fact, "currency") or "").strip().upper()
        if f_curr and claim_currency and f_curr != claim_currency:
            reasons.append(f"Currency mismatch: claim '{claim_currency}' vs fact '{f_curr}'")
            if "CURRENCY_MISMATCH" not in reason_codes:
                reason_codes.append("CURRENCY_MISMATCH")

        # Period Kind mismatch (e.g. quarter vs annual)
        f_period = _get_val(fact, "period")
        f_kind = _get_val(f_period, "kind") if f_period else None
        c_kind = _get_val(claim_period, "kind") if claim_period else None
        if f_kind and c_kind and f_kind != c_kind:
            # Quarter vs Annual trap
            reasons.append(f"Not comparable period kind: claim is '{c_kind}', fact is '{f_kind}'")
            if "NOT_COMPARABLE_PERIOD_KIND" not in reason_codes:
                reason_codes.append("NOT_COMPARABLE_PERIOD_KIND")

    blocked = len(reason_codes) > 0
    return {
        "blocked": blocked,
        "reasons": reasons,
        "reason_codes": reason_codes,
    }


# ---------------------------------------------------------------------------
# Ordered Rules Engine (§10.2)
# ---------------------------------------------------------------------------

def decide(
    claim: Any,
    evidence_facts: Sequence[Any],
    cfg: Optional[DecisionConfig] = None,
    skeptic_reason: Optional[str] = None,
) -> VerdictOutcome:
    """Applies ordered rules R1 through R6 to judge financial claims."""
    if cfg is None:
        cfg = DecisionConfig()

    # -----------------------------------------------------------------------
    # Rule R1: Parseability Check
    # -----------------------------------------------------------------------
    claim_type = _get_val(claim, "claim_type")
    metric = _get_val(claim, "metric")
    text = _get_val(claim, "text")

    if not text or not metric or not claim_type:
        return VerdictOutcome(
            verdict=VerdictType.INCONCLUSIVE,
            reason_code="UNPARSEABLE_CLAIM",
            reasons=["Claim missing required text, metric, or claim_type"],
            rule_triggered="R1",
        )

    claim_type_str = str(claim_type).upper()
    is_direction = "DIRECTION" in claim_type_str
    is_growth = "GROWTH" in claim_type_str
    is_ratio = any(t in claim_type_str for t in ["MARGIN", "RATIO", "EXPENSE_RATIO", "OPEX_RATIO"])

    claim_num = _to_decimal(_get_val(claim, "value_numeric"))
    if claim_num is None:
        claim_num = _to_decimal(_get_val(claim, "value_raw"))

    if not is_direction and claim_num is None:
        return VerdictOutcome(
            verdict=VerdictType.INCONCLUSIVE,
            reason_code="UNPARSEABLE_CLAIM",
            reasons=["Numeric claim cannot be parsed into a valid Decimal value"],
            rule_triggered="R1",
        )

    # -----------------------------------------------------------------------
    # Rule R2: Missing Inputs Check
    # -----------------------------------------------------------------------
    if not evidence_facts:
        return VerdictOutcome(
            verdict=VerdictType.INCONCLUSIVE,
            reason_code="MISSING_INPUT",
            reasons=["No evidence facts provided for verification"],
            rule_triggered="R2",
        )

    # For GROWTH, RATIO/MARGIN, or DIRECTION formulas, we need at least 2 facts
    if (is_growth or is_ratio or is_direction) and len(evidence_facts) < 2:
        return VerdictOutcome(
            verdict=VerdictType.INCONCLUSIVE,
            reason_code="MISSING_INPUT",
            reasons=[f"{claim_type_str} requires at least 2 input facts (current/previous or numerator/denominator)"],
            input_facts=list(evidence_facts),
            rule_triggered="R2",
        )

    # -----------------------------------------------------------------------
    # Rule R3: Comparability Gate (all must pass or be resolvable)
    # -----------------------------------------------------------------------
    gate = check_comparability(claim, evidence_facts, is_compound=is_ratio)
    if gate["blocked"]:
        primary_code = gate["reason_codes"][0] if gate["reason_codes"] else "NOT_COMPARABLE"
        return VerdictOutcome(
            verdict=VerdictType.INCONCLUSIVE,
            reason_code=primary_code,
            reasons=gate["reasons"],
            input_facts=list(evidence_facts),
            gate_clean=False,
            rule_triggered="R3",
        )

    # -----------------------------------------------------------------------
    # Rule R4: Source Disagreement among same-tier facts
    # -----------------------------------------------------------------------
    # Group facts by (tier, metric, period_key, scope, basis) only when period_key is explicitly present
    tier_groups: Dict[tuple, List[Any]] = {}
    for f in evidence_facts:
        p_key = _get_val(f, "period_key")
        if p_key is None:
            p_obj = _get_val(f, "period")
            if p_obj:
                p_key = _get_val(p_obj, "canonical_key")() if hasattr(_get_val(p_obj, "canonical_key"), "__call__") else str(p_obj)

        if p_key is not None:
            key = (
                _get_val(f, "source_tier", "T2"),
                _get_val(f, "metric"),
                p_key,
                _get_val(f, "scope", "consolidated"),
                _get_val(f, "basis", "reported"),
            )
            tier_groups.setdefault(key, []).append(f)

    for group_key, grouped_facts in tier_groups.items():
        if len(grouped_facts) > 1:
            values = [_to_decimal(_get_val(f, "value_base")) for f in grouped_facts]
            valid_values = [v for v in values if v is not None]
            if len(valid_values) > 1:
                # Check for contradiction between same-tier documents
                min_v = min(valid_values)
                max_v = max(valid_values)
                if abs(max_v - min_v) > Decimal("0.001"):
                    return VerdictOutcome(
                        verdict=VerdictType.INCONCLUSIVE,
                        reason_code="SOURCE_DISAGREEMENT",
                        reasons=[f"Conflicting values {valid_values} found in same-tier sources for {group_key}"],
                        input_facts=list(evidence_facts),
                        rule_triggered="R4",
                    )

    # -----------------------------------------------------------------------
    # Rule R5: Confidence Gate
    # -----------------------------------------------------------------------
    confs = [float(_get_val(f, "confidence", 1.0)) for f in evidence_facts]
    min_conf = min(confs) if confs else 1.0
    all_confirmed = all(bool(_get_val(f, "confirmed", False)) for f in evidence_facts)

    if min_conf < cfg.min_conf and not all_confirmed:
        return VerdictOutcome(
            verdict=VerdictType.INCONCLUSIVE,
            reason_code="LOW_CONFIDENCE_EXTRACTION",
            reasons=[f"Extraction confidence ({min_conf:.2f}) below threshold ({cfg.min_conf:.2f}) and unconfirmed"],
            input_facts=list(evidence_facts),
            rule_triggered="R5",
        )

    # -----------------------------------------------------------------------
    # Rule R6: Compute & Compare
    # -----------------------------------------------------------------------
    precision = int(_get_val(claim, "value_precision", 1))
    hedged = bool(_get_val(claim, "hedged", False))
    tol = compute_tolerance(precision, hedged, cfg)
    steps: List[CalculationTraceStep] = []
    derived_used = any(bool(_get_val(f, "derived", False)) for f in evidence_facts)

    # Branch A: DIRECTION claims
    if is_direction:
        if len(evidence_facts) < 2:
            return VerdictOutcome(
                verdict=VerdictType.INCONCLUSIVE,
                reason_code="MISSING_INPUT",
                reasons=["Direction evaluation requires 2 facts (current and previous)"],
                input_facts=list(evidence_facts),
                rule_triggered="R6",
            )
        f_cur = _to_decimal(_get_val(evidence_facts[0], "value_base"))
        f_prev = _to_decimal(_get_val(evidence_facts[1], "value_base"))
        if f_cur is None or f_prev is None:
            return VerdictOutcome(
                verdict=VerdictType.INCONCLUSIVE,
                reason_code="UNPARSEABLE_CLAIM",
                reasons=["Cannot evaluate direction on unparseable fact values"],
                rule_triggered="R6",
            )

        delta = f_cur - f_prev
        steps.append(CalculationTraceStep(
            label="Delta",
            expr="current - previous",
            values={"current": str(f_cur), "previous": str(f_prev)},
            result=str(delta),
        ))

        if delta == 0:
            return VerdictOutcome(
                verdict=VerdictType.INCONCLUSIVE,
                reason_code="ZERO_CHANGE",
                reasons=["Difference between periods is zero; direction claim cannot be validated"],
                calc_steps=steps,
                input_facts=list(evidence_facts),
                rule_triggered="R6",
            )

        # Infer positive vs negative asserted by claim text
        text_lower = text.lower()
        asserts_positive = any(w in text_lower for w in ["grew", "growth", "increased", "increase", "up", "expanded", "higher"])
        asserts_negative = any(w in text_lower for w in ["declined", "decrease", "decreased", "fell", "down", "contracted", "lower"])

        if asserts_positive and delta > 0:
            outcome = VerdictOutcome(
                verdict=VerdictType.CONSISTENT,
                severity=Severity.MATCH,
                reasons=["Direction matches: positive change confirmed"],
                calc_value=delta,
                calc_steps=steps,
                input_facts=list(evidence_facts),
                rule_triggered="R6",
            )
        elif asserts_negative and delta < 0:
            outcome = VerdictOutcome(
                verdict=VerdictType.CONSISTENT,
                severity=Severity.MATCH,
                reasons=["Direction matches: negative change confirmed"],
                calc_value=delta,
                calc_steps=steps,
                input_facts=list(evidence_facts),
                rule_triggered="R6",
            )
        else:
            outcome = VerdictOutcome(
                verdict=VerdictType.CONFLICTING,
                severity=Severity.MATERIAL,
                reasons=[f"Direction contradictory: stated direction opposes calculated change ({delta})"],
                calc_value=delta,
                calc_steps=steps,
                input_facts=list(evidence_facts),
                rule_triggered="R6",
            )

        return _apply_skeptic(outcome, skeptic_reason)

    # Branch B: Formula / Numeric claims
    calc_val: Optional[Decimal] = None

    if is_growth:
        # Sort facts: assume fact[0] = current, fact[1] = previous
        cur_fact = evidence_facts[0]
        prev_fact = evidence_facts[1]
        cur_v = _to_decimal(_get_val(cur_fact, "value_base"))
        prev_v = _to_decimal(_get_val(prev_fact, "value_base"))

        if cur_v is None or prev_v is None:
            return VerdictOutcome(
                verdict=VerdictType.INCONCLUSIVE,
                reason_code="UNPARSEABLE_CLAIM",
                reasons=["Cannot parse values for growth formula"],
                rule_triggered="R6",
            )

        # Trap: Division by zero or negative growth base
        if prev_v <= 0:
            return VerdictOutcome(
                verdict=VerdictType.INCONCLUSIVE,
                reason_code="UNDEFINED_GROWTH_BASE",
                reasons=[f"Previous period value ({prev_v}) is non-positive; growth percentage is undefined"],
                input_facts=list(evidence_facts),
                rule_triggered="R6",
            )

        # growth = (cur - prev) / prev * 100
        calc_val = ((cur_v - prev_v) / prev_v) * Decimal("100")
        steps.append(CalculationTraceStep(
            label="Growth Calculation",
            expr="(current - previous) / previous * 100",
            values={"current": str(cur_v), "previous": str(prev_v)},
            result=f"{calc_val:.4f}%",
        ))

    elif "MARGIN" in claim_type_str or "RATIO" in claim_type_str:
        if len(evidence_facts) < 2:
            return VerdictOutcome(
                verdict=VerdictType.INCONCLUSIVE,
                reason_code="MISSING_INPUT",
                reasons=["Margin or ratio requires numerator and denominator facts"],
                input_facts=list(evidence_facts),
                rule_triggered="R6",
            )
        num_v = _to_decimal(_get_val(evidence_facts[0], "value_base"))
        den_v = _to_decimal(_get_val(evidence_facts[1], "value_base"))
        if num_v is None or den_v is None:
            return VerdictOutcome(
                verdict=VerdictType.INCONCLUSIVE,
                reason_code="UNPARSEABLE_CLAIM",
                reasons=["Cannot parse values for margin formula"],
                rule_triggered="R6",
            )
        if den_v == 0:
            return VerdictOutcome(
                verdict=VerdictType.INCONCLUSIVE,
                reason_code="DIVISION_BY_ZERO",
                reasons=["Denominator is zero in ratio calculation"],
                input_facts=list(evidence_facts),
                rule_triggered="R6",
            )
        calc_val = (num_v / den_v) * Decimal("100")
        steps.append(CalculationTraceStep(
            label="Margin/Ratio",
            expr="numerator / denominator * 100",
            values={"numerator": str(num_v), "denominator": str(den_v)},
            result=f"{calc_val:.4f}%",
        ))

    else:
        # Direct STATISTIC claim
        calc_val = _to_decimal(_get_val(evidence_facts[0], "value_base"))
        steps.append(CalculationTraceStep(
            label="Reported Figure",
            expr="value_base",
            values={"fact_id": str(_get_val(evidence_facts[0], "id"))},
            result=str(calc_val),
        ))

    if calc_val is None or claim_num is None:
        return VerdictOutcome(
            verdict=VerdictType.INCONCLUSIVE,
            reason_code="UNPARSEABLE_CLAIM",
            reasons=["Calculation or claim value could not be resolved"],
            rule_triggered="R6",
        )

    dev = abs(calc_val - claim_num)
    effective_tol = tol.effective_tol

    if dev <= effective_tol:
        outcome = VerdictOutcome(
            verdict=VerdictType.CONSISTENT,
            severity=Severity.MATCH,
            reasons=[f"Calculated value ({calc_val:.2f}) matches claim ({claim_num:.2f}) within tolerance ({effective_tol})"],
            calc_value=calc_val,
            claim_value=claim_num,
            deviation=dev,
            tolerance=tol,
            calc_steps=steps,
            input_facts=list(evidence_facts),
            derived=derived_used,
            gate_clean=True,
            rule_triggered="R6",
        )
    else:
        # Severity assignment: dev <= 3*tol => NearMiss, else Material
        sev = Severity.NEAR_MISS if dev <= (Decimal("3") * effective_tol) else Severity.MATERIAL
        outcome = VerdictOutcome(
            verdict=VerdictType.CONFLICTING,
            severity=sev,
            reasons=[f"Calculated value ({calc_val:.2f}) diverges from claim ({claim_num:.2f}) by {dev:.2f} (tol: {effective_tol})"],
            calc_value=calc_val,
            claim_value=claim_num,
            deviation=dev,
            tolerance=tol,
            calc_steps=steps,
            input_facts=list(evidence_facts),
            derived=derived_used,
            gate_clean=True,
            rule_triggered="R6",
        )

    return _apply_skeptic(outcome, skeptic_reason)


def _apply_skeptic(outcome: VerdictOutcome, skeptic_reason: Optional[str]) -> VerdictOutcome:
    """Skeptic may downgrade Consistent/Conflicting -> Inconclusive, never the reverse."""
    if skeptic_reason and outcome.verdict in (VerdictType.CONSISTENT, VerdictType.CONFLICTING):
        return VerdictOutcome(
            verdict=VerdictType.INCONCLUSIVE,
            reason_code="SKEPTIC_FLAG",
            reasons=[f"Downgraded by skeptic: {skeptic_reason}"] + outcome.reasons,
            calc_value=outcome.calc_value,
            claim_value=outcome.claim_value,
            deviation=outcome.deviation,
            tolerance=outcome.tolerance,
            calc_steps=outcome.calc_steps,
            input_facts=outcome.input_facts,
            derived=outcome.derived,
            gate_clean=False,
            rule_triggered="SKEPTIC",
        )
    return outcome
