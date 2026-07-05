from __future__ import annotations

import logging
from typing import Any

from app.config import Settings
from app.models import CodingResult, ValidationResult
from app.tools.rules_engine import RulesEngine


class ValidationAgent:
    SYSTEM_PROMPT = (
        "You are the Validation Agent. Verify claim business rules and policy constraints using MCP metadata. "
        "Return a validation summary with any violations and policy references for claims processing."
    )

    def __init__(self, settings: Settings) -> None:
        self.logger = logging.getLogger("ValidationAgent")
        self.rules_engine = RulesEngine(settings)

    async def validate(self, coding_result: CodingResult) -> ValidationResult:
        self.logger.debug("ValidationAgent validating claim %s", coding_result.claim_id)
        policy = await self.rules_engine.fetch_policy(coding_result.claim_id)
        validation = await self.rules_engine.validate_claim(coding_result, policy)
        return validation
