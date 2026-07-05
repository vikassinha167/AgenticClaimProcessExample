from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, HttpUrl, model_validator

class ClaimSource(str, Enum):
    document = "document"
    json = "json"


class ProcedureCodeType(str, Enum):
    icd = "ICD"
    cpt = "CPT"


class ClaimItem(BaseModel):
    item_id: str
    description: str
    date_of_service: Optional[str] = None
    amount: float
    provider: str
    diagnosis: Optional[str] = None
    procedure_code: Optional[str] = None
    code_type: Optional[str] = None
    modifiers: Optional[List[str]] = Field(default_factory=list)


class ClaimPayload(BaseModel):
    claim_id: str
    patient_id: str
    provider_id: str
    billed_amount: float
    services: List[ClaimItem]
    metadata: Dict[str, Any] = {}
    source: ClaimSource = ClaimSource.json


class ExtractionResult(BaseModel):
    claim: ClaimPayload
    raw_text: str
    extracted_fields: Dict[str, Any]


class CodingResult(BaseModel):
    claim_id: str
    mapped_items: List[Dict] = []
    reasoning: str
    confidence: float


class ValidationResult(BaseModel):
    claim_id: str
    valid: bool
    violations: List[str] = []
    policy_reference: Optional[str]
    details: Dict[str, Any] = {}


class FraudResult(BaseModel):
    claim_id: str
    flagged: bool
    fraud_score: float
    patterns: List[str] = []
    confidence: float
    api_response: Dict[str, Any] = {}


class DecisionOutcome(str, Enum):
    approve = "approve"
    reject = "reject"
    review = "flag_for_review"

class DecisionResult(BaseModel):
    claim_id: str
    decision: DecisionOutcome
    rationale: str
    score: float
    trace: Dict[str, Any] = {}

class CriticResult(BaseModel):
    claim_id: str
    grounded: bool
    relevant: bool
    safe: bool
    issues: List[str] = []
    reviewer_notes: Optional[str]

class EvaluationMetrics(BaseModel):
    claim_id: str
    groundedness: float
    relevance: float
    safety: float
    fraud_confidence: float
    metadata: Dict[str, Any] = {}
