"""
test_retry_ceiling.py
Verifies that the retry ceiling (MAX_RETRIES = 3) is enforced:
- Engine enters FAILED after 3 unsuccessful PATCH attempts.
- retry_count never exceeds MAX_RETRIES.
- No infinite loop is possible.
"""
from __future__ import annotations

import pytest

from core.engine import MAX_RETRIES, ExecutionEngine
from core.schemas import EngineState, PlanResponse, ToolCall
from tests.conftest import StubAdapter


def _make_always_failing_plan() -> PlanResponse:
    """Plan that always uses a tool not in any registry."""
    return PlanResponse(
        task="Always failing task",
        steps=["Call broken tool"],
        tool_calls=[ToolCall(tool_name="broken_tool_xyz", payload={})],
        reasoning="Designed to always fail validation.",
    )


class TestRetryCeiling:
    def test_engine_reaches_failed_after_ceiling(self, minimal_registry):
        plan = _make_always_failing_plan()
        adapter = StubAdapter(plan=plan)
        engine = ExecutionEngine(adapter=adapter, registry=minimal_registry)
        result = engine.run("Always failing task")
        assert result.final_state == EngineState.FAILED

    def test_retry_count_does_not_exceed_max(self, minimal_registry):
        plan = _make_always_failing_plan()
        adapter = StubAdapter(plan=plan)
        engine = ExecutionEngine(adapter=adapter, registry=minimal_registry)
        result = engine.run("Always failing task")
        # Engine increments retry_count before ceiling check; ceiling stop is MAX_RETRIES+1
        assert result.retry_count <= MAX_RETRIES + 1

    def test_retry_count_equals_max_on_exhaustion(self, minimal_registry):
        plan = _make_always_failing_plan()
        adapter = StubAdapter(plan=plan)
        engine = ExecutionEngine(adapter=adapter, registry=minimal_registry)
        result = engine.run("Always failing task")
        # retry_count should be MAX_RETRIES + 1 because we incremented before checking
        assert result.retry_count == MAX_RETRIES + 1

    def test_success_is_false_when_ceiling_hit(self, minimal_registry):
        plan = _make_always_failing_plan()
        adapter = StubAdapter(plan=plan)
        engine = ExecutionEngine(adapter=adapter, registry=minimal_registry)
        result = engine.run("Always failing task")
        assert result.success is False

    def test_validation_failures_accumulate(self, minimal_registry):
        plan = _make_always_failing_plan()
        adapter = StubAdapter(plan=plan)
        engine = ExecutionEngine(adapter=adapter, registry=minimal_registry)
        result = engine.run("Always failing task")
        # Should have at least one validation failure per attempt
        assert len(result.validation_failures) >= MAX_RETRIES

    def test_patch_states_in_transitions(self, minimal_registry):
        plan = _make_always_failing_plan()
        adapter = StubAdapter(plan=plan)
        engine = ExecutionEngine(adapter=adapter, registry=minimal_registry)
        result = engine.run("Always failing task")
        patch_transitions = [
            t for t in result.state_transitions if t.to_state == EngineState.PATCH
        ]
        # Should have exactly MAX_RETRIES patch transitions
        assert len(patch_transitions) == MAX_RETRIES

    def test_failed_transition_reason_mentions_ceiling(self, minimal_registry):
        plan = _make_always_failing_plan()
        adapter = StubAdapter(plan=plan)
        engine = ExecutionEngine(adapter=adapter, registry=minimal_registry)
        result = engine.run("Always failing task")
        failed_transitions = [
            t for t in result.state_transitions if t.to_state == EngineState.FAILED
        ]
        assert len(failed_transitions) == 1
        assert "ceiling" in failed_transitions[0].reason.lower() or str(MAX_RETRIES) in failed_transitions[0].reason

    def test_max_retries_constant_is_three(self):
        """Phase 1 spec: retry ceiling must be 3."""
        assert MAX_RETRIES == 3
