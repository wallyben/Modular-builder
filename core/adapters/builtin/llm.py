from __future__ import annotations

from adapters.openai_adapter import OpenAIAdapter
from core.schemas import Step

_default_openai = OpenAIAdapter()


def llm_openai_adapter(step: Step) -> dict:
    messages = step.params.get("messages", [])
    return _default_openai.generate(messages)


def llm_anthropic_adapter(step: Step) -> dict:
    from adapters.anthropic_adapter import AnthropicAdapter
    adapter = AnthropicAdapter()
    messages = step.params.get("messages", [])
    return adapter.generate(messages)
