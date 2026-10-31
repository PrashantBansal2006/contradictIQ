import re
import difflib
from dataclasses import dataclass, field

@dataclass(frozen=True)
class Metric:
    """Metric metadata registry per architecture §9."""
    canonical: str
    additive: bool = True  # Flow metrics are additive across quarters; stock metrics are not
    synonyms: tuple[str, ...] = ()
    derivable_from: tuple[str, ...] | None = None

METRICS: dict[str, Metric] = {
    "revenue": Metric(
        canonical="revenue",
        additive=True,
        synonyms=(
            "net sales",
            "turnover",
            "total income from operations",
            "revenue from operations",
            "sales",
            "revenue",
        ),
    ),
    "cogs": Metric(
        canonical="cogs",
        additive=True,
        synonyms=(
            "cost of goods sold",
            "cost of materials consumed",
            "cost of sales",
        ),
    ),
    "gross_profit": Metric(
        canonical="gross_profit",
        additive=True,
        derivable_from=("revenue", "cogs"),
        synonyms=("gross profit",),
    ),
    "operating_expenses": Metric(
        canonical="operating_expenses",
        additive=True,
        synonyms=(
            "opex",
            "operating costs",
            "total operating expenses",
        ),
    ),
    "operating_income": Metric(
        canonical="operating_income",
        additive=True,
        synonyms=(
            "ebit",
            "operating profit",
            "operating income",
        ),
    ),
    "ebitda": Metric(
        canonical="ebitda",
        additive=True,
        synonyms=("ebitda",),
    ),
    "net_income": Metric(
        canonical="net_income",
        additive=True,
        synonyms=(
            "profit after tax",
            "pat",
            "net profit",
            "net income",
            "profit for the period",
            "profit for the year",
        ),
    ),
    "total_expenses": Metric(
        canonical="total_expenses",
        additive=True,
        synonyms=("total expenses",),
    ),
}

# Ambiguous bare labels per architecture §9 that must return unmapped (None)
AMBIGUOUS_LABELS: set[str] = {
    "income",
    "profit",
    "expenses",
    "revenue",
    "cost",
    "operations",
}

def _clean_label(label: str) -> str:
    """Normalizes label text by lowercasing and collapsing whitespace/punctuation."""
    s = label.lower().strip()
    s = re.sub(r"[^\w\s]", " ", s)
    return " ".join(s.split())

def match_metric(label: str, threshold: float = 0.90) -> str | None:
    """
    Matches raw table or text labels to canonical metric names.
    Follows: Ambiguous check -> Exact match -> Synonym match -> Fuzzy match (>=0.90).
    Returns canonical metric key or None (unmapped).
    """
    cleaned = _clean_label(label)
    if not cleaned:
        return None

    # Ambiguous label check per spec
    if cleaned in AMBIGUOUS_LABELS:
        return None

    # 1. Exact canonical match
    if cleaned in METRICS:
        return cleaned

    # 2. Exact synonym match
    for canonical, metric in METRICS.items():
        if cleaned in metric.synonyms or cleaned == canonical:
            return canonical

    # 3. Token-set fuzzy match (>= threshold)
    best_match: str | None = None
    best_score: float = 0.0

    for canonical, metric in METRICS.items():
        for syn in metric.synonyms:
            ratio = difflib.SequenceMatcher(None, cleaned, syn).ratio()
            if ratio >= threshold and ratio > best_score:
                best_score = ratio
                best_match = canonical

    return best_match
