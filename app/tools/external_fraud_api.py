from __future__ import annotations

import json
import logging
from typing import Any

import requests
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from app.config import Settings


class ExternalFraudApiClient:
    MCP_TOOL_NAME = "fraud_score_fraud_score_post"

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

        if self._uses_mcp_transport():
            return await self._score_claim_via_mcp(payload)

        return await self._score_claim_via_http(payload)

    def _uses_mcp_transport(self) -> bool:
        return str(self.settings.fraud_api_url).rstrip("/").endswith("/mcp")

    async def _score_claim_via_mcp(self, payload: dict[str, Any]) -> dict[str, Any]:
        self.logger.info("Calling fraud MCP tool via %s", self.settings.fraud_api_url)
        async with streamable_http_client(str(self.settings.fraud_api_url)) as (read_stream, write_stream, _):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result = await session.call_tool(self.MCP_TOOL_NAME, payload)

        if getattr(result, "isError", False):
            raise RuntimeError(f"MCP fraud tool returned an error: {result}")

        content_text = ""
        for item in getattr(result, "content", []) or []:
            if hasattr(item, "text") and item.text:
                content_text += item.text

        if not content_text:
            raise RuntimeError("MCP fraud tool returned no text content")

        try:
            parsed = json.loads(content_text)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Unable to parse MCP fraud tool response: {content_text}") from exc

        self.logger.debug("Fraud MCP response: %s", parsed)
        return parsed

    async def _score_claim_via_http(self, payload: dict[str, Any]) -> dict[str, Any]:
        headers = {"Content-Type": "application/json"}
        if self.settings.fraud_api_key:
            headers["Authorization"] = f"Bearer {self.settings.fraud_api_key}"

        response = requests.post(self.settings.fraud_api_url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        self.logger.debug("Fraud API response: %s", response.text)
        return response.json()
