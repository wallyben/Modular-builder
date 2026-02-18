"""
Shared fixtures for the Modular AI Execution Engine test suite.
All fixtures are deterministic. No external API calls.
"""
from __future__ import annotations

import json
from typing import List, Optional
from unittest.mock import MagicMock

import pytest

from adapters.base import LLMAdapter
from core.schemas import PlanResponse, ToolCall
from tools.base import BaseTool
from tools.echo_tool import EchoTool
from tools.registry import ToolRegistry


# ── Stub LLM adapter ──────────────────────────────────────────────────────────

class StubAdapter(LLMAdapter):
    """
    Deterministic stub adapter.
    Returns the plan injected at construction time.
    Accepts optional response_override for failure injection tests.
    """

    def __init__(
        self,
        plan: PlanResponse | None = None,
        response_override: str | None = None,
    ) -> None:
        self._plan = plan
        self._response_override = response_override
        self._model = "stub-model-1.0"

    @property
    def model_id(self) -> str:
        return self._model

    def generate(
        self,
        messages: List[dict],
        tools: Optional[List[dict]] = None,
        schema: Optional[dict] = None,
    ) -> dict:
        if self._response_override is not None:
            return {"content": self._response_override, "model": self._model, "finish_reason": "stop"}
        content = self._plan.model_dump_json() if self._plan else "{}"
        return {"content": content, "model": self._model, "finish_reason": "stop"}


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def echo_plan() -> PlanResponse:
    """A minimal valid plan that only calls the echo tool."""
    return PlanResponse(
        task="Test task",
        steps=["Echo the task"],
        tool_calls=[ToolCall(tool_name="echo", payload={"message": "hello"})],
        reasoning="Test plan with echo tool.",
    )


@pytest.fixture
def stub_adapter(echo_plan) -> StubAdapter:
    """Stub adapter pre-loaded with the echo plan."""
    return StubAdapter(plan=echo_plan)


@pytest.fixture
def failing_adapter() -> StubAdapter:
    """Stub adapter that returns an unparseable response (failure injection)."""
    return StubAdapter(response_override="NOT_VALID_JSON{{{{")


@pytest.fixture
def minimal_registry() -> ToolRegistry:
    """Registry with only the echo tool registered."""
    registry = ToolRegistry()
    registry.register("echo", EchoTool())
    return registry


@pytest.fixture
def full_registry() -> ToolRegistry:
    """Registry with all built-in tools registered."""
    from tools.registry import build_default_registry
    return build_default_registry()
