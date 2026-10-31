"""
Jobs API: polling and SSE event streaming (Task 3.11).
"""
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models.models import Job, User
from app.services.access import investigation_access
from app.services.auth import get_current_user
from app.services.jobs import subscribe_job_events

router = APIRouter()


@router.get("/jobs/{id}", response_model=Dict[str, Any])
async def get_job_status(
    id: str,
    session: AsyncSession = Depends(get_session),
):
    res = await session.execute(select(Job).where(Job.id == id))
    job = res.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return {
        "id": job.id,
        "investigation_id": job.investigation_id,
        "document_id": job.document_id,
        "type": job.type,
        "status": job.status,
        "progress": job.progress,
        "step": job.step,
        "error": job.error,
        "created_at": job.created_at.isoformat(),
        "finished_at": job.finished_at.isoformat() if job.finished_at else None,
    }


@router.get("/jobs/{id}/events")
async def stream_job_events(id: str):
    return StreamingResponse(
        subscribe_job_events(id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
