"""
Tests for Tasks 2.3 & 2.4: PDF Parser and Table Extractor
=========================================================
- Task 2.3: PyMuPDF per-page text + words with bbox + char offsets; scanned-PDF detection.
- Task 2.4: Table extraction with pdfplumber (>= 2 numeric cols, headers -> periods, row labels -> metrics).
"""

import io
from pathlib import Path
import pytest
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import pymupdf

from app.ingest import (
    parse_pdf,
    extract_tables_from_pdf,
    extract_facts_from_pdf_tables,
    ScannedPDFError,
)


def create_sample_financial_pdf() -> bytes:
    """Create in-memory PDF with narrative text and a P&L financial table."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter, leftMargin=50, rightMargin=50, topMargin=50, bottomMargin=50)
    styles = getSampleStyleSheet()

    story = [
        Paragraph("Acme Financial Services Limited", styles["Heading1"]),
        Paragraph("Annual Report for the year ended 31 March 2024", styles["Normal"]),
        Paragraph("Statement of Standalone Profit and Loss (₹ in crore)", styles["Heading2"]),
        Spacer(1, 10),
    ]

    table_data = [
        ["Particulars", "FY24", "FY23"],
        ["Revenue from operations", "3,400", "2,977"],
        ["Cost of materials consumed", "1,800", "1,550"],
        ["Operating expenses", "1,150", "1,037"],
        ["Operating profit", "450", "390"],
        ["Profit after tax", "350", "280"],
    ]

    t = Table(table_data, colWidths=[240, 90, 90])
    t.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f0f0f0")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
            ]
        )
    )
    story.append(t)
    story.append(Spacer(1, 15))
    story.append(
        Paragraph(
            "Management Note: Revenue grew 14.2% YoY driven by strong operational execution.",
            styles["Normal"],
        )
    )

    doc.build(story)
    return buf.getvalue()


def create_scanned_mock_pdf() -> bytes:
    """Create PDF with blank page (no text layer) to simulate scanned document."""
    doc = pymupdf.open()
    doc.new_page(width=595, height=842)  # blank page without text
    buf = doc.tobytes()
    doc.close()
    return buf


def create_non_pl_pdf() -> bytes:
    """Create PDF with non-financial directory table (single text column)."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter)
    styles = getSampleStyleSheet()

    table_data = [
        ["Name", "Designation", "Committee"],
        ["John Doe", "Independent Director", "Audit"],
        ["Jane Smith", "Managing Director", "Risk"],
    ]
    t = Table(table_data, colWidths=[150, 150, 150])
    t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 1, colors.black)]))

    doc.build([Paragraph("Board of Directors Directory", styles["Heading1"]), t])
    return buf.getvalue()


# -----------------------------------------------------------------------------
# Task 2.3 Tests: PyMuPDF Page Text, Words BBox, Char Span Lookup, Scanned Check
# -----------------------------------------------------------------------------

def test_pdf_parser_page_text_retrieval():
    """Verify that page text is retrievable from PyMuPDF parser."""
    pdf_bytes = create_sample_financial_pdf()
    parsed = parse_pdf(pdf_bytes)

    assert parsed.page_count >= 1
    page1 = parsed.get_page(1)
    assert page1 is not None
    assert "Acme Financial Services Limited" in page1.text
    assert "Revenue from operations" in page1.text
    assert len(page1.words) > 0


def test_bbox_lookup_by_char_span():
    """Verify that bounding box lookup by character span works accurately."""
    pdf_bytes = create_sample_financial_pdf()
    parsed = parse_pdf(pdf_bytes)
    page1 = parsed.get_page(1)
    assert page1 is not None

    # Search for known phrase
    target = "Acme Financial Services"
    idx = page1.text.find(target)
    assert idx != -1

    bbox = page1.get_bbox_for_char_span(idx, idx + len(target))
    assert bbox is not None
    x0, y0, x1, y1 = bbox
    assert x1 > x0, "Bounding box width must be positive"
    assert y1 > y0, "Bounding box height must be positive"

    # Test quote convenience lookup
    quote_bbox = page1.get_bbox_for_quote("Revenue from operations")
    assert quote_bbox is not None
    assert quote_bbox[2] > quote_bbox[0]


def test_scanned_pdf_detection():
    """Verify that a scanned/empty PDF without text layer raises ScannedPDFError."""
    scanned_bytes = create_scanned_mock_pdf()
    with pytest.raises(ScannedPDFError) as exc_info:
        parse_pdf(scanned_bytes, detect_scanned=True)
    assert exc_info.value.code == "SCANNED_PDF_UNSUPPORTED"


# -----------------------------------------------------------------------------
# Task 2.4 Tests: pdfplumber Table Extraction, Header/Period, Metric Matching
# -----------------------------------------------------------------------------

def test_table_extraction_pl_table_detection():
    """Verify pdfplumber detects P&L table (>= 2 numeric columns) with confidence score."""
    pdf_bytes = create_sample_financial_pdf()
    tables = extract_tables_from_pdf(pdf_bytes)

    assert len(tables) >= 1
    pl_table = tables[0]
    assert pl_table.is_pl_table is True
    assert pl_table.confidence >= 0.70
    assert pl_table.scale == "crore"
    assert pl_table.currency == "INR"
    assert len(pl_table.headers) >= 3


def test_header_cells_mapped_to_periods():
    """Verify that table header cells 'FY24' and 'FY23' are mapped to Period objects."""
    pdf_bytes = create_sample_financial_pdf()
    tables = extract_tables_from_pdf(pdf_bytes)
    pl_table = tables[0]

    # Check periods on extracted facts
    fy24_facts = [f for f in pl_table.facts if f.period.get("fy") == 2024]
    fy23_facts = [f for f in pl_table.facts if f.period.get("fy") == 2023]
    assert len(fy24_facts) >= 3
    assert len(fy23_facts) >= 3


def test_row_labels_mapped_to_canonical_metrics():
    """Verify row labels map to metrics via registry (Revenue -> revenue, Profit after tax -> net_income)."""
    pdf_bytes = create_sample_financial_pdf()
    tables = extract_tables_from_pdf(pdf_bytes)
    pl_table = tables[0]

    metrics = {f.metric for f in pl_table.facts}
    assert "revenue" in metrics
    assert "cogs" in metrics or "operating_expenses" in metrics
    assert "operating_income" in metrics
    assert "net_income" in metrics


def test_demo_annual_report_to_facts_with_locators():
    """
    Done-when criterion for Task 2.4:
    Demo annual report table -> facts with exact locators (page, bbox, row, col).
    """
    pdf_bytes = create_sample_financial_pdf()
    facts = extract_facts_from_pdf_tables(pdf_bytes)

    assert len(facts) >= 4
    rev_fy24 = next(f for f in facts if f.metric == "revenue" and f.period.get("fy") == 2024)
    assert rev_fy24.value_raw == "3,400"
    # Base value normalized with scale crore: 3400 * 10^7 = 34000000000
    assert rev_fy24.value_base == "34000000000"
    assert rev_fy24.locator["page"] == 1
    assert "bbox" in rev_fy24.locator
    assert len(rev_fy24.locator["bbox"]) == 4
    assert rev_fy24.locator["row"] >= 1
    assert rev_fy24.locator["col"] >= 1


def test_non_pl_table_filtering():
    """Verify non-financial tables (e.g. board directory) are not marked as P&L tables."""
    non_pl_bytes = create_non_pl_pdf()
    tables = extract_tables_from_pdf(non_pl_bytes)

    for t in tables:
        assert t.is_pl_table is False
        assert len(t.facts) == 0

