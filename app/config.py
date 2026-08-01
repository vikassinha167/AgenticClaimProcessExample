from __future__ import annotations

from functools import cached_property

from azure.identity import DefaultAzureCredential # type: ignore
from azure.keyvault.secrets import SecretClient # type: ignore
from pydantic import Field, HttpUrl # type: ignore
from pydantic_settings import BaseSettings, SettingsConfigDict # type: ignore


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    # Azure environment
    azure_ai_services_endpoint: HttpUrl = Field(..., env="AZURE_AI_SERVICES_ENDPOINT")
    azure_openai_deployment: str = Field(..., env="AZURE_OPENAI_DEPLOYMENT")

    azure_foundry_project_id: str = Field(..., env="AZURE_FOUNDRY_PROJECT_ID")
    azure_foundry_endpoint: HttpUrl = Field(..., env="AZURE_FOUNDRY_ENDPOINT")
    azure_foundry_scope: str = Field(default="https://cognitiveservices.azure.com/.default", env="AZURE_FOUNDRY_SCOPE")
    azure_foundry_agent_version: str | None = Field(None, env="AZURE_FOUNDRY_AGENT_VERSION")

    azure_document_intelligence_endpoint: HttpUrl = Field(..., env="AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
    azure_document_intelligence_key_secret_name: str | None = Field(None, env="AZURE_DOCUMENT_INTELLIGENCE_KEY_SECRET_NAME")

    azure_language_endpoint: HttpUrl = Field(..., env="AZURE_LANGUAGE_ENDPOINT")
    azure_language_key_secret_name: str | None = Field(None, env="AZURE_LANGUAGE_KEY_SECRET_NAME")

    azure_key_vault_url: HttpUrl = Field(..., env="AZURE_KEY_VAULT_URL")

    azure_openai_key_secret_name: str = Field("AzureOpenAIKey", env="AZURE_OPENAI_KEY_SECRET_NAME")
    azure_foundry_key_secret_name: str = Field("AzureFoundryKey", env="AZURE_FOUNDRY_KEY_SECRET_NAME")

    fraud_api_url: HttpUrl = Field(..., env="FRAUD_API_URL")
    fraud_api_key: str | None = Field(None, env="FRAUD_API_KEY")

    mcp_host: str = Field(default="0.0.0.0", env="MCP_HOST")
    mcp_port: int = Field(default=8000, env="MCP_PORT")

    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    environment: str = Field(default="production", env="ENVIRONMENT")

    @cached_property
    def key_vault_client(self) -> SecretClient:
        credential = DefaultAzureCredential()
        return SecretClient(vault_url=str(self.azure_key_vault_url), credential=credential)

    def get_secret_value(self, secret_name: str) -> str:
        if not secret_name:
            raise ValueError("A Key Vault secret name must be configured")

        secret = self.key_vault_client.get_secret(secret_name)
        if not secret.value:
            raise RuntimeError(f"Secret '{secret_name}' was not returned with a value from Key Vault")
        return secret.value

    def get_openai_key(self) -> str:
        return self.get_secret_value(self.azure_openai_key_secret_name)

    def get_document_intelligence_key(self) -> str:
        if not self.azure_document_intelligence_key_secret_name:
            raise ValueError("AZURE_DOCUMENT_INTELLIGENCE_KEY_SECRET_NAME must be configured")
        return self.get_secret_value(self.azure_document_intelligence_key_secret_name)

    def get_language_key(self) -> str:
        if not self.azure_language_key_secret_name:
            raise ValueError("AZURE_LANGUAGE_KEY_SECRET_NAME must be configured")
        return self.get_secret_value(self.azure_language_key_secret_name)

    def get_foundry_key(self) -> str:
        if not self.azure_foundry_key_secret_name:
            raise ValueError("AZURE_FOUNDRY_KEY_SECRET_NAME must be configured")
        return self.get_secret_value(self.azure_foundry_key_secret_name)

    def validate_required_secrets(self) -> None:
        secret_names = [
            self.azure_openai_key_secret_name,
            self.azure_document_intelligence_key_secret_name,
            self.azure_language_key_secret_name,
            self.azure_foundry_key_secret_name,
        ]
        secret_names = [name for name in secret_names if name]

        failures: list[str] = []
        for secret_name in secret_names:
            try:
                self.get_secret_value(secret_name)
            except Exception as exc:  # pragma: no cover - exercised in runtime path
                failures.append(f"{secret_name}: {exc}")

        if failures:
            raise RuntimeError("Unable to resolve required Key Vault secrets: " + "; ".join(failures))


def get_settings() -> Settings:
    settings = Settings()
    settings.validate_required_secrets()
    return settings
