"""
test_schema_validation.py
Validates all Pydantic schemas: field enforcement, type rejection,
required field detection, and round-trip serialisation.
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from core.schemas import (
    EngineState,
    ExecutionResponse,
    PlanResponse,
    RunResult,
    StateTransition,
    ToolCall,
    ValidationResponse,
)


# ── ToolCall ──────────────────────────────────────────────────────────────────

class TestToolCall:
    def test_valid_tool_call(self):
        tc = ToolCall(tool_name="echo", payload={"message": "hi"})
        assert tc.tool_name == "echo"
        assert tc.payload == {"message": "hi"}

    def test_missing_tool_name_raises(self):
        with pytest.raises(ValidationError):
            ToolCall(payload={"message": "hi"})

    def test_missing_payload_raises(self):
        with pytest.raises(ValidationError):
            ToolCall(tool_name="echo")


# ── PlanResponse ──────────────────────────────────────────────────────────────

class TestPlanResponse:
    def test_valid_plan(self):
        plan = PlanResponse(
            task="Do something",
            steps=["step1", "step2"],
            tool_calls=[ToolCall(tool_name="echo", payload={"message": "x"})],
            reasoning="Because we can.",
        )
        assert plan.task == "Do something"
        assert len(plan.steps) == 2
        assert len(plan.tool_calls) == 1
        assert plan.plan_id  # auto-generated UUID

    def test_plan_id_auto_generated(self):
        p1 = PlanResponse(task="t", steps=[], reasoning="r")
        p2 = PlanResponse(task="t", steps=[], reasoning="r")
        assert p1.plan_id != p2.plan_id

    def test_tool_calls_defaults_to_empty(self):
        plan = PlanResponse(task="t", steps=[], reasoning="r")
        assert plan.tool_calls == []

    def test_missing_task_raises(self):
        with pytest.raises(ValidationError):
            PlanResponse(steps=[], reasoning="r")

    def test_missing_reasoning_raises(self):
        with pytest.raises(ValidationError):
            PlanResponse(task="t", steps=[])

    def test_steps_must_be_list(self):
        with pytest.raises(ValidationError):
            PlanResponse(task="t", steps="not-a-list", reasoning="r")

    def test_round_trip_json(self):
        plan = PlanResponse(task="t", steps=["s1"], reasoning="r")
        restored = PlanResponse.model_validate_json(plan.model_dump_json())
        assert restored.task == plan.task
        assert restored.plan_id == plan.plan_id


# ── ExecutionResponse ─────────────────────────────────────────────────────────

class TestExecutionResponse:
    def test_valid_success(self):
        er = ExecutionResponse(
            plan_id="pid-1",
            tool_name="echo",
            success=True,
            output="hello",
        )
        assert er.success is True
        assert er.error == ""

    def test_valid_failure(self):
        er = ExecutionResponse(
            plan_id="pid-1",
            tool_name="shell",
            success=False,
            output="",
            error="command not found",
        )
        assert er.success is False
        assert er.error == "command not found"

    def test_missing_plan_id_raises(self):
        with pytest.raises(ValidationError):
            ExecutionResponse(tool_name="echo", success=True, output="x")


# ── ValidationResponse ────────────────────────────────────────────────────────

class TestValidationResponse:
    def test_passed_validation(self):
        vr = ValidationResponse(plan_id="pid", passed=True)
        assert vr.issues == []
        assert vr.patch_suggestion == ""

    def test_failed_validation_with_issues(self):
        vr = ValidationResponse(
            plan_id="pid",
            passed=False,
            issues=["Tool echo failed"],
            patch_suggestion="Retry with correct payload",
        )
        assert vr.passed is False
        assert len(vr.issues) == 1

    def test_missing_passed_raises(self):
        with pytest.raises(ValidationError):
            ValidationResponse(plan_id="pid")


# ── StateTransition ───────────────────────────────────────────────────────────

class TestStateTransition:
    def test_valid_transition(self):
        st = StateTransition(
            from_state=EngineState.INIT,
            to_state=EngineState.PLAN,
            reason="Starting",
        )
        assert st.from_state == EngineState.INIT
        assert st.to_state == EngineState.PLAN

    def test_invalid_state_raises(self):
        with pytest.raises(ValidationError):
            StateTransition(from_state="INVALID", to_state=EngineState.PLAN, reason="x")


# ── RunResult ─────────────────────────────────────────────────────────────────

class TestRunResult:
    def test_successful_run_result(self):
        rr = RunResult(
            task="do thing",
            final_state=EngineState.DONE,
            retry_count=0,
            model_used="stub-1.0",
            success=True,
        )
        assert rr.success is True
        assert rr.run_id  # auto-generated

    def test_failed_run_result(self):
        rr = RunResult(
            task="do thing",
            final_state=EngineState.FAILED,
            retry_count=3,
            model_used="stub-1.0",
            success=False,
            validation_failures=["tool failed"],
        )
        assert rr.success is False
        assert rr.retry_count == 3
        assert "tool failed" in rr.validation_failures

    def test_missing_task_raises(self):
        with pytest.raises(ValidationError):
            RunResult(final_state=EngineState.DONE, retry_count=0, model_used="m", success=True)

    def test_missing_model_used_raises(self):
        with pytest.raises(ValidationError):
            RunResult(task="t", final_state=EngineState.DONE, retry_count=0, success=True)
