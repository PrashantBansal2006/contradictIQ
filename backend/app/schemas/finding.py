"""Finding and verdict Pydantic schemas."""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from .calculation import CalculationResponse
from .evidence_link import EvidenceLinkResponse


class Verdict(str, Enum):
    CONSISTENT = "Consistent"
    CONFLICTING = "Conflicting"
    INCONCLUSIVE = "Inconclusive"


class Severity(str, Enum):
    MATCH = "Match"
    NEAR_MISS = "NearMiss"
    MATERIAL = "Material"


class ConclusionStrength(str, Enum):
    DISPROVED = "disproved"
    CONFIRMED = "confirmed"
    INDICATIVE = "indicative"
    INSUFFICIENT = "insufficient"


class ComparabilityCheckResult(BaseModel):
    check_name: str = Field(..., description="E.g. 'Metric', 'Entity', 'Period', 'Period Kind', 'Scope', 'Basis', 'Currency', 'Scale', 'Restatement'")
    passed: bool
    resolved_by: Optional[str] = None
    reason_code: Optional[str] = None
    details: Optional[str] = None


class FindingResponse(BaseModel):
    id: str
    claim_version_id: str
    claim_id: Optional[str] = None
    verdict: Verdict
    severity: Optional[Severity] = None
    conclusion_strength: ConclusionStrength = Field(..., description="Capped strength per Strong-Conclusion Guard")
    cap_reasons: List[str] = Field(default_factory=list, description="Explicit reasons why strength was capped")
    reason_codes: List[str] = Field(default_factory=list, description="Reason codes e.g. 'NOT_COMPARABLE_PERIOD_KIND'")
    comparability_checks: List[ComparabilityCheckResult] = Field(default_factory=list)
    narrative: str = Field(..., description="Deterministic math-grounded explanation")
    superseded: bool = False
    calculation_id: Optional[str] = None
    calculation: Optional[CalculationResponse] = None
    evidence_links: List[EvidenceLinkResponse] = Field(default_factory=list)
    created_at: datetime
    engine_version: str = Field(default="1.0.0")

    class Config:
        from_attributes = True
