"""
metrics.py — Metric registry, synonyms, and additivity properties.

Pure Python, deterministic, no I/O.
Per architecture §9.
"""
from dataclasses import dataclass, field
import re


@dataclass(frozen=True)
class Metric:
    additive: bool = True
    synonyms: list[str] = field(default_factory=list)
    derivable_from: tuple[str, ...] | None = None


METRICS: dict[str, Metric] = {
    "revenue": Metric(
        additive=True,
        synonyms=[
            "revenue",
            "net sales",
            "turnover",
            "total income from operations",
            "revenue from operations",
            "sales",
            "total revenue",
        ],
    ),
    "cogs": Metric(
        additive=True,
        synonyms=[
            "cogs",
            "cost of goods sold",
            "cost of materials consumed",
            "cost of sales",
        ],
    ),
    "gross_profit": Metric(
        additive=True,
        synonyms=["gross profit", "gross income"],
        derivable_from=("revenue", "cogs"),
    ),
    "operating_expenses": Metric(
        additive=True,
        synonyms=[
            "operating expenses",
            "opex",
            "operating costs",
            "total operating expenses",
        ],
    ),
    "operating_income": Metric(
        additive=True,
        synonyms=["operating income", "ebit", "operating profit", "operating earnings"],
        derivable_from=("revenue", "operating_expenses"),
    ),
    "ebitda": Metric(
        additive=True,
        synonyms=["ebitda", "operating profit before depreciation"],
    ),
    "net_income": Metric(
        additive=True,
        synonyms=[
            "net income",
            "profit after tax",
            "pat",
            "net profit",
            "profit for the period",
            "net earnings",
        ],
    ),
    "total_expenses": Metric(
        additive=True,
        synonyms=["total expenses", "expenses"],
    ),
    # Stock metrics (non-additive across time)
    "total_debt": Metric(
        additive=False,
        synonyms=["total debt", "debt", "borrowings", "total borrowings"],
    ),
    "total_assets": Metric(
        additive=False,
        synonyms=["total assets", "assets"],
    ),
    "cash": Metric(
        additive=False,
        synonyms=["cash", "cash and cash equivalents"],
    ),
}


def normalize_text(text: str) -> str:
    """Normalize text by lowercasing and standardizing spaces/punctuation."""
    lowered = text.lower().strip()
    return re.sub(r"[\s\-_]+", " ", lowered)


def canonicalize_metric(label: str) -> str | None:
    """
    Resolve a raw metric label to its canonical metric name.
    1. Exact canonical name match
    2. Synonym match
    3. Token-set fuzzy match (all tokens of synonym in label or vice versa)
    Ambiguous / unmapped returns None.
    """
    cleaned = normalize_text(label)

    # 1. Direct canonical match
    if cleaned in METRICS:
        return cleaned

    # 2. Exact synonym match
    for canonical_name, metric_obj in METRICS.items():
        for syn in metric_obj.synonyms:
            if cleaned == normalize_text(syn):
                return canonical_name

    # 3. Token-based matching
    cleaned_tokens = set(cleaned.split())
    for canonical_name, metric_obj in METRICS.items():
        for syn in metric_obj.synonyms:
            syn_tokens = set(normalize_text(syn).split())
            if syn_tokens == cleaned_tokens:
                return canonical_name
            # If label contains the complete multi-word synonym (e.g. "our revenue from operations is...")
            if len(syn_tokens) > 1 and syn_tokens.issubset(cleaned_tokens):
                return canonical_name

    # Ambiguous names like "income" without qualifier return None
    return None


def is_additive(metric_name: str) -> bool:
    """Check if metric can be summed across quarters into an annual total."""
    canonical = canonicalize_metric(metric_name) or metric_name
    metric_obj = METRICS.get(canonical)
    if metric_obj is not None:
        return metric_obj.additive
    return False
