"""
Facts API: list, confirm, edit facts with ledger event logging (Task 3.6).
"""
import json
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models.models import Fact, User
from app.services.access import investigation_access
from app.services.auth import get_current_user
from app.services.ledger import append_ledger_event

router = APIRouter()


class FactPatchReq(BaseModel):
    value_raw: Optional[str] = None
    value_base: Optional[str] = None
    confirmed: Optional[bool] = None
    metric: Optional[str] = None


@router.get("/investigations/{id}/facts", response_model=List[Dict[str, Any]])
async def list_investigation_facts(
    id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    inv, _ = await investigation_access(id, current_user, session, min_role="viewer")
    res = await session.execute(
        select(Fact).where(Fact.investigation_id == inv.id).order_by(Fact.metric.asc())
    )
    facts = res.scalars().all()
    return [
        {
            "id": f.id,
            "document_id": f.document_id,
            "metric": f.metric,
            "raw_label": f.raw_label,
            "value_raw": f.value_raw,
            "value_base": f.value_base,
            "unit": f.unit,
            "scale": f.scale,
            "currency": f.currency,
            "period": json.loads(f.period_json or "{}"),
            "period_key": f.period_key,
            "scope": f.scope,
            "basis": f.basis,
            "restated": f.restated,
            "confidence": f.confidence,
            "method": f.method,
            "confirmed": f.confirmed,
            "locator": json.loads(f.locator_json or "{}"),
        }
        for f in facts
    ]


@router.patch("/facts/{id}", response_model=Dict[str, Any])
async def update_fact(
    id: str,
    req: FactPatchReq,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    res = await session.execute(select(Fact).where(Fact.id == id))
    fact = res.scalar_one_or_none()
    if not fact:
        raise HTTPException(status_code=404, detail="Fact not found")

    await investigation_access(fact.investigation_id, current_user, session, min_role="reviewer")

    old_val = fact.value_base
    if req.value_raw is not None:
        fact.value_raw = req.value_raw
    if req.value_base is not None:
        fact.value_base = req.value_base
    if req.confirmed is not None:
        fact.confirmed = req.confirmed
    if req.metric is not None:
        fact.metric = req.metric

    await append_ledger_event(
        session=session,
        investigation_id=fact.investigation_id,
        actor_id=current_user.id,
        event_type="FACT_UPDATED",
        payload={"fact_id": fact.id, "old_value_base": old_val, "new_value_base": fact.value_base, "confirmed": fact.confirmed},
    )
    await session.commit()
    await session.refresh(fact)

    return {
        "id": fact.id,
        "metric": fact.metric,
        "value_base": fact.value_base,
        "confirmed": fact.confirmed,
        "status": "updated",
    }

