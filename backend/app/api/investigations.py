"""
Investigations CRUD router per architecture.md §16.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models.models import Investigation, InvestigationMember, User
from app.services.access import investigation_access
from app.services.auth import get_current_user
from app.services.ledger import append_ledger_event

router = APIRouter()


class InvestigationCreateReq(BaseModel):
    title: str
    description: Optional[str] = ""
    entity_name: Optional[str] = ""


class InvestigationUpdateReq(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    entity_name: Optional[str] = None
    status: Optional[str] = None


class InvestigationItem(BaseModel):
    id: str
    owner_id: str
    title: str
    description: str
    status: str
    archived: bool
    entity_name: str
    created_at: str
    updated_at: str


@router.post("", response_model=InvestigationItem, status_code=status.HTTP_201_CREATED)
async def create_investigation(
    req: InvestigationCreateReq,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    inv = Investigation(
        owner_id=current_user.id,
        title=req.title,
        description=req.description or "",
        entity_name=req.entity_name or "",
    )
    session.add(inv)
    await session.commit()
    await session.refresh(inv)

    await append_ledger_event(
        session=session,
        investigation_id=inv.id,
        actor_id=current_user.id,
        event_type="INVESTIGATION_CREATED",
        payload={"title": inv.title, "entity_name": inv.entity_name},
    )
    await session.commit()

    return InvestigationItem(
        id=inv.id,
        owner_id=inv.owner_id,
        title=inv.title,
        description=inv.description,
        status=inv.status,
        archived=inv.archived,
        entity_name=inv.entity_name,
        created_at=inv.created_at.isoformat(),
        updated_at=inv.updated_at.isoformat(),
    )


@router.get("", response_model=List[InvestigationItem])
async def list_investigations(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    stmt = (
        select(Investigation)
        .outerjoin(InvestigationMember, InvestigationMember.investigation_id == Investigation.id)
        .where(
            or_(
                Investigation.owner_id == current_user.id,
                InvestigationMember.user_id == current_user.id,
            ),
            Investigation.archived.is_(False),
        )
        .distinct()
        .order_by(Investigation.created_at.desc())
    )
    res = await session.execute(stmt)
    invs = res.scalars().all()
    return [
        InvestigationItem(
            id=i.id,
            owner_id=i.owner_id,
            title=i.title,
            description=i.description,
            status=i.status,
            archived=i.archived,
            entity_name=i.entity_name,
            created_at=i.created_at.isoformat(),
            updated_at=i.updated_at.isoformat(),
        )
        for i in invs
    ]


@router.get("/{id}", response_model=InvestigationItem)
async def get_investigation(
    id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    inv, _ = await investigation_access(id, current_user, session, min_role="viewer")
    return InvestigationItem(
        id=inv.id,
        owner_id=inv.owner_id,
        title=inv.title,
        description=inv.description,
        status=inv.status,
        archived=inv.archived,
        entity_name=inv.entity_name,
        created_at=inv.created_at.isoformat(),
        updated_at=inv.updated_at.isoformat(),
    )


@router.patch("/{id}", response_model=InvestigationItem)
async def update_investigation(
    id: str,
    req: InvestigationUpdateReq,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    inv, _ = await investigation_access(id, current_user, session, min_role="reviewer")
    if req.title is not None:
        inv.title = req.title
    if req.description is not None:
        inv.description = req.description
    if req.entity_name is not None:
        inv.entity_name = req.entity_name
    if req.status is not None:
        inv.status = req.status

    await append_ledger_event(
        session=session,
        investigation_id=inv.id,
        actor_id=current_user.id,
        event_type="INVESTIGATION_UPDATED",
        payload=req.model_dump(exclude_unset=True),
    )
    await session.commit()
    await session.refresh(inv)

    return InvestigationItem(
        id=inv.id,
        owner_id=inv.owner_id,
        title=inv.title,
        description=inv.description,
        status=inv.status,
        archived=inv.archived,
        entity_name=inv.entity_name,
        created_at=inv.created_at.isoformat(),
        updated_at=inv.updated_at.isoformat(),
    )


@router.post("/{id}/archive")
async def archive_investigation(
    id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    inv, _ = await investigation_access(id, current_user, session, min_role="owner")
    inv.archived = True

    await append_ledger_event(
        session=session,
        investigation_id=inv.id,
        actor_id=current_user.id,
        event_type="INVESTIGATION_ARCHIVED",
        payload={"investigation_id": inv.id},
    )
    await session.commit()
    return {"status": "archived", "id": inv.id}

