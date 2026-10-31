"""
comparability.py — Comparability Gate and Period Derivation Engine.

Pure Python, deterministic, no I/O.
Per architecture §10.1 and tasks.md §1.6.
"""
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any
import re

from app.core.metrics import canonicalize_metric, is_additive
from app.core.periods import Period, parse_period

# Standard Reason Codes from Architecture §10.1
REASON_METRIC_MISMATCH = "METRIC_MISMATCH"
REASON_ENTITY_MISMATCH = "ENTITY_MISMATCH"
REASON_PERIOD_MISMATCH = "PERIOD_MISMATCH"
REASON_NOT_COMPARABLE_PERIOD_KIND = "NOT_COMPARABLE_PERIOD_KIND"
REASON_SCOPE_MISMATCH = "SCOPE_MISMATCH"
REASON_BASIS_MISMATCH = "BASIS_MISMATCH"
REASON_CURRENCY_MISMATCH = "CURRENCY_MISMATCH"
REASON_RESTATEMENT_AMBIGUITY = "RESTATEMENT_AMBIGUITY"
REASON_SOURCE_DISAGREEMENT = "SOURCE_DISAGREEMENT"


@dataclass(frozen=True)
class DerivationResult:
    derived_value: Decimal
    period: Period
    component_facts: list[Any]
    formula: str = "Q1 + Q2 + Q3 + Q4"


@dataclass
class GateResult:
    passed: bool
    blocked: bool
    reasons: list[str] = field(default_factory=list)
    reason_details: dict[str, str] = field(default_factory=dict)
    derived: bool = False
    derived_value: Decimal | None = None
    derivation: DerivationResult | None = None
    matched_facts: list[Any] = field(default_factory=list)
    same_tier_disagreement: bool = False
    disagreement_facts: list[Any] = field(default_factory=list)


def _get_val(obj: Any, key: str, default: Any = None) -> Any:
    """Extract a field from either a dict or an object attribute."""
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _normalize_entity(name: str | None) -> str:
    """Normalize company / entity name for comparison."""
    if not name:
        return ""
    cleaned = name.lower().strip()
    # Strip common corporate suffixes
    cleaned = re.sub(r"\b(ltd|limited|inc|incorporated|corp|corporation|llc|plc|pvt)\b", "", cleaned)
    cleaned = re.sub(r"[^\w\s]", "", cleaned)
    return re.sub(r"\s+", " ", cleaned).strip()


def _normalize_period(p: Any) -> Period | None:
    """Convert string or Period object into Period."""
    if p is None:
        return None
    if isinstance(p, Period):
        return p
    if isinstance(p, str):
        try:
            return parse_period(p)
        except Exception:
            return None
    if isinstance(p, dict):
        kind = p.get("kind")
        fy = p.get("fy")
        idx = p.get("idx")
        fy_end_month = p.get("fy_end_month", 3)
        if kind and fy:
            return Period(kind=kind, fy=int(fy), idx=int(idx) if idx is not None else None, fy_end_month=fy_end_month)
    return None


def derive_fy_from_quarters(quarters: list[Any], metric: str) -> DerivationResult | None:
    """
    Attempt to derive an annual (FY) total by summing all 4 quarters (Q1, Q2, Q3, Q4).
    Only permitted if metric is additive.
    Returns DerivationResult if all 4 quarters exist, else None.
    """
    if not is_additive(metric):
        return None

    # Filter facts that are quarterly
    quarter_facts: dict[int, Any] = {}
    fy_label: int | None = None

    for f in quarters:
        p = _normalize_period(_get_val(f, "period"))
        if p and p.kind == "Q" and p.idx in (1, 2, 3, 4):
            if fy_label is None:
                fy_label = p.fy
            elif fy_label != p.fy:
                continue  # Skip quarters belonging to other fiscal years
            quarter_facts[p.idx] = f

    # All 4 quarters must be present
    if len(quarter_facts) == 4 and fy_label is not None:
        total = Decimal("0")
        components = []
        for idx in (1, 2, 3, 4):
            fact = quarter_facts[idx]
            val = _get_val(fact, "value_base")
            if val is None:
                val = _get_val(fact, "value")
            if val is None:
                return None
            total += Decimal(str(val))
            components.append(fact)

        return DerivationResult(
            derived_value=total,
            period=Period(kind="FY", fy=fy_label),
            component_facts=components,
            formula="Q1 + Q2 + Q3 + Q4",
        )

    return None


def check_comparability_pair(claim: Any, fact: Any) -> list[tuple[str, str]]:
    """
    Check if a single fact is comparable with the claim.
    Returns list of (reason_code, detail_message).
    Empty list means the pair is fully comparable.
    """
    reasons: list[tuple[str, str]] = []

    # 1. Metric check
    claim_metric = canonicalize_metric(str(_get_val(claim, "metric", "")))
    fact_metric = canonicalize_metric(str(_get_val(fact, "metric", "")))
    if not claim_metric or not fact_metric or claim_metric != fact_metric:
        reasons.append(
            (
                REASON_METRIC_MISMATCH,
                f"Metric mismatch: claim metric '{_get_val(claim, 'metric')}' (canonical: {claim_metric}) vs fact metric '{_get_val(fact, 'metric')}' (canonical: {fact_metric})",
            )
        )

    # 2. Entity check
    claim_entity = _normalize_entity(_get_val(claim, "entity"))
    fact_entity = _normalize_entity(_get_val(fact, "entity"))
    if claim_entity and fact_entity and claim_entity != fact_entity:
        reasons.append(
            (
                REASON_ENTITY_MISMATCH,
                f"Entity mismatch: claim entity '{_get_val(claim, 'entity')}' vs fact entity '{_get_val(fact, 'entity')}'",
            )
        )

    # 3. Period and Period Kind check
    claim_p = _normalize_period(_get_val(claim, "period"))
    fact_p = _normalize_period(_get_val(fact, "period"))
    if claim_p and fact_p:
        if claim_p.fy != fact_p.fy:
            reasons.append(
                (
                    REASON_PERIOD_MISMATCH,
                    f"Fiscal year mismatch: claim is FY{claim_p.fy} vs fact is FY{fact_p.fy}",
                )
            )
        elif claim_p.kind != fact_p.kind:
            reasons.append(
                (
                    REASON_NOT_COMPARABLE_PERIOD_KIND,
                    f"Period kind mismatch: claim is {claim_p.kind} vs fact is {fact_p.kind} (quarter vs annual)",
                )
            )
        elif claim_p.idx != fact_p.idx:
            reasons.append(
                (
                    REASON_PERIOD_MISMATCH,
                    f"Period index mismatch: claim is index {claim_p.idx} vs fact is index {fact_p.idx}",
                )
            )

    # 4. Scope check (e.g. consolidated vs standalone)
    claim_scope = (_get_val(claim, "scope") or "consolidated").lower()
    fact_scope = (_get_val(fact, "scope") or "consolidated").lower()
    if claim_scope != fact_scope:
        reasons.append(
            (
                REASON_SCOPE_MISMATCH,
                f"Scope mismatch: claim is '{claim_scope}' vs fact is '{fact_scope}'",
            )
        )

    # 5. Basis check (reported vs adjusted)
    claim_basis = (_get_val(claim, "basis") or "reported").lower()
    fact_basis = (_get_val(fact, "basis") or "reported").lower()
    if claim_basis != fact_basis:
        reasons.append(
            (
                REASON_BASIS_MISMATCH,
                f"Accounting basis mismatch: claim is '{claim_basis}' vs fact is '{fact_basis}'",
            )
        )

    # 6. Currency check
    claim_curr = _get_val(claim, "currency")
    fact_curr = _get_val(fact, "currency")
    if claim_curr and fact_curr and str(claim_curr).upper() != str(fact_curr).upper():
        reasons.append(
            (
                REASON_CURRENCY_MISMATCH,
                f"Currency mismatch: claim currency '{claim_curr}' vs fact currency '{fact_curr}'",
            )
        )

    return reasons


def check_comparability(claim: Any, evidence_facts: list[Any]) -> GateResult:
    """
    Comparability Gate: checks all evidence against the claim per Architecture §10.1.
    If period kinds differ (e.g. Claim is FY but evidence has quarters):
      Attempts period algebra to derive FY from 4 quarters if metric is additive.
    Detects same-tier disagreements among evidence facts.
    """
    if not evidence_facts:
        return GateResult(
            passed=False,
            blocked=True,
            reasons=["MISSING_EVIDENCE"],
            reason_details={"evidence": "No evidence facts provided for verification."},
        )

    claim_metric = canonicalize_metric(str(_get_val(claim, "metric", ""))) or str(_get_val(claim, "metric", ""))
    claim_p = _normalize_period(_get_val(claim, "period"))

    # Check if this is an Annual claim with Quarterly evidence candidates
    if claim_p and claim_p.kind == "FY":
        quarter_candidates = [
            f for f in evidence_facts
            if _normalize_period(_get_val(f, "period"))
            and _normalize_period(_get_val(f, "period")).kind == "Q"
            and _normalize_period(_get_val(f, "period")).fy == claim_p.fy
        ]
        # Direct FY facts
        direct_fy_facts = [
            f for f in evidence_facts
            if _normalize_period(_get_val(f, "period"))
            and _normalize_period(_get_val(f, "period")).kind == "FY"
            and _normalize_period(_get_val(f, "period")).fy == claim_p.fy
        ]

        # If no direct FY facts exist but quarters do:
        if not direct_fy_facts and quarter_candidates:
            if not is_additive(claim_metric):
                return GateResult(
                    passed=False,
                    blocked=True,
                    reasons=[REASON_NOT_COMPARABLE_PERIOD_KIND],
                    reason_details={
                        "derivation": f"Metric '{claim_metric}' is non-additive across quarters. Cannot derive annual total from quarterly components."
                    },
                )
            derivation = derive_fy_from_quarters(quarter_candidates, claim_metric)
            if derivation:
                return GateResult(
                    passed=True,
                    blocked=False,
                    derived=True,
                    derived_value=derivation.derived_value,
                    derivation=derivation,
                    matched_facts=derivation.component_facts,
                )
            else:
                found_quarters = sorted({
                    _normalize_period(_get_val(f, "period")).idx
                    for f in quarter_candidates
                    if _normalize_period(_get_val(f, "period")).idx is not None
                })
                missing = sorted(set([1, 2, 3, 4]) - set(found_quarters))
                return GateResult(
                    passed=False,
                    blocked=True,
                    reasons=[REASON_NOT_COMPARABLE_PERIOD_KIND],
                    reason_details={
                        "derivation": f"Quarter vs annual: Incomplete quarters for FY{claim_p.fy} derivation (found Q{found_quarters}, missing Q{missing})."
                    },
                )

    # Check each fact against claim
    matched: list[Any] = []
    accumulated_reasons: list[str] = []
    accumulated_details: dict[str, str] = {}

    for f in evidence_facts:
        pair_issues = check_comparability_pair(claim, f)
        if not pair_issues:
            matched.append(f)
        else:
            for r_code, r_detail in pair_issues:
                if r_code not in accumulated_reasons:
                    accumulated_reasons.append(r_code)
                    accumulated_details[r_code] = r_detail

    # Check if we matched any comparable facts
    if not matched:
        return GateResult(
            passed=False,
            blocked=True,
            reasons=accumulated_reasons or ["NOT_COMPARABLE"],
            reason_details=accumulated_details,
        )

    # Check same-tier disagreement among matched facts
    # Disagreement: same tier, same metric, same period, different values
    by_tier: dict[str, list[Any]] = {}
    for f in matched:
        tier = str(_get_val(f, "source_tier", "T1"))
        by_tier.setdefault(tier, []).append(f)

    disagreement_found = False
    disagreement_facts: list[Any] = []

    for tier, facts in by_tier.items():
        if len(facts) > 1:
            vals = set()
            for fact in facts:
                v = _get_val(fact, "value_base")
                if v is None:
                    v = _get_val(fact, "value")
                if v is not None:
                    vals.add(Decimal(str(v)))
            if len(vals) > 1:
                disagreement_found = True
                disagreement_facts.extend(facts)

    if disagreement_found:
        return GateResult(
            passed=False,
            blocked=True,
            reasons=[REASON_SOURCE_DISAGREEMENT],
            reason_details={
                "disagreement": f"Multiple facts from the same source tier report contradictory values: {[str(_get_val(f, 'value')) for f in disagreement_facts]}"
            },
            matched_facts=matched,
            same_tier_disagreement=True,
            disagreement_facts=disagreement_facts,
        )

    return GateResult(
        passed=True,
        blocked=False,
        matched_facts=matched,
    )
