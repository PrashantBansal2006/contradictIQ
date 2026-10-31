"""Decision-Table Tests for Ordered Rules R1 through R6 in verdict.py (Task 1.7).

Covers:
- R1: Parseability checks (missing text, missing metric, unparseable values)
- R2: Missing inputs (empty facts, insufficient periods for growth/margin)
- R3: Comparability gate (metric, entity, scope, basis, currency, period kind)
- R4: Source disagreement among same-tier documents
- R5: Extraction confidence gate & human confirmation override
- R6: Calculations (STATISTIC, GROWTH_YOY, MARGIN, DIRECTION)
- R6: Tolerance (precision-aware half-ULP, hedged multiplier, min_abs_tol)
- R6: Severity classification (Match, NearMiss, Material)
- Traps: Zero/negative growth base, division by zero, zero change
- Skeptic downgrade
"""

from decimal import Decimal
import pytest

from app.core.verdict import (
    DecisionConfig,
    Severity,
    VerdictOutcome,
    VerdictType,
    compute_tolerance,
    decide,
)


class TestVerdictRules:
    @pytest.fixture
    def cfg(self):
        return DecisionConfig(min_conf=0.8, approx_multiplier=2.0, min_abs_tol=Decimal("0.1"))

    # =======================================================================
    # Rule R1: Parseability
    # =======================================================================

    def test_r1_missing_text(self, cfg):
        claim = {"metric": "revenue", "claim_type": "GROWTH_YOY", "value_raw": "25%"}
        res = decide(claim, [{"value_base": "100"}], cfg)
        assert res.verdict == VerdictType.INCONCLUSIVE
        assert res.reason_code == "UNPARSEABLE_CLAIM"
        assert res.rule_triggered == "R1"

    def test_r1_missing_metric(self, cfg):
        claim = {"text": "Grew by 25%", "claim_type": "GROWTH_YOY", "value_raw": "25%"}
        res = decide(claim, [{"value_base": "100"}], cfg)
        assert res.verdict == VerdictType.INCONCLUSIVE
        assert res.reason_code == "UNPARSEABLE_CLAIM"
        assert res.rule_triggered == "R1"

    def test_r1_missing_claim_type(self, cfg):
        claim = {"text": "Revenue was 100", "metric": "revenue", "value_raw": "100"}
        res = decide(claim, [{"value_base": "100"}], cfg)
        assert res.verdict == VerdictType.INCONCLUSIVE
        assert res.reason_code == "UNPARSEABLE_CLAIM"

    def test_r1_unparseable_numeric_value(self, cfg):
        claim = {
            "text": "Revenue was strong",
            "metric": "revenue",
            "claim_type": "STATISTIC",
            "value_raw": "n/a",
        }
        res = decide(claim, [{"value_base": "100"}], cfg)
        assert res.verdict == VerdictType.INCONCLUSIVE
        assert res.reason_code == "UNPARSEABLE_CLAIM"

    # =======================================================================
    # Rule R2: Missing Inputs
    # =======================================================================

    def test_r2_empty_evidence_facts(self, cfg):
        claim = {
            "text": "Revenue was ₹3,400 cr",
            "metric": "revenue",
            "claim_type": "STATISTIC",
            "value_raw": "3400",
        }
        res = decide(claim, [], cfg)
        assert res.verdict == VerdictType.INCONCLUSIVE
        assert res.reason_code == "MISSING_INPUT"
        assert res.rule_triggered == "R2"

    def test_r2_growth_missing_previous_period_fact(self, cfg):
        claim = {
            "text": "Revenue grew by 25%",
            "metric": "revenue",
            "claim_type": "GROWTH_YOY",
            "value_raw": "25",
        }
        # Only 1 fact provided; growth requires current & previous
        facts = [{"metric": "revenue", "value_base": "3400", "period_key": "FY2025"}]
        res = decide(claim, facts, cfg)
        assert res.verdict == VerdictType.INCONCLUSIVE
        assert res.reason_code == "MISSING_INPUT"
        assert res.rule_triggered == "R2"

    def test_r2_margin_missing_denominator(self, cfg):
        claim = {
            "text": "Operating margin was 15%",
            "metric": "operating_margin",
            "claim_type": "MARGIN",
            "value_raw": "15",
        }
        facts = [{"metric": "operating_income", "value_base": "500"}]
        res = decide(claim, facts, cfg)
        assert res.verdict == VerdictType.INCONCLUSIVE
        assert res.reason_code == "MISSING_INPUT"

    # =======================================================================
    # Rule R3: Comparability Gate
    # =======================================================================

    def test_r3_metric_mismatch(self, cfg):
        claim = {
            "text": "Revenue was 3400",
            "metric": "revenue",
            "claim_type": "STATISTIC",
            "value_raw": "3400",
        }
        facts = [{"metric": "operating_expenses", "value_base": "3400"}]
        res = decide(claim, facts, cfg)
        assert res.verdict == VerdictType.INCONCLUSIVE
        assert res.reason_code == "METRIC_MISMATCH"
        assert res.rule_triggered == "R3"

    def test_r3_entity_mismatch(self, cfg):
        claim = {
            "text": "Veridian revenue 3400",
            "metric": "revenue",
            "entity": "Veridian Foods",
            "claim_type": "STATISTIC",
            "value_raw": "3400",
        }
        facts = [{"metric": "revenue", "entity": "Apex Tech", "value_base": "3400"}]
        res = decide(claim, facts, cfg)
        assert res.verdict == VerdictType.INCONCLUSIVE
        assert res.reason_code == "ENTITY_MISMATCH"

    def test_r3_scope_mismatch(self, cfg):
        claim = {
            "text": "Consolidated revenue 3400",
            "metric": "revenue",
            "scope": "consolidated",
            "claim_type": "STATISTIC",
            "value_raw": "3400",
        }
        facts = [{"metric": "revenue", "scope": "standalone", "value_base": "3400"}]
        res = decide(claim, facts, cfg)
        assert res.verdict == VerdictType.INCONCLUSIVE
        assert res.reason_code == "SCOPE_MISMATCH"

    def test_r3_basis_mismatch(self, cfg):
        claim = {
            "text": "Reported EBITDA 500",
            "metric": "ebitda",
            "basis": "reported",
            "claim_type": "STATISTIC",
            "value_raw": "500",
        }
        facts = [{"metric": "ebitda", "basis": "adjusted", "value_base": "500"}]
        res = decide(claim, facts, cfg)
        assert res.verdict == VerdictType.INCONCLUSIVE
        assert res.reason_code == "BASIS_MISMATCH"

    def test_r3_currency_mismatch(self, cfg):
        claim = {
            "text": "Revenue $4,000",
            "metric": "revenue",
            "currency": "USD",
            "claim_type": "STATISTIC",
            "value_raw": "4000",
        }
        facts = [{"metric": "revenue", "currency": "INR", "value_base": "4000"}]
        res = decide(claim, facts, cfg)
        assert res.verdict == VerdictType.INCONCLUSIVE
        assert res.reason_code == "CURRENCY_MISMATCH"

    def test_r3_quarter_vs_annual_trap(self, cfg):
        claim = {
            "text": "Annual revenue 3400",
            "metric": "revenue",
            "period": {"kind": "FY", "fy": 2025},
            "claim_type": "STATISTIC",
            "value_raw": "3400",
        }
        facts = [{"metric": "revenue", "period": {"kind": "Q", "fy": 2025, "idx": 3}, "value_base": "900"}]
        res = decide(claim, facts, cfg)
        assert res.verdict == VerdictType.INCONCLUSIVE
        assert res.reason_code == "NOT_COMPARABLE_PERIOD_KIND"

    # =======================================================================
    # Rule R4: Source Disagreement
    # =======================================================================

    def test_r4_source_disagreement_same_tier(self, cfg):
        claim = {
            "text": "Revenue was 3400",
            "metric": "revenue",
            "period_key": "FY2025",
            "claim_type": "STATISTIC",
            "value_raw": "3400",
        }
        # Two audited T2 filings reporting conflicting numbers
        facts = [
            {"metric": "revenue", "period_key": "FY2025", "source_tier": "T2", "value_base": "3400"},
            {"metric": "revenue", "period_key": "FY2025", "source_tier": "T2", "value_base": "3100"},
        ]
        res = decide(claim, facts, cfg)
        assert res.verdict == VerdictType.INCONCLUSIVE
        assert res.reason_code == "SOURCE_DISAGREEMENT"
        assert res.rule_triggered == "R4"

    def test_r4_source_agreement_passes(self, cfg):
        claim = {
            "text": "Revenue was 3400",
            "metric": "revenue",
            "period_key": "FY2025",
            "claim_type": "STATISTIC",
            "value_raw": "3400",
        }
        facts = [
            {"metric": "revenue", "period_key": "FY2025", "source_tier": "T2", "value_base": "3400"},
            {"metric": "revenue", "period_key": "FY2025", "source_tier": "T2", "value_base": "3400"},
        ]
        res = decide(claim, facts, cfg)
        assert res.verdict == VerdictType.CONSISTENT
        assert res.severity == Severity.MATCH

    # =======================================================================
    # Rule R5: Confidence Gate
    # =======================================================================

    def test_r5_low_confidence_rejected(self, cfg):
        claim = {
            "text": "Revenue was 3400",
            "metric": "revenue",
            "claim_type": "STATISTIC",
            "value_raw": "3400",
        }
        facts = [{"metric": "revenue", "value_base": "3400", "confidence": 0.65, "confirmed": False}]
        res = decide(claim, facts, cfg)
        assert res.verdict == VerdictType.INCONCLUSIVE
        assert res.reason_code == "LOW_CONFIDENCE_EXTRACTION"
        assert res.rule_triggered == "R5"

    def test_r5_human_confirmation_overrides_low_confidence(self, cfg):
        claim = {
            "text": "Revenue was 3400",
            "metric": "revenue",
            "claim_type": "STATISTIC",
            "value_raw": "3400",
        }
        facts = [{"metric": "revenue", "value_base": "3400", "confidence": 0.55, "confirmed": True}]
        res = decide(claim, facts, cfg)
        assert res.verdict == VerdictType.CONSISTENT
        assert res.severity == Severity.MATCH

    # =======================================================================
    # Rule R6: Calculation, Tolerance & Severity
    # =======================================================================

    def test_r6_statistic_exact_match(self, cfg):
        claim = {
            "text": "Revenue was 3400",
            "metric": "revenue",
            "claim_type": "STATISTIC",
            "value_raw": "3400",
            "value_precision": 0,
        }
        facts = [{"metric": "revenue", "value_base": "3400"}]
        res = decide(claim, facts, cfg)
        assert res.verdict == VerdictType.CONSISTENT
        assert res.severity == Severity.MATCH
        assert res.calc_value == Decimal("3400")

    def test_r6_rounding_tolerance_accepted(self, cfg):
        # Claim states 18% (precision=0 -> half_ulp=0.5). Computed: 17.6%. Diff: 0.4 <= 0.5 -> Consistent
        claim = {
            "text": "Revenue grew by 18%",
            "metric": "revenue",
            "claim_type": "GROWTH_YOY",
            "value_raw": "18",
            "value_precision": 0,
        }
        # (1176 - 1000) / 1000 * 100 = 17.6%
        facts = [
            {"metric": "revenue", "value_base": "1176"},
            {"metric": "revenue", "value_base": "1000"},
        ]
        res = decide(claim, facts, cfg)
        assert res.verdict == VerdictType.CONSISTENT
        assert res.severity == Severity.MATCH

    def test_r6_rounding_tolerance_precision_1_accepted(self, cfg):
        # Claim 18.2% (precision=1 -> half_ulp=0.05). Computed: 18.24% (diff 0.04 <= 0.1 min_tol)
        claim = {
            "text": "Growth 18.2%",
            "metric": "revenue",
            "claim_type": "GROWTH_YOY",
            "value_raw": "18.2",
            "value_precision": 1,
        }
        facts = [
            {"metric": "revenue", "value_base": "1182.4"},
            {"metric": "revenue", "value_base": "1000"},
        ]
        res = decide(claim, facts, cfg)
        assert res.verdict == VerdictType.CONSISTENT
        assert res.severity == Severity.MATCH

    def test_r6_hedged_claim_doubles_tolerance(self, cfg):
        # Claim "about 18%" (precision 0, hedged=True -> tol = 0.5 * 2.0 = 1.0).
        # Computed: 17.2% (diff: 0.8 <= 1.0) -> Consistent
        claim = {
            "text": "About 18% revenue growth",
            "metric": "revenue",
            "claim_type": "GROWTH_YOY",
            "value_raw": "18",
            "value_precision": 0,
            "hedged": True,
        }
        facts = [
            {"metric": "revenue", "value_base": "1172"},
            {"metric": "revenue", "value_base": "1000"},
        ]
        res = decide(claim, facts, cfg)
        assert res.verdict == VerdictType.CONSISTENT
        assert res.severity == Severity.MATCH
        assert res.tolerance.approx_multiplier == 2.0

    def test_r6_near_miss_severity(self, cfg):
        # Claim: 18.0% (precision 1 -> tol=0.1). Computed: 18.25% (dev: 0.25 <= 3*0.1 = 0.3) -> NearMiss
        claim = {
            "text": "Growth 18.0%",
            "metric": "revenue",
            "claim_type": "GROWTH_YOY",
            "value_raw": "18.0",
            "value_precision": 1,
        }
        facts = [
            {"metric": "revenue", "value_base": "1182.5"},
            {"metric": "revenue", "value_base": "1000"},
        ]
        res = decide(claim, facts, cfg)
        assert res.verdict == VerdictType.CONFLICTING
        assert res.severity == Severity.NEAR_MISS

    def test_r6_material_discrepancy_veridian_case(self, cfg):
        # Seeded demo: Claim 25% YoY vs computed 14.2% -> Material Conflicting
        claim = {
            "text": "Veridian Foods revenue grew by 25% in FY25",
            "metric": "revenue",
            "claim_type": "GROWTH_YOY",
            "value_raw": "25.0",
            "value_precision": 1,
        }
        # (3400 - 2977) / 2977 * 100 = 14.2089%
        facts = [
            {"metric": "revenue", "value_base": "3400"},
            {"metric": "revenue", "value_base": "2977"},
        ]
        res = decide(claim, facts, cfg)
        assert res.verdict == VerdictType.CONFLICTING
        assert res.severity == Severity.MATERIAL
        assert res.deviation > Decimal("10")

    def test_r6_margin_calculation(self, cfg):
        # Operating Margin = (op_inc / rev) * 100 = (510 / 3400) * 100 = 15.0%
        claim = {
            "text": "Operating margin was 15.0%",
            "metric": "operating_margin",
            "claim_type": "MARGIN",
            "value_raw": "15.0",
            "value_precision": 1,
        }
        facts = [
            {"metric": "operating_income", "value_base": "510"},
            {"metric": "revenue", "value_base": "3400"},
        ]
        res = decide(claim, facts, cfg)
        assert res.verdict == VerdictType.CONSISTENT
        assert res.severity == Severity.MATCH
        assert res.calc_value == Decimal("15")

    def test_r6_division_by_zero_margin_trap(self, cfg):
        claim = {
            "text": "Operating margin was 10%",
            "metric": "operating_margin",
            "claim_type": "MARGIN",
            "value_raw": "10",
        }
        facts = [
            {"metric": "operating_income", "value_base": "100"},
            {"metric": "revenue", "value_base": "0"},
        ]
        res = decide(claim, facts, cfg)
        assert res.verdict == VerdictType.INCONCLUSIVE
        assert res.reason_code == "DIVISION_BY_ZERO"

    def test_r6_undefined_growth_base_zero(self, cfg):
        claim = {
            "text": "Grew by 50%",
            "metric": "revenue",
            "claim_type": "GROWTH_YOY",
            "value_raw": "50",
        }
        facts = [
            {"metric": "revenue", "value_base": "100"},
            {"metric": "revenue", "value_base": "0"},
        ]
        res = decide(claim, facts, cfg)
        assert res.verdict == VerdictType.INCONCLUSIVE
        assert res.reason_code == "UNDEFINED_GROWTH_BASE"

    def test_r6_undefined_growth_base_negative(self, cfg):
        claim = {
            "text": "Grew by 50%",
            "metric": "net_income",
            "claim_type": "GROWTH_YOY",
            "value_raw": "50",
        }
        facts = [
            {"metric": "net_income", "value_base": "100"},
            {"metric": "net_income", "value_base": "-50"},
        ]
        res = decide(claim, facts, cfg)
        assert res.verdict == VerdictType.INCONCLUSIVE
        assert res.reason_code == "UNDEFINED_GROWTH_BASE"

    def test_r6_direction_positive_match(self, cfg):
        claim = {
            "text": "Profits grew in FY25",
            "metric": "net_income",
            "claim_type": "DIRECTION",
        }
        facts = [
            {"metric": "net_income", "value_base": "250"},
            {"metric": "net_income", "value_base": "200"},
        ]
        res = decide(claim, facts, cfg)
        assert res.verdict == VerdictType.CONSISTENT
        assert res.severity == Severity.MATCH

    def test_r6_direction_contradiction(self, cfg):
        claim = {
            "text": "Profits declined significantly",
            "metric": "net_income",
            "claim_type": "DIRECTION",
        }
        facts = [
            {"metric": "net_income", "value_base": "300"},
            {"metric": "net_income", "value_base": "200"},
        ]
        res = decide(claim, facts, cfg)
        assert res.verdict == VerdictType.CONFLICTING
        assert res.severity == Severity.MATERIAL

    def test_r6_direction_zero_change_trap(self, cfg):
        claim = {
            "text": "Profits increased",
            "metric": "net_income",
            "claim_type": "DIRECTION",
        }
        facts = [
            {"metric": "net_income", "value_base": "200"},
            {"metric": "net_income", "value_base": "200"},
        ]
        res = decide(claim, facts, cfg)
        assert res.verdict == VerdictType.INCONCLUSIVE
        assert res.reason_code == "ZERO_CHANGE"

    # =======================================================================
    # Skeptic Post-Processing Downgrade
    # =======================================================================

    def test_skeptic_downgrade(self, cfg):
        claim = {
            "text": "Revenue was 3400",
            "metric": "revenue",
            "claim_type": "STATISTIC",
            "value_raw": "3400",
        }
        facts = [{"metric": "revenue", "value_base": "3400"}]
        # Without skeptic: Consistent
        clean_res = decide(claim, facts, cfg)
        assert clean_res.verdict == VerdictType.CONSISTENT

        # With skeptic reason: downgraded to Inconclusive
        skeptic_res = decide(claim, facts, cfg, skeptic_reason="POSSIBLE_UNANNOUNCED_RESTATEMENT")
        assert skeptic_res.verdict == VerdictType.INCONCLUSIVE
        assert skeptic_res.reason_code == "SKEPTIC_FLAG"
