from __future__ import annotations

import json
import logging
from typing import Any

from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential

from app.config import Settings


class LanguagePiiClient:
    def __init__(self, settings: Settings) -> None:
        self.logger = logging.getLogger("LanguagePiiClient")
        self.settings = settings
        self.client = TextAnalyticsClient(
            endpoint=str(settings.azure_language_endpoint),
            credential=self._get_credential(),
        )

    def _get_credential(self):
        if not self.settings.azure_language_key_secret_name:
            raise ValueError(
                "AZURE_LANGUAGE_KEY_SECRET_NAME must be configured to fetch the Azure Language key from Key Vault"
            )

        key = self.settings.get_secret_value(self.settings.azure_language_key_secret_name)
        return AzureKeyCredential(key)

    def analyze_claim(self, claim: dict[str, Any]) -> dict[str, Any]:
        claim_text = json.dumps(claim, indent=2, default=str)
        response = self.client.recognize_pii_entities(
            documents=[claim_text],
            language="en",
        )[0]

        if response.is_error:
            raise RuntimeError(f"Azure Language PII analysis failed: {response.error.message}")

        entities = [
            {
                "category": entity.category,
                "subcategory": entity.subcategory,
                "text": entity.text,
                "offset": entity.offset,
                "length": entity.length,
                "confidence_score": entity.confidence_score,
            }
            for entity in response.entities
        ]

        return {
            "has_pii": bool(entities),
            "entity_count": len(entities),
            "entities": entities,
            "redacted_claim": response.redacted_text,
        }