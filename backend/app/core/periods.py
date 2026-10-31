import re
from dataclasses import dataclass
from typing import Literal

MONTHS: dict[str, int] = {
    "jan": 1, "january": 1,
    "feb": 2, "february": 2,
    "mar": 3, "march": 3,
    "apr": 4, "april": 4,
    "may": 5,
    "jun": 6, "june": 6,
    "jul": 7, "july": 7,
    "aug": 8, "august": 8,
    "sep": 9, "september": 9,
    "oct": 10, "october": 10,
    "nov": 11, "november": 11,
    "dec": 12, "december": 12,
}

@dataclass(frozen=True)
class Period:
    """Fiscal or calendar reporting period per architecture §8.2."""
    kind: Literal["Q", "H", "9M", "FY", "TTM"]
    fy: int
    idx: int | None = None
    fy_end_month: int = 3  # India default Mar; configurable per investigation

    @property
    def key(self) -> str:
        """Returns standard period key (e.g. 'FY2025', 'FY2025-Q3')."""
        if self.kind == "FY":
            return f"FY{self.fy}"
        if self.kind in ("Q", "H"):
            return f"FY{self.fy}-{self.kind}{self.idx}"
        return f"FY{self.fy}-{self.kind}"

def _normalize_year(year_str: str) -> int:
    y = int(year_str)
    if y < 100:
        return 2000 + y
    return y

def parse_period(text: str, default_fy_end_month: int = 3) -> Period:
    """
    Parses period strings such as 'Q3 FY25', 'FY2025', 'H1 FY25',
    'year ended 31 March 2025', 'Jul–Sep 2024'.
    """
    s = text.strip()

    # 1. 'Q3 FY25' or 'Q3 FY2025' or 'Q3'
    m_q = re.search(r"(?i)\bQ([1-4])\s*(?:(?:of\s+)?FY\s*(\d{2,4}))?\b", s)
    if m_q and m_q.group(2):
        return Period(
            kind="Q",
            fy=_normalize_year(m_q.group(2)),
            idx=int(m_q.group(1)),
            fy_end_month=default_fy_end_month
        )

    # 2. 'H1 FY25' or 'H2 FY2024'
    m_h = re.search(r"(?i)\bH([1-2])\s*(?:(?:of\s+)?FY\s*(\d{2,4}))?\b", s)
    if m_h and m_h.group(2):
        return Period(
            kind="H",
            fy=_normalize_year(m_h.group(2)),
            idx=int(m_h.group(1)),
            fy_end_month=default_fy_end_month
        )

    # 3. '9M FY25' or '9M FY2025'
    m_9m = re.search(r"(?i)\b9M\s*(?:(?:of\s+)?FY\s*(\d{2,4}))?\b", s)
    if m_9m and m_9m.group(1):
        return Period(
            kind="9M",
            fy=_normalize_year(m_9m.group(1)),
            idx=None,
            fy_end_month=default_fy_end_month
        )

    # 4. 'year ended 31 March 2025' or 'year ended 31 December 2024'
    m_ye = re.search(r"(?i)(?:financial\s+)?year\s+ended\s+(?:\d{1,2}\s+)?([a-z]+)\s+(\d{4})", s)
    if m_ye:
        month_name = m_ye.group(1).lower()
        end_month = MONTHS.get(month_name, default_fy_end_month)
        fy = int(m_ye.group(2))
        return Period(kind="FY", fy=fy, idx=None, fy_end_month=end_month)

    # 5. 'nine months ended 31 December 2024'
    m_9me = re.search(r"(?i)nine\s+months\s+ended\s+(?:\d{1,2}\s+)?([a-z]+)\s+(\d{4})", s)
    if m_9me:
        month_name = m_9me.group(1).lower()
        end_month = MONTHS.get(month_name, default_fy_end_month)
        end_year = int(m_9me.group(2))
        fy = end_year if end_month <= default_fy_end_month else end_year + 1
        return Period(kind="9M", fy=fy, idx=None, fy_end_month=default_fy_end_month)

    # 6. 'Jul–Sep 2024' or 'Jul-Sep 2024' or 'July - September 2024'
    m_range = re.search(r"(?i)([a-z]+)\s*[\-–—]\s*([a-z]+)\s+(\d{4})", s)
    if m_range:
        start_m = MONTHS.get(m_range.group(1).lower())
        end_m = MONTHS.get(m_range.group(2).lower())
        end_year = int(m_range.group(3))
        if start_m and end_m:
            # Calculate quarter index based on fy_end_month
            q_idx = ((end_m - (default_fy_end_month % 12) - 1) % 12) // 3 + 1
            fy = end_year if end_m <= default_fy_end_month else end_year + 1
            return Period(kind="Q", fy=fy, idx=q_idx, fy_end_month=default_fy_end_month)

    # 7. Plain 'FY25' or 'FY2025'
    m_fy = re.search(r"(?i)\bFY\s*(\d{2,4})\b", s)
    if m_fy:
        return Period(
            kind="FY",
            fy=_normalize_year(m_fy.group(1)),
            idx=None,
            fy_end_month=default_fy_end_month
        )

    raise ValueError(f"Could not parse period from: '{text}'")

def prev_year(p: Period) -> Period:
    """Returns corresponding period in prior fiscal year."""
    return Period(
        kind=p.kind,
        fy=p.fy - 1,
        idx=p.idx,
        fy_end_month=p.fy_end_month
    )

def prev_quarter(p: Period) -> Period:
    """Returns prior sequential quarter."""
    if p.kind != "Q" or p.idx is None:
        raise ValueError(f"Cannot take prev_quarter of non-quarter period: {p}")
    if p.idx > 1:
        return Period(kind="Q", fy=p.fy, idx=p.idx - 1, fy_end_month=p.fy_end_month)
    return Period(kind="Q", fy=p.fy - 1, idx=4, fy_end_month=p.fy_end_month)

def can_derive_fy(quarters: list[Period]) -> bool:
    """True if quarters contain Q1, Q2, Q3, and Q4 for the same FY."""
    if len(quarters) < 4:
        return False
    fy_groups: dict[tuple[int, int], set[int]] = {}
    for q in quarters:
        if q.kind == "Q" and q.idx is not None:
            key = (q.fy, q.fy_end_month)
            fy_groups.setdefault(key, set()).add(q.idx)
    return any(idxs.issuperset({1, 2, 3, 4}) for idxs in fy_groups.values())

def derive_fy(quarters: list[Period]) -> Period:
    """Derives FY Period from 4 quarters."""
    for q in quarters:
        if q.kind == "Q" and q.idx is not None:
            key = (q.fy, q.fy_end_month)
            q_set = {x.idx for x in quarters if x.kind == "Q" and (x.fy, x.fy_end_month) == key}
            if q_set.issuperset({1, 2, 3, 4}):
                return Period(kind="FY", fy=q.fy, idx=None, fy_end_month=q.fy_end_month)
    raise ValueError("Cannot derive FY: Missing quarters.")

def can_derive_h1(quarters: list[Period]) -> bool:
    """True if quarters contain Q1 and Q2 for the same FY."""
    fy_groups: dict[tuple[int, int], set[int]] = {}
    for q in quarters:
        if q.kind == "Q" and q.idx is not None:
            fy_groups.setdefault((q.fy, q.fy_end_month), set()).add(q.idx)
    return any(idxs.issuperset({1, 2}) for idxs in fy_groups.values())

def derive_h1(quarters: list[Period]) -> Period:
    """Derives H1 Period from Q1 and Q2."""
    for q in quarters:
        if q.kind == "Q" and q.idx is not None:
            key = (q.fy, q.fy_end_month)
            q_set = {x.idx for x in quarters if x.kind == "Q" and (x.fy, x.fy_end_month) == key}
            if q_set.issuperset({1, 2}):
                return Period(kind="H", fy=q.fy, idx=1, fy_end_month=q.fy_end_month)
    raise ValueError("Cannot derive H1: Missing Q1 or Q2.")

def can_derive_9m(quarters: list[Period]) -> bool:
    """True if quarters contain Q1, Q2, and Q3 for the same FY."""
    fy_groups: dict[tuple[int, int], set[int]] = {}
    for q in quarters:
        if q.kind == "Q" and q.idx is not None:
            fy_groups.setdefault((q.fy, q.fy_end_month), set()).add(q.idx)
    return any(idxs.issuperset({1, 2, 3}) for idxs in fy_groups.values())

def derive_9m(quarters: list[Period]) -> Period:
    """Derives 9M Period from Q1, Q2, and Q3."""
    for q in quarters:
        if q.kind == "Q" and q.idx is not None:
            key = (q.fy, q.fy_end_month)
            q_set = {x.idx for x in quarters if x.kind == "Q" and (x.fy, x.fy_end_month) == key}
            if q_set.issuperset({1, 2, 3}):
                return Period(kind="9M", fy=q.fy, idx=None, fy_end_month=q.fy_end_month)
    raise ValueError("Cannot derive 9M: Missing Q1, Q2, or Q3.")
