"""
Ledger API: list events and verify cryptographic hash chain integrity (Task 3.9).
"""
import json
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models.models import LedgerEvent, User
from app.services.access import investigation_access
from app.services.auth import get_current_user
from app.services.ledger import verify_ledger_chain

router = APIRouter()


@router.get("/investigations/{id}/ledger", response_model=List[Dict[str, Any]])
async def list_ledger_events(
    id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    inv, _ = await investigation_access(id, current_user, session, min_role="viewer")
    res = await session.execute(
        select(LedgerEvent)
        .where(LedgerEvent.investigation_id == inv.id)
        .order_by(LedgerEvent.id.asc())
    )
    events = res.scalars().all()
    return [
        {
            "id": ev.id,
            "investigation_id": ev.investigation_id,
            "actor_id": ev.actor_id,
            "type": ev.type,
            "payload": json.loads(ev.payload_json or "{}"),
            "prev_hash": ev.prev_hash,
            "hash": ev.hash,
            "created_at": ev.created_at.isoformat(),
        }
        for ev in events
    ]


@router.get("/investigations/{id}/ledger/verify", response_model=Dict[str, Any])
async def verify_ledger(
    id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    inv, _ = await investigation_access(id, current_user, session, min_role="viewer")
    is_valid, head_hash, count, tampered_id = await verify_ledger_chain(session, inv.id)
    return {
        "valid": is_valid,
        "head_hash": head_hash,
        "events_count": count,
        "tampered_event_id": tampered_id,
        "investigation_id": inv.id,
    }

