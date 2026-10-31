"""
Unit tests for Ingestion tasks 2.4, 2.5, 2.6.
Covers:
- Task 2.4: PDF table extraction with pdfplumber, P&L detection (>=2 numeric cols), period mapping
- Task 2.5: fact_extractor.py: Table -> FactBase conversion, scale normalization, locators
- Task 2.6: Narrative regex claims with >= 5 patterns tested (YoY, QoQ, Margins, Ratios, Directional, Absolute)
"""
import tempfile
from pathlib import Path
from decimal import Decimal
import pytest
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
from reportlab.lib.styles import getSampleStyleSheet

from app.ingest.pdf_parser import (
    extract_tables_from_pdf,
    extract_pages_with_pymupdf,
    detect_scale_and_currency,
    ScannedPDFError,
    TableExtract,
)
from app.ingest.fact_extractor import (
    extract_facts_from_table,
    extract_facts_from_raw_grid,
    extract_narrative_regex_claims,
    extract_narrative_regex_facts,
)
from app.schemas.claim import ClaimType
from app.schemas.fact import FactMethod, FactScope, FactBasis


# ==============================================================================
# Helper to generate test PDF documents
# ==============================================================================

@pytest.fixture
def sample_financial_pdf(tmp_path: Path) -> Path:
    """Generates a demo annual report PDF with a P&L financial table."""
    pdf_path = tmp_path / "annual_report_sample.pdf"
    doc = SimpleDocTemplate(str(pdf_path), pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Title & Caption with Scale / Currency hint
    story.append(Paragraph("Veridian Foods Limited — Annual Report FY 2024-25", styles["Title"]))
    story.append(Paragraph("Statement of Profit and Loss (₹ in Crores)", styles["Heading2"]))
    story.append(Spacer(1, 10))

    # P&L Table with >= 2 numeric columns and header periods
    data = [
        ["Particulars", "FY2025", "FY2024"],
        ["Revenue from Operations", "3,400", "2,977"],
        ["Cost of Materials Consumed", "1,850", "1,620"],
        ["Operating Expenses", "750", "650"],
        ["Operating Profit", "800", "707"],
        ["Net Profit for the period", "285", "210"],
    ]
    t = Table(data, colWidths=[200, 100, 100])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#f0f0f0")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ]))
    story.append(t)

    # Narrative text paragraph with financial claims
    story.append(Spacer(1, 15))
    story.append(Paragraph(
        "During FY2025, revenue grew 25% driven by market expansion. "
        "Net margin was 8.4% compared to 7.0% in the previous year. "
        "Operating expenses rose by approximately 15% due to logistics. "
        "The company reported revenue of ₹3,400 crore.",
        styles["Normal"]
    ))

    doc.build(story)
    return pdf_path


# ==============================================================================
# Task 2.4 Tests: PDF Table Extraction
# ==============================================================================

def test_detect_scale_and_currency():
    scale, curr = detect_scale_and_currency("Statement of Profit and Loss (₹ in Crores)")
    assert scale == "crore"
    assert curr == "INR"

    scale_usd, curr_usd = detect_scale_and_currency("Financial results ($ in Millions)")
    assert scale_usd == "million"
    assert curr_usd == "USD"

    scale_lakh, curr_lakh = detect_scale_and_currency("Amounts in Rs. Lakhs")
    assert scale_lakh == "lakh"
    assert curr_lakh == "INR"


def test_extract_tables_from_sample_pdf(sample_financial_pdf: Path):
    tables = extract_tables_from_pdf(sample_financial_pdf)
    assert len(tables) >= 1

    pnl_table = tables[0]
    assert pnl_table.is_financial is True
    assert pnl_table.scale == "crore"
    assert pnl_table.currency == "INR"
    assert pnl_table.confidence >= 0.8

    # Headers and periods
    assert "Particulars" in pnl_table.headers[0]
    assert 1 in pnl_table.period_columns
    assert 2 in pnl_table.period_columns
    assert pnl_table.period_columns[1].fy == 2025
    assert pnl_table.period_columns[2].fy == 2024


def test_scanned_pdf_detection(tmp_path: Path):
    """Test scanned PDF detection raises ScannedPDFError when text length is < threshold."""
    empty_pdf = tmp_path / "scanned_dummy.pdf"
    doc = SimpleDocTemplate(str(empty_pdf), pagesize=letter)
    # Build empty document with no printable text
    doc.build([Spacer(1, 100)])

    with pytest.raises(ScannedPDFError) as exc_info:
        extract_pages_with_pymupdf(empty_pdf, min_total_text=50)
    assert exc_info.value.code == "SCANNED_PDF_UNSUPPORTED"


# ==============================================================================
# Task 2.5 Tests: Fact Extractor
# ==============================================================================

def test_extract_facts_from_table(sample_financial_pdf: Path):
    tables = extract_tables_from_pdf(sample_financial_pdf)
    pnl_table = tables[0]

    facts = extract_facts_from_table(pnl_table, document_id="doc_sample")
    assert len(facts) >= 6

    # Verify Revenue for FY2025 normalized to crore scale in base units
    rev_fy25 = next(f for f in facts if f.metric == "revenue" and f.period.fy == 2025)
    assert rev_fy25.raw_label == "Revenue from Operations"
    assert rev_fy25.value_raw == "3,400"
    # 3,400 in crore scale = 34,000,000,000 base units
    assert rev_fy25.value_base == "34000000000"
    assert rev_fy25.scale == "crore"
    assert rev_fy25.currency == "INR"
    assert rev_fy25.period_key == "FY2025"
    assert rev_fy25.method == FactMethod.TABLE
    assert rev_fy25.locator.page == 1
    assert "Revenue from Operations: 3,400" in rev_fy25.locator.quote

    # Verify Net Income
    net_inc = next(f for f in facts if f.metric == "net_income" and f.period.fy == 2025)
    assert net_inc.value_base == "2850000000"


def test_extract_facts_from_raw_grid():
    headers = ["Metric", "Q1 FY25", "Q2 FY25"]
    rows = [
        ["Turnover", "800", "850"],
        ["Cost of sales", "400", "420"],
    ]
    facts = extract_facts_from_raw_grid(
        headers=headers,
        rows=rows,
        scale="crore",
        currency="INR",
        method=FactMethod.CSV,
    )
    assert len(facts) == 4
    f1 = facts[0]
    assert f1.metric == "revenue"
    assert f1.value_base == "8000000000"
    assert f1.period_key == "Q1_FY2025"
    assert f1.method == FactMethod.CSV


# ==============================================================================
# Task 2.6 Tests: Narrative Regex Extraction (>= 5 patterns tested)
# ==============================================================================

def test_regex_claim_pattern_1_yoy_growth():
    """Pattern 1: YoY Growth ('revenue grew 25%')"""
    text = "In the reported fiscal year, revenue grew 25% across all segments."
    claims = extract_narrative_regex_claims(text, page=1)
    assert len(claims) == 1
    c = claims[0]
    assert c.claim_type == ClaimType.GROWTH_YOY
    assert c.metric == "revenue"
    assert c.value_raw == "25%"
    assert c.value_numeric == 25.0
    assert c.value_precision == 0
    assert c.unit == "percent"


def test_regex_claim_pattern_2_qoq_growth():
    """Pattern 2: QoQ Growth ('revenue grew 5% sequentially')"""
    text = "For Q3, sales grew 5.2% sequentially compared to Q2."
    claims = extract_narrative_regex_claims(text, page=2)
    assert len(claims) >= 1
    c = claims[0]
    assert c.claim_type == ClaimType.GROWTH_QOQ
    assert c.metric == "revenue"
    assert c.value_numeric == 5.2
    assert c.value_precision == 1


def test_regex_claim_pattern_3_margins():
    """Pattern 3: Margins ('net margin of 8.4%')"""
    text = "The business delivered a strong net margin of 8.4% in FY25."
    claims = extract_narrative_regex_claims(text, page=1)
    assert len(claims) == 1
    c = claims[0]
    assert c.claim_type == ClaimType.MARGIN
    assert c.metric == "net_margin"
    assert c.value_numeric == 8.4
    assert c.value_precision == 1


def test_regex_claim_pattern_4_ratios():
    """Pattern 4: Opex / Expense Ratio ('opex ratio was 30%')"""
    text = "Our opex ratio was 30.5% for the current period."
    claims = extract_narrative_regex_claims(text, page=1)
    assert len(claims) == 1
    c = claims[0]
    assert c.claim_type == ClaimType.OPEX_RATIO
    assert c.metric == "operating_expenses"
    assert c.value_numeric == 30.5


def test_regex_claim_pattern_5_directional():
    """Pattern 5: Directional Claims ('profit declined')"""
    text = "Due to commodity price inflation, operating income declined during the period."
    claims = extract_narrative_regex_claims(text, page=3)
    assert len(claims) == 1
    c = claims[0]
    assert c.claim_type == ClaimType.DIRECTION
    assert c.metric == "operating_income"
    assert c.value_raw == "declined"


def test_regex_claim_pattern_6_absolute_statistics():
    """Pattern 6: Absolute Statistics ('reported revenue of ₹3,400 cr')"""
    text = "The group reported revenue of ₹3,400 cr for FY2025."
    claims = extract_narrative_regex_claims(text, page=1)
    assert len(claims) >= 1
    c = claims[0]
    assert c.claim_type == ClaimType.STATISTIC
    assert c.metric == "revenue"
    assert c.value_numeric == 3400.0
    assert c.scale == "crore"
    assert c.currency == "INR"


def test_hedged_narrative_claim_detection():
    """Hedged indicators e.g. 'approximately', 'about' double tolerance."""
    text = "Net profit grew approximately 18% during the year."
    claims = extract_narrative_regex_claims(text)
    assert len(claims) == 1
    assert claims[0].hedged is True


def test_extract_narrative_regex_facts():
    """Extracts direct facts with method=FactMethod.REGEX."""
    text = "The company recorded revenue of ₹3,400 crore in FY2025."
    facts = extract_narrative_regex_facts(text, page=1)
    assert len(facts) == 1
    f = facts[0]
    assert f.metric == "revenue"
    assert f.value_base == "34000000000"
    assert f.currency == "INR"
    assert f.scale == "crore"
    assert f.method == FactMethod.REGEX

