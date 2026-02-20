from __future__ import annotations


class LLMAdapter:
    def generate(self, messages: list[dict], schema: type | None = None) -> dict:
        raise NotImplementedError
