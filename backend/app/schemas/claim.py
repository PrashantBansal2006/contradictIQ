"""Claim and ClaimVersion Pydantic schemas."""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

from .common import Locator, Period


class ClaimOrigin(str, Enum):
    MANUAL = "manual"
    AI = "ai"
    PARSED = "parsed"


class ClaimState(str, Enum):
    DRAFT = "draft"
    NEEDS_CONFIRMATION = "needs_confirmation"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"


class ClaimType(str, Enum):
    STATISTIC = "STATISTIC"
    GROWTH_YOY = "GROWTH_YOY"
    GROWTH_QOQ = "GROWTH_QOQ"
    MARGIN = "MARGIN"
    EXPENSE_RATIO = "EXPENSE_RATIO"
    OPEX_RATIO = "OPEX_RATIO"
    DIRECTION = "DIRECTION"


class ClaimVersionBase(BaseModel):
    text: str = Field(..., description="Stated natural language claim text")
    claim_type: ClaimType = Field(default=ClaimType.GROWTH_YOY, description="Type of financial claim")
    metric: str = Field(..., description="Target canonical metric e.g. 'revenue', 'operating_margin'")
    value_raw: Optional[str] = Field(default=None, description="Stated numeric value e.g. '25%', '₹3,400 cr'")
    value_numeric: Optional[float] = Field(default=None, description="Parsed numeric value for formula evaluation e.g. 25.0")
    value_precision: int = Field(default=1, description="Number of decimal digits in stated value (determines tolerance)")
    unit: str = Field(default="percent", description="Unit: 'percent', 'currency', 'ratio'")
    scale: str = Field(default="unit", description="Scale e.g. 'unit', 'crore', 'million'")
    currency: Optional[str] = Field(default=None, description="ISO currency code if monetary")
    period: Period
    scope: str = Field(default="consolidated", description="Scope e.g. 'consolidated', 'standalone'")
    basis: str = Field(default="reported", description="Accounting basis: 'reported' or 'adjusted'")
    entity: Optional[str] = Field(default=None, description="Entity name the claim is asserted about")
    hedged: bool = Field(default=False, description="True if hedged e.g. 'approximately', 'about', doubling tolerance")
    quote: Optional[str] = Field(default=None, description="Direct quote from source document")
    source_doc_id: Optional[str] = Field(default=None, description="Document ID where quote was extracted")
    source_locator: Optional[Locator] = Field(default=None, description="Locator for highlighted viewing")
    grounded: bool = Field(default=True, description="Grounding validator pass status")
    change_note: Optional[str] = Field(default=None, description="Reason for version edit")


class ClaimVersionResponse(ClaimVersionBase):
    id: str
    claim_id: str
    version: int
    author_id: str
    created_at: datetime

    class Config:
        from_attributes = True


class ClaimCreate(ClaimVersionBase):
    investigation_id: str
    origin: ClaimOrigin = ClaimOrigin.MANUAL


class ClaimUpdate(BaseModel):
    text: Optional[str] = None
    claim_type: Optional[ClaimType] = None
    metric: Optional[str] = None
    value_raw: Optional[str] = None
    value_numeric: Optional[float] = None
    value_precision: Optional[int] = None
    period: Optional[Period] = None
    scope: Optional[str] = None
    basis: Optional[str] = None
    change_note: str = Field(..., description="Required note explaining this version edit")


class ClaimResponse(BaseModel):
    id: str
    investigation_id: str
    current_version: int
    state: ClaimState
    origin: ClaimOrigin
    created_by: str
    created_at: datetime
    active_version: ClaimVersionResponse
    all_versions: Optional[List[ClaimVersionResponse]] = None
    latest_finding_id: Optional[str] = None

    class Config:
        from_attributes = True
