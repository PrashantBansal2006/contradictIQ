import re
from dataclasses import dataclass
from decimal import Decimal

# Scale multipliers per architecture §8.1
SCALE_FACTORS: dict[str, Decimal] = {
    "unit": Decimal("1"),
    "k": Decimal("1000"),
    "thousand": Decimal("1000"),
    "thousands": Decimal("1000"),
    "lakh": Decimal("100000"),
    "lakhs": Decimal("100000"),
    "lac": Decimal("100000"),
    "lacs": Decimal("100000"),
    "m": Decimal("1000000"),
    "mn": Decimal("1000000"),
    "million": Decimal("1000000"),
    "millions": Decimal("1000000"),
    "cr": Decimal("10000000"),
    "crore": Decimal("10000000"),
    "crores": Decimal("10000000"),
    "b": Decimal("1000000000"),
    "bn": Decimal("1000000000"),
    "billion": Decimal("1000000000"),
    "billions": Decimal("1000000000"),
}

SCALE_CANONICAL: dict[str, str] = {
    "unit": "unit",
    "k": "thousand",
    "thousand": "thousand",
    "thousands": "thousand",
    "lakh": "lakh",
    "lakhs": "lakh",
    "lac": "lakh",
    "lacs": "lakh",
    "m": "million",
    "mn": "million",
    "million": "million",
    "millions": "million",
    "cr": "crore",
    "crore": "crore",
    "crores": "crore",
    "b": "billion",
    "bn": "billion",
    "billion": "billion",
    "billions": "billion",
}

# Currency symbols & tokens -> ISO codes
CURRENCY_MAP: dict[str, str] = {
    "₹": "INR",
    "rs.": "INR",
    "rs": "INR",
    "inr": "INR",
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
    """Normalized numeric value with currency, scale, and stated precision."""
    raw: str
    value: Decimal         # Normalized value in base units
    raw_number: Decimal    # Stated number before scaling
    unit: str              # "currency", "percent", or "number"
    scale: str             # Canonical scale ("unit", "thousand", "crore", etc.)
    currency: str | None   # ISO code ("INR", "USD", etc.) or None
    precision: int         # Decimal places in the stated number
    is_negative: bool

def parse_value(
    text: str,
    default_currency: str | None = None,
    default_scale: str | None = None
) -> ParsedValue:
    """
    Parses money and percent strings (e.g. '₹340 cr', '$4.2B', '(1,234)', '12.5%').
    Converts amounts to base units as Decimal while preserving stated precision.
    """
    s = text.strip()
    is_neg = False

    # Check for negative in parentheses: '(1,234)'
    if s.startswith("(") and s.endswith(")"):
        is_neg = True
        s = s[1:-1].strip()
    elif s.startswith("-") or s.startswith("\u2212"):
        is_neg = True
        s = s[1:].strip()

    unit = "number"
    currency = default_currency
    scale = default_scale or "unit"

    # Detect percent
    if "%" in s or re.search(r"\b(percent|percentage)\b", s, re.IGNORECASE):
        unit = "percent"
        s = re.sub(r"%|\b(percent|percentage)\b", "", s, flags=re.IGNORECASE).strip()

    # Detect currency symbols / ISO codes
    for token, iso in CURRENCY_MAP.items():
        pattern = re.escape(token) if not token.isalnum() else r"\b" + re.escape(token) + r"\b"
        if re.search(pattern, s, re.IGNORECASE):
            currency = iso
            if unit != "percent":
                unit = "currency"
            s = re.sub(pattern, "", s, flags=re.IGNORECASE).strip()
            break

    # Detect scale (word or suffix like 'cr', 'bn', 'k', 'B')
    scale_match = re.search(
        r"(?i)\b(crores?|cr|billions?|bn|millions?|mn|lakhs?|lacs?|thousands?|k)\b|([kmb])(?!\w)",
        s
    )
    if scale_match:
        tok = (scale_match.group(1) or scale_match.group(2)).lower()
        scale = SCALE_CANONICAL.get(tok, scale)
        s = s[:scale_match.start()] + s[scale_match.end():]

    # Extract digits with optional decimal point and commas
    num_match = re.search(r"[-+]?\d[\d,]*(?:\.\d+)?", s)
    if not num_match:
        raise ValueError(f"Could not parse numeric value from: '{text}'")

    num_str = num_match.group(0).replace(",", "")
    raw_num = Decimal(num_str)
    precision = len(num_str.split(".")[1]) if "." in num_str else 0

    factor = SCALE_FACTORS.get(scale, Decimal("1"))
    multiplier = Decimal("-1") if is_neg else Decimal("1")
    normalized_value = raw_num * factor * multiplier

    return ParsedValue(
        raw=text,
        value=normalized_value,
        raw_number=raw_num,
        unit=unit,
        scale=scale,
        currency=currency,
        precision=precision,
        is_negative=is_neg
    )
