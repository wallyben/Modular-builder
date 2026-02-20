from __future__ import annotations

import json
import os
import urllib.request

from adapters.base import LLMAdapter

_STUB = {"role": "assistant", "content": "stub: no OPENAI_API_KEY set", "model": "stub"}


class OpenAIAdapter(LLMAdapter):
    def __init__(self, model: str = "gpt-4o-mini") -> None:
        self._key = os.environ.get("OPENAI_API_KEY", "")
        self._model = model

    def generate(self, messages: list[dict], schema: type | None = None) -> dict:
        if not self._key:
            return _STUB

        payload = json.dumps({"model": self._model, "messages": messages}).encode()
        req = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._key}",
            },
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = json.loads(resp.read())

        choice = body["choices"][0]["message"]
        return {"role": choice["role"], "content": choice["content"], "model": body["model"]}
