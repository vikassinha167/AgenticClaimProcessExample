from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from app.config import Settings
from app.models import ClaimPayload, ExtractionResult
from app.tools.document_intelligence import DocumentIntelligenceClient


class ExtractionAgent:
    SYSTEM_PROMPT = (
        "You are the Extraction Agent for healthcare claims. "
        "Use Azure Document Intelligence to extract structured claim fields, patient metadata, and line items. "
        "Return normalized fields with dates, provider IDs, billed amounts, diagnoses, and service lines."
    )

    def __init__(self, settings: Settings) -> None:
        self.logger = logging.getLogger("ExtractionAgent")
        self.client = DocumentIntelligenceClient(settings)

    async def extract(self, claim_payload: ClaimPayload) -> ExtractionResult:
        self.logger.debug("ExtractionAgent running for claim %s", claim_payload.claim_id)
        if claim_payload.source == claim_payload.source.document:
            raw_text, normalized = await self.client.extract_from_document(claim_payload.metadata.get("document_path"))
            claim = self._normalize_payload(normalized)
            return ExtractionResult(claim=claim, raw_text=raw_text, extracted_fields=normalized)

        raw_json = claim_payload.dict()
        claim = self._normalize_payload(raw_json)
        return ExtractionResult(claim=claim, raw_text="", extracted_fields=raw_json)

    def _normalize_payload(self, payload: dict[str, Any]) -> ClaimPayload:
        if isinstance(payload, ClaimPayload):
            return payload

        if "services" in payload and not isinstance(payload["services"], list):
            payload["services"] = []

        return ClaimPayload.parse_obj(payload)
