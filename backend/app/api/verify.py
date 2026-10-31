"""
Verification API: assemble facts, run deterministic decide(), persist Finding, Calculation, and EvidenceLinks (Task 3.8).
"""
from decimal import Decimal
import json
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import decide
from app.db import get_session
from app.models.models import Calculation, Claim, ClaimVersion, EvidenceLink, Fact, Finding, User
from app.services.access import investigation_access
from app.services.auth import get_current_user
from app.services.ledger import append_ledger_event

router = APIRouter()


@router.post("/claims/{id}/verify", response_model=Dict[str, Any])
async def verify_claim(
    id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Verify claim against available facts using the deterministic core engine.
    Persists Finding + Calculation trace + EvidenceLinks, logs ledger event.
    """
    res = await session.execute(select(Claim).where(Claim.id == id))
    claim = res.scalar_one_or_none()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    inv, _ = await investigation_access(claim.investigation_id, current_user, session, min_role="reviewer")

    v_res = await session.execute(
        select(ClaimVersion).where(ClaimVersion.claim_id == claim.id, ClaimVersion.version == claim.current_version)
    )
    v = v_res.scalar_one_or_none()
    if not v:
        raise HTTPException(status_code=404, detail="Claim version not found")

    # Fetch facts for this investigation
    facts_res = await session.execute(
        select(Fact).where(Fact.investigation_id == claim.investigation_id)
    )
    facts = facts_res.scalars().all()

    # Prepare claim dict for decide()
    import re
    num_val = None
    if v.value_raw:
        m = re.search(r"[-+]?[0-9]+(?:\.[0-9]+)?", v.value_raw.replace(",", ""))
        if m:
            try:
                num_val = float(m.group(0))
            except Exception:
                num_val = None

    claim_dict = {
        "id": claim.id,
        "text": v.text,
        "claim_type": v.claim_type,
        "metric": v.metric,
        "value": num_val,
        "value_raw": v.value_raw,
        "value_precision": v.value_precision,
        "unit": v.unit,
        "scale": v.scale,
        "currency": v.currency,
        "period": json.loads(v.period_json or "{}"),
        "scope": v.scope,
        "basis": v.basis,
        "entity": v.entity,
        "hedged": "around" in v.text.lower() or "approx" in v.text.lower(),
        "parseable": True,
    }

    # Prepare facts list for decide()
    facts_list = []
    for f in facts:
        facts_list.append({
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
            "scope": f.scope,
            "basis": f.basis,
            "restated": f.restated,
            "confidence": f.confidence,
            "method": f.method,
            "confirmed": f.confirmed,
            "locator": json.loads(f.locator_json or "{}"),
        })

    # Call deterministic verification core
    result = decide(claim_dict, facts_list)

    # Persist Calculation if computation occurred
    calc_id = None
    if result.calculation:
        calc_row = Calculation(
            formula_id=result.calculation.formula_id,
            input_fact_ids_json=json.dumps(result.calculation.inputs),
            steps_json=json.dumps([
                {
                    "label": s.label,
                    "expr": s.expr,
                    "values": {k: float(val) if isinstance(val, Decimal) else val for k, val in s.values.items()},
                    "result": float(s.result),
                }
                for s in result.calculation.steps
            ]),
            result_value=str(result.calculation.value),
            result_unit=result.calculation.unit,
            tolerance_json=json.dumps({"tolerance": float(result.calculation.tolerance)}),
            derived=result.calculation.derived,
            engine_version=result.engine_version,
        )
        session.add(calc_row)
        await session.flush()
        calc_id = calc_row.id

    # Persist Finding
    finding = Finding(
        claim_version_id=v.id,
        investigation_id=claim.investigation_id,
        verdict=result.verdict,
        severity=result.severity,
        reason_codes_json=json.dumps(result.reasons),
        comparability_json=json.dumps({"cap_reasons": result.cap_reasons}),
        conclusion_strength=result.conclusion_strength,
        narrative=result.narrative,
        superseded=False,
        calculation_id=calc_id,
        engine_version=result.engine_version,
    )
    session.add(finding)
    await session.flush()

    # Persist EvidenceLinks
    links_payload = []
    for link in result.evidence_links:
        link_row = EvidenceLink(
            finding_id=finding.id,
            fact_id=link.fact_id,
            stance=link.stance,
            document_id=link.document_id,
            locator_json=json.dumps(link.locator or {}),
            note=link.note or "",
        )
        session.add(link_row)
        links_payload.append({
            "fact_id": link.fact_id,
            "stance": link.stance,
            "document_id": link.document_id,
            "locator": link.locator,
        })

    # Log to Ledger
    await append_ledger_event(
        session=session,
        investigation_id=claim.investigation_id,
        actor_id=current_user.id,
        event_type="VERIFICATION_RUN",
        payload={
            "finding_id": finding.id,
            "claim_id": claim.id,
            "claim_version": v.version,
            "verdict": result.verdict,
            "severity": result.severity,
            "strength": result.conclusion_strength,
        },
    )
    await session.commit()

    return {
        "finding_id": finding.id,
        "verdict": result.verdict,
        "severity": result.severity,
        "conclusion_strength": result.conclusion_strength,
        "reasons": result.reasons,
        "narrative": result.narrative,
        "calculation": result.to_dict()["calculation"],
        "evidence_links": links_payload,
        "engine_version": result.engine_version,
    }


@router.post("/investigations/{id}/verify-all", response_model=Dict[str, Any])
async def verify_all_claims(
    id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    inv, _ = await investigation_access(id, current_user, session, min_role="reviewer")
    claims_res = await session.execute(
        select(Claim).where(Claim.investigation_id == inv.id, Claim.state.in_(["active", "confirmed"]))
    )
    claims = claims_res.scalars().all()
    verified_count = 0
    for c in claims:
        await verify_claim(c.id, current_user=current_user, session=session)
        verified_count += 1
    return {"investigation_id": inv.id, "verified_count": verified_count}


@router.get("/findings/{id}", response_model=Dict[str, Any])
async def get_finding(
    id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    res = await session.execute(select(Finding).where(Finding.id == id))
    finding = res.scalar_one_or_none()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")

    await investigation_access(finding.investigation_id, current_user, session, min_role="viewer")

    calc_dict = None
    if finding.calculation_id:
        calc_res = await session.execute(
            select(Calculation).where(Calculation.id == finding.calculation_id)
        )
        calc = calc_res.scalar_one_or_none()
        if calc:
            calc_dict = {
                "formula_id": calc.formula_id,
                "result_value": calc.result_value,
                "result_unit": calc.result_unit,
                "steps": json.loads(calc.steps_json or "[]"),
                "derived": calc.derived,
            }

    links_res = await session.execute(
        select(EvidenceLink).where(EvidenceLink.finding_id == finding.id)
    )
    links = links_res.scalars().all()

    return {
        "id": finding.id,
        "claim_version_id": finding.claim_version_id,
        "verdict": finding.verdict,
        "severity": finding.severity,
        "conclusion_strength": finding.conclusion_strength,
        "reasons": json.loads(finding.reason_codes_json or "[]"),
        "narrative": finding.narrative,
        "superseded": finding.superseded,
        "calculation": calc_dict,
        "evidence_links": [
            {
                "fact_id": l.fact_id,
                "stance": l.stance,
                "document_id": l.document_id,
                "locator": json.loads(l.locator_json or "{}"),
            }
            for l in links
        ],
        "engine_version": finding.engine_version,
    }
