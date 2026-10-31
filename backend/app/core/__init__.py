"""
Deterministic Verification Core
===============================
This package contains the pure-Python, deterministic verification engine.
No I/O, no network, no LLM dependencies.
"""

from app.core.decide import (
    ENGINE_VERSION,
    engine_version,
    decide,
    EngineConfig,
    VerdictResult,
    CalcResult,
    Step,
    Period,
    EvidenceLink,
)

__all__ = [
    "ENGINE_VERSION",
    "engine_version",
    "decide",
    "EngineConfig",
    "VerdictResult",
    "CalcResult",
    "Step",
    "Period",
    "EvidenceLink",
]

