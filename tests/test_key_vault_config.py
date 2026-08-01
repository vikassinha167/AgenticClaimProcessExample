import unittest
from unittest.mock import MagicMock, patch

from app.config import Settings


class KeyVaultConfigTests(unittest.TestCase):
    def test_get_secret_value_uses_key_vault_client_with_default_credential(self) -> None:
        settings = Settings(
            azure_ai_services_endpoint="https://example.openai.azure.com/",
            azure_openai_deployment="gpt-4o",
            azure_foundry_project_id="project-id",
            azure_foundry_endpoint="https://example.services.ai.azure.com/api/projects/project-id",
            azure_document_intelligence_endpoint="https://example.cognitiveservices.azure.com/",
            azure_language_endpoint="https://example.cognitiveservices.azure.com/",
            azure_key_vault_url="https://example.vault.azure.net/",
            fraud_api_url="http://127.0.0.1:8000/fraud-score",
        )

        fake_credential = object()
        fake_secret_client = MagicMock()
        fake_secret_client.get_secret.return_value.value = "resolved-from-key-vault"

        with patch("app.config.DefaultAzureCredential", return_value=fake_credential) as mock_credential, patch(
            "app.config.SecretClient", return_value=fake_secret_client
        ) as mock_secret_client:
            secret_value = settings.get_secret_value("AzureOpenAIKey")

        self.assertEqual(secret_value, "resolved-from-key-vault")
        mock_credential.assert_called_once_with()
        mock_secret_client.assert_called_once_with(vault_url="https://example.vault.azure.net/", credential=fake_credential)
        fake_secret_client.get_secret.assert_called_once_with("AzureOpenAIKey")

    def test_validate_required_secrets_raises_when_any_secret_missing(self) -> None:
        settings = Settings(
            azure_ai_services_endpoint="https://example.openai.azure.com/",
            azure_openai_deployment="gpt-4o",
            azure_foundry_project_id="project-id",
            azure_foundry_endpoint="https://example.services.ai.azure.com/api/projects/project-id",
            azure_document_intelligence_endpoint="https://example.cognitiveservices.azure.com/",
            azure_language_endpoint="https://example.cognitiveservices.azure.com/",
            azure_key_vault_url="https://example.vault.azure.net/",
            fraud_api_url="http://127.0.0.1:8000/fraud-score",
        )

        with patch("app.config.Settings.get_secret_value", side_effect=RuntimeError("secret missing")):
            with self.assertRaisesRegex(RuntimeError, "Unable to resolve required Key Vault secrets"):
                settings.validate_required_secrets()


if __name__ == "__main__":
    unittest.main()
