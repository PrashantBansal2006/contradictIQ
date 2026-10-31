"""
units.py — Normalization of money, scales, currency, and percentages.

Pure Python, deterministic, no I/O.
Per architecture §8.1.
"""
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import re

SCALE = {
    "unit": Decimal("1"),
    "thousand": Decimal("1000"),
    "k": Decimal("1000"),
    "lakh": Decimal("100000"),
    "million": Decimal("1000000"),
    "mn": Decimal("1000000"),
    "m": Decimal("1000000"),
    "crore": Decimal("10000000"),
    "cr": Decimal("10000000"),
    "billion": Decimal("1000000000"),
    "bn": Decimal("1000000000"),
    "b": Decimal("1000000000"),
}

CURRENCY_MAP = {
    "₹": "INR",
    "inr": "INR",
    "rs": "INR",
    "rs.": "INR",
    "$": "USD",
    "usd": "USD",
    "€": "EUR",
    "eur": "EUR",
    "£": "GBP",
    "gbp": "GBP",
    "¥": "JPY",
    "jpy": "JPY",
}


@dataclass(frozen=True)
class ParsedValue:
    raw_text: str
    value: Decimal  # Normalized to base units
    stated_value: Decimal  # Stated number before scale multiplier
    scale: Decimal
    currency: str | None
    unit: str  # "currency", "percent", "count", "ratio"
    precision: int  # Stated decimal places


def count_decimals(num_str: str) -> int:
    """Return count of decimal places in a numeric string."""
    cleaned = num_str.strip().replace(",", "")
    if "." in cleaned:
        return len(cleaned.split(".")[1])
    return 0


def parse_money_or_percent(text: str) -> ParsedValue:
    """
    Parse money, percentage, or plain numeric string.
    Handles:
      - ₹3,400 cr -> 34,000,000,000 INR
      - $4.2B -> 4,200,000,000 USD
      - (1,234) -> -1234
      - 12.5% -> 12.5 percent
    """
    cleaned = text.strip()
    is_negative = False

    # Check parentheses for negative numbers like (1,234)
    if cleaned.startswith("(") and cleaned.endswith(")"):
        is_negative = True
        cleaned = cleaned[1:-1].strip()
    elif cleaned.startswith("-"):
        is_negative = True
        cleaned = cleaned[1:].strip()

    # Detect percentage
    is_percent = "%" in cleaned
    if is_percent:
        cleaned = cleaned.replace("%", "").strip()
        num_match = re.search(r"[\d,]+(?:\.\d+)?", cleaned)
        if not num_match:
            raise ValueError(f"Could not parse numeric percentage from: {text}")
        num_str = num_match.group(0)
        precision = count_decimals(num_str)
        val = Decimal(num_str.replace(",", ""))
        if is_negative:
            val = -val
        return ParsedValue(
            raw_text=text,
            value=val,
            stated_value=val,
            scale=Decimal("1"),
            currency=None,
            unit="percent",
            precision=precision,
        )

    # Detect currency
    currency = None
    for sym, iso in CURRENCY_MAP.items():
        if sym in cleaned.lower():
            currency = iso
            # Remove currency symbol case-insensitively
            pattern = re.compile(re.escape(sym), re.IGNORECASE)
            cleaned = pattern.sub("", cleaned).strip()
            break

    # Detect scale
    scale = Decimal("1")
    lower_cleaned = cleaned.lower()
    for scale_key, scale_val in sorted(SCALE.items(), key=lambda x: -len(x[0])):
        pattern = rf"\b{re.escape(scale_key)}\b"
        if re.search(pattern, lower_cleaned):
            scale = scale_val
            cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE).strip()
            break

    # Extract numeric part
    num_match = re.search(r"[\d,]+(?:\.\d+)?", cleaned)
    if not num_match:
        raise ValueError(f"Could not parse numeric value from: {text}")

    num_str = num_match.group(0)
    precision = count_decimals(num_str)
    stated_val = Decimal(num_str.replace(",", ""))
    if is_negative:
        stated_val = -stated_val

    base_val = stated_val * scale
    unit = "currency" if currency else "count"

    return ParsedValue(
        raw_text=text,
        value=base_val,
        stated_value=stated_val,
        scale=scale,
        currency=currency,
        unit=unit,
        precision=precision,
    )
