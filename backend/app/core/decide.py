"""
ContradictIQ — Deterministic Verification Engine Facade
======================================================
Task 1.9: decide() public facade + engine_version constant.

This module provides the single deterministic entry point used by the
verification API, evaluation harness, and test suites. Pure Python, no I/O,
no LLM dependencies.

Architecture References:
- architecture.md §10 (Comparability Gate & Verdict Engine)
- architecture.md §8 (Normalization)
- architecture.md §9 (Metric Registry & Formulas)
- architecture.md §10.4 (Strong-Conclusion Guard)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Literal, Optional, Tuple, Union

# Public engine version constant (Architecture §10.2, §18)
ENGINE_VERSION: str = "0.1.0"
engine_version: str = ENGINE_VERSION

# Scale multipliers
SCALES: Dict[str, Decimal] = {
    "unit": Decimal("1"),
    "k": Decimal("1000"),
    "thousand": Decimal("1000"),
    "lakh": Decimal("100000"),
    "million": Decimal("1000000"),
    "mn": Decimal("1000000"),
    "crore": Decimal("10000000"),
    "cr": Decimal("10000000"),
    "billion": Decimal("1000000000"),
    "bn": Decimal("1000000000"),
}

# Metric registry: canonical name -> additive flag and synonyms
METRIC_REGISTRY: Dict[str, Dict[str, Any]] = {
    "revenue": {
        "additive": True,
        "synonyms": ["revenue", "net sales", "turnover", "total income from operations", "revenue from operations", "sales"],
    },
    "cogs": {
        "additive": True,
        "synonyms": ["cogs", "cost of goods sold", "cost of materials consumed", "cost of sales"],
    },
    "gross_profit": {
        "additive": True,
        "synonyms": ["gross profit", "gross margin"],
    },
    "operating_expenses": {
        "additive": True,
        "synonyms": ["operating expenses", "opex", "operating costs", "total operating expenses"],
    },
    "operating_income": {
        "additive": True,
        "synonyms": ["operating income", "operating profit", "ebit"],
    },
    "ebitda": {
        "additive": True,
        "synonyms": ["ebitda"],
    },
    "net_income": {
        "additive": True,
        "synonyms": ["net income", "profit after tax", "pat", "net profit"],
    },
    "total_expenses": {
        "additive": True,
        "synonyms": ["total expenses"],
    },
}


@dataclass(frozen=True)
class Period:
    """Normalized period representation per architecture §8.2."""
    kind: Literal["Q", "H", "9M", "FY", "TTM"]
    fy: int
    idx: Optional[int] = None
    fy_end_month: int = 3

    @classmethod
    def from_any(cls, val: Any) -> Optional["Period"]:
        if isinstance(val, Period):
            return val
        if isinstance(val, dict):
            return cls(
                kind=val.get("kind", "FY"),
                fy=int(val.get("fy", 0)),
                idx=int(val["idx"]) if val.get("idx") is not None else None,
                fy_end_month=int(val.get("fy_end_month", 3)),
            )
        if isinstance(val, str):
            s = val.strip().upper()
            if s.startswith("FY"):
                fy_str = s[2:].strip()
                fy = int(fy_str) if len(fy_str) == 4 else int("20" + fy_str)
                return cls(kind="FY", fy=fy)
            if s.startswith("Q") and "FY" in s:
                parts = s.split("FY")
                q_idx = int(parts[0].replace("Q", "").strip())
                fy_str = parts[1].strip()
                fy = int(fy_str) if len(fy_str) == 4 else int("20" + fy_str)
                return cls(kind="Q", fy=fy, idx=q_idx)
            if s.startswith("H") and "FY" in s:
                parts = s.split("FY")
                h_idx = int(parts[0].replace("H", "").strip())
                fy_str = parts[1].strip()
                fy = int(fy_str) if len(fy_str) == 4 else int("20" + fy_str)
                return cls(kind="H", fy=fy, idx=h_idx)
        return None

    def prev_year(self) -> "Period":
        return Period(kind=self.kind, fy=self.fy - 1, idx=self.idx, fy_end_month=self.fy_end_month)

    def prev_quarter(self) -> "Period":
        if self.kind != "Q" or self.idx is None:
            return self.prev_year()
        if self.idx > 1:
            return Period(kind="Q", fy=self.fy, idx=self.idx - 1, fy_end_month=self.fy_end_month)
        return Period(kind="Q", fy=self.fy - 1, idx=4, fy_end_month=self.fy_end_month)

    def key(self) -> str:
        if self.idx is not None:
            return f"{self.kind}{self.idx}_FY{self.fy}"
        return f"{self.kind}_FY{self.fy}"


@dataclass
class Step:
    """A calculation trace step."""
    label: str
    expr: str
    values: Dict[str, Any]
    result: Decimal


@dataclass
class CalcResult:
    """Output of a deterministic formula calculation."""
    formula_id: str
    value: Decimal
    unit: str
    steps: List[Step] = field(default_factory=list)
    inputs: List[str] = field(default_factory=list)
    tolerance: Decimal = field(default_factory=lambda: Decimal("0.01"))
    derived: bool = False


@dataclass
class EvidenceLink:
    """Link between finding and source fact."""
    fact_id: str
    stance: Literal["supports", "opposes", "neutral", "not_comparable"]
    document_id: Optional[str] = None
    locator: Optional[Dict[str, Any]] = None
    note: Optional[str] = None


@dataclass
class EngineConfig:
    """Runtime parameters for the verification engine."""
    min_conf: float = 0.70
    approx_multiplier: Decimal = Decimal("2.0")
    min_abs_tol: Decimal = Decimal("0.01")
    engine_version: str = ENGINE_VERSION


@dataclass
class VerdictResult:
    """Standardized output of decide() public facade."""
    verdict: Literal["Consistent", "Conflicting", "Inconclusive"]
    severity: Optional[Literal["Match", "NearMiss", "Material"]]
    reasons: List[str] = field(default_factory=list)
    conclusion_strength: Literal["Confirmed", "Indicative", "Insufficient evidence", "Disproved"] = "Insufficient evidence"
    cap_reasons: List[str] = field(default_factory=list)
    calculation: Optional[CalcResult] = None
    evidence_links: List[EvidenceLink] = field(default_factory=list)
    narrative: str = ""
    engine_version: str = ENGINE_VERSION

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to serializable dictionary for API/eval harness."""
        return {
            "verdict": self.verdict,
            "severity": self.severity,
            "reasons": self.reasons,
            "conclusion_strength": self.conclusion_strength,
            "cap_reasons": self.cap_reasons,
            "narrative": self.narrative,
            "engine_version": self.engine_version,
            "calculation": (
                {
                    "formula_id": self.calculation.formula_id,
                    "value": float(self.calculation.value),
                    "unit": self.calculation.unit,
                    "derived": self.calculation.derived,
                    "tolerance": float(self.calculation.tolerance),
                    "steps": [
                        {
                            "label": s.label,
                            "expr": s.expr,
                            "values": {k: float(v) if isinstance(v, Decimal) else v for k, v in s.values.items()},
                            "result": float(s.result),
                        }
                        for s in self.calculation.steps
                    ],
                }
                if self.calculation
                else None
            ),
            "evidence_links": [
                {
                    "fact_id": link.fact_id,
                    "stance": link.stance,
                    "document_id": link.document_id,
                    "locator": link.locator,
                    "note": link.note,
                }
                for link in self.evidence_links
            ],
        }


def _canonicalize_metric(name: Optional[str]) -> Optional[str]:
    """Map raw metric labels or aliases to canonical registry metrics."""
    if not name:
        return None
    raw = name.strip().lower()
    for canonical, info in METRIC_REGISTRY.items():
        if raw == canonical or raw in info["synonyms"]:
            return canonical
    return raw


def _to_decimal(val: Any) -> Optional[Decimal]:
    """Convert input string/number/Decimal to Decimal."""
    if val is None:
        return None
    if isinstance(val, Decimal):
        return val
    if isinstance(val, (int, float)):
        return Decimal(str(val))
    if isinstance(val, str):
        cleaned = val.replace(",", "").replace("$", "").replace("₹", "").replace("€", "").replace("%", "").strip()
        if cleaned.startswith("(") and cleaned.endswith(")"):
            cleaned = "-" + cleaned[1:-1]
        try:
            return Decimal(cleaned)
        except InvalidOperation:
            return None
    return None


def _get_val(obj: Any, key: str, default: Any = None) -> Any:
    """Helper to access dict or object attributes transparently."""
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _compute_tolerance(claim_val: Decimal, precision: int, hedged: bool, cfg: EngineConfig, is_percent: bool) -> Decimal:
    """Compute precision-aware half-ULP tolerance per architecture §10.3."""
    if is_percent:
        half_ulp = Decimal("5") * (Decimal("10") ** -(precision + 1))
        approx = cfg.approx_multiplier if hedged else Decimal("1.0")
        return max(half_ulp * approx, cfg.min_abs_tol)
    else:
        half_ulp = Decimal("5") * (Decimal("10") ** -(precision + 1))
        approx = cfg.approx_multiplier if hedged else Decimal("1.0")
        # Relative tolerance based on claim magnitude
        rel_tol = max(half_ulp * approx, cfg.min_abs_tol)
        return max(abs(claim_val) * rel_tol / Decimal("100"), cfg.min_abs_tol)


def decide(claim: Any, evidence_facts: List[Any], cfg: Optional[EngineConfig] = None) -> VerdictResult:
    """
    Deterministic Verification Engine Entry Point (Public Facade).

    Evaluates a claim against a list of evidence facts using ordered rules R1–R6
    and enforces the Strong-Conclusion Guard.

    Args:
        claim: Dict or Claim object containing claim text, metric, value, period, etc.
        evidence_facts: List of Dict or Fact objects extracted from documents.
        cfg: Optional EngineConfig for tolerance and confidence thresholds.

    Returns:
        VerdictResult containing verdict, severity, reasons, calculation trace,
        and conclusion strength label.
    """
    if cfg is None:
        cfg = EngineConfig()

    # -------------------------------------------------------------
    # R1: Unparseable claim check
    # -------------------------------------------------------------
    parseable = _get_val(claim, "parseable", True)
    if not parseable:
        return VerdictResult(
            verdict="Inconclusive",
            severity=None,
            reasons=["UNPARSEABLE_CLAIM"],
            conclusion_strength="Insufficient evidence",
            cap_reasons=["claim_is_unparseable"],
            narrative="Claim is unparseable or cannot be interpreted by the engine.",
            engine_version=cfg.engine_version,
        )

    metric_raw = _get_val(claim, "metric")
    canonical_metric = _canonicalize_metric(metric_raw)
    claim_type = _get_val(claim, "claim_type", "value")
    claim_text = _get_val(claim, "text", "")
    claim_period = Period.from_any(_get_val(claim, "period"))

    # Direct malformed / unmapped check
    if not canonical_metric or (claim_type != "direction" and _to_decimal(_get_val(claim, "value")) is None):
        return VerdictResult(
            verdict="Inconclusive",
            severity=None,
            reasons=["UNPARSEABLE_CLAIM"],
            conclusion_strength="Insufficient evidence",
            cap_reasons=["unmapped_metric_or_missing_value"],
            narrative=f"Claim '{claim_text}' has unmapped metric '{metric_raw}' or invalid numeric value.",
            engine_version=cfg.engine_version,
        )

    # -------------------------------------------------------------
    # R2: Input Planning & Missing Input Check
    # -------------------------------------------------------------
    claim_val = _to_decimal(_get_val(claim, "value"))
    claim_unit = _get_val(claim, "unit", "currency")
    claim_currency = _get_val(claim, "currency", "INR")
    claim_scale = _get_val(claim, "scale", "unit")
    claim_basis = _get_val(claim, "basis", "reported")
    claim_scope = _get_val(claim, "scope", "consolidated")
    claim_entity = _get_val(claim, "entity")
    claim_precision = int(_get_val(claim, "value_precision", 0))
    claim_hedged = bool(_get_val(claim, "hedged", False))

    # Scale normalization for claim value
    scale_mult = SCALES.get(str(claim_scale).lower(), Decimal("1"))
    claim_base_val = (claim_val * scale_mult) if claim_val is not None else None

    # Filter candidate facts by metric
    matching_facts = []
    for f in evidence_facts:
        f_metric = _canonicalize_metric(_get_val(f, "metric"))
        if f_metric == canonical_metric:
            matching_facts.append(f)

    # -------------------------------------------------------------
    # R3: Comparability Gate (architecture §10.1)
    # -------------------------------------------------------------
    # Currency Check
    for f in evidence_facts:
        f_currency = _get_val(f, "currency")
        if f_currency and claim_currency and f_currency.upper() != claim_currency.upper():
            return VerdictResult(
                verdict="Inconclusive",
                severity=None,
                reasons=["CURRENCY_MISMATCH"],
                conclusion_strength="Insufficient evidence",
                cap_reasons=["different_currencies_without_fx_rate"],
                narrative=f"Currency mismatch between claim ({claim_currency}) and fact ({f_currency}) without verified FX.",
                engine_version=cfg.engine_version,
            )

    # Basis Check (reported vs adjusted)
    for f in matching_facts:
        f_basis = _get_val(f, "basis", "reported")
        if f_basis and claim_basis and f_basis.lower() != claim_basis.lower():
            return VerdictResult(
                verdict="Inconclusive",
                severity=None,
                reasons=["BASIS_MISMATCH"],
                conclusion_strength="Insufficient evidence",
                cap_reasons=["adjusted_vs_reported_basis_conflict"],
                narrative=f"Basis mismatch: claim basis is {claim_basis} but evidence basis is {f_basis}.",
                engine_version=cfg.engine_version,
            )

    # Entity Check
    if claim_entity:
        for f in matching_facts:
            f_entity = _get_val(f, "entity")
            if f_entity and f_entity.strip().lower() != claim_entity.strip().lower():
                return VerdictResult(
                    verdict="Inconclusive",
                    severity=None,
                    reasons=["ENTITY_MISMATCH"],
                    conclusion_strength="Insufficient evidence",
                    cap_reasons=["entity_mismatch"],
                    narrative=f"Entity mismatch: claim entity '{claim_entity}' does not match evidence '{f_entity}'.",
                    engine_version=cfg.engine_version,
                )

    # Scope Check
    for f in matching_facts:
        f_scope = _get_val(f, "scope", "consolidated")
        if f_scope and claim_scope and f_scope.lower() != claim_scope.lower():
            return VerdictResult(
                verdict="Inconclusive",
                severity=None,
                reasons=["SCOPE_MISMATCH"],
                conclusion_strength="Insufficient evidence",
                cap_reasons=["scope_mismatch"],
                narrative=f"Scope mismatch: claim scope {claim_scope} vs evidence scope {f_scope}.",
                engine_version=cfg.engine_version,
            )

    # Formula-based input planning: YoY Growth
    if claim_type == "growth_yoy":
        if not claim_period:
            return VerdictResult(
                verdict="Inconclusive",
                severity=None,
                reasons=["MISSING_INPUT"],
                conclusion_strength="Insufficient evidence",
                narrative="Period is required to compute YoY growth.",
                engine_version=cfg.engine_version,
            )
        prev_period = claim_period.prev_year()
        cur_fact = next((f for f in matching_facts if Period.from_any(_get_val(f, "period")) == claim_period), None)
        prev_fact = next((f for f in matching_facts if Period.from_any(_get_val(f, "period")) == prev_period), None)

        if not cur_fact:
            return VerdictResult(
                verdict="Inconclusive",
                severity=None,
                reasons=[f"MISSING_INPUT: {canonical_metric} {claim_period.key()}"],
                conclusion_strength="Insufficient evidence",
                narrative=f"Missing current period fact for {canonical_metric} in {claim_period.key()}.",
                engine_version=cfg.engine_version,
            )
        if not prev_fact:
            return VerdictResult(
                verdict="Inconclusive",
                severity=None,
                reasons=[f"MISSING_INPUT: {canonical_metric} {prev_period.key()}"],
                conclusion_strength="Insufficient evidence",
                narrative=f"Missing prior year base fact for {canonical_metric} in {prev_period.key()}.",
                engine_version=cfg.engine_version,
            )

        cur_val = _to_decimal(_get_val(cur_fact, "value_base") or _get_val(cur_fact, "value_raw"))
        prev_val = _to_decimal(_get_val(prev_fact, "value_base") or _get_val(prev_fact, "value_raw"))

        if prev_val is None or prev_val <= Decimal("0"):
            return VerdictResult(
                verdict="Inconclusive",
                severity=None,
                reasons=["UNDEFINED_GROWTH_BASE"],
                conclusion_strength="Insufficient evidence",
                narrative="YoY growth base is zero or negative; division undefined.",
                engine_version=cfg.engine_version,
            )

        growth = ((cur_val - prev_val) / prev_val) * Decimal("100")
        tol = _compute_tolerance(claim_val, claim_precision, claim_hedged, cfg, is_percent=True)
        dev = abs(growth - claim_val)

        calc = CalcResult(
            formula_id="growth_yoy",
            value=growth,
            unit="percent",
            steps=[
                Step("Base Inputs", "cur, prev", {"cur": cur_val, "prev": prev_val}, cur_val),
                Step("YoY Growth", "(cur - prev) / prev * 100", {"diff": cur_val - prev_val, "base": prev_val}, growth),
            ],
            inputs=[str(_get_val(cur_fact, "id", "f1")), str(_get_val(prev_fact, "id", "f2"))],
            tolerance=tol,
            derived=False,
        )

        links = [
            EvidenceLink(
                fact_id=str(_get_val(cur_fact, "id")),
                stance="supports" if dev <= tol else "opposes",
                document_id=_get_val(cur_fact, "document_id"),
                locator=_get_val(cur_fact, "locator"),
            ),
            EvidenceLink(
                fact_id=str(_get_val(prev_fact, "id")),
                stance="supports" if dev <= tol else "opposes",
                document_id=_get_val(prev_fact, "document_id"),
                locator=_get_val(prev_fact, "locator"),
            ),
        ]

        if dev <= tol:
            return VerdictResult(
                verdict="Consistent",
                severity="Match",
                reasons=[],
                conclusion_strength="Confirmed",
                calculation=calc,
                evidence_links=links,
                narrative=f"Computed YoY growth = {growth:.2f}%; matches claim {claim_val}% within tolerance {tol} pp.",
                engine_version=cfg.engine_version,
            )
        else:
            sev = "NearMiss" if dev <= Decimal("3") * tol else "Material"
            strength = "Disproved" if sev == "Material" else "Indicative"
            return VerdictResult(
                verdict="Conflicting",
                severity=sev,
                reasons=[f"DEVIATION_EXCEEDS_TOLERANCE: diff={dev:.2f}pp"],
                conclusion_strength=strength,
                calculation=calc,
                evidence_links=links,
                narrative=f"Computed YoY growth = {growth:.2f}%; claim states {claim_val}%; deviation {dev:.2f} pp exceeds tolerance {tol} pp.",
                engine_version=cfg.engine_version,
            )

    # Margin / Formula planning: Margin calculation
    if claim_type in ("margin", "ratio", "operating_margin", "gross_margin", "net_margin"):
        margin_metric_map = {
            "operating_margin": ("operating_income", "revenue"),
            "gross_margin": ("gross_profit", "revenue"),
            "net_margin": ("net_income", "revenue"),
        }
        num_m, den_m = margin_metric_map.get(canonical_metric, ("operating_income", "revenue"))
        num_fact = next((f for f in evidence_facts if _canonicalize_metric(_get_val(f, "metric")) == num_m), None)
        den_fact = next((f for f in evidence_facts if _canonicalize_metric(_get_val(f, "metric")) == den_m), None)

        if not num_fact:
            return VerdictResult(
                verdict="Inconclusive",
                severity=None,
                reasons=[f"MISSING_INPUT: {num_m}"],
                conclusion_strength="Insufficient evidence",
                narrative=f"Missing input fact for {num_m} needed to compute margin.",
                engine_version=cfg.engine_version,
            )
        if not den_fact:
            return VerdictResult(
                verdict="Inconclusive",
                severity=None,
                reasons=[f"MISSING_INPUT: {den_m}"],
                conclusion_strength="Insufficient evidence",
                narrative=f"Missing input fact for {den_m} needed to compute margin.",
                engine_version=cfg.engine_version,
            )

        num_val = _to_decimal(_get_val(num_fact, "value_base") or _get_val(num_fact, "value_raw"))
        den_val = _to_decimal(_get_val(den_fact, "value_base") or _get_val(den_fact, "value_raw"))

        if den_val is None or den_val == Decimal("0"):
            return VerdictResult(
                verdict="Inconclusive",
                severity=None,
                reasons=["UNDEFINED_GROWTH_BASE"],
                conclusion_strength="Insufficient evidence",
                narrative="Revenue is zero; margin calculation undefined.",
                engine_version=cfg.engine_version,
            )

        computed_margin = (num_val / den_val) * Decimal("100")
        tol = _compute_tolerance(claim_val, claim_precision, claim_hedged, cfg, is_percent=True)
        dev = abs(computed_margin - claim_val)

        calc = CalcResult(
            formula_id=f"{canonical_metric}_formula",
            value=computed_margin,
            unit="percent",
            steps=[Step("Margin", f"{num_m} / {den_m} * 100", {"num": num_val, "den": den_val}, computed_margin)],
            inputs=[str(_get_val(num_fact, "id")), str(_get_val(den_fact, "id"))],
            tolerance=tol,
        )

        if dev <= tol:
            return VerdictResult(
                verdict="Consistent",
                severity="Match",
                reasons=[],
                conclusion_strength="Confirmed",
                calculation=calc,
                narrative=f"Computed {canonical_metric} = {computed_margin:.2f}%; matches claim within tolerance {tol} pp.",
                engine_version=cfg.engine_version,
            )
        else:
            sev = "NearMiss" if dev <= Decimal("3") * tol else "Material"
            strength = "Disproved" if sev == "Material" else "Indicative"
            return VerdictResult(
                verdict="Conflicting",
                severity=sev,
                reasons=[f"DEVIATION_EXCEEDS_TOLERANCE: diff={dev:.2f}pp"],
                conclusion_strength=strength,
                calculation=calc,
                narrative=f"Computed {canonical_metric} = {computed_margin:.2f}%; claim states {claim_val}%; deviation {dev:.2f} pp exceeds tolerance.",
                engine_version=cfg.engine_version,
            )

    # Direction Claims ("revenue declined")
    if claim_type == "direction":
        expected_dir = _get_val(claim, "direction", "increase")
        if len(matching_facts) < 2:
            return VerdictResult(
                verdict="Inconclusive",
                severity=None,
                reasons=["MISSING_INPUT: need 2 periods for direction claim"],
                conclusion_strength="Insufficient evidence",
                narrative="Direction claims require at least two sequential periods.",
                engine_version=cfg.engine_version,
            )
        v1 = _to_decimal(_get_val(matching_facts[0], "value_base") or _get_val(matching_facts[0], "value_raw"))
        v2 = _to_decimal(_get_val(matching_facts[1], "value_base") or _get_val(matching_facts[1], "value_raw"))
        diff = v2 - v1
        if diff == Decimal("0"):
            return VerdictResult(
                verdict="Inconclusive",
                severity=None,
                reasons=["ZERO_CHANGE"],
                conclusion_strength="Insufficient evidence",
                narrative="Direction claim inconclusive: zero change observed between periods.",
                engine_version=cfg.engine_version,
            )
        observed_dir = "increase" if diff > 0 else "decrease"
        if observed_dir == expected_dir:
            return VerdictResult(
                verdict="Consistent",
                severity="Match",
                reasons=[],
                conclusion_strength="Confirmed",
                narrative=f"Direction claim confirmed: {observed_dir}.",
                engine_version=cfg.engine_version,
            )
        else:
            return VerdictResult(
                verdict="Conflicting",
                severity="Material",
                reasons=[f"DIRECTION_MISMATCH: expected {expected_dir}, observed {observed_dir}"],
                conclusion_strength="Disproved",
                narrative=f"Direction conflict: claimed {expected_dir} but observed {observed_dir}.",
                engine_version=cfg.engine_version,
            )

    # -------------------------------------------------------------
    # Standard Value Claim Verification & Periodicity Check
    # -------------------------------------------------------------
    if not matching_facts:
        return VerdictResult(
            verdict="Inconclusive",
            severity=None,
            reasons=[f"MISSING_INPUT: {canonical_metric}"],
            conclusion_strength="Insufficient evidence",
            cap_reasons=["no_facts_found_for_metric"],
            narrative=f"No facts found in evidence for canonical metric '{canonical_metric}'.",
            engine_version=cfg.engine_version,
        )

    # Period Matching & Quarter-vs-Annual Trap Handling (Test B1)
    direct_period_facts = []
    quarter_facts = []

    for f in matching_facts:
        p = Period.from_any(_get_val(f, "period"))
        if p and claim_period:
            if p == claim_period:
                direct_period_facts.append(f)
            elif claim_period.kind == "FY" and p.kind == "Q" and p.fy == claim_period.fy:
                quarter_facts.append(f)
        elif not claim_period:
            direct_period_facts.append(f)

    # Quarter vs Annual Trap Check
    if claim_period and claim_period.kind == "FY" and not direct_period_facts and quarter_facts:
        metric_info = METRIC_REGISTRY.get(canonical_metric, {"additive": True})
        if metric_info.get("additive", True):
            # Check if all 4 quarters exist
            q_indices = {Period.from_any(_get_val(f, "period")).idx for f in quarter_facts if Period.from_any(_get_val(f, "period"))}
            if {1, 2, 3, 4}.issubset(q_indices):
                # Derive FY by summing 4 quarters
                derived_sum = Decimal("0")
                step_vals = {}
                inputs = []
                for q in (1, 2, 3, 4):
                    qf = next(f for f in quarter_facts if Period.from_any(_get_val(f, "period")).idx == q)
                    val = _to_decimal(_get_val(qf, "value_base") or _get_val(qf, "value_raw"))
                    derived_sum += val
                    step_vals[f"Q{q}"] = val
                    inputs.append(str(_get_val(qf, "id", f"q{q}")))

                calc = CalcResult(
                    formula_id="derive_annual_sum",
                    value=derived_sum,
                    unit=claim_unit,
                    steps=[Step("Derive FY", "Q1 + Q2 + Q3 + Q4", step_vals, derived_sum)],
                    inputs=inputs,
                    derived=True,
                )

                dev = abs(derived_sum - (claim_base_val or Decimal("0")))
                tol = _compute_tolerance(claim_val, claim_precision, claim_hedged, cfg, is_percent=False)

                if dev <= tol:
                    return VerdictResult(
                        verdict="Consistent",
                        severity="Match",
                        reasons=[],
                        conclusion_strength="Indicative",  # Capped at Indicative because derived
                        cap_reasons=["derived_value_used"],
                        calculation=calc,
                        narrative=f"Derived FY {claim_period.fy} sum = {derived_sum}; matches claim within tolerance.",
                        engine_version=cfg.engine_version,
                    )
                else:
                    sev = "NearMiss" if dev <= Decimal("3") * tol else "Material"
                    return VerdictResult(
                        verdict="Conflicting",
                        severity=sev,
                        reasons=[f"DEVIATION_EXCEEDS_TOLERANCE: diff={dev}"],
                        conclusion_strength="Indicative",
                        calculation=calc,
                        narrative=f"Derived FY sum {derived_sum} conflicts with claimed {claim_base_val}.",
                        engine_version=cfg.engine_version,
                    )
            else:
                # Incomplete quarters vs annual: reject comparability
                return VerdictResult(
                    verdict="Inconclusive",
                    severity=None,
                    reasons=["NOT_COMPARABLE", "quarter vs annual"],
                    conclusion_strength="Insufficient evidence",
                    cap_reasons=["quarter_vs_annual_period_mismatch"],
                    narrative=f"Periodicity mismatch: claim is annual (FY{claim_period.fy}) but only partial quarterly facts are available.",
                    engine_version=cfg.engine_version,
                )

    # If claim was a quarter and compared to an annual fact without comparability
    if claim_period and claim_period.kind == "Q" and not direct_period_facts:
        annual_facts = [f for f in matching_facts if Period.from_any(_get_val(f, "period")) and Period.from_any(_get_val(f, "period")).kind == "FY"]
        if annual_facts:
            return VerdictResult(
                verdict="Inconclusive",
                severity=None,
                reasons=["NOT_COMPARABLE", "quarter vs annual"],
                conclusion_strength="Insufficient evidence",
                cap_reasons=["quarter_vs_annual_period_mismatch"],
                narrative="Cannot directly compare quarterly claim to annual filing fact.",
                engine_version=cfg.engine_version,
            )

    if not direct_period_facts:
        return VerdictResult(
            verdict="Inconclusive",
            severity=None,
            reasons=[f"MISSING_INPUT: {canonical_metric} for period"],
            conclusion_strength="Insufficient evidence",
            narrative=f"No facts found for metric {canonical_metric} in stated period.",
            engine_version=cfg.engine_version,
        )

    # -------------------------------------------------------------
    # R4: Source Disagreement / Restatement Check (Test B4)
    # -------------------------------------------------------------
    first_fact_val = None
    disagreement_found = False
    restatement_found = False

    for f in direct_period_facts:
        val = _to_decimal(_get_val(f, "value_base") or _get_val(f, "value_raw"))
        is_restated = _get_val(f, "restated", False)
        if is_restated:
            restatement_found = True
        if first_fact_val is None:
            first_fact_val = val
        else:
            if val is not None and abs(val - first_fact_val) > cfg.min_abs_tol:
                disagreement_found = True

    if disagreement_found:
        if restatement_found:
            return VerdictResult(
                verdict="Inconclusive",
                severity=None,
                reasons=["RESTATEMENT_AMBIGUITY"],
                conclusion_strength="Insufficient evidence",
                cap_reasons=["source_disagreement_with_restatements"],
                narrative="Multiple versions of financial figures exist due to restatement ambiguity.",
                engine_version=cfg.engine_version,
            )
        return VerdictResult(
            verdict="Inconclusive",
            severity=None,
            reasons=["SOURCE_DISAGREEMENT"],
            conclusion_strength="Insufficient evidence",
            cap_reasons=["conflicting_evidence_from_same_tier_documents"],
            narrative="Source disagreement: two documents in the same tier report conflicting figures for the same period.",
            engine_version=cfg.engine_version,
        )

    # -------------------------------------------------------------
    # R5: Confidence check
    # -------------------------------------------------------------
    min_confidence = min(float(_get_val(f, "confidence", 1.0)) for f in direct_period_facts)
    all_confirmed = all(bool(_get_val(f, "confirmed", False)) for f in direct_period_facts)
    if min_confidence < cfg.min_conf and not all_confirmed:
        return VerdictResult(
            verdict="Inconclusive",
            severity=None,
            reasons=["LOW_CONFIDENCE_EXTRACTION"],
            conclusion_strength="Insufficient evidence",
            cap_reasons=["low_confidence_fact_extraction"],
            narrative=f"Fact extraction confidence {min_confidence:.2f} is below minimum threshold {cfg.min_conf}.",
            engine_version=cfg.engine_version,
        )

    # -------------------------------------------------------------
    # R6: Compute + Compare with Precision-Aware Tolerance
    # -------------------------------------------------------------
    chosen_fact = direct_period_facts[0]
    fact_scale = _get_val(chosen_fact, "scale", "unit")
    fact_scale_mult = SCALES.get(str(fact_scale).lower(), Decimal("1"))
    fact_val = _to_decimal(_get_val(chosen_fact, "value_base") or _get_val(chosen_fact, "value_raw"))

    # If fact_val was raw and not pre-scaled to base units
    if _get_val(chosen_fact, "value_base") is None and fact_scale_mult != Decimal("1"):
        fact_base_val = fact_val * fact_scale_mult
    else:
        fact_base_val = fact_val

    is_percent = (claim_unit == "percent")
    tol = _compute_tolerance(claim_val or Decimal("0"), claim_precision, claim_hedged, cfg, is_percent=is_percent)

    # Compare base values
    target_claim_val = claim_base_val if claim_base_val is not None else claim_val
    dev = abs((fact_base_val or Decimal("0")) - (target_claim_val or Decimal("0")))

    calc = CalcResult(
        formula_id="identity_comparison",
        value=fact_base_val,
        unit=claim_unit,
        steps=[Step("Identity", "fact_base_val", {"fact": fact_base_val, "claim": target_claim_val}, fact_base_val)],
        inputs=[str(_get_val(chosen_fact, "id", "f1"))],
        tolerance=tol,
    )

    links = [
        EvidenceLink(
            fact_id=str(_get_val(chosen_fact, "id")),
            stance="supports" if dev <= tol else "opposes",
            document_id=_get_val(chosen_fact, "document_id"),
            locator=_get_val(chosen_fact, "locator"),
        )
    ]

    method = _get_val(chosen_fact, "method", "table")
    has_locator = _get_val(chosen_fact, "locator") is not None
    is_solid_provenance = (method in ("csv", "table") or _get_val(chosen_fact, "confirmed", False)) and has_locator

    if dev <= tol:
        strength = "Confirmed" if is_solid_provenance else "Indicative"
        cap = [] if is_solid_provenance else ["unconfirmed_or_missing_locator"]
        return VerdictResult(
            verdict="Consistent",
            severity="Match",
            reasons=[],
            conclusion_strength=strength,
            cap_reasons=cap,
            calculation=calc,
            evidence_links=links,
            narrative=f"Evidence value {fact_base_val} matches claim {target_claim_val} within tolerance.",
            engine_version=cfg.engine_version,
        )
    else:
        sev = "NearMiss" if dev <= Decimal("3") * tol else "Material"
        if sev == "Material" and is_solid_provenance:
            strength = "Disproved"
            cap = []
        else:
            strength = "Indicative"
            cap = ["near_miss_verdict" if sev == "NearMiss" else "unconfirmed_source"]

        return VerdictResult(
            verdict="Conflicting",
            severity=sev,
            reasons=[f"DEVIATION_EXCEEDS_TOLERANCE: diff={dev}"],
            conclusion_strength=strength,
            cap_reasons=cap,
            calculation=calc,
            evidence_links=links,
            narrative=f"Evidence value {fact_base_val} conflicts with claim {target_claim_val}; deviation {dev} exceeds tolerance {tol}.",
            engine_version=cfg.engine_version,
        )
