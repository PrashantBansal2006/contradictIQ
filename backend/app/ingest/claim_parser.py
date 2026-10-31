"""
claim_parser.py — Rule-based text-to-claim parsing.

Per architecture §4 and tasks.md §2.6.
Provides high-level extraction of claims from unstructured text.
"""
from typing import Optional

from app.ingest.fact_extractor import extract_narrative_regex_claims
from app.schemas.claim import ClaimVersionBase


def parse_claims_from_text(
    text: str,
    page: int = 1,
    entity: Optional[str] = None,
    source_doc_id: Optional[str] = None,
) -> list[ClaimVersionBase]:
    """
    Parses candidate financial claims from narrative text using verified regex patterns.
    """
    return extract_narrative_regex_claims(
        text=text,
        page=page,
        entity=entity,
        source_doc_id=source_doc_id,
    )
