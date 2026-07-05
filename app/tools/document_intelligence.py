from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from azure.ai.documentintelligence.aio import DocumentIntelligenceClient as AzureDocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential

from app.config import Settings


class DocumentIntelligenceClient:
    def __init__(self, settings: Settings) -> None:
        self.logger = logging.getLogger("DocumentIntelligenceClient")
        self.settings = settings
        credential = self._get_credential()
        self.client = AzureDocumentIntelligenceClient(
            endpoint=str(settings.azure_document_intelligence_endpoint),
            credential=credential,
        )

    def _get_credential(self):
        if self.settings.azure_document_intelligence_key_secret_name:
            key = self.settings.get_secret_value(self.settings.azure_document_intelligence_key_secret_name)
            return AzureKeyCredential(key)

        self.logger.debug("Using DefaultAzureCredential for Document Intelligence")
        return DefaultAzureCredential()

    async def extract_from_document(self, document_path: str | None) -> tuple[str, dict[str, Any]]:
        if not document_path:
            raise ValueError("document_path is required for document extractions")

        document_file = Path(document_path)
        if not document_file.exists():
            raise FileNotFoundError(f"Document not found: {document_path}")

        with document_file.open("rb") as source:
            poller = await self.client.begin_analyze_document("prebuilt-document", source)
            result = await poller.result()

        raw_text = "\n".join([p.content for p in result.pages or []])
        fields: dict[str, Any] = {"pages": len(result.pages or []), "lines": raw_text}

        for idx, paragraph in enumerate(result.paragraphs or []):
            fields[f"paragraph_{idx}"] = paragraph.content

        if result.key_value_pairs:
            for kv in result.key_value_pairs:
                key = kv.key.content if kv.key else None
                value = kv.value.content if kv.value else None
                if key and value:
                    fields[key] = value

        return raw_text, fields
