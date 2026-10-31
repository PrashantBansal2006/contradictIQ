"""
fact_extractor.py — Extract structured Facts and narrative Claims from tables and text.

Per tasks.md §2.4, §2.5, §2.6 and architecture §6.1, §7.2.
Converts table rows and narrative text to FactBase and ClaimVersionBase objects.
"""
from decimal import Decimal
import re
from typing import Optional

from app.core.metrics import match_metric
from app.core.periods import parse_period
from app.core.units import parse_value, SCALE_FACTORS
from app.ingest.pdf_parser import TableExtract, is_numeric_cell
from app.schemas.common import Locator, Period as PeriodSchema
from app.schemas.fact import FactBase, FactBasis, FactMethod, FactScope
from app.schemas.claim import ClaimType, ClaimVersionBase


# ==============================================================================
# Task 2.5: Table Facts Extraction
# ==============================================================================

def extract_facts_from_table(
    table: TableExtract,
    document_id: str = "doc_1",
    default_fy_end_month: int = 3,
    scope: str = FactScope.CONSOLIDATED.value,
    basis: FactBasis = FactBasis.REPORTED,
) -> list[FactBase]:
    """
    Converts extracted table rows to FactBase models with normalized values,
    canonical metrics, periods, and provenance locators.
    """
    facts: list[FactBase] = []

    # Map column headers to periods if not already mapped
    period_columns: dict[int, PeriodSchema] = dict(table.period_columns)
    for col_idx, h_text in enumerate(table.headers):
        if col_idx not in period_columns and col_idx > 0:
            try:
                p_core = parse_period(h_text, default_fy_end_month=default_fy_end_month)
                period_columns[col_idx] = PeriodSchema(
                    kind=p_core.kind,
                    fy=p_core.fy,
                    idx=p_core.idx,
                    fy_end_month=p_core.fy_end_month,
                )
            except Exception:
                pass

    for row_idx, row in enumerate(table.rows):
        if not row:
            continue

        raw_label = row[0].strip()
        canonical_metric = match_metric(raw_label)
        if not canonical_metric:
            continue  # Row is not a recognized financial metric

        for col_idx in range(1, len(row)):
            cell_val = row[col_idx].strip()
            if not is_numeric_cell(cell_val):
                continue

            period_schema = period_columns.get(col_idx)
            if not period_schema:
                continue

            # Parse value using table scale and currency as defaults
            try:
                parsed = parse_value(
                    cell_val,
                    default_currency=table.currency,
                    default_scale=table.scale,
                )
            except Exception:
                continue

            val_base_str = str(parsed.value)
            period_key = period_schema.canonical_key()

            locator = Locator(
                page=table.page_no,
                bbox=table.bbox,
                row=row_idx + 1,  # 1-indexed relative to data
                col=col_idx,
                quote=f"{raw_label}: {cell_val}",
            )

            fact = FactBase(
                metric=canonical_metric,
                raw_label=raw_label,
                value_raw=cell_val,
                value_base=val_base_str,
                unit=parsed.unit,
                scale=parsed.scale or table.scale or "unit",
                currency=parsed.currency or table.currency,
                period=period_schema,
                period_key=period_key,
                scope=scope,
                basis=basis,
                confidence=table.confidence,
                method=FactMethod.TABLE,
                locator=locator,
            )
            facts.append(fact)

    return facts


def extract_facts_from_raw_grid(
    headers: list[str],
    rows: list[list[str]],
    page_no: int = 1,
    scale: str = "unit",
    currency: Optional[str] = None,
    default_fy_end_month: int = 3,
    scope: str = FactScope.CONSOLIDATED.value,
    basis: FactBasis = FactBasis.REPORTED,
    method: FactMethod = FactMethod.CSV,
) -> list[FactBase]:
    """
    Extracts facts from raw tabular grids (e.g. CSV or test tables).
    """
    tbl = TableExtract(
        page_no=page_no,
        bbox=[0.0, 0.0, 100.0, 100.0],
        headers=headers,
        rows=rows,
        scale=scale,
        currency=currency,
        confidence=0.9,
    )
    facts = extract_facts_from_table(
        tbl,
        default_fy_end_month=default_fy_end_month,
        scope=scope,
        basis=basis,
    )
    # Adjust method if CSV
    return [
        FactBase(
            metric=f.metric,
            raw_label=f.raw_label,
            value_raw=f.value_raw,
            value_base=f.value_base,
            unit=f.unit,
            scale=f.scale,
            currency=f.currency,
            period=f.period,
            period_key=f.period_key,
            scope=f.scope,
            basis=f.basis,
            confidence=f.confidence,
            method=method,
            locator=f.locator,
        )
        for f in facts
    ]


# ==============================================================================
# Task 2.6: Narrative Regex Extraction
# ==============================================================================

# Regex patterns for narrative financial assertions (>= 5 patterns per tasks.md §2.6)

# 2. QoQ Growth checked BEFORE generic growth: "revenue grew 5% sequentially", "QoQ growth of 3.5%"
P_QOQ_GROWTH = re.compile(
    r"(?i)\b(revenue|net sales|sales|profit|net income|operating profit|ebitda)\s+(?:grew|increased|rose|expanded)\s+(?:approximately|about|around|nearly|roughly)?\s*(?:by\s+)?(\d+(?:\.\d+)?)\s*%\s*(?:quarter[\s\-]on[\s\-]quarter|QoQ|sequentially)\b",
)

# 1. YoY Growth: "revenue grew 25%", "net sales increased by 14.2%", "turnover rose 10%"
P_YOY_GROWTH_1 = re.compile(
    r"(?i)\b(revenue|net sales|turnover|sales|profit|net income|operating profit|ebitda)\s+(?:grew|increased|rose|expanded|surged)\s+(?:approximately|about|around|nearly|roughly)?\s*(?:by\s+)?(\d+(?:\.\d+)?)\s*%",
)
P_YOY_GROWTH_2 = re.compile(
    r"(?i)\b(\d+(?:\.\d+)?)\s*%\s+(?:year[\s\-]on[\s\-]year|YoY)\s+(?:growth|increase)\s+in\s+(revenue|sales|profit|net income)\b",
)

# 3. Margins: "net margin of 8.4%", "operating margin expanded to 18%", "gross margin of 35%"
P_MARGIN = re.compile(
    r"(?i)\b(gross|operating|net)\s+(?:profit\s+)?margin\s+(?:of|was|reached|expanded to|at)\s+(\d+(?:\.\d+)?)\s*%",
)

# 4. Expense / Opex Ratio: "opex ratio was 30%", "expense ratio of 75%"
P_RATIO = re.compile(
    r"(?i)\b(opex|operating expense|total expense|expense)\s+ratio\s+(?:of|was|reached|at)\s+(\d+(?:\.\d+)?)\s*%",
)

# 5. Directional Claims: "profit declined", "revenue decreased", "operating income fell"
P_DIRECTION = re.compile(
    r"(?i)\b(revenue|profit|operating income|ebitda|net income|sales)\s+(declined|decreased|fell|dropped|contracted)\b",
)

# 6. Absolute Financial Statistics: "reported revenue of ₹3,400 cr", "net profit was ₹84 crore"
P_STATISTIC = re.compile(
    r"(?i)\b(?:reported|posted|achieved|recorded|had)\s+(?:a\s+)?(revenue|net profit|operating profit|net sales|cogs)\s+of\s+(₹|Rs\.?|\$|€|£)?\s*([\d,]+(?:\.\d+)?)\s*(crores?|cr|billions?|bn|millions?|mn|lakhs?|k)?\b",
)

# Hedging indicator pattern ("approximately", "about", "around", "nearly")
P_HEDGED = re.compile(r"(?i)\b(approx|approximately|about|around|nearly|roughly|estimated)\b")


def _find_period_in_context(sentence: str, default_fy: int = 2025) -> PeriodSchema:
    """Detects period from sentence context or defaults to FY2025."""
    try:
        p_core = parse_period(sentence)
        return PeriodSchema(
            kind=p_core.kind,
            fy=p_core.fy,
            idx=p_core.idx,
            fy_end_month=p_core.fy_end_month,
        )
    except Exception:
        return PeriodSchema(kind="FY", fy=default_fy, idx=None, fy_end_month=3)


def _count_decimals(num_str: str) -> int:
    if "." in num_str:
        return len(num_str.split(".")[1])
    return 0


def extract_narrative_regex_claims(
    text: str,
    page: int = 1,
    entity: Optional[str] = None,
    source_doc_id: Optional[str] = None,
    default_fy: int = 2025,
) -> list[ClaimVersionBase]:
    """
    Extracts candidate claims from narrative text using regex patterns per Task 2.6.
    Covers YoY growth, QoQ growth, margins, ratios, directional, and absolute claims.
    """
    claims: list[ClaimVersionBase] = []

    # Split text into sentence-like clauses
    clauses = re.split(r"(?<=[.!?\n])\s+", text)

    for clause in clauses:
        clause_str = clause.strip()
        if not clause_str:
            continue

        is_hedged = bool(P_HEDGED.search(clause_str))
        period_schema = _find_period_in_context(clause_str, default_fy=default_fy)

        # Check QoQ Growth first
        matched_qoq = False
        for m in P_QOQ_GROWTH.finditer(clause_str):
            matched_qoq = True
            metric_raw = m.group(1)
            metric_canon = match_metric(metric_raw) or metric_raw.lower().replace(" ", "_")
            val_str = m.group(2)
            num_val = float(val_str)
            claims.append(
                ClaimVersionBase(
                    text=clause_str,
                    claim_type=ClaimType.GROWTH_QOQ,
                    metric=metric_canon,
                    value_raw=f"{val_str}%",
                    value_numeric=num_val,
                    value_precision=_count_decimals(val_str),
                    unit="percent",
                    scale="unit",
                    period=period_schema,
                    entity=entity,
                    hedged=is_hedged,
                    quote=m.group(0),
                    source_doc_id=source_doc_id,
                    source_locator=Locator(page=page, quote=m.group(0)),
                )
            )

        # 1. YoY Growth (only if not matched QoQ)
        if not matched_qoq:
            for m in P_YOY_GROWTH_1.finditer(clause_str):
                metric_raw = m.group(1)
                metric_canon = match_metric(metric_raw) or metric_raw.lower().replace(" ", "_")
                val_str = m.group(2)
                num_val = float(val_str)
                claims.append(
                    ClaimVersionBase(
                        text=clause_str,
                        claim_type=ClaimType.GROWTH_YOY,
                        metric=metric_canon,
                        value_raw=f"{val_str}%",
                        value_numeric=num_val,
                        value_precision=_count_decimals(val_str),
                        unit="percent",
                        scale="unit",
                        period=period_schema,
                        entity=entity,
                        hedged=is_hedged,
                        quote=m.group(0),
                        source_doc_id=source_doc_id,
                        source_locator=Locator(page=page, quote=m.group(0)),
                    )
                )

        # YoY Growth Pattern 2: "25% YoY growth in revenue"
        for m in P_YOY_GROWTH_2.finditer(clause_str):
            val_str = m.group(1)
            metric_raw = m.group(2)
            metric_canon = match_metric(metric_raw) or metric_raw.lower().replace(" ", "_")
            num_val = float(val_str)
            claims.append(
                ClaimVersionBase(
                    text=clause_str,
                    claim_type=ClaimType.GROWTH_YOY,
                    metric=metric_canon,
                    value_raw=f"{val_str}%",
                    value_numeric=num_val,
                    value_precision=_count_decimals(val_str),
                    unit="percent",
                    scale="unit",
                    period=period_schema,
                    entity=entity,
                    hedged=is_hedged,
                    quote=m.group(0),
                    source_doc_id=source_doc_id,
                    source_locator=Locator(page=page, quote=m.group(0)),
                )
            )

        # 3. Margins: "net margin of 8.4%"
        for m in P_MARGIN.finditer(clause_str):
            margin_type = m.group(1).lower()
            metric_canon = f"{margin_type}_margin"
            val_str = m.group(2)
            num_val = float(val_str)
            claims.append(
                ClaimVersionBase(
                    text=clause_str,
                    claim_type=ClaimType.MARGIN,
                    metric=metric_canon,
                    value_raw=f"{val_str}%",
                    value_numeric=num_val,
                    value_precision=_count_decimals(val_str),
                    unit="percent",
                    scale="unit",
                    period=period_schema,
                    entity=entity,
                    hedged=is_hedged,
                    quote=m.group(0),
                    source_doc_id=source_doc_id,
                    source_locator=Locator(page=page, quote=m.group(0)),
                )
            )

        # 4. Expense / Opex Ratio: "opex ratio was 30%"
        for m in P_RATIO.finditer(clause_str):
            ratio_raw = m.group(1).lower()
            val_str = m.group(2)
            claim_type = ClaimType.OPEX_RATIO if "opex" in ratio_raw or "operating" in ratio_raw else ClaimType.EXPENSE_RATIO
            metric_canon = "operating_expenses" if claim_type == ClaimType.OPEX_RATIO else "total_expenses"
            claims.append(
                ClaimVersionBase(
                    text=clause_str,
                    claim_type=claim_type,
                    metric=metric_canon,
                    value_raw=f"{val_str}%",
                    value_numeric=float(val_str),
                    value_precision=_count_decimals(val_str),
                    unit="percent",
                    scale="unit",
                    period=period_schema,
                    entity=entity,
                    hedged=is_hedged,
                    quote=m.group(0),
                    source_doc_id=source_doc_id,
                    source_locator=Locator(page=page, quote=m.group(0)),
                )
            )

        # 5. Directional Claims: "profit declined"
        for m in P_DIRECTION.finditer(clause_str):
            metric_raw = m.group(1)
            metric_canon = match_metric(metric_raw) or metric_raw.lower().replace(" ", "_")
            direction_word = m.group(2).lower()
            claims.append(
                ClaimVersionBase(
                    text=clause_str,
                    claim_type=ClaimType.DIRECTION,
                    metric=metric_canon,
                    value_raw=direction_word,
                    value_numeric=None,
                    value_precision=0,
                    unit="direction",
                    scale="unit",
                    period=period_schema,
                    entity=entity,
                    hedged=is_hedged,
                    quote=m.group(0),
                    source_doc_id=source_doc_id,
                    source_locator=Locator(page=page, quote=m.group(0)),
                )
            )

        # 6. Absolute Financial Statistics: "reported revenue of ₹3,400 cr"
        for m in P_STATISTIC.finditer(clause_str):
            metric_raw = m.group(1)
            curr_sym = m.group(2) or ""
            val_raw_num = m.group(3)
            scale_word = m.group(4) or "unit"
            full_raw = f"{curr_sym}{val_raw_num} {scale_word}".strip()

            metric_canon = match_metric(metric_raw) or metric_raw.lower().replace(" ", "_")
            try:
                parsed = parse_value(full_raw)
                val_num = float(parsed.raw_number)
                scale_canon = parsed.scale
                currency_iso = parsed.currency
            except Exception:
                val_num = float(val_raw_num.replace(",", ""))
                scale_canon = scale_word
                currency_iso = "INR" if "₹" in curr_sym or "rs" in curr_sym.lower() else None

            claims.append(
                ClaimVersionBase(
                    text=clause_str,
                    claim_type=ClaimType.STATISTIC,
                    metric=metric_canon,
                    value_raw=full_raw,
                    value_numeric=val_num,
                    value_precision=_count_decimals(val_raw_num),
                    unit="currency" if currency_iso else "count",
                    scale=scale_canon,
                    currency=currency_iso,
                    period=period_schema,
                    entity=entity,
                    hedged=is_hedged,
                    quote=m.group(0),
                    source_doc_id=source_doc_id,
                    source_locator=Locator(page=page, quote=m.group(0)),
                )
            )

    return claims


def extract_narrative_regex_facts(
    text: str,
    document_id: str = "doc_1",
    page: int = 1,
    default_fy: int = 2025,
) -> list[FactBase]:
    """
    Extracts direct numerical facts from narrative sentences into FactBase with method=FactMethod.REGEX.
    """
    facts: list[FactBase] = []
    clauses = re.split(r"(?<=[.!?\n])\s+", text)

    for clause in clauses:
        clause_str = clause.strip()
        if not clause_str:
            continue

        period_schema = _find_period_in_context(clause_str, default_fy=default_fy)

        for m in P_STATISTIC.finditer(clause_str):
            metric_raw = m.group(1)
            curr_sym = m.group(2) or ""
            val_raw_num = m.group(3)
            scale_word = m.group(4) or "unit"
            full_raw = f"{curr_sym}{val_raw_num} {scale_word}".strip()

            metric_canon = match_metric(metric_raw)
            if not metric_canon:
                continue

            try:
                parsed = parse_value(full_raw)
                val_base = str(parsed.value)
                currency = parsed.currency
                scale = parsed.scale
                unit = parsed.unit
            except Exception:
                continue

            locator = Locator(page=page, quote=m.group(0))

            facts.append(
                FactBase(
                    metric=metric_canon,
                    raw_label=metric_raw,
                    value_raw=full_raw,
                    value_base=val_base,
                    unit=unit,
                    scale=scale,
                    currency=currency,
                    period=period_schema,
                    period_key=period_schema.canonical_key(),
                    scope=FactScope.CONSOLIDATED.value,
                    basis=FactBasis.REPORTED,
                    confidence=0.85,
                    method=FactMethod.REGEX,
                    locator=locator,
                )
            )

    return facts
