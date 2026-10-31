"""
periods.py — Period representation, parsing, and algebra.

Pure Python, deterministic, no I/O.
Per architecture §8.2.
"""
from dataclasses import dataclass
from typing import Literal
import re


@dataclass(frozen=True)
class Period:
    kind: Literal["Q", "H", "9M", "FY", "TTM"]
    fy: int                # Fiscal year label, e.g. 2025
    idx: int | None = None # Quarter 1-4 or Half 1-2
    fy_end_month: int = 3  # India default Mar (3); 12 for calendar-year

    @property
    def key(self) -> str:
        """Canonical period key for indexing and exact matching."""
        if self.kind == "Q":
            return f"FY{self.fy}Q{self.idx}"
        elif self.kind == "H":
            return f"FY{self.fy}H{self.idx}"
        elif self.kind == "9M":
            return f"FY{self.fy}-9M"
        elif self.kind == "TTM":
            return f"FY{self.fy}-TTM"
        return f"FY{self.fy}"


def prev_year(p: Period) -> Period:
    """Return the equivalent period one fiscal year prior."""
    return Period(
        kind=p.kind,
        fy=p.fy - 1,
        idx=p.idx,
        fy_end_month=p.fy_end_month,
    )


def prev_quarter(p: Period) -> Period:
    """Return the preceding quarter period."""
    if p.kind != "Q" or p.idx is None:
        raise ValueError(f"prev_quarter is only defined for quarterly periods, got {p.kind}")
    if p.idx == 1:
        return Period(kind="Q", fy=p.fy - 1, idx=4, fy_end_month=p.fy_end_month)
    return Period(kind="Q", fy=p.fy, idx=p.idx - 1, fy_end_month=p.fy_end_month)


def parse_period(text: str, fy_end_month: int = 3) -> Period:
    """
    Parse a period string into a Period instance.
    Examples:
      - 'Q3 FY25' or 'Q3 FY2025' -> Period('Q', 2025, 3)
      - 'FY2025' or 'FY25' -> Period('FY', 2025, None)
      - 'H1 FY25' -> Period('H', 2025, 1)
      - '9M FY25' or 'nine months ended ...' -> Period('9M', 2025, None)
      - 'year ended 31 March 2025' -> Period('FY', 2025, None)
      - 'quarter ended 31 December 2024' (with Mar FY) -> Period('Q', 2025, 3)
      - 'Jul–Sep 2024' or 'Jul-Sep 2024' (with Mar FY) -> Period('Q', 2025, 2)
    """
    cleaned = text.strip()

    # Normalize FY years, e.g. FY25 -> FY2025
    def expand_fy(yr_str: str) -> int:
        yr = int(yr_str)
        return 2000 + yr if yr < 100 else yr

    # Pattern: Q[1-4] FY(YYYY|YY)
    m = re.search(r"Q([1-4])\s*(?:FY|Fiscal\s*Year)?\s*['’]?(\d{2,4})", cleaned, re.IGNORECASE)
    if m:
        q_idx = int(m.group(1))
        fy = expand_fy(m.group(2))
        return Period(kind="Q", fy=fy, idx=q_idx, fy_end_month=fy_end_month)

    # Pattern: H[1-2] FY(YYYY|YY)
    m = re.search(r"H([1-2])\s*(?:FY|Fiscal\s*Year)?\s*['’]?(\d{2,4})", cleaned, re.IGNORECASE)
    if m:
        h_idx = int(m.group(1))
        fy = expand_fy(m.group(2))
        return Period(kind="H", fy=fy, idx=h_idx, fy_end_month=fy_end_month)

    # Pattern: 9M FY(YYYY|YY)
    m = re.search(r"(?:9M|nine\s*months?)\s*(?:FY|Fiscal\s*Year)?\s*['’]?(\d{2,4})", cleaned, re.IGNORECASE)
    if m:
        fy = expand_fy(m.group(1))
        return Period(kind="9M", fy=fy, idx=None, fy_end_month=fy_end_month)

    # Pattern: FY(YYYY|YY) or Full Year YYYY
    m = re.search(r"(?:FY|Fiscal\s*Year|Full\s*Year)\s*['’]?(\d{2,4})", cleaned, re.IGNORECASE)
    if m:
        fy = expand_fy(m.group(1))
        return Period(kind="FY", fy=fy, idx=None, fy_end_month=fy_end_month)

    # Pattern: Year ended 31 March 2025
    m = re.search(r"year\s*ended\s*(?:\d{1,2}\s+[A-Za-z]+\s+)?(\d{4})", cleaned, re.IGNORECASE)
    if m:
        fy = int(m.group(1))
        return Period(kind="FY", fy=fy, idx=None, fy_end_month=fy_end_month)

    # Pattern: Quarter ended 31 Dec 2024
    m = re.search(r"quarter\s*ended\s*(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})", cleaned, re.IGNORECASE)
    if m:
        day, month_name, cal_year = int(m.group(1)), m.group(2).lower()[:3], int(m.group(3))
        month_num = {
            "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
            "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
        }.get(month_name, 3)
        # Calculate FY and Quarter relative to fy_end_month
        # For fy_end_month = 3 (Mar): Apr-Jun=Q1(FY+1), Jul-Sep=Q2(FY+1), Oct-Dec=Q3(FY+1), Jan-Mar=Q4(FY)
        if fy_end_month == 3:
            if month_num in (4, 5, 6):
                return Period(kind="Q", fy=cal_year + 1, idx=1, fy_end_month=3)
            elif month_num in (7, 8, 9):
                return Period(kind="Q", fy=cal_year + 1, idx=2, fy_end_month=3)
            elif month_num in (10, 11, 12):
                return Period(kind="Q", fy=cal_year + 1, idx=3, fy_end_month=3)
            else:
                return Period(kind="Q", fy=cal_year, idx=4, fy_end_month=3)
        elif fy_end_month == 12:
            q = (month_num - 1) // 3 + 1
            return Period(kind="Q", fy=cal_year, idx=q, fy_end_month=12)

    # Pattern: Month range like Jul-Sep 2024 or Jul–Sep 2024
    m = re.search(r"(apr|jul|oct|jan)[a-z]*[–\-](jun|sep|dec|mar)[a-z]*\s+(\d{4})", cleaned, re.IGNORECASE)
    if m:
        start_month = m.group(1).lower()
        cal_year = int(m.group(3))
        if fy_end_month == 3:
            q_map = {"apr": 1, "jul": 2, "oct": 3, "jan": 4}
            idx = q_map.get(start_month, 1)
            fy = cal_year if idx == 4 else cal_year + 1
            return Period(kind="Q", fy=fy, idx=idx, fy_end_month=3)

    # Fallback: Plain 4-digit year as FY
    m = re.search(r"\b(20\d{2})\b", cleaned)
    if m:
        return Period(kind="FY", fy=int(m.group(1)), idx=None, fy_end_month=fy_end_month)

    raise ValueError(f"Unrecognized period format: {text}")
