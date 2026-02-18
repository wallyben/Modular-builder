"""
test_regression_snapshot.py
Snapshot comparison tests for deterministic engine output.
Snapshots are stored inline — no external files required.
Each test verifies that a known input produces an exact expected output shape
and that key fields do not drift between runs.
"""
from __future__ import annotations

import json

import pytest

from core.engine import ExecutionEngine, MAX_RETRIES
from core.schemas import EngineState, PlanResponse, ToolCall
from tests.conftest import StubAdapter


# ── Snapshot: happy-path run result shape ────────────────────────────────────

HAPPY_PATH_SNAPSHOT = {
    "final_state": "DONE",
    "success": True,
    "retry_count": 0,
    "model_used": "stub-model-1.0",
    "plan_task": "Snapshot test task",
    "first_transition_to": "PLAN",
    "last_transition_to": "DONE",
    "tool_calls_count": 1,
    "tool_name": "echo",
    "tool_success": True,
    "validation_failures_count": 0,
}


class TestHappyPathSnapshot:
    @pytest.fixture
    def result(self, minimal_registry):
        plan = PlanResponse(
            task="Snapshot test task",
            steps=["Echo the task description"],
            tool_calls=[ToolCall(tool_name="echo", payload={"message": "Snapshot test task"})],
            reasoning="Regression snapshot plan.",
        )
        adapter = StubAdapter(plan=plan)
        engine = ExecutionEngine(adapter=adapter, registry=minimal_registry)
        return engine.run("Snapshot test task")

    def test_final_state_matches_snapshot(self, result):
        assert result.final_state.value == HAPPY_PATH_SNAPSHOT["final_state"]

    def test_success_matches_snapshot(self, result):
        assert result.success == HAPPY_PATH_SNAPSHOT["success"]

    def test_retry_count_matches_snapshot(self, result):
        assert result.retry_count == HAPPY_PATH_SNAPSHOT["retry_count"]

    def test_model_used_matches_snapshot(self, result):
        assert result.model_used == HAPPY_PATH_SNAPSHOT["model_used"]

    def test_plan_task_matches_snapshot(self, result):
        assert result.plan.task == HAPPY_PATH_SNAPSHOT["plan_task"]

    def test_first_transition_matches_snapshot(self, result):
        assert result.state_transitions[0].to_state.value == HAPPY_PATH_SNAPSHOT["first_transition_to"]

    def test_last_transition_matches_snapshot(self, result):
        assert result.state_transitions[-1].to_state.value == HAPPY_PATH_SNAPSHOT["last_transition_to"]

    def test_tool_calls_count_matches_snapshot(self, result):
        assert len(result.tool_calls) == HAPPY_PATH_SNAPSHOT["tool_calls_count"]

    def test_tool_name_matches_snapshot(self, result):
        assert result.tool_calls[0].tool_name == HAPPY_PATH_SNAPSHOT["tool_name"]

    def test_tool_success_matches_snapshot(self, result):
        assert result.tool_calls[0].success == HAPPY_PATH_SNAPSHOT["tool_success"]

    def test_no_validation_failures_matches_snapshot(self, result):
        assert len(result.validation_failures) == HAPPY_PATH_SNAPSHOT["validation_failures_count"]


# ── Snapshot: failure / ceiling exhaustion shape ──────────────────────────────

FAILURE_SNAPSHOT = {
    "final_state": "FAILED",
    "success": False,
    "retry_count": MAX_RETRIES + 1,
    "model_used": "stub-model-1.0",
    "patch_transitions_count": MAX_RETRIES,
}


class TestFailureSnapshot:
    @pytest.fixture
    def result(self, minimal_registry):
        plan = PlanResponse(
            task="Always broken",
            steps=["Use missing tool"],
            tool_calls=[ToolCall(tool_name="does_not_exist", payload={})],
            reasoning="Snapshot failure plan.",
        )
        adapter = StubAdapter(plan=plan)
        engine = ExecutionEngine(adapter=adapter, registry=minimal_registry)
        return engine.run("Always broken")

    def test_final_state_matches_snapshot(self, result):
        assert result.final_state.value == FAILURE_SNAPSHOT["final_state"]

    def test_success_matches_snapshot(self, result):
        assert result.success == FAILURE_SNAPSHOT["success"]

    def test_retry_count_matches_snapshot(self, result):
        assert result.retry_count == FAILURE_SNAPSHOT["retry_count"]

    def test_model_used_matches_snapshot(self, result):
        assert result.model_used == FAILURE_SNAPSHOT["model_used"]

    def test_patch_transition_count_matches_snapshot(self, result):
        patch_count = sum(
            1 for t in result.state_transitions if t.to_state == EngineState.PATCH
        )
        assert patch_count == FAILURE_SNAPSHOT["patch_transitions_count"]


# ── Serialisation stability ───────────────────────────────────────────────────

class TestSerialisationStability:
    """RunResult must serialise to/from JSON without data loss."""

    def test_run_result_json_round_trip(self, minimal_registry):
        plan = PlanResponse(
            task="Round-trip task",
            steps=["Echo"],
            tool_calls=[ToolCall(tool_name="echo", payload={"message": "rt"})],
            reasoning="Round-trip test.",
        )
        adapter = StubAdapter(plan=plan)
        engine = ExecutionEngine(adapter=adapter, registry=minimal_registry)
        result = engine.run("Round-trip task")

        serialised = result.model_dump_json()
        restored = result.model_validate_json(serialised)

        assert restored.run_id == result.run_id
        assert restored.final_state == result.final_state
        assert restored.success == result.success
        assert restored.model_used == result.model_used

    def test_run_result_dict_has_required_keys(self, minimal_registry):
        plan = PlanResponse(
            task="Dict key test",
            steps=["Echo"],
            tool_calls=[ToolCall(tool_name="echo", payload={"message": "k"})],
            reasoning="Key test.",
        )
        adapter = StubAdapter(plan=plan)
        engine = ExecutionEngine(adapter=adapter, registry=minimal_registry)
        result = engine.run("Dict key test")

        d = result.model_dump()
        required_keys = {
            "run_id", "task", "final_state", "success",
            "retry_count", "model_used", "state_transitions",
            "validation_failures", "tool_calls", "log_path",
        }
        assert required_keys.issubset(d.keys())
