"""Calculation and verification math trace schemas."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CalculationStep(BaseModel):
    label: str = Field(..., description="Human-readable step name e.g. 'Previous Year Revenue', 'Difference'")
    expr: str = Field(..., description="Formula algebraic expression e.g. '(current - previous) / previous * 100'")
    values: Dict[str, Any] = Field(default_factory=dict, description="Resolved numeric inputs in expression")
    result: str = Field(..., description="Computed intermediate result as string")


class CalculationTolerance(BaseModel):
    half_ulp: str = Field(..., description="Half unit in last place based on precision (e.g. '0.5' for 18%, '0.05' for 18.2%)")
    approx_multiplier: float = Field(default=1.0, description="Tolerance multiplier for hedged claims (2.0 if hedged)")
    min_abs_tol: str = Field(default="0.1", description="Configured minimum absolute tolerance")
    effective_tol: str = Field(..., description="Final combined tolerance value applied")


class CalculationResponse(BaseModel):
    id: str
    formula_id: str = Field(..., description="Formula used e.g. 'growth_yoy', 'gross_margin', 'net_margin'")
    input_fact_ids: List[str] = Field(default_factory=list, description="IDs of facts used as inputs")
    steps: List[CalculationStep] = Field(default_factory=list, description="Step-by-step arithmetic trace")
    result_value: str = Field(..., description="Computed final value as string")
    result_unit: str = Field(default="percent", description="Computed unit: 'percent', 'currency', 'ratio'")
    tolerance: CalculationTolerance
    derived: bool = Field(default=False, description="True if any input fact was algebraically derived (e.g. Q1-Q4 -> FY)")
    engine_version: str = Field(default="1.0.0", description="Deterministic engine release version")

    class Config:
        from_attributes = True
