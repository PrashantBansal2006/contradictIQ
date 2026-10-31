"""Investigation Pydantic schemas."""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class InvestigationStatus(str, Enum):
    OPEN = "open"
    IN_REVIEW = "in_review"
    CONCLUDED = "concluded"


class InvestigationMemberRole(str, Enum):
    OWNER = "owner"
    REVIEWER = "reviewer"
    VIEWER = "viewer"


class InvestigationBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Title of the investigation")
    description: Optional[str] = Field(default=None, description="Detailed notes, hypotheses, or objectives")
    entity_name: Optional[str] = Field(default=None, max_length=255, description="Primary company or entity under investigation")


class InvestigationCreate(InvestigationBase):
    pass


class InvestigationUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = Field(default=None)
    entity_name: Optional[str] = Field(default=None, max_length=255)
    status: Optional[InvestigationStatus] = Field(default=None)
    archived: Optional[bool] = Field(default=None)


class InvestigationMemberResponse(BaseModel):
    user_id: str
    email: str
    name: Optional[str] = None
    role: InvestigationMemberRole


class InvestigationResponse(InvestigationBase):
    id: str
    owner_id: str
    status: InvestigationStatus
    archived: bool
    created_at: datetime
    updated_at: datetime
    document_count: Optional[int] = 0
    claim_count: Optional[int] = 0
    finding_count: Optional[int] = 0

    class Config:
        from_attributes = True
