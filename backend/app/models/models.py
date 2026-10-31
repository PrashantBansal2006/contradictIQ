"""
SQLAlchemy ORM models per architecture.md §5.
All financial decimals stored as strings. IDs are standard UUID strings.
"""
from datetime import datetime, timezone
import json
import uuid
from typing import Any, Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.db import Base


def _gen_uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    role = Column(String(50), default="user", nullable=False)
    created_at = Column(DateTime, default=_now, nullable=False)


class Investigation(Base):
    __tablename__ = "investigations"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    owner_id = Column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, default="")
    status = Column(String(50), default="open", nullable=False)
    archived = Column(Boolean, default=False, nullable=False)
    entity_name = Column(String(255), default="")
    created_at = Column(DateTime, default=_now, nullable=False)
    updated_at = Column(DateTime, default=_now, onupdate=_now, nullable=False)


class InvestigationMember(Base):
    __tablename__ = "investigation_members"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    investigation_id = Column(String(36), ForeignKey("investigations.id"), index=True, nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    role = Column(String(50), default="viewer", nullable=False)  # reviewer | viewer


class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    investigation_id = Column(String(36), ForeignKey("investigations.id"), index=True, nullable=False)
    filename = Column(String(255), nullable=False)
    mime = Column(String(100), default="application/pdf")
    size = Column(Integer, default=0)
    sha256 = Column(String(64), index=True, default="")
    storage_path = Column(String(500), default="")
    page_count = Column(Integer, default=0)
    source_tier = Column(String(10), default="T1")
    doc_date = Column(String(50), default="")
    entity_name = Column(String(255), default="")
    status = Column(String(50), default="queued", nullable=False)
    error_code = Column(String(50), nullable=True)
    error_msg = Column(Text, nullable=True)
    warnings_json = Column(Text, default="[]")
    uploaded_by = Column(String(36), nullable=False)
    created_at = Column(DateTime, default=_now, nullable=False)


class Page(Base):
    __tablename__ = "pages"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    document_id = Column(String(36), ForeignKey("documents.id"), index=True, nullable=False)
    page_no = Column(Integer, nullable=False)
    text = Column(Text, default="")
    words_json = Column(Text, default="[]")


class TableExtract(Base):
    __tablename__ = "table_extracts"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    document_id = Column(String(36), ForeignKey("documents.id"), index=True, nullable=False)
    page_no = Column(Integer, nullable=False)
    bbox_json = Column(Text, default="[]")
    header_json = Column(Text, default="[]")
    rows_json = Column(Text, default="[]")
    method = Column(String(50), default="pdfplumber")
    confidence = Column(Float, default=1.0)


class Fact(Base):
    __tablename__ = "facts"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    document_id = Column(String(36), ForeignKey("documents.id"), index=True, nullable=False)
    investigation_id = Column(String(36), ForeignKey("investigations.id"), index=True, nullable=False)
    metric = Column(String(100), index=True, nullable=False)
    raw_label = Column(String(255), default="")
    value_raw = Column(String(100), default="")
    value_base = Column(String(100), nullable=False)  # Decimal as string
    unit = Column(String(50), default="currency")
    scale = Column(String(50), default="unit")
    currency = Column(String(10), default="INR")
    period_json = Column(Text, default="{}")
    period_key = Column(String(50), index=True, default="")
    scope = Column(String(100), default="consolidated")
    basis = Column(String(50), default="reported")
    restated = Column(Boolean, default=False)
    confidence = Column(Float, default=1.0)
    method = Column(String(50), default="table")
    confirmed = Column(Boolean, default=False)
    locator_json = Column(Text, default="{}")


class Claim(Base):
    __tablename__ = "claims"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    investigation_id = Column(String(36), ForeignKey("investigations.id"), index=True, nullable=False)
    current_version = Column(Integer, default=1, nullable=False)
    state = Column(String(50), default="active", nullable=False)
    created_by = Column(String(36), nullable=False)
    origin = Column(String(50), default="manual", nullable=False)
    created_at = Column(DateTime, default=_now, nullable=False)


class ClaimVersion(Base):
    __tablename__ = "claim_versions"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    claim_id = Column(String(36), ForeignKey("claims.id"), index=True, nullable=False)
    version = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    claim_type = Column(String(50), default="value")
    metric = Column(String(100), default="")
    value_raw = Column(String(100), default="")
    value_precision = Column(Integer, default=0)
    unit = Column(String(50), default="currency")
    scale = Column(String(50), default="unit")
    currency = Column(String(10), default="INR")
    period_json = Column(Text, default="{}")
    scope = Column(String(100), default="consolidated")
    basis = Column(String(50), default="reported")
    entity = Column(String(255), default="")
    source_doc_id = Column(String(36), nullable=True)
    source_locator_json = Column(Text, default="{}")
    quote = Column(Text, default="")
    grounded = Column(Boolean, default=True)
    author_id = Column(String(36), nullable=False)
    created_at = Column(DateTime, default=_now, nullable=False)
    change_note = Column(String(255), default="")


class Finding(Base):
    __tablename__ = "findings"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    claim_version_id = Column(String(36), ForeignKey("claim_versions.id"), index=True, nullable=False)
    investigation_id = Column(String(36), ForeignKey("investigations.id"), index=True, nullable=False)
    verdict = Column(String(50), nullable=False)
    severity = Column(String(50), nullable=True)
    reason_codes_json = Column(Text, default="[]")
    comparability_json = Column(Text, default="{}")
    conclusion_strength = Column(String(50), default="Insufficient evidence")
    narrative = Column(Text, default="")
    superseded = Column(Boolean, default=False, nullable=False)
    calculation_id = Column(String(36), nullable=True)
    created_at = Column(DateTime, default=_now, nullable=False)
    engine_version = Column(String(50), default="0.1.0")


class Calculation(Base):
    __tablename__ = "calculations"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    formula_id = Column(String(100), nullable=False)
    input_fact_ids_json = Column(Text, default="[]")
    steps_json = Column(Text, default="[]")
    result_value = Column(String(100), default="")  # Decimal as string
    result_unit = Column(String(50), default="")
    tolerance_json = Column(Text, default="{}")
    derived = Column(Boolean, default=False)
    engine_version = Column(String(50), default="0.1.0")


class EvidenceLink(Base):
    __tablename__ = "evidence_links"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    finding_id = Column(String(36), ForeignKey("findings.id"), index=True, nullable=False)
    fact_id = Column(String(36), ForeignKey("facts.id"), index=True, nullable=False)
    stance = Column(String(50), default="supports")
    document_id = Column(String(36), nullable=True)
    locator_json = Column(Text, default="{}")
    note = Column(String(255), default="")


class Comment(Base):
    __tablename__ = "comments"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    investigation_id = Column(String(36), ForeignKey("investigations.id"), index=True, nullable=False)
    claim_id = Column(String(36), nullable=True)
    finding_id = Column(String(36), nullable=True)
    author_id = Column(String(36), nullable=False)
    body = Column(Text, nullable=False)
    assignee_id = Column(String(36), nullable=True)
    status = Column(String(50), default="open")
    created_at = Column(DateTime, default=_now, nullable=False)


class LedgerEvent(Base):
    __tablename__ = "ledger_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    investigation_id = Column(String(36), ForeignKey("investigations.id"), index=True, nullable=False)
    actor_id = Column(String(36), nullable=False)
    type = Column(String(100), nullable=False)
    payload_json = Column(Text, nullable=False)
    prev_hash = Column(String(64), nullable=False)
    hash = Column(String(64), index=True, nullable=False)
    created_at = Column(DateTime, default=_now, nullable=False)


class Job(Base):
    __tablename__ = "jobs"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    investigation_id = Column(String(36), ForeignKey("investigations.id"), index=True, nullable=False)
    document_id = Column(String(36), nullable=True)
    type = Column(String(50), default="ingest")
    status = Column(String(50), default="queued")
    progress = Column(Integer, default=0)
    step = Column(String(100), default="queued")
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_now, nullable=False)
    finished_at = Column(DateTime, nullable=True)


class ShareToken(Base):
    __tablename__ = "share_tokens"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    investigation_id = Column(String(36), ForeignKey("investigations.id"), index=True, nullable=False)
    token_hash = Column(String(64), index=True, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    scope = Column(String(50), default="read_only")
