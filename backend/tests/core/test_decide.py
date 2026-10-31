"""
ContradictIQ — Tests for decide() Facade and 30 Labelled Eval Cases
==================================================================
Tasks 1.9 & 1.10: Public decide() facade + reusing dataset.jsonl as parametrized tests.
"""

import json
from pathlib import Path
import pytest

from app.core import decide, ENGINE_VERSION, engine_version, EngineConfig


def get_dataset_path() -> Path:
    """Find dataset.jsonl in backend/app/eval or eval/."""
    candidates = [
        Path(__file__).resolve().parent.parent.parent / "app" / "eval" / "dataset.jsonl",
        Path(__file__).resolve().parent.parent.parent.parent / "eval" / "dataset.jsonl",
    ]
    for c in candidates:
        if c.exists():
            return c
    raise FileNotFoundError("dataset.jsonl not found in search paths")


def load_eval_cases():
    """Load all labelled cases from dataset.jsonl."""
    dataset_file = get_dataset_path()
    lines = [line.strip() for line in dataset_file.read_text(encoding="utf-8").splitlines() if line.strip()]
    return [json.loads(line) for line in lines]


eval_cases = load_eval_cases()


def test_engine_version_constants():
    """Test engine version constant existence and format."""
    assert ENGINE_VERSION == "0.1.0"
    assert engine_version == ENGINE_VERSION
    assert isinstance(ENGINE_VERSION, str)


def test_dataset_contains_at_least_30_cases():
    """Verify that dataset.jsonl contains at least 30 labelled cases (Task 1.10)."""
    assert len(eval_cases) >= 30


@pytest.mark.parametrize("case", eval_cases, ids=[c["id"] for c in eval_cases])
def test_decide_eval_cases(case):
    """
    Parametrized evaluation test running decide() on every case in dataset.jsonl.
    Validates expected verdict, severity, and reason codes across all categories.
    """
    claim = case["claim"]
    facts = case["facts"]
    expected_verdict = case["expected_verdict"]
    expected_severity = case.get("expected_severity")
    expected_reason = case.get("expected_reason")

    cfg = EngineConfig()
    result = decide(claim, facts, cfg)

    # 1. Validate Verdict
    assert result.verdict == expected_verdict, (
        f"Case {case['id']} ({case['category']}): Expected verdict '{expected_verdict}', "
        f"got '{result.verdict}'. Narrative: {result.narrative}"
    )

    # 2. Validate Severity if specified
    if expected_severity is not None:
        assert result.severity == expected_severity, (
            f"Case {case['id']} ({case['category']}): Expected severity '{expected_severity}', "
            f"got '{result.severity}'."
        )

    # 3. Validate Reason code substring if specified
    if expected_reason is not None:
        matched = any(expected_reason in r for r in result.reasons)
        assert matched, (
            f"Case {case['id']} ({case['category']}): Expected reason code '{expected_reason}' "
            f"in {result.reasons}."
        )

    # 4. Validate output schema integrity
    res_dict = result.to_dict()
    assert res_dict["verdict"] in ("Consistent", "Conflicting", "Inconclusive")
    assert res_dict["engine_version"] == ENGINE_VERSION
    assert isinstance(res_dict["narrative"], str)


def test_period_parsing_and_algebra():
    """Test period parsing, string variants, and algebra."""
    from app.core import Period
    p1 = Period.from_any("FY25")
    assert p1.kind == "FY" and p1.fy == 2025
    p2 = Period.from_any("Q3 FY2025")
    assert p2.kind == "Q" and p2.fy == 2025 and p2.idx == 3
    p3 = Period.from_any("H1 FY25")
    assert p3.kind == "H" and p3.fy == 2025 and p3.idx == 1
    assert Period.from_any(None) is None
    assert Period.from_any(123) is None

    # Algebra
    prev_y = p2.prev_year()
    assert prev_y.fy == 2024 and prev_y.idx == 3
    prev_q = p2.prev_quarter()
    assert prev_q.fy == 2025 and prev_q.idx == 2
    p_q1 = Period(kind="Q", fy=2025, idx=1)
    prev_q_boundary = p_q1.prev_quarter()
    assert prev_q_boundary.fy == 2024 and prev_q_boundary.idx == 4


def test_decide_entity_and_scope_mismatch():
    """Test entity and scope mismatch gates."""
    claim = {
        "text": "Acme revenue is 100",
        "metric": "revenue",
        "value": 100,
        "entity": "Acme Corp",
        "scope": "consolidated",
    }
    fact_diff_entity = {
        "metric": "revenue",
        "value_base": "100",
        "entity": "Beta Corp",
    }
    res_entity = decide(claim, [fact_diff_entity])
    assert res_entity.verdict == "Inconclusive"
    assert "ENTITY_MISMATCH" in res_entity.reasons

    fact_diff_scope = {
        "metric": "revenue",
        "value_base": "100",
        "entity": "Acme Corp",
        "scope": "standalone",
    }
    res_scope = decide(claim, [fact_diff_scope])
    assert res_scope.verdict == "Inconclusive"
    assert "SCOPE_MISMATCH" in res_scope.reasons


def test_decide_direction_claims():
    """Test direction claims increase, decrease, mismatch."""
    claim_inc = {
        "claim_type": "direction",
        "metric": "revenue",
        "direction": "increase",
        "period": "Q2 FY25",
    }
    facts_inc = [
        {"metric": "revenue", "value_base": "100"},
        {"metric": "revenue", "value_base": "150"},
    ]
    res_inc = decide(claim_inc, facts_inc)
    assert res_inc.verdict == "Consistent"

    claim_dec = {
        "claim_type": "direction",
        "metric": "revenue",
        "direction": "decrease",
        "period": "Q2 FY25",
    }
    res_mismatch = decide(claim_dec, facts_inc)
    assert res_mismatch.verdict == "Conflicting"
    assert any("DIRECTION_MISMATCH" in r for r in res_mismatch.reasons)


def test_decide_low_confidence_and_unmapped():
    """Test confidence gate and unmapped metric."""
    claim = {"metric": "revenue", "value": 100}
    fact_low_conf = {
        "metric": "revenue",
        "value_base": "100",
        "confidence": 0.40,
        "confirmed": False,
    }
    res_conf = decide(claim, [fact_low_conf])
    assert res_conf.verdict == "Inconclusive"
    assert "LOW_CONFIDENCE_EXTRACTION" in res_conf.reasons

    claim_bad_metric = {"metric": None, "value": 100}
    res_bad = decide(claim_bad_metric, [fact_low_conf])
    assert res_bad.verdict == "Inconclusive"
    assert "UNPARSEABLE_CLAIM" in res_bad.reasons

