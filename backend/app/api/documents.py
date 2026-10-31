"""
Documents router: upload, download, metadata, pages, facts.
"""
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import get_session
from app.ingest.pipeline import process_document_pipeline
from app.models.models import Document, Fact, Page, User
from app.services.access import investigation_access
from app.services.auth import get_current_user
from app.services.jobs import create_job

settings = get_settings()
router = APIRouter()


class DocumentItem(BaseModel):
    id: str
    investigation_id: str
    filename: str
    mime: str
    size: int
    sha256: str
    page_count: int
    status: str
    source_tier: str
    created_at: str


class PageItem(BaseModel):
    page_no: int
    text: str
    words: List[Dict[str, Any]]


@router.post("/investigations/{id}/documents", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def upload_document(
    id: str,
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    inv, _ = await investigation_access(id, current_user, session, min_role="reviewer")

    content = await file.read()
    if len(content) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"File exceeds maximum allowed size {settings.max_upload_mb}MB")

    sha256_hash = hashlib.sha256(content).hexdigest()
    ext = Path(file.filename or "file").suffix.lower() or ".bin"

    upload_dir = Path("data/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    stored_path = upload_dir / f"{sha256_hash}{ext}"
    stored_path.write_bytes(content)

    doc = Document(
        investigation_id=inv.id,
        filename=file.filename or "document",
        mime=file.content_type or "application/octet-stream",
        size=len(content),
        sha256=sha256_hash,
        storage_path=str(stored_path),
        uploaded_by=current_user.id,
        status="queued",
    )
    session.add(doc)
    await session.commit()
    await session.refresh(doc)

    job = await create_job(session, investigation_id=inv.id, document_id=doc.id, job_type="ingest")

    # Run processing directly or asynchronously
    await process_document_pipeline(session, doc, job_id=job.id)

    return {
        "document": {
            "id": doc.id,
            "filename": doc.filename,
            "size": doc.size,
            "status": doc.status,
            "sha256": doc.sha256,
        },
        "job_id": job.id,
    }


@router.get("/investigations/{id}/documents", response_model=List[DocumentItem])
async def list_documents(
    id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    inv, _ = await investigation_access(id, current_user, session, min_role="viewer")
    res = await session.execute(
        select(Document).where(Document.investigation_id == inv.id).order_by(Document.created_at.desc())
    )
    docs = res.scalars().all()
    return [
        DocumentItem(
            id=d.id,
            investigation_id=d.investigation_id,
            filename=d.filename,
            mime=d.mime,
            size=d.size,
            sha256=d.sha256,
            page_count=d.page_count,
            status=d.status,
            source_tier=d.source_tier,
            created_at=d.created_at.isoformat(),
        )
        for d in docs
    ]


@router.get("/documents/{id}", response_model=DocumentItem)
async def get_document(
    id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    res = await session.execute(select(Document).where(Document.id == id))
    doc = res.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    await investigation_access(doc.investigation_id, current_user, session, min_role="viewer")

    return DocumentItem(
        id=doc.id,
        investigation_id=doc.investigation_id,
        filename=doc.filename,
        mime=doc.mime,
        size=doc.size,
        sha256=doc.sha256,
        page_count=doc.page_count,
        status=doc.status,
        source_tier=doc.source_tier,
        created_at=doc.created_at.isoformat(),
    )


@router.get("/documents/{id}/file")
async def download_document_file(
    id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    res = await session.execute(select(Document).where(Document.id == id))
    doc = res.scalar_one_or_none()
    if not doc or not Path(doc.storage_path).exists():
        raise HTTPException(status_code=404, detail="Document file not found")
    await investigation_access(doc.investigation_id, current_user, session, min_role="viewer")

    return FileResponse(
        path=doc.storage_path,
        filename=doc.filename,
        media_type=doc.mime,
    )


@router.get("/documents/{id}/pages/{n}", response_model=PageItem)
async def get_document_page(
    id: str,
    n: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    res = await session.execute(select(Document).where(Document.id == id))
    doc = res.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    await investigation_access(doc.investigation_id, current_user, session, min_role="viewer")

    page_res = await session.execute(
        select(Page).where(Page.document_id == id, Page.page_no == n)
    )
    page = page_res.scalar_one_or_none()
    if not page:
        raise HTTPException(status_code=404, detail=f"Page {n} not found")

    return PageItem(
        page_no=page.page_no,
        text=page.text,
        words=json.loads(page.words_json or "[]"),
    )


@router.get("/documents/{id}/facts", response_model=List[Dict[str, Any]])
async def get_document_facts(
    id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    res = await session.execute(select(Document).where(Document.id == id))
    doc = res.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    await investigation_access(doc.investigation_id, current_user, session, min_role="viewer")

    facts_res = await session.execute(select(Fact).where(Fact.document_id == id))
    facts = facts_res.scalars().all()
    return [
        {
            "id": f.id,
            "metric": f.metric,
            "raw_label": f.raw_label,
            "value_raw": f.value_raw,
            "value_base": f.value_base,
            "scale": f.scale,
            "currency": f.currency,
            "period": json.loads(f.period_json or "{}"),
            "confirmed": f.confirmed,
            "confidence": f.confidence,
            "method": f.method,
            "locator": json.loads(f.locator_json or "{}"),
        }
        for f in facts
    ]
