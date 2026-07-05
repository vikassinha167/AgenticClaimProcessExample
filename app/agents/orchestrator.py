from __future__ import annotations

import asyncio
import logging
from typing import Any

from app.config import Settings
from app.agents.coding_agent import CodingAgent
from app.agents.critic_agent import CriticAgent
from app.agents.decision_agent import DecisionAgent
from app.agents.extraction_agent import ExtractionAgent
from app.agents.fraud_agent import FraudDetectionAgent
from app.agents.validation_agent import ValidationAgent
from app.evaluations.evaluator import EvaluationPipeline
from app.models import ClaimPayload, DecisionResult
from app.tools.foundry_sdk import FoundryClient


class ClaimsOrchestrator:
    def __init__(self, settings: Settings) -> None:
        self.logger = logging.getLogger("ClaimsOrchestrator")
        self.settings = settings
        self.foundry = FoundryClient(settings)
        self.planner = PlannerAgent()
        self.extraction_agent = ExtractionAgent(settings)
        self.coding_agent = CodingAgent(settings)
        self.validation_agent = ValidationAgent(settings)
        self.fraud_agent = FraudDetectionAgent(settings)
        self.decision_agent = DecisionAgent(settings)
        self.critic_agent = CriticAgent(settings)
        self.evaluator = EvaluationPipeline(settings)

    async def process_claim(self, claim_payload: ClaimPayload) -> DecisionResult:
        self.logger.info("Starting claim orchestration for %s", claim_payload.claim_id)
        trace: dict[str, Any] = {}

        workflow = await self.planner.plan(claim_payload)
        self.logger.info("Planner selected workflow: %s", workflow)
        trace["workflow"] = workflow

        extraction = await self.extraction_agent.extract(claim_payload)
        trace["extraction"] = extraction.dict(exclude_none=True)

        coding = await self.coding_agent.map_codes(extraction)
        trace["coding"] = coding.dict(exclude_none=True)

        validation = await self.validation_agent.validate(coding)
        trace["validation"] = validation.dict(exclude_none=True)

        fraud = await self.fraud_agent.assess(coding, validation)
        trace["fraud"] = fraud.dict(exclude_none=True)

        decision = await self.decision_agent.decide(coding, validation, fraud)
        trace["decision"] = decision.dict(exclude_none=True)

        critic = await self.critic_agent.review(decision, trace)
        trace["critic"] = critic.dict(exclude_none=True)

        evaluation = await self.evaluator.evaluate(claim_payload.claim_id, trace)
        trace["evaluation"] = evaluation.dict()

        self.logger.info("Completed claim orchestration for %s", claim_payload.claim_id)
        decision.trace = trace
        return decision


class PlannerAgent:
    async def plan(self, claim_payload: ClaimPayload) -> dict[str, Any]:
        steps = [
            "extract",
            "code_mapping",
            "validation",
            "fraud_detection",
            "decision",
            "critique",
            "evaluation",
        ]
        return {"steps": steps, "source": claim_payload.source}
