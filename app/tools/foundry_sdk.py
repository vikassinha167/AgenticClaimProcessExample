from __future__ import annotations

import logging
from typing import Any

import requests
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition
from azure.identity import DefaultAzureCredential

from app.config import Settings


class FoundryClient:
    def __init__(self, settings: Settings) -> None:
        self.logger = logging.getLogger("FoundryClient")
        self.settings = settings
        self.base_url = str(settings.azure_foundry_endpoint).rstrip("/")
        self.project_id = settings.azure_foundry_project_id
        self.azure_foundry_key_secret_name = settings.azure_foundry_key_secret_name
        self.foundry_api_key = None

        if self.azure_foundry_key_secret_name:
            try:
                self.foundry_api_key = settings.get_secret_value(self.azure_foundry_key_secret_name)
            except Exception as exc:
                self.logger.warning(
                    "Unable to load Foundry API key from Key Vault secret '%s': %s",
                    self.azure_foundry_key_secret_name,
                    exc,
                )

    @property
    def headers(self) -> dict[str, str]:
        credential = DefaultAzureCredential()

        token = credential.get_token(
            "https://ai.azure.com/.default"
        )
        # token = self.foundry_api_key or self._get_fallback_token()
        headers = {
                        "Authorization": f"Bearer {token.token}",
                        "Content-Type": "application/json"
                    }
        return headers

    def _get_fallback_token(self) -> str:
        self.logger.debug("Acquiring Azure AD token for Foundry endpoint using DefaultAzureCredential")
        credential = DefaultAzureCredential()
        access_token = credential.get_token(self.settings.azure_foundry_scope)
        return access_token.token

    def register_agent(self, agent_name: str, agent_type: str, metadata: dict[str, Any]) -> dict[str, Any]:
        self.logger.debug("Creating/updating Foundry agent version for %s", agent_name)

        credential = DefaultAzureCredential()
        project_client = AIProjectClient(endpoint=str(self.settings.azure_foundry_endpoint), credential=credential)

        instructions = metadata.get("description", "")
        if agent_type:
            instructions = f"You are a {agent_type} agent. {instructions}".strip()

        definition = PromptAgentDefinition(
            kind="prompt",
            model=self.settings.azure_openai_deployment,
            instructions=instructions,
        )

        version = project_client.agents.create_version(
            agent_name=agent_name,
            definition=definition,
            description=metadata.get("description"),
            metadata={"type": str(agent_type)} if agent_type else None,
        )

        return {"name": agent_name, "version": version.version, "id": version.id}

    def register_agents(self, agents: list[dict[str, Any]]) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for agent in agents:
            name = agent.get("name")
            agent_type = agent.get("type", "")
            metadata = agent.get("metadata", {})
            result = self.register_agent(agent_name=name, agent_type=agent_type, metadata=metadata)
            results.append(result)
        return results

    async def log_trace(self, claim_id: str, step: str, payload: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.base_url}/traces"
        body = {"claim_id": claim_id, "step": step, "payload": payload}
        self.logger.debug("Logging Foundry trace: %s %s", claim_id, step)
        response = requests.post(url, json=body, headers=self.headers, timeout=10)
        response.raise_for_status()
        return response.json()

    async def store_evaluation(self, claim_id: str, metrics: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.base_url}/evaluations"
        body = {"claim_id": claim_id, "metrics": metrics}
        self.logger.debug("Storing Foundry evaluation for %s", claim_id)
        response = requests.post(url, json=body, headers=self.headers, timeout=10)
        response.raise_for_status()
        return response.json()
