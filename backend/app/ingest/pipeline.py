"""
Document ingestion pipeline orchestrating validation, parsing, table extraction, and fact persistence.
"""
import csv
from decimal import Decimal
import io
import json
from pathlib import Path
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.ingest.pdf_parser import (
    extract_tables_from_pdf,
    parse_pdf,
    ScannedPDFError,
)
from app.models.models import Document, Fact, Page, TableExtract
from app.services.jobs import update_job_progress
from app.services.ledger import append_ledger_event


async def process_document_pipeline(
    session: AsyncSession,
    document: Document,
    job_id: Optional[str] = None,
) -> None:
    """Execute end-to-end ingestion pipeline on an uploaded document."""
    file_path = Path(document.storage_path)
    if not file_path.exists():
        if job_id:
            await update_job_progress(session, job_id, "failed", 0, "file_missing", "File not found on disk")
        document.status = "failed"
        document.error_code = "FILE_NOT_FOUND"
        document.error_msg = "Stored file not found"
        await session.commit()
        return

    try:
        if job_id:
            await update_job_progress(session, job_id, "processing", 20, "validating")

        is_pdf = document.filename.lower().endswith(".pdf") or document.mime == "application/pdf"
        is_csv = document.filename.lower().endswith(".csv") or document.mime in ("text/csv", "application/csv")

        if is_pdf:
            if job_id:
                await update_job_progress(session, job_id, "processing", 50, "parsing_pdf")

            # Parse pages & words
            parsed_pdf = parse_pdf(file_path, detect_scanned=False)
            document.page_count = parsed_pdf.page_count

            for p in parsed_pdf.pages:
                page_row = Page(
                    document_id=document.id,
                    page_no=p.page_no,
                    text=p.text,
                    words_json=json.dumps([w.to_dict() for w in p.words]),
                )
                session.add(page_row)

            if job_id:
                await update_job_progress(session, job_id, "processing", 75, "extracting_tables")

            # Extract tables & facts
            tables = extract_tables_from_pdf(file_path)
            for t in tables:
                t_row = TableExtract(
                    document_id=document.id,
                    page_no=t.page_no,
                    bbox_json=json.dumps(t.bbox),
                    header_json=json.dumps(t.headers),
                    rows_json=json.dumps(t.rows),
                    method="pdfplumber",
                    confidence=t.confidence,
                )
                session.add(t_row)

                for f in t.facts:
                    period_dict = f.period if isinstance(f.period, dict) else {}
                    p_key = f"{period_dict.get('kind', 'FY')}{period_dict.get('idx', '')}_{period_dict.get('fy', '')}"
                    fact_row = Fact(
                        document_id=document.id,
                        investigation_id=document.investigation_id,
                        metric=f.metric,
                        raw_label=f.raw_label,
                        value_raw=f.value_raw,
                        value_base=f.value_base,
                        unit=f.unit,
                        scale=f.scale,
                        currency=f.currency,
                        period_json=json.dumps(period_dict),
                        period_key=p_key,
                        scope="consolidated",
                        basis="reported",
                        restated=False,
                        confidence=f.confidence,
                        method="table",
                        confirmed=True,
                        locator_json=json.dumps(f.locator),
                    )
                    session.add(fact_row)

        elif is_csv:
            if job_id:
                await update_job_progress(session, job_id, "processing", 50, "parsing_csv")

            content = file_path.read_text(encoding="utf-8", errors="ignore")
            # Parse CSV rows
            reader = list(csv.reader(io.StringIO(content)))
            if reader:
                headers = [h.strip() for h in reader[0]]
                # Look for columns: metric, period, value or layout
                for r_idx, row in enumerate(reader[1:]):
                    if not row or len(row) < 2:
                        continue
                    # Heuristic parsing for simple CSV: metric/label in col 0, value in col 1 or 2
                    metric = row[0].strip().lower().replace(" ", "_")
                    val_str = row[1].strip() if len(row) > 1 else ""
                    cleaned = val_str.replace(",", "").replace("$", "").replace("₹", "").strip()
                    try:
                        num = Decimal(cleaned)
                    except Exception:
                        continue

                    period_dict = {"kind": "FY", "fy": 2024}
                    if len(row) > 2 and row[2].strip():
                        period_dict = {"kind": "FY", "fy": int(row[2].strip()[-4:])} if len(row[2].strip()) >= 4 else period_dict

                    fact_row = Fact(
                        document_id=document.id,
                        investigation_id=document.investigation_id,
                        metric=metric,
                        raw_label=row[0].strip(),
                        value_raw=val_str,
                        value_base=str(num),
                        unit="currency",
                        scale="unit",
                        currency="INR",
                        period_json=json.dumps(period_dict),
                        period_key="FY2024",
                        scope="consolidated",
                        basis="reported",
                        confidence=1.0,
                        method="csv",
                        confirmed=True,
                        locator_json=json.dumps({"row": r_idx + 2, "col": 2, "quote": f"{row[0]}: {val_str}"}),
                    )
                    session.add(fact_row)

            document.page_count = 1

        document.status = "ready"
        await session.commit()

        if job_id:
            await update_job_progress(session, job_id, "ready", 100, "ready")

        await append_ledger_event(
            session=session,
            investigation_id=document.investigation_id,
            actor_id=document.uploaded_by,
            event_type="DOCUMENT_INGESTED",
            payload={"document_id": document.id, "filename": document.filename, "status": "ready"},
        )
        await session.commit()

    except Exception as exc:
        document.status = "failed"
        document.error_code = getattr(exc, "code", "INGESTION_ERROR")
        document.error_msg = str(exc)
        await session.commit()
        if job_id:
            await update_job_progress(session, job_id, "failed", 0, "failed", str(exc))
