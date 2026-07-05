from __future__ import annotations

import logging
from typing import Any

from openai import OpenAI
from azure.ai.projects import AIProjectClient
from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential

from app.config import Settings

class FoundryOpenAIClient:
    def __init__(self, settings: Settings) -> None:
        self.logger = logging.getLogger("FoundryOpenAIClient")
        self.settings = settings
        openai_key = settings.get_secret_value(settings.azure_openai_key_secret_name)
        # self.client = OpenAI(
        #     endpoint=str(settings.azure_ai_services_endpoint),
        #     credential=AzureKeyCredential(openai_key),
        # )
        self.client = OpenAI(
            base_url=str(settings.azure_ai_services_endpoint),
            api_key=AzureKeyCredential(openai_key),
        )

    def _get_project_openai_client(self):
        credential = DefaultAzureCredential()
        project_client = AIProjectClient(endpoint=str(self.settings.azure_foundry_endpoint), credential=credential)
        return project_client.get_openai_client()

    async def generate(
        self,
        prompt: str,
        max_tokens: int = 1200,
        agent_name: str | None = None,
        agent_version: str | None = None,
    ) -> str:
        if agent_name:
            openai_client = self._get_project_openai_client()
            agent_reference: dict[str, str] = {
                "name": agent_name,
                "type": "agent_reference",
            }
            if agent_version:
                agent_reference["version"] = agent_version

            response = openai_client.responses.create(
                input=[{"role": "user", "content": prompt}],
                extra_body={"agent_reference": agent_reference},
            )
            self.logger.debug("Foundry agent response for %s", agent_name)
            return self._extract_response_text(response)

        response = self.client.chat.completions.create(
            engine=self.settings.azure_openai_deployment,
            messages=[{"role": "system", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0.0,
        )
        self.logger.debug("OpenAI response usage: %s", response.usage)
        return response.choices[0].message.content.strip()

    def _extract_response_text(self, response: Any) -> str:
        if hasattr(response, "output_text"):
            return response.output_text
        if hasattr(response, "output") and response.output:
            first_output = response.output[0]
            if hasattr(first_output, "content") and first_output.content:
                first_content = first_output.content[0]
                return getattr(first_content, "text", str(first_content))
        return str(response)
