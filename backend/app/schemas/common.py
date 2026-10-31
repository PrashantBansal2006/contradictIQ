"""Common schemas: Period, Locator, ErrorBody, Pagination."""

from enum import Enum
from typing import Any, Generic, List, Literal, Optional, Tuple, TypeVar
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Error Schemas (Architecture §14 & §18)
# Standard error body: { "error": { "code": "...", "message": "...", "details": {...} } }
# ---------------------------------------------------------------------------

class ErrorDetail(BaseModel):
    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable description of the error")
    details: Optional[dict[str, Any]] = Field(default=None, description="Additional context or diagnostics")


class ErrorBody(BaseModel):
    error: ErrorDetail


class ErrorResponse(BaseModel):
    error: ErrorDetail


# ---------------------------------------------------------------------------
# Period Schema (Architecture §8.2)
# ---------------------------------------------------------------------------

PeriodKind = Literal["Q", "H", "9M", "FY", "TTM"]


class Period(BaseModel):
    kind: PeriodKind = Field(..., description="Period classification: Q (quarter), H (half-year), 9M (nine-months), FY (fiscal year), TTM (trailing 12 months)")
    fy: int = Field(..., description="Fiscal year label, e.g. 2025")
    idx: Optional[int] = Field(default=None, ge=1, le=4, description="Quarter index (1-4) or half-year index (1-2)")
    fy_end_month: int = Field(default=3, ge=1, le=12, description="Fiscal year ending month (default: 3 for March)")

    def canonical_key(self) -> str:
        """Returns standard lookup key e.g. 'FY2025', 'Q3_FY2025', 'H1_FY2025'."""
        if self.kind == "FY":
            return f"FY{self.fy}"
        if self.idx is not None:
            return f"{self.kind}{self.idx}_FY{self.fy}"
        return f"{self.kind}_FY{self.fy}"


# ---------------------------------------------------------------------------
# Locator Schema (Architecture §1.4 & §5.1)
# ---------------------------------------------------------------------------

class Locator(BaseModel):
    page: Optional[int] = Field(default=None, description="1-indexed page number in the source document")
    bbox: Optional[List[float]] = Field(default=None, description="Bounding box [x0, y0, x1, y1] on the page in PDF coordinate space")
    table_id: Optional[str] = Field(default=None, description="ID of the extracted table if from a tabular structure")
    row: Optional[int] = Field(default=None, description="0-indexed row position in table or CSV")
    col: Optional[int] = Field(default=None, description="0-indexed column position in table or CSV")
    char_span: Optional[Tuple[int, int]] = Field(default=None, description="Character offset [start, end] in page text")
    quote: Optional[str] = Field(default=None, description="Verbatim text passage or cell content cited")


# ---------------------------------------------------------------------------
# Generic Pagination & List Envelopes
# ---------------------------------------------------------------------------

T = TypeVar("T")


class PaginatedList(BaseModel, Generic[T]):
    items: List[T]
    total: int
    offset: int = 0
    limit: int = 50
