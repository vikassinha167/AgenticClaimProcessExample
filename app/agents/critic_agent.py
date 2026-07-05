from __future__ import annotations

import logging

from app.config import Settings
from app.models import CriticResult, DecisionResult
from app.tools.foundry_guardrails import FoundryGuardrailsClient
from app.tools.foundry_sdk import FoundryClient
from app.tools.openai_client import FoundryOpenAIClient


class CriticAgent:
    SYSTEM_PROMPT = (
        "You are the Critic Agent. Validate the final decision for groundedness, relevance, and safety. "
        "Highlight any issues or biased assertions and ensure the response follows healthcare responsible AI guidelines."
    )

    def __init__(self, settings: Settings) -> None:
        self.logger = logging.getLogger("CriticAgent")
        self.openai = FoundryOpenAIClient(settings)
        self.guardrails = FoundryGuardrailsClient(settings)
        self.foundry = FoundryClient(settings)
        self.settings = settings

    async def review(self, decision_result: DecisionResult, trace: dict[str, object]) -> CriticResult:
        prompt = self._build_prompt(decision_result, trace)
        response = await self.openai.generate(
            prompt,
            agent_name="CriticAgent",
            agent_version=self.settings.azure_foundry_agent_version,
        )
        issues = self._parse_issues(response)
        safe, guardrail_issues = await self.guardrails.is_safe(decision_result.claim_id, trace)
        issues.extend([issue for issue in guardrail_issues if issue not in issues])
        critic = CriticResult(
            claim_id=decision_result.claim_id,
            grounded=not bool(issues),
            relevant=True,
            safe=safe,
            issues=issues,
            reviewer_notes=response,
        )
        return critic

    def _build_prompt(self, decision_result: DecisionResult, trace: dict[str, object]) -> str:
        return (
            f"{self.SYSTEM_PROMPT}\n"
            f"Decision: {decision_result.decision}\n"
            f"Rationale: {decision_result.rationale}\n"
            f"Trace: {trace}\n"
            "Return a list of any issues in JSON format."
        )

    def _parse_issues(self, response: str) -> list[str]:
        import json

        try:
            cleaned_response = (
                                    response
                                    .replace("```json", "")
                                    .replace("```", "")
                                    .strip()
                                )
            payload = json.loads(cleaned_response)
            if isinstance(payload, list):
                return [str(item) for item in payload]
            if isinstance(payload, dict) and "issues" in payload:
                return [str(item) for item in payload["issues"]]
        except Exception as ex:
            self.logger.error("Error parsing critic issues: %s", ex)
            self.logger.warning("Failed to parse critic response, falling back to original content")
            return []
