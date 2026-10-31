"""
metrics.py — Metric registry, synonyms, fuzzy matching, and additivity properties.

Pure Python, deterministic, no I/O.
Per architecture §9.
"""
import re
import difflib
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Metric:
    """Metric metadata registry per architecture §9."""
    canonical: str = ""
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
            "total revenue",
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
            "cogs",
        ),
    ),
    "gross_profit": Metric(
        canonical="gross_profit",
        additive=True,
        derivable_from=("revenue", "cogs"),
        synonyms=("gross profit", "gross income"),
    ),
    "operating_expenses": Metric(
        canonical="operating_expenses",
        additive=True,
        synonyms=(
            "opex",
            "operating costs",
            "total operating expenses",
            "operating expenses",
        ),
    ),
    "operating_income": Metric(
        canonical="operating_income",
        additive=True,
        derivable_from=("revenue", "operating_expenses"),
        synonyms=(
            "ebit",
            "operating profit",
            "operating income",
            "operating earnings",
        ),
    ),
    "ebitda": Metric(
        canonical="ebitda",
        additive=True,
        synonyms=("ebitda", "operating profit before depreciation"),
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
            "net earnings",
        ),
    ),
    "total_expenses": Metric(
        canonical="total_expenses",
        additive=True,
        synonyms=("total expenses", "expenses"),
    ),
    # Stock metrics (non-additive across time per architecture §8.2)
    "total_debt": Metric(
        canonical="total_debt",
        additive=False,
        synonyms=("total debt", "debt", "borrowings", "total borrowings"),
    ),
    "total_assets": Metric(
        canonical="total_assets",
        additive=False,
        synonyms=("total assets", "assets"),
    ),
    "cash": Metric(
        canonical="cash",
        additive=False,
        synonyms=("cash", "cash and cash equivalents"),
    ),
}

# Ambiguous bare labels per architecture §9 that must return unmapped (None)
AMBIGUOUS_LABELS: set[str] = {
    "income",
    "profit",
    "expenses",
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
        cleaned_syns = [_clean_label(syn) for syn in metric.synonyms]
        if cleaned in cleaned_syns or cleaned == canonical:
            return canonical

    # 3. Token-set fuzzy match (>= threshold)
    best_match: str | None = None
    best_score: float = 0.0

    for canonical, metric in METRICS.items():
        for syn in metric.synonyms:
            ratio = difflib.SequenceMatcher(None, cleaned, _clean_label(syn)).ratio()
            if ratio >= threshold and ratio > best_score:
                best_score = ratio
                best_match = canonical

    return best_match


canonicalize_metric = match_metric


def is_additive(metric_name: str) -> bool:
    """Check if metric can be summed across quarters into an annual total."""
    canonical = match_metric(metric_name) or metric_name
    metric_obj = METRICS.get(canonical)
    if metric_obj is not None:
        return metric_obj.additive
    return False
