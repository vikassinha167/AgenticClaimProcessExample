from __future__ import annotations

import asyncio
import json
import logging
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.config import get_settings
from app.evaluations.evaluator import EvaluationPipeline
from app.logger import configure_logging


async def main() -> None:
    configure_logging()
    logger = logging.getLogger("eval_run")
    settings = get_settings()

    sample_path = Path(__file__).resolve().parents[1] / "app" / "data" / "sample" / "claim_sample.json"
    with sample_path.open("r", encoding="utf-8") as file:
        claim = json.load(file)

    evaluator = EvaluationPipeline(settings)
    evaluation = await evaluator.evaluate(claim_id=claim["claim_id"], trace={"sample": claim})
    logger.info("Evaluation results: %s", evaluation)


if __name__ == "__main__":
    asyncio.run(main())
