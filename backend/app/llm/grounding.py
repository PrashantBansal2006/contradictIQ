import re
import difflib
from dataclasses import dataclass
from typing import Any
from backend.app.core.metrics import match_metric

@dataclass(frozen=True)
class GroundingResult:
    """Outcome of the grounding gate check per architecture §7.3."""
    is_grounded: bool
    rejection_reason: str | None = None
    canonical_metric: str | None = None
    char_span: tuple[int, int] | None = None
    bbox: list[float] | None = None
    claim: dict[str, Any] | None = None

def _normalize_ws(text: str) -> str:
    """Collapses consecutive whitespace and trims."""
    return " ".join(text.split())

def validate_claim_grounding(
    claim: dict[str, Any],
    page_text: str,
    word_boxes: list[dict[str, Any]] | None = None,
    fuzzy_threshold: float = 0.92
) -> GroundingResult:
    """
    Hard gate validating AI-extracted claims:
    1. Quote verbatim existence in page text (exact or fuzzy >= 0.92).
    2. Number verification (asserts claim value appears in the quote).
    3. Metric validation against the registry.
    4. Computes char span & bounding box if word_boxes are provided.
    """
    quote = (claim.get("quote") or "").strip()
    if not quote:
        return GroundingResult(
            is_grounded=False,
            rejection_reason="UNGROUNDED_EXTRACTION: Empty quote provided."
        )

    norm_quote = _normalize_ws(quote)
    norm_page = _normalize_ws(page_text)

    # Gate 1: Quote existence in page text
    char_span: tuple[int, int] | None = None
    exact_idx = page_text.find(quote)
    if exact_idx != -1:
        char_span = (exact_idx, exact_idx + len(quote))
    else:
        # Check normalized exact match
        norm_idx = norm_page.find(norm_quote)
        if norm_idx != -1:
            char_span = (norm_idx, norm_idx + len(norm_quote))
        else:
            # Fuzzy check via sequence matching
            matcher = difflib.SequenceMatcher(None, norm_page, norm_quote)
            match = matcher.find_longest_match(0, len(norm_page), 0, len(norm_quote))
            similarity = match.size / max(len(norm_quote), 1)
            if similarity < fuzzy_threshold:
                return GroundingResult(
                    is_grounded=False,
                    rejection_reason=f"UNGROUNDED_EXTRACTION: Quote '{quote}' not found in page text (similarity {similarity:.2f} < {fuzzy_threshold})."
                )
            char_span = (match.a, match.a + match.size)

    # Gate 2: Number checker (every number in claim must appear in quote)
    claim_val = claim.get("value")
    if claim_val is not None:
        quote_numbers = re.findall(r"[-+]?\d[\d,]*(?:\.\d+)?", quote)
        cleaned_numbers = [n.replace(",", "") for n in quote_numbers]
        
        # Check if float or int representation is in the quote numbers
        val_str = str(claim_val)
        val_float = float(claim_val)
        number_found = any(
            (val_str == n or val_float == float(n) or f"{val_float:.1f}" == n or f"{val_float:.2f}" == n)
            for n in cleaned_numbers
            if n.replace(".", "", 1).replace("-", "", 1).isdigit()
        )
        if not number_found:
            return GroundingResult(
                is_grounded=False,
                rejection_reason=f"UNGROUNDED_EXTRACTION: Claim value '{claim_val}' does not appear in quote '{quote}'."
            )

    # Gate 3: Metric must exist in registry
    raw_metric = claim.get("metric", "")
    canonical = match_metric(raw_metric)
    if not canonical:
        return GroundingResult(
            is_grounded=False,
            rejection_reason=f"UNGROUNDED_EXTRACTION: Metric '{raw_metric}' is unmapped in canonical registry."
        )

    # Gate 4: Compute bounding box from word_boxes if available
    bbox: list[float] | None = None
    if word_boxes and char_span:
        c_start, c_end = char_span
        matched_boxes = [
            wb["bbox"] for wb in word_boxes
            if wb.get("char_start", 0) >= c_start and wb.get("char_end", 0) <= c_end and "bbox" in wb
        ]
        if matched_boxes:
            bbox = [
                min(b[0] for b in matched_boxes),
                min(b[1] for b in matched_boxes),
                max(b[2] for b in matched_boxes),
                max(b[3] for b in matched_boxes),
            ]

    # Grounded successfully
    grounded_claim = dict(claim)
    grounded_claim["metric"] = canonical
    grounded_claim["grounded"] = True
    grounded_claim["char_span"] = char_span
    grounded_claim["bbox"] = bbox
    grounded_claim["state"] = "needs_confirmation"

    return GroundingResult(
        is_grounded=True,
        canonical_metric=canonical,
        char_span=char_span,
        bbox=bbox,
        claim=grounded_claim
    )
