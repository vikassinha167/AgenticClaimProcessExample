from __future__ import annotations


class FraudSearchClient:
    def __init__(self, settings: object) -> None:  # pragma: no cover - compatibility shim
        self.settings = settings

    async def query_patterns(self, coding_result: object) -> list[str]:
        return []
