/**
 * Frozen Shared Contracts for ContradictIQ (Phase 0 - Task 0.4)
 * Mirrors Pydantic schemas in `backend/app/schemas/`
 */

// ---------------------------------------------------------------------------
// Error Schemas (Architecture §14 & §18)
// ---------------------------------------------------------------------------

export interface ErrorDetail {
  code: string;
  message: string;
  details?: Record<string, unknown> | null;
}

export interface ErrorBody {
  error: ErrorDetail;
}

export interface ErrorResponse {
  error: ErrorDetail;
}

// ---------------------------------------------------------------------------
// Common: Period & Locator (Architecture §1.4, §5.1, §8.2)
// ---------------------------------------------------------------------------

export type PeriodKind = 'Q' | 'H' | '9M' | 'FY' | 'TTM';

export interface Period {
  kind: PeriodKind;
  fy: number;
  idx?: number | null;
  fy_end_month?: number;
}

export interface Locator {
  page?: number | null;
  bbox?: [number, number, number, number] | null; // [x0, y0, x1, y1]
  table_id?: string | null;
  row?: number | null;
  col?: number | null;
  char_span?: [number, number] | null;
  quote?: string | null;
}

export interface PaginatedList<T> {
  items: T[];
  total: number;
  offset: number;
  limit: number;
}

// ---------------------------------------------------------------------------
// Investigation Schemas (Architecture §5.1, FR-1.x)
// ---------------------------------------------------------------------------

export type InvestigationStatus = 'open' | 'in_review' | 'concluded';
export type InvestigationMemberRole = 'owner' | 'reviewer' | 'viewer';

export interface InvestigationBase {
  title: string;
  description?: string | null;
  entity_name?: string | null;
}

export interface InvestigationCreate extends InvestigationBase {}

export interface InvestigationUpdate {
  title?: string;
  description?: string | null;
  entity_name?: string | null;
  status?: InvestigationStatus;
  archived?: boolean;
}

export interface InvestigationMemberResponse {
  user_id: string;
  email: string;
  name?: string | null;
  role: InvestigationMemberRole;
}

export interface InvestigationResponse extends InvestigationBase {
  id: string;
  owner_id: string;
  status: InvestigationStatus;
  archived: boolean;
  created_at: string;
  updated_at: string;
  document_count?: number;
  claim_count?: number;
  finding_count?: number;
}

// ---------------------------------------------------------------------------
// Document Schemas (Architecture §5.1, §6, FR-2.x)
// ---------------------------------------------------------------------------

export type SourceTier = 'T1' | 'T2' | 'T3' | 'T4';
export type DocumentStatus = 'queued' | 'parsing' | 'extracting' | 'ready' | 'failed';

export interface DataQualityWarning {
  code: string;
  message: string;
  location?: string | null;
  details?: Record<string, unknown> | null;
}

export interface DocumentCreate {
  investigation_id: string;
  source_tier?: SourceTier;
  doc_date?: string | null;
  entity_name?: string | null;
}

export interface DocumentResponse {
  id: string;
  investigation_id: string;
  filename: string;
  mime: string;
  size: number;
  sha256: string;
  page_count?: number | null;
  source_tier: SourceTier;
  doc_date?: string | null;
  entity_name?: string | null;
  status: DocumentStatus;
  error_code?: string | null;
  error_msg?: string | null;
  warnings?: DataQualityWarning[];
  uploaded_by: string;
  created_at: string;
  fact_count?: number;
}

export interface WordBox {
  word: string;
  bbox: [number, number, number, number];
  char_start: number;
  char_end: number;
}

export interface PageResponse {
  id: string;
  document_id: string;
  page_no: number;
  text: string;
  words?: WordBox[] | null;
}

export interface TableExtractResponse {
  id: string;
  document_id: string;
  page_no: number;
  bbox?: [number, number, number, number] | null;
  header: string[];
  rows: unknown[][];
  method: 'pdfplumber' | 'csv' | string;
  confidence: number;
}

// ---------------------------------------------------------------------------
// Fact Schemas (Architecture §5.1, §8)
// ---------------------------------------------------------------------------

export type FactScope = 'consolidated' | 'standalone' | string;
export type FactBasis = 'reported' | 'adjusted';
export type FactMethod = 'csv' | 'table' | 'regex' | 'llm';

export interface FactBase {
  metric: string;
  raw_label: string;
  value_raw: string;
  value_base: string; // Decimal string to avoid float precision bugs
  unit: string;
  scale: string;
  currency?: string | null;
  period: Period;
  period_key: string;
  scope: string;
  basis: FactBasis;
  restated?: boolean;
  confidence: number;
  method: FactMethod;
  locator: Locator;
}

export interface FactCreate extends FactBase {
  document_id: string;
}

export interface FactUpdate {
  metric?: string;
  value_base?: string;
  confirmed?: boolean;
  scope?: string;
  basis?: FactBasis;
}

export interface FactResponse extends FactBase {
  id: string;
  document_id: string;
  document_filename?: string | null;
  confirmed: boolean;
  created_at?: string | null;
}

// ---------------------------------------------------------------------------
// Claim Schemas (Architecture §5.1, §7.2, FR-4.x)
// ---------------------------------------------------------------------------

export type ClaimOrigin = 'manual' | 'ai' | 'parsed';
export type ClaimState = 'draft' | 'needs_confirmation' | 'confirmed' | 'rejected';
export type ClaimType =
  | 'STATISTIC'
  | 'GROWTH_YOY'
  | 'GROWTH_QOQ'
  | 'MARGIN'
  | 'EXPENSE_RATIO'
  | 'OPEX_RATIO'
  | 'DIRECTION';

export interface ClaimVersionBase {
  text: string;
  claim_type: ClaimType;
  metric: string;
  value_raw?: string | null;
  value_numeric?: number | null;
  value_precision: number;
  unit: string;
  scale: string;
  currency?: string | null;
  period: Period;
  scope: string;
  basis: string;
  entity?: string | null;
  hedged?: boolean;
  quote?: string | null;
  source_doc_id?: string | null;
  source_locator?: Locator | null;
  grounded?: boolean;
  change_note?: string | null;
}

export interface ClaimVersionResponse extends ClaimVersionBase {
  id: string;
  claim_id: string;
  version: number;
  author_id: string;
  created_at: string;
}

export interface ClaimCreate extends ClaimVersionBase {
  investigation_id: string;
  origin?: ClaimOrigin;
}

export interface ClaimUpdate {
  text?: string;
  claim_type?: ClaimType;
  metric?: string;
  value_raw?: string | null;
  value_numeric?: number | null;
  value_precision?: number;
  period?: Period;
  scope?: string;
  basis?: string;
  change_note: string;
}

export interface ClaimResponse {
  id: string;
  investigation_id: string;
  current_version: number;
  state: ClaimState;
  origin: ClaimOrigin;
  created_by: string;
  created_at: string;
  active_version: ClaimVersionResponse;
  all_versions?: ClaimVersionResponse[];
  latest_finding_id?: string | null;
}

// ---------------------------------------------------------------------------
// Calculation Schemas (Architecture §5.1, §9, §10.3)
// ---------------------------------------------------------------------------

export interface CalculationStep {
  label: string;
  expr: string;
  values: Record<string, unknown>;
  result: string;
}

export interface CalculationTolerance {
  half_ulp: string;
  approx_multiplier: number;
  min_abs_tol: string;
  effective_tol: string;
}

export interface CalculationResponse {
  id: string;
  formula_id: string;
  input_fact_ids: string[];
  steps: CalculationStep[];
  result_value: string;
  result_unit: string;
  tolerance: CalculationTolerance;
  derived: boolean;
  engine_version: string;
}

// ---------------------------------------------------------------------------
// Evidence Link Schemas (Architecture §5.1, FR-7.x)
// ---------------------------------------------------------------------------

export type EvidenceStance = 'supports' | 'opposes' | 'neutral' | 'not_comparable';

export interface EvidenceLinkResponse {
  id: string;
  finding_id: string;
  fact_id: string;
  stance: EvidenceStance;
  document_id: string;
  document_filename?: string | null;
  locator: Locator;
  note?: string | null;
  fact?: FactResponse | null;
}

// ---------------------------------------------------------------------------
// Finding & Verdict Schemas (Architecture §5.1, §10, FR-5–7)
// ---------------------------------------------------------------------------

export type Verdict = 'Consistent' | 'Conflicting' | 'Inconclusive';
export type Severity = 'Match' | 'NearMiss' | 'Material';
export type ConclusionStrength = 'disproved' | 'confirmed' | 'indicative' | 'insufficient';

export interface ComparabilityCheckResult {
  check_name: string;
  passed: boolean;
  resolved_by?: string | null;
  reason_code?: string | null;
  details?: string | null;
}

export interface FindingResponse {
  id: string;
  claim_version_id: string;
  claim_id?: string | null;
  verdict: Verdict;
  severity?: Severity | null;
  conclusion_strength: ConclusionStrength;
  cap_reasons: string[];
  reason_codes: string[];
  comparability_checks: ComparabilityCheckResult[];
  narrative: string;
  superseded: boolean;
  calculation_id?: string | null;
  calculation?: CalculationResponse | null;
  evidence_links: EvidenceLinkResponse[];
  created_at: string;
  engine_version: string;
}
