"""Fact Pydantic schemas."""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

from .common import Locator, Period


class FactScope(str, Enum):
    CONSOLIDATED = "consolidated"
    STANDALONE = "standalone"


class FactBasis(str, Enum):
    REPORTED = "reported"
    ADJUSTED = "adjusted"


class FactMethod(str, Enum):
    CSV = "csv"
    TABLE = "table"
    REGEX = "regex"
    LLM = "llm"


class FactBase(BaseModel):
    metric: str = Field(..., description="Canonical metric ID, e.g. 'revenue', 'net_income', 'cogs'")
    raw_label: str = Field(..., description="Verbatim row label or text mention in source document")
    value_raw: str = Field(..., description="Unmodified stated value e.g. '₹3,400 cr', '(1,234)'")
    value_base: str = Field(..., description="Normalized value as Decimal string in base units (e.g. '34000000000')")
    unit: str = Field(default="currency", description="Unit type: 'currency', 'percent', 'ratio', 'count'")
    scale: str = Field(default="unit", description="Scale e.g. 'unit', 'thousand', 'lakh', 'crore', 'million', 'billion'")
    currency: Optional[str] = Field(default=None, description="ISO currency code: 'INR', 'USD', 'EUR', etc.")
    period: Period
    period_key: str = Field(..., description="Canonical period key e.g. 'FY2025', 'Q3_FY2025'")
    scope: str = Field(default=FactScope.CONSOLIDATED.value, description="Scope: 'consolidated', 'standalone', or 'segment:<name>'")
    basis: FactBasis = Field(default=FactBasis.REPORTED, description="Accounting basis: reported vs adjusted")
    restated: bool = Field(default=False, description="True if this figure was restated in a subsequent filing")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Extraction confidence score (0.0 to 1.0)")
    method: FactMethod = Field(default=FactMethod.TABLE, description="Source extraction method")
    locator: Locator = Field(default_factory=Locator, description="Precise provenance locator in document")


class FactCreate(FactBase):
    document_id: str


class FactUpdate(BaseModel):
    metric: Optional[str] = None
    value_base: Optional[str] = None
    confirmed: Optional[bool] = None
    scope: Optional[str] = None
    basis: Optional[FactBasis] = None


class FactResponse(FactBase):
    id: str
    document_id: str
    document_filename: Optional[str] = None
    confirmed: bool = False
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
