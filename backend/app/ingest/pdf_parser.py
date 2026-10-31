"""
pdf_parser.py — PDF parsing and table extraction using pdfplumber and PyMuPDF.

Per architecture §6.1 and tasks.md §2.3, §2.4.
Extracts pages, text with bounding boxes, detects scanned PDFs,
and extracts P&L-like financial tables with headers and periods.
"""
from dataclasses import dataclass, field
from typing import Any, Optional
import re
from pathlib import Path

import pdfplumber
import pymupdf  # PyMuPDF

from app.core.periods import parse_period
from app.schemas.common import Period as PeriodSchema


class PDFParsingError(Exception):
    """Base error for PDF parsing."""
    code: str = "PDF_PARSE_ERROR"


class ScannedPDFError(PDFParsingError):
    """Raised when PDF contains essentially no text (scanned document)."""
    code: str = "SCANNED_PDF_UNSUPPORTED"


class EncryptedPDFError(PDFParsingError):
    """Raised when PDF is password-protected or encrypted."""
    code: str = "PDF_ENCRYPTED"


@dataclass
class WordBox:
    text: str
    x0: float
    y0: float
    x1: float
    y1: float
    char_start: int
    char_end: int


@dataclass
class PageExtract:
    page_no: int
    text: str
    words: list[WordBox] = field(default_factory=list)
    char_count: int = 0


@dataclass
class TableExtract:
    page_no: int
    bbox: list[float]  # [x0, top, x1, bottom]
    headers: list[str]
    rows: list[list[str]]
    period_columns: dict[int, PeriodSchema] = field(default_factory=dict)
    caption: str = ""
    scale: str = "unit"
    currency: Optional[str] = None
    confidence: float = 0.8
    is_financial: bool = False


# Scale detection patterns from captions e.g. "(₹ in Crores)", "(in millions)"
SCALE_PATTERNS = [
    (re.compile(r"(?i)\b(crores?|cr)\b"), "crore"),
    (re.compile(r"(?i)\b(lakhs?|lacs?)\b"), "lakh"),
    (re.compile(r"(?i)\b(millions?|mn)\b"), "million"),
    (re.compile(r"(?i)\b(billions?|bn)\b"), "billion"),
    (re.compile(r"(?i)\b(thousands?|k)\b"), "thousand"),
]

CURRENCY_PATTERNS = [
    (re.compile(r"(?i)(₹|rs\.?|inr)"), "INR"),
    (re.compile(r"(?i)(\$|usd)"), "USD"),
    (re.compile(r"(?i)(€|eur)"), "EUR"),
    (re.compile(r"(?i)(£|gbp)"), "GBP"),
]


def detect_scale_and_currency(text: str) -> tuple[str, Optional[str]]:
    """
    Detect scale and currency hints in a caption or header string.
    e.g. "(₹ in Crores)" -> ("crore", "INR")
    """
    detected_scale = "unit"
    detected_currency = None

    for pat, scale_val in SCALE_PATTERNS:
        if pat.search(text):
            detected_scale = scale_val
            break

    for pat, curr_val in CURRENCY_PATTERNS:
        if pat.search(text):
            detected_currency = curr_val
            break

    return detected_scale, detected_currency


def is_numeric_cell(cell: Any) -> bool:
    """Check if a cell text looks like a financial number."""
    if cell is None:
        return False
    s = str(cell).strip()
    if not s or s in ("-", "--", "—", "N/A", "nil", "None"):
        return False
    # Remove commas, currency symbols, parens, %
    cleaned = re.sub(r"[₹\$,\(\)\s%€£]", "", s)
    try:
        float(cleaned)
        return True
    except ValueError:
        return False


def extract_pages_with_pymupdf(pdf_path: str | Path, min_total_text: int = 50) -> list[PageExtract]:
    """
    Extracts text and word bounding boxes per page using PyMuPDF.
    Raises ScannedPDFError if the PDF has virtually no extractable text.
    Raises EncryptedPDFError if the PDF is password-protected.
    """
    doc = pymupdf.open(str(pdf_path))
    if doc.is_encrypted:
        doc.close()
        raise EncryptedPDFError("The PDF document is encrypted or password-protected.")

    pages: list[PageExtract] = []
    total_text_len = 0

    for idx, page in enumerate(doc):
        page_no = idx + 1
        page_text = page.get_text()
        total_text_len += len(page_text.strip())

        words_data = page.get_text("words")  # [x0, y0, x1, y1, word, block_no, line_no, word_no]
        words: list[WordBox] = []

        char_cursor = 0
        for w in words_data:
            w_text = w[4]
            # locate in page text
            found_idx = page_text.find(w_text, char_cursor)
            if found_idx != -1:
                char_start = found_idx
                char_end = found_idx + len(w_text)
                char_cursor = char_end
            else:
                char_start = char_cursor
                char_end = char_cursor + len(w_text)

            words.append(
                WordBox(
                    text=w_text,
                    x0=float(w[0]),
                    y0=float(w[1]),
                    x1=float(w[2]),
                    y1=float(w[3]),
                    char_start=char_start,
                    char_end=char_end,
                )
            )

        pages.append(
            PageExtract(
                page_no=page_no,
                text=page_text,
                words=words,
                char_count=len(page_text),
            )
        )

    doc.close()

    if total_text_len < min_total_text and len(pages) > 0:
        raise ScannedPDFError(
            f"PDF has only {total_text_len} characters of text. Scanned or image-only PDFs are unsupported.",
        )

    return pages


def extract_tables_from_pdf(pdf_path: str | Path, default_fy_end_month: int = 3) -> list[TableExtract]:
    """
    Extracts financial / P&L tables from PDF using pdfplumber per architecture §6.1 and task 2.4.
    Identifies tables with >= 2 numeric columns, header cells -> periods, scale/currency detection.
    """
    tables: list[TableExtract] = []

    with pdfplumber.open(str(pdf_path)) as pdf:
        for page_idx, page in enumerate(pdf.pages):
            page_no = page_idx + 1

            # Extract raw text around page to detect global scale/currency hints
            page_text = page.extract_text() or ""
            page_scale, page_currency = detect_scale_and_currency(page_text)

            found_tables = page.find_tables()
            for t in found_tables:
                raw_data = t.extract()
                if not raw_data or len(raw_data) < 2:
                    continue

                bbox = [float(b) for b in t.bbox]

                # Clean cells
                cleaned_rows: list[list[str]] = []
                for row in raw_data:
                    cleaned_rows.append([str(c).strip() if c is not None else "" for c in row])

                headers = cleaned_rows[0]
                data_rows = cleaned_rows[1:]

                # Count numeric columns
                col_count = len(headers)
                numeric_col_count = 0
                for col_idx in range(col_count):
                    num_numeric = sum(
                        1 for r in data_rows if col_idx < len(r) and is_numeric_cell(r[col_idx])
                    )
                    if len(data_rows) > 0 and (num_numeric / len(data_rows)) >= 0.4:
                        numeric_col_count += 1

                # Task 2.4 requirement: Detect P&L-like tables (>= 2 numeric columns)
                is_financial = numeric_col_count >= 2

                # Parse periods in header row
                period_cols: dict[int, PeriodSchema] = {}
                for col_idx, h_text in enumerate(headers):
                    try:
                        p_core = parse_period(h_text, default_fy_end_month=default_fy_end_month)
                        period_cols[col_idx] = PeriodSchema(
                            kind=p_core.kind,
                            fy=p_core.fy,
                            idx=p_core.idx,
                            fy_end_month=p_core.fy_end_month,
                        )
                    except Exception:
                        pass

                # Check table caption / top header text for scale hints
                header_str = " ".join(headers)
                tbl_scale, tbl_currency = detect_scale_and_currency(header_str)
                final_scale = tbl_scale if tbl_scale != "unit" else page_scale
                final_currency = tbl_currency or page_currency

                # Compute extraction confidence score
                # Higher when financial table, periods recognized, and high numeric density
                conf = 0.5
                if is_financial:
                    conf += 0.2
                if period_cols:
                    conf += 0.2
                if final_scale != "unit":
                    conf += 0.05
                if final_currency:
                    conf += 0.05
                conf = min(conf, 0.95)

                tables.append(
                    TableExtract(
                        page_no=page_no,
                        bbox=bbox,
                        headers=headers,
                        rows=data_rows,
                        period_columns=period_cols,
                        caption=header_str,
                        scale=final_scale,
                        currency=final_currency,
                        confidence=conf,
                        is_financial=is_financial,
                    )
                )

    return tables
