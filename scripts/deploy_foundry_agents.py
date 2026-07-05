from __future__ import annotations

import logging
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.config import get_settings
from app.logger import configure_logging
from app.tools.foundry_sdk import FoundryClient


AGENT_REGISTRY = [
    {"name": "ExtractionAgent", "type": "extraction", "metadata": {"description": "Document Intelligence extraction agent."}},
    {"name": "CodingAgent", "type": "coding", "metadata": {"description": "ICD/CPT mapping and code reasoning agent."}},
    {"name": "ValidationAgent", "type": "validation", "metadata": {"description": "Policy and rules validation agent."}},
    {"name": "FraudDetectionAgent", "type": "fraud", "metadata": {"description": "Hybrid fraud detection agent using ML, RAG, and heuristics."}},
    {"name": "DecisionAgent", "type": "decision", "metadata": {"description": "Final claim decision agent."}},
    {"name": "CriticAgent", "type": "critic", "metadata": {"description": "Quality and safety review agent."}},
    {"name": "EvaluationAgent", "type": "evaluation", "metadata": {"description": "Claim workflow quality evaluation agent."}},
]

def main() -> None:
    configure_logging()
    logger = logging.getLogger("deploy_foundry_agents")
    settings = get_settings()

    logger.warning(
        "Foundry agent registration via raw REST is not supported for this endpoint. "
        "Please register agents using the Azure Foundry portal or an official SDK.")
    logger.info("Configured Foundry endpoint: %s", settings.azure_foundry_endpoint)
    logger.info("Foundry project ID: %s", settings.azure_foundry_project_id)

    foundry = FoundryClient(settings)
    for agent in AGENT_REGISTRY:
        try:
            result = foundry.register_agent(
                agent_name=agent["name"],
                agent_type=agent["type"],
                metadata=agent["metadata"],
            )
            logger.info(
                "Registered agent %s: version=%s id=%s",
                result["name"], result["version"], result["id"],
            )
        except Exception as exc:
            logger.exception("Failed to register Foundry agent %s: %s", agent["name"], exc)


if __name__ == "__main__":
    main()
