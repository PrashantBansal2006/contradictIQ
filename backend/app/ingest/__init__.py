"""
ContradictIQ Ingestion Package
==============================
Parsers, validators, fact extractors for PDF and CSV documents.
"""

from app.ingest.pdf_parser import (
    parse_pdf,
    extract_tables_from_pdf,
    extract_facts_from_pdf_tables,
    ParsedPDF,
    PageData,
    WordBox,
    TableExtract,
    ExtractedFact,
    ScannedPDFError,
)

__all__ = [
    "parse_pdf",
    "extract_tables_from_pdf",
    "extract_facts_from_pdf_tables",
    "ParsedPDF",
    "PageData",
    "WordBox",
    "TableExtract",
    "ExtractedFact",
    "ScannedPDFError",
]

