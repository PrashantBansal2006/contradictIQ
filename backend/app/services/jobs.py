"""
Background job tracking and SSE broadcasting service per architecture.md §6.
"""
import asyncio
from datetime import datetime, timezone
import json
from typing import Any, AsyncGenerator, Dict, Optional, Set

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Job

# In-memory pub/sub listeners for SSE: job_id -> set of asyncio.Queue
_listeners: Dict[str, Set[asyncio.Queue]] = {}


def broadcast_job_event(job_id: str, data: Dict[str, Any]) -> None:
    """Push update to all active SSE subscribers for this job."""
    if job_id in _listeners:
        for q in list(_listeners[job_id]):
            try:
                q.put_nowait(data)
            except asyncio.QueueFull:
                pass


async def subscribe_job_events(job_id: str) -> AsyncGenerator[str, None]:
    """Yield SSE data events for a given job."""
    q: asyncio.Queue = asyncio.Queue(maxsize=50)
    _listeners.setdefault(job_id, set()).add(q)
    try:
        while True:
            try:
                data = await asyncio.wait_for(q.get(), timeout=20.0)
                yield f"data: {json.dumps(data)}\n\n"
                if data.get("status") in ("ready", "failed"):
                    break
            except asyncio.TimeoutError:
                # Keep-alive heartbeat
                yield ": keep-alive\n\n"
    finally:
        if job_id in _listeners:
            _listeners[job_id].discard(q)
            if not _listeners[job_id]:
                del _listeners[job_id]


async def create_job(
    session: AsyncSession,
    investigation_id: str,
    document_id: Optional[str] = None,
    job_type: str = "ingest",
) -> Job:
    job = Job(
        investigation_id=investigation_id,
        document_id=document_id,
        type=job_type,
        status="queued",
        progress=0,
        step="queued",
        created_at=datetime.now(timezone.utc),
    )
    session.add(job)
    await session.commit()
    await session.refresh(job)
    broadcast_job_event(job.id, {"job_id": job.id, "status": "queued", "progress": 0, "step": "queued"})
    return job


async def update_job_progress(
    session: AsyncSession,
    job_id: str,
    status: str,
    progress: int,
    step: str,
    error: Optional[str] = None,
) -> None:
    res = await session.execute(select(Job).where(Job.id == job_id))
    job = res.scalar_one_or_none()
    if job:
        job.status = status
        job.progress = progress
        job.step = step
        job.error = error
        if status in ("ready", "failed"):
            job.finished_at = datetime.now(timezone.utc)
        await session.commit()
        broadcast_job_event(
            job_id,
            {"job_id": job_id, "status": status, "progress": progress, "step": step, "error": error},
        )
