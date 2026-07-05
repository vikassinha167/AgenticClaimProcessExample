from __future__ import annotations

import logging
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

import uvicorn # type: ignore
from app.config import get_settings
from app.logger import configure_logging

def main() -> None:
    configure_logging()
    logger = logging.getLogger("run_mcp")
    settings = get_settings()
    logger.info("Starting MCP server on %s:%s", settings.mcp_host, settings.mcp_port)
    uvicorn.run("app.mcp.server:app", host=settings.mcp_host, port=settings.mcp_port, log_level=settings.log_level.lower())

if __name__ == "__main__":
    main()
