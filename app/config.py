from __future__ import annotations

from functools import cached_property

from azure.identity import AzureCliCredential, ChainedTokenCredential, ManagedIdentityCredential # type: ignore
from azure.keyvault.secrets import SecretClient # type: ignore
from pydantic import Field, HttpUrl # type: ignore
from pydantic_settings import BaseSettings # type: ignore


class Settings(BaseSettings):
    # Azure environment
    azure_ai_services_endpoint: HttpUrl = Field(..., env="AZURE_AI_SERVICES_ENDPOINT")
    azure_openai_deployment: str = Field(..., env="AZURE_OPENAI_DEPLOYMENT")

    azure_search_endpoint: HttpUrl = Field(..., env="AZURE_SEARCH_ENDPOINT")
    azure_search_index: str = Field(..., env="AZURE_SEARCH_INDEX")

    azure_foundry_project_id: str = Field(..., env="AZURE_FOUNDRY_PROJECT_ID")
    azure_foundry_endpoint: HttpUrl = Field(..., env="AZURE_FOUNDRY_ENDPOINT")
    azure_foundry_scope: str = Field(default="https://cognitiveservices.azure.com/.default", env="AZURE_FOUNDRY_SCOPE")
    azure_foundry_agent_version: str | None = Field(None, env="AZURE_FOUNDRY_AGENT_VERSION")

    azure_document_intelligence_endpoint: HttpUrl = Field(..., env="AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
    azure_document_intelligence_key_secret_name: str | None = Field(None, env="AZURE_DOCUMENT_INTELLIGENCE_KEY_SECRET_NAME")

    azure_key_vault_url: HttpUrl = Field(..., env="AZURE_KEY_VAULT_URL")
    azure_key_vault_client_id: str | None = Field(None, env="AZURE_KEY_VAULT_CLIENT_ID")

    azure_openai_key_secret_name: str = Field("AzureOpenAIKey", env="AZURE_OPENAI_KEY_SECRET_NAME")
    azure_form_recognizer_key_secret_name: str = Field("AzureFormRecognizerKey", env="AZURE_FORM_RECOGNIZER_KEY_SECRET_NAME")
    azure_search_key_secret_name: str = Field("AzureSearchKey", env="AZURE_SEARCH_KEY_SECRET_NAME")
    azure_foundry_key_secret_name: str = Field("AzureFoundryKey", env="AZURE_FOUNDRY_KEY_SECRET_NAME")

    fraud_api_url: HttpUrl = Field(..., env="FRAUD_API_URL")
    fraud_api_key: str | None = Field(None, env="FRAUD_API_KEY")

    mcp_host: str = Field(default="0.0.0.0", env="MCP_HOST")
    mcp_port: int = Field(default=8000, env="MCP_PORT")

    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    environment: str = Field(default="production", env="ENVIRONMENT")

    @cached_property
    def key_vault_client(self) -> SecretClient:
        credentials = []
        if self.azure_key_vault_client_id:
            credentials.append(ManagedIdentityCredential(client_id=self.azure_key_vault_client_id))
        else:
            credentials.append(ManagedIdentityCredential())
        credentials.append(AzureCliCredential())
        credential = ChainedTokenCredential(*credentials)
        return SecretClient(vault_url=str(self.azure_key_vault_url), credential=credential)

    def get_secret_value(self, secret_name: str) -> str:
        secret = self.key_vault_client.get_secret(secret_name)
        return secret.value

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


def get_settings() -> Settings:
    return Settings()
