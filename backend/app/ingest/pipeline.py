import os
import re
import hashlib
from pathlib import Path
from typing import Any, Callable
from dataclasses import dataclass, field

from backend.app.core.units import parse_value
from backend.app.core.periods import parse_period
from backend.app.core.metrics import match_metric
from backend.app.llm.extract import extract_claims_from_text
from backend.app.llm.grounding import validate_claim_grounding

ProgressCallback = Callable[[str, int, str], None]

@dataclass
class PipelineResult:
    """Document processing result per architecture §6."""
    document_id: str
    status: str  # "ready" or "failed"
    progress: int
    step: str
    sha256: str
    storage_path: str
    page_count: int
    facts: list[dict[str, Any]] = field(default_factory=list)
    claims: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[dict[str, str]] = field(default_factory=list)
    error_code: str | None = None
    error_msg: str | None = None

class IngestionPipeline:
    """
    Sequential pipeline per architecture §6.1:
    VALIDATE -> STORE -> PARSE -> TABLES -> FACTS(rule) -> LLM EXTRACT -> NORMALIZE -> QUALITY CHECKS -> READY
    """
    def __init__(self, upload_dir: str | Path = "./data/uploads"):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def process(
        self,
        file_bytes: bytes,
        filename: str,
        document_id: str = "doc_test_1",
        on_progress: ProgressCallback | None = None
    ) -> PipelineResult:
        warnings: list[dict[str, str]] = []
        facts: list[dict[str, Any]] = []
        claims: list[dict[str, Any]] = []

        def report(step_name: str, pct: int, msg: str):
            if on_progress:
                on_progress(step_name, pct, msg)

        # -------------------------------------------------------------
        # 1. VALIDATE (5%)
        # -------------------------------------------------------------
        report("validate", 5, "Validating file magic bytes and size")
        if not file_bytes:
            return PipelineResult(
                document_id=document_id, status="failed", progress=5, step="validate",
                sha256="", storage_path="", page_count=0,
                error_code="EMPTY_FILE", error_msg="Uploaded file is empty."
            )

        max_mb = int(os.getenv("MAX_UPLOAD_MB", "20"))
        if len(file_bytes) > max_mb * 1024 * 1024:
            return PipelineResult(
                document_id=document_id, status="failed", progress=5, step="validate",
                sha256="", storage_path="", page_count=0,
                error_code="FILE_TOO_LARGE", error_msg=f"File exceeds {max_mb}MB limit."
            )

        ext = Path(filename).suffix.lower()
        if ext not in (".pdf", ".csv", ".txt"):
            return PipelineResult(
                document_id=document_id, status="failed", progress=5, step="validate",
                sha256="", storage_path="", page_count=0,
                error_code="UNSUPPORTED_FORMAT", error_msg=f"Unsupported format '{ext}'."
            )

        if ext == ".pdf" and not file_bytes.startswith(b"%PDF-"):
            return PipelineResult(
                document_id=document_id, status="failed", progress=5, step="validate",
                sha256="", storage_path="", page_count=0,
                error_code="INVALID_PDF_HEADER", error_msg="Corrupt PDF: Missing %PDF- magic bytes."
            )

        # -------------------------------------------------------------
        # 2. STORE (10%)
        # -------------------------------------------------------------
        report("store", 10, "Storing file to upload storage")
        file_sha256 = hashlib.sha256(file_bytes).hexdigest()
        storage_file = self.upload_dir / f"{file_sha256}{ext}"
        try:
            with open(storage_file, "wb") as f:
                f.write(file_bytes)
        except Exception as e:
            return PipelineResult(
                document_id=document_id, status="failed", progress=10, step="store",
                sha256=file_sha256, storage_path="", page_count=0,
                error_code="STORAGE_ERROR", error_msg=str(e)
            )

        # -------------------------------------------------------------
        # 3. PARSE (30%)
        # -------------------------------------------------------------
        report("parse", 30, "Extracting document text and pages")
        pages_text: list[str] = []
        if ext in (".csv", ".txt"):
            try:
                decoded = file_bytes.decode("utf-8")
            except UnicodeDecodeError:
                decoded = file_bytes.decode("latin-1", errors="replace")
            pages_text = [decoded]
        elif ext == ".pdf":
            try:
                import fitz  # PyMuPDF
                doc = fitz.open(stream=file_bytes, filetype="pdf")
                for p in doc:
                    pages_text.append(p.get_text() or "")
                doc.close()
            except Exception as e:
                warnings.append({"code": "PDF_PARSE_WARNING", "message": f"PyMuPDF fallback: {e}"})
                pages_text = [file_bytes.decode("utf-8", errors="replace")]

        if not any(p.strip() for p in pages_text):
            return PipelineResult(
                document_id=document_id, status="failed", progress=30, step="parse",
                sha256=file_sha256, storage_path=str(storage_file), page_count=len(pages_text),
                error_code="SCANNED_PDF_UNSUPPORTED", error_msg="No extractable text found in document."
            )

        # -------------------------------------------------------------
        # 4. TABLES (50%)
        # -------------------------------------------------------------
        report("tables", 50, "Detecting tabular data")
        table_rows: list[list[str]] = []
        if ext == ".csv":
            import csv
            import io
            reader = csv.reader(io.StringIO(pages_text[0]))
            table_rows = [row for row in reader if any(cell.strip() for cell in row)]

        # -------------------------------------------------------------
        # 5. FACTS (rules) (65%)
        # -------------------------------------------------------------
        report("facts", 65, "Extracting rule-based facts from tables and text")
        # Rule facts from CSV rows if present
        for r_idx, row in enumerate(table_rows):
            if len(row) >= 2:
                metric_label = row[0].strip()
                canonical = match_metric(metric_label)
                if canonical:
                    for c_idx, cell in enumerate(row[1:], start=1):
                        try:
                            pv = parse_value(cell)
                            facts.append({
                                "id": f"fact_{len(facts)+1}",
                                "metric": canonical,
                                "raw_label": metric_label,
                                "value_raw": cell,
                                "value_base": str(pv.value),
                                "unit": pv.unit,
                                "scale": pv.scale,
                                "currency": pv.currency,
                                "method": "csv",
                                "confidence": 1.0,
                                "confirmed": True,
                                "locator": {"page": 1, "row": r_idx, "col": c_idx}
                            })
                        except Exception:
                            pass

        # -------------------------------------------------------------
        # 6. LLM EXTRACT (85%)
        # -------------------------------------------------------------
        report("llm_extract", 85, "Running narrative claim extraction with grounding validation")
        try:
            for p_no, p_text in enumerate(pages_text, start=1):
                raw_claims = extract_claims_from_text(p_text, page_no=p_no)
                for rc in raw_claims:
                    gr = validate_claim_grounding(rc, p_text)
                    if gr.is_grounded and gr.claim:
                        claims.append(gr.claim)
                    else:
                        warnings.append({
                            "code": "UNGROUNDED_EXTRACTION",
                            "message": gr.rejection_reason or "Rejected by grounding gate"
                        })
        except Exception as e:
            # Failure isolation per architecture §6.2
            warnings.append({"code": "AI_UNAVAILABLE", "message": f"LLM extraction skipped: {e}"})

        # -------------------------------------------------------------
        # 7. NORMALIZE (92%)
        # -------------------------------------------------------------
        report("normalize", 92, "Normalizing units and resolving period algebra")
        for claim in claims:
            # Normalize stated value and period
            raw_period = claim.get("period", "")
            if raw_period:
                try:
                    p_obj = parse_period(raw_period)
                    claim["period_key"] = p_obj.key
                except Exception:
                    claim["period_key"] = raw_period

        # -------------------------------------------------------------
        # 8. QUALITY CHECKS (100%)
        # -------------------------------------------------------------
        report("quality_checks", 100, "Performing quality checks and finalizing")
        # Quality check: negative revenue warning
        for f in facts:
            if f["metric"] == "revenue" and float(f["value_base"]) < 0:
                warnings.append({
                    "code": "NEGATIVE_REVENUE",
                    "message": f"Negative revenue detected in fact {f['id']}"
                })

        return PipelineResult(
            document_id=document_id,
            status="ready",
            progress=100,
            step="ready",
            sha256=file_sha256,
            storage_path=str(storage_file),
            page_count=len(pages_text),
            facts=facts,
            claims=claims,
            warnings=warnings
        )
