from __future__ import annotations

import json
import os
import urllib.request

from adapters.base import LLMAdapter

_STUB = {"role": "assistant", "content": "stub: no ANTHROPIC_API_KEY set", "model": "stub"}


class AnthropicAdapter(LLMAdapter):
    def __init__(self, model: str = "claude-haiku-4-5-20251001") -> None:
        self._key = os.environ.get("ANTHROPIC_API_KEY", "")
        self._model = model

    def generate(self, messages: list[dict], schema: type | None = None) -> dict:
        if not self._key:
            return _STUB

        system_msgs = [m["content"] for m in messages if m.get("role") == "system"]
        user_msgs = [m for m in messages if m.get("role") != "system"]

        payload = json.dumps({
            "model": self._model,
            "max_tokens": 1024,
            "messages": user_msgs,
            **({"system": system_msgs[0]} if system_msgs else {}),
        }).encode()

        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "x-api-key": self._key,
                "anthropic-version": "2023-06-01",
            },
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = json.loads(resp.read())

        return {"role": body["role"], "content": body["content"][0]["text"], "model": body["model"]}
