"""Strong-Conclusion Guard (Architecture §10.4 — Task 1.8).

Enforces conclusion strength labels and explicitly surfaces why strong conclusions were capped:
- Disproved: verdict Conflicting + Material severity + csv/table or confirmed + >=1 locator + clean doc + clean gate
- Confirmed: verdict Consistent + Match severity + csv/table or confirmed + >=1 locator + clean doc + clean gate
- Indicative: verdict decided, but capped due to NearMiss, unconfirmed regex/llm, derived value, missing locator, or doc warnings
- Insufficient: any Inconclusive verdict
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence

from .verdict import Severity, VerdictOutcome, VerdictType


class ConclusionStrength(str, Enum):
    DISPROVED = "disproved"
    CONFIRMED = "confirmed"
    INDICATIVE = "indicative"
    INSUFFICIENT = "insufficient"


@dataclass
class GuardResult:
    strength: ConclusionStrength
    cap_reasons: List[str] = field(default_factory=list)
    is_capped: bool = False
    verdict: VerdictType = VerdictType.INCONCLUSIVE
    severity: Optional[Severity] = None


def _get_attr(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def has_valid_locator(fact: Any) -> bool:
    """Verifies that a fact has at least one physical document provenance anchor."""
    loc = _get_attr(fact, "locator")
    if not loc:
        return False
    # If loc is an object or dict, inspect fields
    page = _get_attr(loc, "page")
    bbox = _get_attr(loc, "bbox")
    table_id = _get_attr(loc, "table_id")
    row = _get_attr(loc, "row")
    col = _get_attr(loc, "col")
    char_span = _get_attr(loc, "char_span")
    quote = _get_attr(loc, "quote")

    return bool(
        page is not None
        or bbox is not None
        or table_id is not None
        or (row is not None and col is not None)
        or char_span is not None
        or quote
    )


def apply_guard(
    outcome: VerdictOutcome,
    document_warnings: Optional[Dict[str, List[str]]] = None,
) -> GuardResult:
    """Enforces Strong-Conclusion Guard rules per Architecture Table 10.4.
    
    Returns a GuardResult containing the conclusion strength and an explicit
    list of cap reasons if the conclusion was capped.
    """
    cap_reasons: List[str] = []

    # -----------------------------------------------------------------------
    # Case 1: Insufficient Evidence (Any Inconclusive verdict)
    # -----------------------------------------------------------------------
    if outcome.verdict == VerdictType.INCONCLUSIVE:
        primary_reason = outcome.reason_code or "INCONCLUSIVE_VERDICT"
        details = f": {'; '.join(outcome.reasons)}" if outcome.reasons else ""
        cap_reasons.append(f"Inconclusive verdict [{primary_reason}]{details}")
        return GuardResult(
            strength=ConclusionStrength.INSUFFICIENT,
            cap_reasons=cap_reasons,
            is_capped=True,
            verdict=outcome.verdict,
            severity=outcome.severity,
        )

    # -----------------------------------------------------------------------
    # Provenance and Quality Checks for Decided Verdicts
    # -----------------------------------------------------------------------
    input_facts = outcome.input_facts or []

    # Check 1: NearMiss severity for Conflicting verdicts
    if outcome.verdict == VerdictType.CONFLICTING and outcome.severity == Severity.NEAR_MISS:
        cap_reasons.append(
            "Capped from Disproved: Severity is NearMiss (within 3x tolerance), which is indicative rather than material contradiction"
        )

    # Check 2: Method check (csv/table or human-confirmed)
    for idx, fact in enumerate(input_facts):
        method = str(_get_attr(fact, "method", "table")).lower()
        confirmed = bool(_get_attr(fact, "confirmed", False))
        fact_id = _get_attr(fact, "id", f"fact_{idx}")

        if method in ("regex", "llm") and not confirmed:
            cap_reasons.append(
                f"Capped to Indicative: Input fact '{fact_id}' extracted via probabilistic '{method}' without human confirmation"
            )

    # Check 3: Locator provenance check (must have >= 1 physical locator)
    for idx, fact in enumerate(input_facts):
        fact_id = _get_attr(fact, "id", f"fact_{idx}")
        if not has_valid_locator(fact):
            cap_reasons.append(
                f"Capped to Indicative: Input fact '{fact_id}' lacks document physical locator/receipt"
            )

    # Check 4: Derived fact check (e.g. Q1-Q4 algebra used instead of annual report)
    if outcome.derived:
        cap_reasons.append(
            "Capped to Indicative: Input values were derived algebraically across periods rather than reported as a single filing"
        )

    # Check 5: Document quality warnings check
    if document_warnings:
        for idx, fact in enumerate(input_facts):
            doc_id = _get_attr(fact, "document_id")
            if doc_id and doc_id in document_warnings and document_warnings[doc_id]:
                warn_list = ", ".join(document_warnings[doc_id])
                cap_reasons.append(
                    f"Capped to Indicative: Source document '{doc_id}' has open data quality issues ({warn_list})"
                )

    # Check 6: Gate cleanliness check
    if not outcome.gate_clean:
        cap_reasons.append(
            "Capped to Indicative: Comparability gate resolved with caveats or skeptic adjustments"
        )

    # -----------------------------------------------------------------------
    # Assign Strength
    # -----------------------------------------------------------------------
    if cap_reasons:
        return GuardResult(
            strength=ConclusionStrength.INDICATIVE,
            cap_reasons=cap_reasons,
            is_capped=True,
            verdict=outcome.verdict,
            severity=outcome.severity,
        )

    # All criteria met for strong conclusions
    if outcome.verdict == VerdictType.CONSISTENT:
        return GuardResult(
            strength=ConclusionStrength.CONFIRMED,
            cap_reasons=[],
            is_capped=False,
            verdict=outcome.verdict,
            severity=outcome.severity,
        )

    if outcome.verdict == VerdictType.CONFLICTING and outcome.severity == Severity.MATERIAL:
        return GuardResult(
            strength=ConclusionStrength.DISPROVED,
            cap_reasons=[],
            is_capped=False,
            verdict=outcome.verdict,
            severity=outcome.severity,
        )

    # Fallback to indicative
    return GuardResult(
        strength=ConclusionStrength.INDICATIVE,
        cap_reasons=["Unmet strong conclusion criteria"],
        is_capped=True,
        verdict=outcome.verdict,
        severity=outcome.severity,
    )
