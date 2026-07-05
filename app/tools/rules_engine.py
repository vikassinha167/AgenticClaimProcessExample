from __future__ import annotations

import logging
from typing import Any

import requests

from app.config import Settings
from app.models import CodingResult, ValidationResult


class RulesEngine:
    def __init__(self, settings: Settings) -> None:
        self.logger = logging.getLogger("RulesEngine")
        self.settings = settings
        self.base_url = f"{settings.mcp_host}:{settings.mcp_port}"

    async def fetch_policy(self, claim_id: str) -> dict[str, Any]:
        url = f"http://{self.base_url}/policies"
        self.logger.debug("Fetching MCP policies from %s", url)
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()

    async def validate_claim(self, coding_result: CodingResult, policy: dict[str, Any]) -> ValidationResult:
        violations: list[str] = []
        allowed_procedures = set(policy.get("allowed_procedures", []))

        for item in coding_result.mapped_items:
            if item["procedure_code"] and item["procedure_code"] not in allowed_procedures:
                violations.append(f"Unauthorized procedure code {item['procedure_code']}")

            if item["amount"] > policy.get("max_line_item_amount", 10000):
                violations.append(f"Line item amount exceeds policy maximum: {item['amount']}")

        valid = not violations
        return ValidationResult(
            claim_id=coding_result.claim_id,
            valid=valid,
            violations=violations,
            policy_reference=policy.get("policy_id", "mcp-policy-v1"),
            details={"policy": policy},
        )
