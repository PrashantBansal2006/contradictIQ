"""EvidenceLink Pydantic schemas."""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

from .common import Locator
from .fact import FactResponse


class EvidenceStance(str, Enum):
    SUPPORTS = "supports"
    OPPOSES = "opposes"
    NEUTRAL = "neutral"
    NOT_COMPARABLE = "not_comparable"


class EvidenceLinkResponse(BaseModel):
    id: str
    finding_id: str
    fact_id: str
    stance: EvidenceStance
    document_id: str
    document_filename: Optional[str] = None
    locator: Locator
    note: Optional[str] = None
    fact: Optional[FactResponse] = None

    class Config:
        from_attributes = True
