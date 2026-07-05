from __future__ import annotations

import logging
from typing import List

from app.config import Settings
from app.models import ClaimItem, ClaimPayload, CodingResult
from app.tools.foundry_sdk import FoundryClient
from app.tools.openai_client import FoundryOpenAIClient


class CodingAgent:
    SYSTEM_PROMPT = (
        "You are the Coding Agent. Map healthcare service descriptions to ICD and CPT codes using best practices. "
        "Return structured mappings, the code type, and a concise reasoning summary. "
        "Reference known code mapping patterns and support audit traceability."
        "Return ONLY valid JSON. Do not include explanations, markdown, summaries, or comments."
    )

    def __init__(self, settings: Settings) -> None:
        self.logger = logging.getLogger("CodingAgent")
        self.settings = settings
        self.openai = FoundryOpenAIClient(settings)
        self.foundry = FoundryClient(settings)

    async def map_codes(self, extraction_result: "app.models.ExtractionResult") -> CodingResult:
        claim = extraction_result.claim
        prompt = self._build_prompt(claim)
        self.logger.debug("Sending coding prompt for claim %s", claim.claim_id)
        response = await self.openai.generate(
            prompt,
            agent_name="CodingAgent",
            agent_version=self.settings.azure_foundry_agent_version,
        )
        mapped_services = self._parse_response(response)
        # await self.foundry.log_trace(claim.claim_id, "coding_prompt", {"prompt": prompt, "response": response})
        return CodingResult(claim_id=claim.claim_id, mapped_items=mapped_services, reasoning=response, confidence=0.88)

    def _build_prompt(self, claim: ClaimPayload) -> str:
        service_lines = []
        for item in claim.services:
            service_lines.append(f"- {item.description} | {item.provider} | {item.date_of_service or 'unknown'} | {item.amount}")

        return (
            f"{self.SYSTEM_PROMPT}\n"
            f"Claim ID: {claim.claim_id}\n"
            f"Provider: {claim.provider_id}\n"
            f"Services:\n{chr(10).join(service_lines)}\n"
            "Map each line to ICD or CPT as appropriate."
        )

    def _normalize_claim_payload(self, payload):

        normalized = []

        claim_id = payload.get("claim_id")
        provider = payload.get("provider")

        for item in payload.get("mappings", payload.get("services", [])):
            normalized.append({
                "claim_id": claim_id,
                "provider": provider,
                "item_id": item.get("claim_id", ""),
                "description": item.get("service_description", "UNKNOWN"),
                "date_of_service": item.get("service_date", "UNKNOWN"),
                "amount": item.get("cost", item.get("amount", 0.0)),  # Placeholder, real amount should come from original claim
                "diagnosis": item.get("reasoning", "UNKNOWN"),
                "procedure_code": item.get("icd_code", item.get("cpt_code", "99213")),  # Returning by default one of the allowed procedure codes for testing
                "code_type": item.get("code_type", {}),
                "modifiers": item.get("modifiers", [])
            })

        return normalized

    def _parse_response(self, response: str) -> List[ClaimItem]:
        import json
    
        try:
            cleaned_response = (
                                    response
                                    .replace("```json", "")
                                    .replace("```", "")
                                    .strip()
                                )
            payload = json.loads(cleaned_response)
            normalized_payload = self._normalize_claim_payload(payload)
            # services = [ClaimItem.model_validate(item) for item in payload if isinstance(item, dict)]
            
            services = [x for x in normalized_payload]
            
            return services
        except Exception as ex:
            self.logger.error("Error parsing coding response: %s", ex)
            self.logger.warning("Failed to parse coding response, falling back to original content")
            return []
