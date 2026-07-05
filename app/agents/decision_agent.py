from __future__ import annotations

import logging

from app.config import Settings
from app.models import CodingResult, DecisionOutcome, DecisionResult, FraudResult, ValidationResult
from app.tools.foundry_sdk import FoundryClient
from app.tools.openai_client import FoundryOpenAIClient


class DecisionAgent:
    SYSTEM_PROMPT = (
        "You are the Decision Agent. Use validation results, fraud risk, and enterprise policy to select a final outcome. "
        "Return exactly one of Approve, Reject, or Flag for Review with a decision score and rationale."
    )

    def __init__(self, settings: Settings) -> None:
        self.logger = logging.getLogger("DecisionAgent")
        self.settings = settings
        self.openai = FoundryOpenAIClient(settings)
        self.foundry = FoundryClient(settings)

    async def decide(self, coding_result: CodingResult, validation_result: ValidationResult, fraud_result: FraudResult) -> DecisionResult:
        prompt = self._build_prompt(coding_result, validation_result, fraud_result)
        self.logger.debug("DecisionAgent prompt built for %s", coding_result.claim_id)
        response = await self.openai.generate(
            prompt,
            agent_name="DecisionAgent",
            agent_version=self.settings.azure_foundry_agent_version,
        )
        decision = self._parse_response(response, coding_result.claim_id)
        return decision

    def _build_prompt(self, coding_result: CodingResult, validation_result: ValidationResult, fraud_result: FraudResult) -> str:
        return (
            f"{self.SYSTEM_PROMPT}\n"
            f"Claim ID: {coding_result.claim_id}\n"
            f"Validation: {validation_result.valid} Violations: {validation_result.violations}\n"
            f"Fraud Score: {fraud_result.fraud_score} Flagged: {fraud_result.flagged} Patterns: {fraud_result.patterns}\n"
            f"Coding Summary: {coding_result.reasoning}\n"
            "Output format:\n{\"decision\": \"approve|reject|flag_for_review\", \"score\": 0.00, \"rationale\": \"...\"}"
        )

    def _parse_response(self, response: str, claim_id: str) -> DecisionResult:
        import json

        try:
            cleaned_response = (
                                    response
                                    .replace("```json", "")
                                    .replace("```", "")
                                    .strip()
                                )
            payload = json.loads(cleaned_response)
            outcome = DecisionOutcome(payload.get("decision"))
            return DecisionResult(
                claim_id=claim_id,
                decision=outcome,
                rationale=payload.get("rationale", "No rationale provided."),
                score=float(payload.get("score", 0.0)),
                trace={},
            )
        except Exception as ex:
            self.logger.error("Error parsing decision response: %s", ex)
            self.logger.warning("Failed to parse decision response, applying fallback logic")
            return DecisionResult(
                claim_id=claim_id,
                decision=DecisionOutcome.review,
                rationale="Fallback review path due to response parse failure.",
                score=0.5,
                trace={},
            )
