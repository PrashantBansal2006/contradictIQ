"""
Cryptographic hash-chained audit ledger service per architecture.md §13.
"""
from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import LedgerEvent

GENESIS_HASH = "0" * 64


def compute_event_hash(
    prev_hash: str,
    investigation_id: str,
    actor_id: str,
    event_type: str,
    payload_json: str,
) -> str:
    payload_hash = hashlib.sha256(payload_json.encode("utf-8")).hexdigest()
    content = f"{prev_hash}:{investigation_id}:{actor_id}:{event_type}:{payload_hash}"
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


async def append_ledger_event(
    session: AsyncSession,
    investigation_id: str,
    actor_id: str,
    event_type: str,
    payload: Dict[str, Any],
) -> LedgerEvent:
    """Append an event to the hash-chained ledger for an investigation."""
    latest_res = await session.execute(
        select(LedgerEvent)
        .where(LedgerEvent.investigation_id == investigation_id)
        .order_by(LedgerEvent.id.desc())
        .limit(1)
    )
    latest = latest_res.scalar_one_or_none()
    prev_hash = latest.hash if latest else GENESIS_HASH

    payload_json = json.dumps(payload, sort_keys=True)
    event_hash = compute_event_hash(
        prev_hash=prev_hash,
        investigation_id=investigation_id,
        actor_id=actor_id,
        event_type=event_type,
        payload_json=payload_json,
    )

    event = LedgerEvent(
        investigation_id=investigation_id,
        actor_id=actor_id,
        type=event_type,
        payload_json=payload_json,
        prev_hash=prev_hash,
        hash=event_hash,
        created_at=datetime.now(timezone.utc),
    )
    session.add(event)
    await session.flush()
    return event


async def verify_ledger_chain(
    session: AsyncSession,
    investigation_id: str,
) -> Tuple[bool, Optional[str], int, Optional[int]]:
    """
    Verify the cryptographic integrity of the ledger chain for an investigation.
    Returns (is_valid, head_hash, event_count, tampered_id).
    """
    events_res = await session.execute(
        select(LedgerEvent)
        .where(LedgerEvent.investigation_id == investigation_id)
        .order_by(LedgerEvent.id.asc())
    )
    events = events_res.scalars().all()

    if not events:
        return True, None, 0, None

    expected_prev = GENESIS_HASH
    for ev in events:
        if ev.prev_hash != expected_prev:
            return False, ev.hash, len(events), ev.id

        recalculated = compute_event_hash(
            prev_hash=ev.prev_hash,
            investigation_id=ev.investigation_id,
            actor_id=ev.actor_id,
            event_type=ev.type,
            payload_json=ev.payload_json,
        )
        if ev.hash != recalculated:
            return False, ev.hash, len(events), ev.id

        expected_prev = ev.hash

    return True, events[-1].hash, len(events), None
