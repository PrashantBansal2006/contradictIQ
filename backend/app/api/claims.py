"""
Claims API: create, patch->new version, confirm, list versions with ledger event logging (Task 3.7).
"""
import json
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models.models import Claim, ClaimVersion, Finding, User
from app.services.access import investigation_access
from app.services.auth import get_current_user
from app.services.ledger import append_ledger_event

router = APIRouter()


class ClaimCreateReq(BaseModel):
    text: str
    claim_type: str = "value"
    metric: str
    value_raw: Optional[str] = ""
    value: Optional[float] = None
    value_precision: int = 0
    unit: str = "currency"
    scale: str = "unit"
    currency: str = "INR"
    period: Optional[Dict[str, Any]] = None
    scope: str = "consolidated"
    basis: str = "reported"
    entity: Optional[str] = ""
    quote: Optional[str] = ""
    source_doc_id: Optional[str] = None


class ClaimUpdateReq(BaseModel):
    text: Optional[str] = None
    metric: Optional[str] = None
    value_raw: Optional[str] = None
    value: Optional[float] = None
    unit: Optional[str] = None
    scale: Optional[str] = None
    currency: Optional[str] = None
    period: Optional[Dict[str, Any]] = None
    change_note: Optional[str] = "Updated claim"


@router.post("/investigations/{id}/claims", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_claim(
    id: str,
    req: ClaimCreateReq,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    inv, _ = await investigation_access(id, current_user, session, min_role="reviewer")

    claim = Claim(
        investigation_id=inv.id,
        current_version=1,
        state="active",
        created_by=current_user.id,
        origin="manual",
    )
    session.add(claim)
    await session.flush()

    c_version = ClaimVersion(
        claim_id=claim.id,
        version=1,
        text=req.text,
        claim_type=req.claim_type,
        metric=req.metric,
        value_raw=req.value_raw or (str(req.value) if req.value is not None else ""),
        value_precision=req.value_precision,
        unit=req.unit,
        scale=req.scale,
        currency=req.currency,
        period_json=json.dumps(req.period or {"kind": "FY", "fy": 2024}),
        scope=req.scope,
        basis=req.basis,
        entity=req.entity or inv.entity_name,
        source_doc_id=req.source_doc_id,
        quote=req.quote or "",
        grounded=True,
        author_id=current_user.id,
        change_note="Initial version",
    )
    session.add(c_version)

    await append_ledger_event(
        session=session,
        investigation_id=inv.id,
        actor_id=current_user.id,
        event_type="CLAIM_CREATED",
        payload={"claim_id": claim.id, "version": 1, "text": req.text, "metric": req.metric},
    )
    await session.commit()

    return {
        "id": claim.id,
        "investigation_id": claim.investigation_id,
        "current_version": 1,
        "state": claim.state,
        "text": c_version.text,
        "metric": c_version.metric,
        "value_raw": c_version.value_raw,
    }


@router.get("/investigations/{id}/claims", response_model=List[Dict[str, Any]])
async def list_claims(
    id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    inv, _ = await investigation_access(id, current_user, session, min_role="viewer")
    res = await session.execute(
        select(Claim).where(Claim.investigation_id == inv.id).order_by(Claim.created_at.desc())
    )
    claims = res.scalars().all()

    items = []
    for c in claims:
        v_res = await session.execute(
            select(ClaimVersion).where(ClaimVersion.claim_id == c.id, ClaimVersion.version == c.current_version)
        )
        v = v_res.scalar_one_or_none()
        items.append({
            "id": c.id,
            "investigation_id": c.investigation_id,
            "current_version": c.current_version,
            "state": c.state,
            "text": v.text if v else "",
            "metric": v.metric if v else "",
            "value_raw": v.value_raw if v else "",
            "period": json.loads(v.period_json or "{}") if v else {},
            "created_at": c.created_at.isoformat(),
        })
    return items


@router.get("/claims/{id}", response_model=Dict[str, Any])
async def get_claim(
    id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    res = await session.execute(select(Claim).where(Claim.id == id))
    claim = res.scalar_one_or_none()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    await investigation_access(claim.investigation_id, current_user, session, min_role="viewer")

    v_res = await session.execute(
        select(ClaimVersion).where(ClaimVersion.claim_id == claim.id, ClaimVersion.version == claim.current_version)
    )
    v = v_res.scalar_one_or_none()

    return {
        "id": claim.id,
        "investigation_id": claim.investigation_id,
        "current_version": claim.current_version,
        "state": claim.state,
        "version_data": {
            "version": v.version if v else 1,
            "text": v.text if v else "",
            "metric": v.metric if v else "",
            "value_raw": v.value_raw if v else "",
            "period": json.loads(v.period_json or "{}") if v else {},
            "scale": v.scale if v else "unit",
            "currency": v.currency if v else "INR",
        },
    }


@router.patch("/claims/{id}", response_model=Dict[str, Any])
async def update_claim_new_version(
    id: str,
    req: ClaimUpdateReq,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Patch a claim: increments version, creates new ClaimVersion, marks prior findings superseded,
    and logs CLAIM_UPDATED to the ledger (Task 3.7 & FR-14).
    """
    res = await session.execute(select(Claim).where(Claim.id == id))
    claim = res.scalar_one_or_none()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    await investigation_access(claim.investigation_id, current_user, session, min_role="reviewer")

    # Get latest version
    cur_v_res = await session.execute(
        select(ClaimVersion).where(ClaimVersion.claim_id == claim.id, ClaimVersion.version == claim.current_version)
    )
    cur_v = cur_v_res.scalar_one_or_none()

    new_version_num = claim.current_version + 1
    claim.current_version = new_version_num

    new_v = ClaimVersion(
        claim_id=claim.id,
        version=new_version_num,
        text=req.text if req.text is not None else (cur_v.text if cur_v else ""),
        claim_type=cur_v.claim_type if cur_v else "value",
        metric=req.metric if req.metric is not None else (cur_v.metric if cur_v else ""),
        value_raw=req.value_raw if req.value_raw is not None else (cur_v.value_raw if cur_v else ""),
        unit=req.unit if req.unit is not None else (cur_v.unit if cur_v else "currency"),
        scale=req.scale if req.scale is not None else (cur_v.scale if cur_v else "unit"),
        currency=req.currency if req.currency is not None else (cur_v.currency if cur_v else "INR"),
        period_json=json.dumps(req.period) if req.period is not None else (cur_v.period_json if cur_v else "{}"),
        scope=cur_v.scope if cur_v else "consolidated",
        basis=cur_v.basis if cur_v else "reported",
        entity=cur_v.entity if cur_v else "",
        source_doc_id=cur_v.source_doc_id if cur_v else None,
        quote=cur_v.quote if cur_v else "",
        grounded=True,
        author_id=current_user.id,
        change_note=req.change_note or "Version bump",
    )
    session.add(new_v)

    # Mark prior findings for this claim as superseded (Task 3.7 & Brownie B10)
    if cur_v:
        await session.execute(
            update(Finding)
            .where(Finding.claim_version_id == cur_v.id)
            .values(superseded=True)
        )

    await append_ledger_event(
        session=session,
        investigation_id=claim.investigation_id,
        actor_id=current_user.id,
        event_type="CLAIM_UPDATED",
        payload={
            "claim_id": claim.id,
            "version": new_version_num,
            "change_note": req.change_note,
            "new_text": new_v.text,
        },
    )
    await session.commit()

    return {
        "id": claim.id,
        "investigation_id": claim.investigation_id,
        "current_version": new_version_num,
        "text": new_v.text,
        "metric": new_v.metric,
        "value_raw": new_v.value_raw,
        "status": "version_created",
    }


@router.post("/claims/{id}/confirm")
async def confirm_claim(
    id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    res = await session.execute(select(Claim).where(Claim.id == id))
    claim = res.scalar_one_or_none()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    await investigation_access(claim.investigation_id, current_user, session, min_role="reviewer")
    claim.state = "confirmed"

    await append_ledger_event(
        session=session,
        investigation_id=claim.investigation_id,
        actor_id=current_user.id,
        event_type="CLAIM_CONFIRMED",
        payload={"claim_id": claim.id, "version": claim.current_version},
    )
    await session.commit()
    return {"id": claim.id, "state": "confirmed"}


@router.get("/claims/{id}/versions", response_model=List[Dict[str, Any]])
async def list_claim_versions(
    id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    res = await session.execute(select(Claim).where(Claim.id == id))
    claim = res.scalar_one_or_none()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    await investigation_access(claim.investigation_id, current_user, session, min_role="viewer")

    v_res = await session.execute(
        select(ClaimVersion).where(ClaimVersion.claim_id == claim.id).order_by(ClaimVersion.version.asc())
    )
    versions = v_res.scalars().all()
    return [
        {
            "id": v.id,
            "version": v.version,
            "text": v.text,
            "metric": v.metric,
            "value_raw": v.value_raw,
            "period": json.loads(v.period_json or "{}"),
            "change_note": v.change_note,
            "created_at": v.created_at.isoformat(),
        }
        for v in versions
    ]
