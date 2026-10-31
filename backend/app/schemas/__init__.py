"""Pydantic schemas freeze for ContradictIQ (Phase 0 - Task 0.4).

Shared contracts between Backend (FastAPI) and Frontend (TypeScript).
"""

from .common import (
    ErrorBody,
    ErrorDetail,
    ErrorResponse,
    Locator,
    PaginatedList,
    Period,
    PeriodKind,
)
from .investigation import (
    InvestigationCreate,
    InvestigationMemberResponse,
    InvestigationMemberRole,
    InvestigationResponse,
    InvestigationStatus,
    InvestigationUpdate,
)
from .document import (
    DataQualityWarning,
    DocumentCreate,
    DocumentResponse,
    DocumentStatus,
    PageResponse,
    SourceTier,
    TableExtractResponse,
    WordBox,
)
from .fact import (
    FactBasis,
    FactCreate,
    FactMethod,
    FactResponse,
    FactScope,
    FactUpdate,
)
from .claim import (
    ClaimCreate,
    ClaimOrigin,
    ClaimResponse,
    ClaimState,
    ClaimType,
    ClaimUpdate,
    ClaimVersionBase,
    ClaimVersionResponse,
)
from .calculation import (
    CalculationResponse,
    CalculationStep,
    CalculationTolerance,
)
from .evidence_link import (
    EvidenceLinkResponse,
    EvidenceStance,
)
from .finding import (
    ComparabilityCheckResult,
    ConclusionStrength,
    FindingResponse,
    Severity,
    Verdict,
)

__all__ = [
    # Common & Errors
    "ErrorDetail",
    "ErrorBody",
    "ErrorResponse",
    "Period",
    "PeriodKind",
    "Locator",
    "PaginatedList",
    # Investigation
    "InvestigationStatus",
    "InvestigationMemberRole",
    "InvestigationCreate",
    "InvestigationUpdate",
    "InvestigationResponse",
    "InvestigationMemberResponse",
    # Document
    "SourceTier",
    "DocumentStatus",
    "DataQualityWarning",
    "DocumentCreate",
    "DocumentResponse",
    "WordBox",
    "PageResponse",
    "TableExtractResponse",
    # Fact
    "FactScope",
    "FactBasis",
    "FactMethod",
    "FactCreate",
    "FactUpdate",
    "FactResponse",
    # Claim
    "ClaimOrigin",
    "ClaimState",
    "ClaimType",
    "ClaimVersionBase",
    "ClaimVersionResponse",
    "ClaimCreate",
    "ClaimUpdate",
    "ClaimResponse",
    # Calculation
    "CalculationStep",
    "CalculationTolerance",
    "CalculationResponse",
    # EvidenceLink
    "EvidenceStance",
    "EvidenceLinkResponse",
    # Finding
    "Verdict",
    "Severity",
    "ConclusionStrength",
    "ComparabilityCheckResult",
    "FindingResponse",
]
