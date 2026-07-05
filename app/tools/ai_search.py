from __future__ import annotations

import logging
from typing import List

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient

from app.config import Settings
from app.models import CodingResult


class FraudSearchClient:
    def __init__(self, settings: Settings) -> None:
        self.logger = logging.getLogger("FraudSearchClient")
        search_api_key = settings.get_secret_value(settings.azure_search_key_secret_name)
        self.client = SearchClient(
            endpoint=str(settings.azure_search_endpoint),
            index_name=settings.azure_search_index,
            credential=AzureKeyCredential(search_api_key),
        )

    async def query_patterns(self, coding_result: CodingResult) -> List[str]:
        query_text = self._build_query(coding_result)
        self.logger.debug("Querying Azure AI Search for %s", query_text)
        results = self.client.search(query_text, top=5)
        patterns: list[str] = []
        for item in results:
            title = item.get("title") or item.get("pattern")
            if title:
                patterns.append(str(title))
        return patterns

    def _build_query(self, coding_result: CodingResult) -> str:
        codes = [item["procedure_code"] for item in coding_result.mapped_items if item["procedure_code"]]
        return " ".join(codes + [coding_result.reasoning])
