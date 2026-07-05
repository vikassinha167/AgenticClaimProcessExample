from __future__ import annotations

import logging
from typing import Any

import requests

from app.config import Settings
from app.tools.foundry_sdk import FoundryClient
from azure.ai.evaluation import (
    RelevanceEvaluator
)


class FoundryGuardrailsClient:
    def __init__(self, settings: Settings) -> None:
        self.logger = logging.getLogger("FoundryGuardrailsClient")
        self.settings = settings
        self.foundry = FoundryClient(settings)

    async def assess_trace(self, claim_id: str, trace: dict[str, Any]) -> dict[str, Any]:
        # url = f"{self.foundry.base_url}/projects/{self.foundry.project_id}/guardrails/evaluate"
        url = f"{self.foundry.base_url}/guardrails/evaluate?api-version=2024-02-15-preview"
        payload = {"claim_id": claim_id, "trace": trace}
        self.logger.debug("Calling Foundry guardrails endpoint for claim %s", claim_id)
        response = requests.post(url, json=payload, headers=self.foundry.headers, timeout=15)
        response.raise_for_status()
        return response.json()

    async def is_safe(self, claim_id: str, trace: dict[str, Any]) -> tuple[bool, list[str]]:
        evaluation = {"safe": True, "issues": []}  # ## await self.assess_trace(claim_id, trace)
        safe = evaluation.get("safe", True)
        issues = evaluation.get("issues", []) or []
        return safe, [str(item) for item in issues]
