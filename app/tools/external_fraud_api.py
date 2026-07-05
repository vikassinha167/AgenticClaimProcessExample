from __future__ import annotations

import logging
from typing import Any

import requests

from app.config import Settings


class ExternalFraudApiClient:
    def __init__(self, settings: Settings) -> None:
        self.logger = logging.getLogger("ExternalFraudApiClient")
        self.settings = settings

    async def score_claim(self, coding_result: "app.models.CodingResult") -> dict[str, Any]:
        payload = {
            "claim_id": coding_result.claim_id,
            "items": [
                {
                    "procedure_code": item.get("procedure_code") if isinstance(item, dict) else None,
                    "amount": item.get("amount") if isinstance(item, dict) else None,
                    "provider": item.get("provider") if isinstance(item, dict) else None,
                    "diagnosis": item.get("diagnosis") if isinstance(item, dict) else None,
                }
                for item in coding_result.mapped_items
            ],
        }
        headers = {"Content-Type": "application/json"}
        if self.settings.fraud_api_key:
            headers["Authorization"] = f"Bearer {self.settings.fraud_api_key}"

        response = requests.post(self.settings.fraud_api_url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        self.logger.debug("Fraud API response: %s", response.text)
        return response.json()
