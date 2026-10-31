"""
Access control service: investigation_access() helper.
Returns 404 on non-existent OR unauthorized access (no ID enumeration leak).
"""
from typing import Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Investigation, InvestigationMember, User

ROLE_HIERARCHY = {"viewer": 1, "reviewer": 2, "owner": 3}


async def investigation_access(
    investigation_id: str,
    user: User,
    session: AsyncSession,
    min_role: str = "viewer",
) -> Tuple[Investigation, str]:
    """
    Verify user access to investigation.
    Raises strict 404 if investigation does not exist or user lacks access.
    """
    res = await session.execute(
        select(Investigation).where(Investigation.id == investigation_id)
    )
    inv = res.scalar_one_or_none()
    if not inv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Investigation not found")

    if inv.owner_id == user.id:
        return inv, "owner"

    member_res = await session.execute(
        select(InvestigationMember).where(
            InvestigationMember.investigation_id == investigation_id,
            InvestigationMember.user_id == user.id,
        )
    )
    member = member_res.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Investigation not found")

    user_level = ROLE_HIERARCHY.get(member.role, 0)
    required_level = ROLE_HIERARCHY.get(min_role, 1)
    if user_level < required_level:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Investigation not found")

    return inv, member.role

