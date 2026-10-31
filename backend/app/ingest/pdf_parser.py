"""
ContradictIQ — PDF Parser and Table Extractor
============================================
Tasks 2.3 & 2.4:
- Task 2.3: PyMuPDF per-page text, words with bboxes, character offsets,
            char-span bounding box lookup, and scanned-PDF detection.
- Task 2.4: Table extraction with pdfplumber, detecting P&L tables (>= 2 numeric columns),
            header cells -> periods, row labels -> canonical metrics, and confidence scoring.

Architecture References:
- architecture.md §6 (Pipeline Steps: Parse PDF, Tables)
- architecture.md §5 (pages, table_extracts, facts data model)
- architecture.md §18 (Error codes: SCANNED_PDF_UNSUPPORTED)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
import io
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Tuple, Union

import pymupdf
import pdfplumber

from app.core.decide import METRIC_REGISTRY, SCALES, Period


class ScannedPDFError(Exception):
    """Raised when a PDF has no extractable text layer (scanned PDF)."""
    def __init__(self, message: str = "Scanned PDF without text layer is unsupported. Please upload text PDF or CSV."):
        super().__init__(message)
        self.code = "SCANNED_PDF_UNSUPPORTED"


@dataclass
class WordBox:
    """Word bounding box with character offsets within the page text."""
    word: str
    x0: float
    y0: float
    x1: float
    y1: float
    char_start: int
    char_end: int
    block_no: int = 0
    line_no: int = 0
    word_no: int = 0

    @property
    def bbox(self) -> Tuple[float, float, float, float]:
        return (self.x0, self.y0, self.x1, self.y1)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "word": self.word,
            "x0": round(self.x0, 2),
            "y0": round(self.y0, 2),
            "x1": round(self.x1, 2),
            "y1": round(self.y1, 2),
            "char_start": self.char_start,
            "char_end": self.char_end,
            "block_no": self.block_no,
            "line_no": self.line_no,
            "word_no": self.word_no,
        }


@dataclass
class PageData:
    """Extracted text, dimensions, and word coordinates for a single PDF page."""
    page_no: int  # 1-indexed
    text: str
    words: List[WordBox] = field(default_factory=list)
    width: float = 0.0
    height: float = 0.0

    def get_bbox_for_char_span(self, char_start: int, char_end: int) -> Optional[Tuple[float, float, float, float]]:
        """
        Lookup bounding box union for a given character span [char_start, char_end).
        Returns (min_x0, min_y0, max_x1, max_y1) in page coordinate space.
        """
        if char_start >= char_end:
            return None

        overlapping = [
            w for w in self.words
            if max(w.char_start, char_start) < min(w.char_end, char_end)
        ]
        if not overlapping:
            # Fallback to nearest word if exact span falls between words
            return None

        min_x0 = min(w.x0 for w in overlapping)
        min_y0 = min(w.y0 for w in overlapping)
        max_x1 = max(w.x1 for w in overlapping)
        max_y1 = max(w.y1 for w in overlapping)
        return (round(min_x0, 2), round(min_y0, 2), round(max_x1, 2), round(max_y1, 2))

    def get_bbox_for_quote(self, quote: str) -> Optional[Tuple[float, float, float, float]]:
        """Find quote substring in page text and compute its bounding box."""
        if not quote or not self.text:
            return None

        idx = self.text.lower().find(quote.lower().strip())
        if idx == -1:
            return None

        return self.get_bbox_for_char_span(idx, idx + len(quote.strip()))


@dataclass
class ParsedPDF:
    """Document-level parse result containing pages and metadata."""
    page_count: int
    pages: List[PageData] = field(default_factory=list)
    is_scanned: bool = False

    def get_page(self, page_no: int) -> Optional[PageData]:
        for p in self.pages:
            if p.page_no == page_no:
                return p
        return None

    def get_bbox_for_char_span(self, page_no: int, char_start: int, char_end: int) -> Optional[Tuple[float, float, float, float]]:
        page = self.get_page(page_no)
        if not page:
            return None
        return page.get_bbox_for_char_span(char_start, char_end)

    def find_quote(self, quote: str) -> Optional[Tuple[int, Tuple[float, float, float, float]]]:
        """Search for a quote across all pages; returns (page_no, bbox)."""
        for page in self.pages:
            bbox = page.get_bbox_for_quote(quote)
            if bbox:
                return (page.page_no, bbox)
        return None


@dataclass
class ExtractedFact:
    """A tabular financial fact with exact locator and confidence."""
    metric: str
    raw_label: str
    value_raw: str
    value_base: str
    unit: str
    scale: str
    currency: str
    period: Dict[str, Any]
    locator: Dict[str, Any]
    confidence: float
    method: str = "table"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric": self.metric,
            "raw_label": self.raw_label,
            "value_raw": self.value_raw,
            "value_base": self.value_base,
            "unit": self.unit,
            "scale": self.scale,
            "currency": self.currency,
            "period": self.period,
            "locator": self.locator,
            "confidence": self.confidence,
            "method": self.method,
        }


@dataclass
class TableExtract:
    """Structured table extracted by pdfplumber with P&L classification and facts."""
    page_no: int
    bbox: Tuple[float, float, float, float]
    headers: List[str]
    rows: List[List[str]]
    confidence: float
    is_pl_table: bool
    scale: str = "unit"
    currency: str = "INR"
    facts: List[ExtractedFact] = field(default_factory=list)


def _open_pymupdf(file_path_or_bytes: Union[str, Path, bytes]) -> pymupdf.Document:
    """Open a PyMuPDF document from file path or bytes."""
    if isinstance(file_path_or_bytes, bytes):
        return pymupdf.open(stream=file_path_or_bytes, filetype="pdf")
    p = Path(file_path_or_bytes)
    return pymupdf.open(str(p))


def _open_pdfplumber(file_path_or_bytes: Union[str, Path, bytes]) -> pdfplumber.PDF:
    """Open a pdfplumber PDF from file path or bytes."""
    if isinstance(file_path_or_bytes, bytes):
        return pdfplumber.open(io.BytesIO(file_path_or_bytes))
    return pdfplumber.open(str(file_path_or_bytes))


def parse_pdf(file_path_or_bytes: Union[str, Path, bytes], detect_scanned: bool = True) -> ParsedPDF:
    """
    Parse PDF into per-page text and word bounding boxes with char offsets.
    Detects scanned PDFs and raises ScannedPDFError.

    Task 2.3 implementation using PyMuPDF.
    """
    doc = _open_pymupdf(file_path_or_bytes)
    pages: List[PageData] = []
    total_text_len = 0

    try:
        for page_idx, page in enumerate(doc):
            page_no = page_idx + 1
            full_text = page.get_text("text") or ""
            total_text_len += len(full_text.strip())

            # Words extraction: (x0, y0, x1, y1, word, block_no, line_no, word_no)
            raw_words = page.get_text("words") or []
            word_boxes: List[WordBox] = []

            # Match words against page text to calculate char_start & char_end
            cursor = 0
            for w in raw_words:
                x0, y0, x1, y1, word_str, block_no, line_no, word_no = w[:8]
                # Find word starting from current cursor
                found_pos = full_text.find(word_str, cursor)
                if found_pos != -1:
                    char_start = found_pos
                    char_end = found_pos + len(word_str)
                    cursor = char_end
                else:
                    # Fallback if text differs slightly
                    char_start = cursor
                    char_end = cursor + len(word_str)

                word_boxes.append(
                    WordBox(
                        word=word_str,
                        x0=float(x0),
                        y0=float(y0),
                        x1=float(x1),
                        y1=float(y1),
                        char_start=char_start,
                        char_end=char_end,
                        block_no=int(block_no),
                        line_no=int(line_no),
                        word_no=int(word_no),
                    )
                )

            rect = page.rect
            pages.append(
                PageData(
                    page_no=page_no,
                    text=full_text,
                    words=word_boxes,
                    width=float(rect.width),
                    height=float(rect.height),
                )
            )

        # Scanned PDF Detection (per architecture §6 / §18: text length ≈ 0)
        is_scanned = (total_text_len == 0) or (len(pages) > 0 and (total_text_len / len(pages)) < 15)
        if detect_scanned and is_scanned and len(pages) > 0:
            raise ScannedPDFError("Scanned PDF without text layer is unsupported (text length ≈ 0).")

        return ParsedPDF(page_count=len(pages), pages=pages, is_scanned=is_scanned)
    finally:
        doc.close()


def _is_numeric_cell(cell: Optional[str]) -> bool:
    """Check if table cell contains numeric financial values."""
    if not cell:
        return False
    cleaned = str(cell).replace(",", "").replace("$", "").replace("₹", "").replace("€", "").replace("%", "").strip()
    if cleaned.startswith("(") and cleaned.endswith(")"):
        cleaned = cleaned[1:-1]
    if not cleaned:
        return False
    try:
        float(cleaned)
        return True
    except ValueError:
        return False


def _parse_cell_number(cell: Optional[str]) -> Optional[Decimal]:
    """Parse numeric cell into Decimal."""
    if not cell:
        return None
    cleaned = str(cell).replace(",", "").replace("$", "").replace("₹", "").replace("€", "").replace("%", "").strip()
    if cleaned.startswith("(") and cleaned.endswith(")"):
        cleaned = "-" + cleaned[1:-1]
    try:
        return Decimal(cleaned)
    except (InvalidOperation, ValueError):
        return None


def _sniff_scale_and_currency(text_context: str) -> Tuple[str, str]:
    """Detect scale and currency hints from captions/headers (e.g. '₹ in crore')."""
    lower = text_context.lower()
    currency = "INR"
    if "$" in text_context or "usd" in lower or "dollar" in lower:
        currency = "USD"
    elif "€" in text_context or "eur" in lower or "euro" in lower:
        currency = "EUR"
    elif "₹" in text_context or "rs" in lower or "inr" in lower or "rupee" in lower:
        currency = "INR"

    scale = "unit"
    if "crore" in lower or " cr" in lower or "/cr" in lower or "in cr" in lower:
        scale = "crore"
    elif "lakh" in lower or "lacs" in lower:
        scale = "lakh"
    elif "billion" in lower or " bn" in lower:
        scale = "billion"
    elif "million" in lower or " mn" in lower:
        scale = "million"
    elif "thousand" in lower or "in '000" in lower:
        scale = "thousand"

    return scale, currency


def _map_header_to_period(header_str: str) -> Optional[Dict[str, Any]]:
    """Convert header text (e.g. 'FY24', 'Q3 FY25', 'Year ended 31 Mar 2025') into Period dict."""
    if not header_str:
        return None

    s = header_str.strip()
    # Try Period.from_any
    p = Period.from_any(s)
    if p:
        return {"kind": p.kind, "fy": p.fy, "idx": p.idx}

    # Regex search for FY24 / FY2024 / Q3 FY25
    m_q = re.search(r"Q([1-4])\s*(?:FY)?(\d{2,4})", s, re.IGNORECASE)
    if m_q:
        q_idx = int(m_q.group(1))
        fy_raw = m_q.group(2)
        fy = int(fy_raw) if len(fy_raw) == 4 else int("20" + fy_raw)
        return {"kind": "Q", "fy": fy, "idx": q_idx}

    m_fy = re.search(r"(?:FY|FY\s*)(\d{2,4})", s, re.IGNORECASE)
    if m_fy:
        fy_raw = m_fy.group(1)
        fy = int(fy_raw) if len(fy_raw) == 4 else int("20" + fy_raw)
        return {"kind": "FY", "fy": fy, "idx": None}

    # 4-digit year e.g. "2024" or "2025"
    m_yr = re.search(r"\b(20\d{2})\b", s)
    if m_yr:
        return {"kind": "FY", "fy": int(m_yr.group(1)), "idx": None}

    return None


def _match_row_to_metric(label: str) -> Optional[str]:
    """Map table row label to canonical metric via registry synonyms."""
    if not label:
        return None
    raw = label.strip().lower()
    # Clean bullet points, numbers, parentheses
    clean = re.sub(r"^[0-9ivx\.\-\)\s]+", "", raw).strip()
    clean = re.sub(r"\(.*?\)", "", clean).strip()

    for canonical, info in METRIC_REGISTRY.items():
        if clean == canonical:
            return canonical
        for syn in info["synonyms"]:
            if syn in clean or clean in syn:
                return canonical
    return None


def extract_tables_from_pdf(file_path_or_bytes: Union[str, Path, bytes]) -> List[TableExtract]:
    """
    Extract tables using pdfplumber, filter for P&L-like tables (>= 2 numeric columns),
    map header cells -> periods, row labels -> metrics, and produce facts with locators.

    Task 2.4 implementation.
    """
    table_extracts: List[TableExtract] = []

    with _open_pdfplumber(file_path_or_bytes) as pdf:
        for page_idx, page in enumerate(pdf.pages):
            page_no = page_idx + 1
            page_text = page.extract_text() or ""
            page_scale, page_currency = _sniff_scale_and_currency(page_text)

            found_tables = page.find_tables()
            if not found_tables:
                continue

            for t_obj in found_tables:
                raw_table = t_obj.extract()
                if not raw_table or len(raw_table) < 2:
                    continue

                headers = [str(c or "").strip() for c in raw_table[0]]
                data_rows = raw_table[1:]

                # Count numeric columns (excluding first label column)
                num_cols = len(headers)
                numeric_col_counts = [0] * num_cols

                for row in data_rows:
                    for c_idx, cell in enumerate(row):
                        if c_idx < num_cols and _is_numeric_cell(cell):
                            numeric_col_counts[c_idx] += 1

                # Check P&L criterion: >= 2 numeric columns (architecture §6)
                numeric_columns = [idx for idx, cnt in enumerate(numeric_col_counts) if cnt >= 1 and idx > 0]
                is_pl_table = len(numeric_columns) >= 2 or (len(headers) >= 3 and sum(cnt >= 1 for cnt in numeric_col_counts[1:]) >= 2)

                # Contextual scale & currency sniffing around table
                t_bbox = t_obj.bbox
                scale, currency = page_scale, page_currency
                header_context = " ".join(headers)
                t_scale, t_curr = _sniff_scale_and_currency(header_context)
                if t_scale != "unit":
                    scale = t_scale
                if t_curr != "INR":
                    currency = t_curr

                # Map column indices to periods
                col_periods: Dict[int, Dict[str, Any]] = {}
                for c_idx in range(1, len(headers)):
                    p_info = _map_header_to_period(headers[c_idx])
                    if p_info:
                        col_periods[c_idx] = p_info

                # Extract facts from matching rows
                facts: List[ExtractedFact] = []
                mapped_metric_rows = 0

                for r_idx, row in enumerate(data_rows):
                    if not row or not row[0]:
                        continue
                    label = str(row[0]).strip()
                    metric = _match_row_to_metric(label)
                    if not metric:
                        continue

                    mapped_metric_rows += 1

                    for c_idx in range(1, min(len(row), len(headers))):
                        val_str = str(row[c_idx] or "").strip()
                        num_val = _parse_cell_number(val_str)
                        if num_val is None:
                            continue

                        period = col_periods.get(c_idx, {"kind": "FY", "fy": 2024})
                        scale_mult = SCALES.get(scale.lower(), Decimal("1"))
                        base_val = num_val * scale_mult

                        # Cell bbox locator if available
                        cell_bbox = list(t_bbox)
                        if hasattr(t_obj, "rows") and r_idx + 1 < len(t_obj.rows):
                            row_obj = t_obj.rows[r_idx + 1]
                            if hasattr(row_obj, "cells") and c_idx < len(row_obj.cells):
                                cell_box = row_obj.cells[c_idx]
                                if cell_box:
                                    cell_bbox = [round(float(v), 2) for v in cell_box]

                        locator = {
                            "page": page_no,
                            "bbox": cell_bbox,
                            "row": r_idx + 1,
                            "col": c_idx,
                            "quote": f"{label}: {val_str}",
                        }

                        facts.append(
                            ExtractedFact(
                                metric=metric,
                                raw_label=label,
                                value_raw=val_str,
                                value_base=str(base_val),
                                unit="currency",
                                scale=scale,
                                currency=currency,
                                period=period,
                                locator=locator,
                                confidence=0.95,
                                method="table",
                            )
                        )

                # Confidence calculation based on mapped rows and numeric presence
                conf = 0.50
                if is_pl_table:
                    conf += 0.20
                if mapped_metric_rows > 0:
                    conf += min(0.25, mapped_metric_rows * 0.08)
                if len(col_periods) >= 2:
                    conf += 0.05
                conf = round(min(1.0, conf), 2)

                table_extracts.append(
                    TableExtract(
                        page_no=page_no,
                        bbox=tuple(round(float(x), 2) for x in t_bbox),
                        headers=headers,
                        rows=[[str(c or "") for c in r] for r in data_rows],
                        confidence=conf,
                        is_pl_table=is_pl_table,
                        scale=scale,
                        currency=currency,
                        facts=facts,
                    )
                )

    return table_extracts


def extract_facts_from_pdf_tables(file_path_or_bytes: Union[str, Path, bytes]) -> List[ExtractedFact]:
    """Convenience function: extracts and returns all facts from PDF tables."""
    tables = extract_tables_from_pdf(file_path_or_bytes)
    all_facts: List[ExtractedFact] = []
    for t in tables:
        all_facts.extend(t.facts)
    return all_facts
