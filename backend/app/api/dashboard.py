"""
Dashboard API: aggregate counts, findings summary, and unresolved queue (Task 3.10).
"""
import json
from typing import Any, Dict, List
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models.models import Claim, ClaimVersion, Document, Finding, User
from app.services.access import investigation_access
from app.services.auth import get_current_user

router = APIRouter()


@router.get("/investigations/{id}/dashboard", response_model=Dict[str, Any])
async def get_dashboard(
    id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    inv, _ = await investigation_access(id, current_user, session, min_role="viewer")

    # Document count
    docs_count = await session.scalar(
        select(func.count(Document.id)).where(Document.investigation_id == inv.id)
    )

    # Claim count
    claims_count = await session.scalar(
        select(func.count(Claim.id)).where(Claim.investigation_id == inv.id)
    )

    # Findings summary
    findings_res = await session.execute(
        select(Finding).where(Finding.investigation_id == inv.id, Finding.superseded.is_(False))
    )
    active_findings = findings_res.scalars().all()

    summary = {"Consistent": 0, "Conflicting": 0, "Inconclusive": 0}
    unresolved_queue: List[Dict[str, Any]] = []

    for f in active_findings:
        summary[f.verdict] = summary.get(f.verdict, 0) + 1
        if f.verdict in ("Inconclusive", "Conflicting"):
            reasons = json.loads(f.reason_codes_json or "[]")
            next_action = "Review source documents for reconciliation" if f.verdict == "Conflicting" else "Upload missing period facts or verify units"
            unresolved_queue.append({
                "finding_id": f.id,
                "claim_version_id": f.claim_version_id,
                "verdict": f.verdict,
                "severity": f.severity,
                "strength": f.conclusion_strength,
                "reasons": reasons,
                "narrative": f.narrative,
                "recommended_action": next_action,
            })

    return {
        "investigation_id": inv.id,
        "title": inv.title,
        "status": inv.status,
        "counts": {
            "documents": docs_count or 0,
            "claims": claims_count or 0,
            "findings": len(active_findings),
        },
        "findings_summary": summary,
        "unresolved_queue": unresolved_queue,
    }

