"""Document and parsed extract schemas."""

from datetime import datetime
from enum import Enum
from typing import Any, List, Optional
from pydantic import BaseModel, Field


class SourceTier(str, Enum):
    T1 = "T1"  # Regulatory filings (SEBI, SEC, MCA)
    T2 = "T2"  # Audited annual reports
    T3 = "T3"  # Investor presentations, earnings calls, press releases
    T4 = "T4"  # Third-party news, analyst notes, blog posts


class DocumentStatus(str, Enum):
    QUEUED = "queued"
    PARSING = "parsing"
    EXTRACTING = "extracting"
    READY = "ready"
    FAILED = "failed"


class DataQualityWarning(BaseModel):
    code: str = Field(..., description="Quality issue code e.g. 'SUM_MISMATCH', 'UNPARSEABLE_VALUE'")
    message: str
    location: Optional[str] = None
    details: Optional[dict[str, Any]] = None


class DocumentCreate(BaseModel):
    investigation_id: str
    source_tier: SourceTier = SourceTier.T2
    doc_date: Optional[str] = Field(default=None, description="Document publication/filing date (YYYY-MM-DD)")
    entity_name: Optional[str] = Field(default=None, description="Reporting entity name")


class DocumentResponse(BaseModel):
    id: str
    investigation_id: str
    filename: str
    mime: str
    size: int
    sha256: str
    page_count: Optional[int] = None
    source_tier: SourceTier
    doc_date: Optional[str] = None
    entity_name: Optional[str] = None
    status: DocumentStatus
    error_code: Optional[str] = None
    error_msg: Optional[str] = None
    warnings: List[DataQualityWarning] = Field(default_factory=list)
    uploaded_by: str
    created_at: datetime
    fact_count: Optional[int] = 0

    class Config:
        from_attributes = True


class WordBox(BaseModel):
    word: str
    bbox: List[float] = Field(..., description="[x0, y0, x1, y1]")
    char_start: int
    char_end: int


class PageResponse(BaseModel):
    id: str
    document_id: str
    page_no: int
    text: str
    words: Optional[List[WordBox]] = None

    class Config:
        from_attributes = True


class TableExtractResponse(BaseModel):
    id: str
    document_id: str
    page_no: int
    bbox: Optional[List[float]] = None
    header: List[str] = Field(default_factory=list)
    rows: List[List[Any]] = Field(default_factory=list)
    method: str = Field(..., description="Extraction method: 'pdfplumber' or 'csv'")
    confidence: float = Field(..., ge=0.0, le=1.0)

    class Config:
        from_attributes = True
