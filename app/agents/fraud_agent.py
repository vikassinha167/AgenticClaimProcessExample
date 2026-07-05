from __future__ import annotations

import logging
from typing import List

from app.config import Settings
from app.models import CodingResult, FraudResult, ValidationResult
from app.tools.ai_search import FraudSearchClient
from app.tools.external_fraud_api import ExternalFraudApiClient
from app.tools.foundry_sdk import FoundryClient


class FraudDetectionAgent:
    SYSTEM_PROMPT = (
        "You are the Fraud Detection Agent. Correlate claim features, policy exceptions, and search evidence to assess fraud risk. "
        "Return a score, confidence, and any pattern names that justify a flag."
    )

    def __init__(self, settings: Settings) -> None:
        self.logger = logging.getLogger("FraudDetectionAgent")
        self.search_client = FraudSearchClient(settings)
        self.external_api = ExternalFraudApiClient(settings)
        self.foundry = FoundryClient(settings)

    async def assess(self, coding_result: CodingResult, validation_result: ValidationResult) -> FraudResult:
        self.logger.debug("FraudDetectionAgent assessing %s", coding_result.claim_id)
        patterns = await self.search_client.query_patterns(coding_result)
        external = await self.external_api.score_claim(coding_result)
        score = float(external.get("fraud_score", 0.0))
        flagged = score >= 0.75 or bool(patterns)
        confidence = min(1.0, score * 0.9 + (len(patterns) * 0.05))
        fraud_result = FraudResult(
            claim_id=coding_result.claim_id,
            flagged=flagged,
            fraud_score=score,
            patterns=patterns,
            confidence=confidence,
            api_response=external,
        )
        # await self.foundry.log_trace(coding_result.claim_id, "fraud_patterns", {"patterns": patterns, "external": external})
        return fraud_result
