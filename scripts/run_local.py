from __future__ import annotations

import asyncio
import json, os
import logging
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.agents.orchestrator import ClaimsOrchestrator
from app.config import get_settings
from app.logger import configure_logging
from app.models import ClaimPayload

async def main() -> None:
    configure_logging()
    logger = logging.getLogger("run_local")
    settings = get_settings()

    sample_path = Path(__file__).resolve().parents[1] / "app" / "data" / "sample" / "claim_sample.json"
    logger.info("Loading sample claim from %s", sample_path)

    with sample_path.open("r", encoding="utf-8") as input_file:
        sample_claim = ClaimPayload.model_validate(json.load(input_file))

    orchestrator = ClaimsOrchestrator(settings)
    result = await orchestrator.process_claim(sample_claim)
    logger.info("Final decision: %s", result.decision)
    logger.info("Decision trace: %s", json.dumps(result.trace, indent=2))

    # -------------------------------
    # Save JSON to Output folder
    # -------------------------------

    # Create Output directory if it doesn't exist
    output_dir = "Output"
    os.makedirs(output_dir, exist_ok=True)

    # Create a safe filename
    file_name = f"{result.claim_id}_{result.decision}.json"
    file_path = os.path.join(output_dir, file_name)

    # Write JSON to file
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(result.model_dump(mode="json"), f, indent=2, default=str)

    print(f"\n JSON saved to: {file_path}")
    
if __name__ == "__main__":
    asyncio.run(main())
