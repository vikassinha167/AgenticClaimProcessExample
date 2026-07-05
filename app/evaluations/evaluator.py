from __future__ import annotations

import logging
from typing import Any

from app.config import Settings
from app.models import DecisionResult, EvaluationMetrics
from app.tools.openai_client import FoundryOpenAIClient


class EvaluationPipeline:
    def __init__(self, settings: Settings) -> None:
        self.logger = logging.getLogger("EvaluationPipeline")
        self.openai = FoundryOpenAIClient(settings)
        self.settings = settings

    async def evaluate(self, claim_id: str, trace: dict[str, Any]) -> EvaluationMetrics:
        self.logger.debug("Running evaluation for %s", claim_id)
        prompt = self._build_evaluation_prompt(claim_id, trace)
        response = await self.openai.generate(
            prompt,
            max_tokens=600,
            agent_name="EvaluationAgent",
            agent_version=self.settings.azure_foundry_agent_version,
        )
        values = self._parse_response(response)
        return EvaluationMetrics(claim_id=claim_id, **values, metadata={"evaluation_text": response})

    def _build_evaluation_prompt(self, claim_id: str, trace: dict[str, Any]) -> str:
        return (
            f"Evaluate the claim processing workflow for claim {claim_id}. "
            "Provide groundedness, relevance, safety, and fraud confidence as numeric values between 0.0 and 1.0. "
            f"Use the internal trace: {trace}.\n"
            "Return JSON object with keys groundedness, relevance, safety, fraud_confidence. No need to include explanations or any text outside these keys in the JSON."
        )

    def _parse_response(self, response: str) -> dict[str, Any]:
        import json

        self.logger.debug("Evaluation response: %s", response)
        try:
            cleaned_response = (
                                    response
                                    .replace("```json", "")
                                    .replace("```", "")
                                    .strip()
                                )
            payload = json.loads(cleaned_response)
            return {
                "groundedness": float(payload.get("groundedness", 0.0)),
                "relevance": float(payload.get("relevance", 0.0)),
                "safety": float(payload.get("safety", 0.0)),
                "fraud_confidence": float(payload.get("fraud_confidence", 0.0)),
            }
        except Exception as ex:
            self.logger.warning("Failed to parse evaluation response; using defaults: %s", ex)
            return {"groundedness": 0.75, "relevance": 0.8, "safety": 0.9, "fraud_confidence": 0.5}
