"""
test_state_machine.py
Verifies deterministic state machine transitions:
INIT → PLAN → EXECUTE → VALIDATE → DONE (happy path)
INIT → PLAN → EXECUTE → VALIDATE → PATCH → EXECUTE → VALIDATE → DONE (patch path)
INIT → PLAN → FAILED (plan parse failure)
"""
from __future__ import annotations

import json
from typing import List, Optional
from unittest.mock import patch

import pytest

from adapters.base import LLMAdapter
from core.engine import ExecutionEngine
from core.schemas import EngineState, PlanResponse, ToolCall
from tests.conftest import StubAdapter


class TestStateMachineHappyPath:
    """Engine completes DONE in one pass with a valid echo plan."""

    def test_final_state_is_done(self, stub_adapter, minimal_registry):
        engine = ExecutionEngine(adapter=stub_adapter, registry=minimal_registry)
        result = engine.run("Test task")
        assert result.final_state == EngineState.DONE

    def test_success_flag_true(self, stub_adapter, minimal_registry):
        engine = ExecutionEngine(adapter=stub_adapter, registry=minimal_registry)
        result = engine.run("Test task")
        assert result.success is True

    def test_zero_retries_on_happy_path(self, stub_adapter, minimal_registry):
        engine = ExecutionEngine(adapter=stub_adapter, registry=minimal_registry)
        result = engine.run("Test task")
        assert result.retry_count == 0

    def test_state_sequence_contains_required_states(self, stub_adapter, minimal_registry):
        engine = ExecutionEngine(adapter=stub_adapter, registry=minimal_registry)
        result = engine.run("Test task")
        visited = [t.to_state for t in result.state_transitions]
        assert EngineState.PLAN in visited
        assert EngineState.EXECUTE in visited
        assert EngineState.VALIDATE in visited
        assert EngineState.DONE in visited

    def test_no_failed_state_on_happy_path(self, stub_adapter, minimal_registry):
        engine = ExecutionEngine(adapter=stub_adapter, registry=minimal_registry)
        result = engine.run("Test task")
        visited = [t.to_state for t in result.state_transitions]
        assert EngineState.FAILED not in visited

    def test_plan_is_populated(self, stub_adapter, minimal_registry):
        engine = ExecutionEngine(adapter=stub_adapter, registry=minimal_registry)
        result = engine.run("Test task")
        assert result.plan is not None
        assert result.plan.task == "Test task"

    def test_model_recorded_correctly(self, stub_adapter, minimal_registry):
        engine = ExecutionEngine(adapter=stub_adapter, registry=minimal_registry)
        result = engine.run("Test task")
        assert result.model_used == "stub-model-1.0"

    def test_log_path_set(self, stub_adapter, minimal_registry, tmp_path):
        engine = ExecutionEngine(adapter=stub_adapter, registry=minimal_registry)
        result = engine.run("Test task")
        assert result.log_path.endswith(".json")

    def test_tool_calls_recorded(self, stub_adapter, minimal_registry):
        engine = ExecutionEngine(adapter=stub_adapter, registry=minimal_registry)
        result = engine.run("Test task")
        assert len(result.tool_calls) >= 1
        assert result.tool_calls[0].tool_name == "echo"


class TestStateMachinePlanFailure:
    """If the LLM returns unparseable JSON in PLAN, engine goes to FAILED."""

    def test_final_state_is_failed(self, failing_adapter, minimal_registry):
        engine = ExecutionEngine(adapter=failing_adapter, registry=minimal_registry)
        result = engine.run("Any task")
        assert result.final_state == EngineState.FAILED

    def test_success_is_false(self, failing_adapter, minimal_registry):
        engine = ExecutionEngine(adapter=failing_adapter, registry=minimal_registry)
        result = engine.run("Any task")
        assert result.success is False

    def test_failed_state_in_transitions(self, failing_adapter, minimal_registry):
        engine = ExecutionEngine(adapter=failing_adapter, registry=minimal_registry)
        result = engine.run("Any task")
        visited = [t.to_state for t in result.state_transitions]
        assert EngineState.FAILED in visited


class TestStateMachinePatchPath:
    """Engine enters PATCH state when a tool fails, then retries."""

    def test_patch_state_entered_on_tool_failure(self, echo_plan, minimal_registry):
        """Use a plan that references a non-existent tool to force failure."""
        failing_plan = PlanResponse(
            task="Fail task",
            steps=["Use missing tool"],
            tool_calls=[ToolCall(tool_name="nonexistent_tool", payload={})],
            reasoning="Force failure",
        )
        adapter = StubAdapter(plan=failing_plan)
        engine = ExecutionEngine(adapter=adapter, registry=minimal_registry)
        result = engine.run("Fail task")
        visited = [t.to_state for t in result.state_transitions]
        assert EngineState.PATCH in visited

    def test_transitions_are_ordered_correctly(self, stub_adapter, minimal_registry):
        """State transitions must appear in causal order."""
        engine = ExecutionEngine(adapter=stub_adapter, registry=minimal_registry)
        result = engine.run("Test task")
        # The first transition must land on PLAN
        first_dest = result.state_transitions[0].to_state
        assert first_dest == EngineState.PLAN
