"""Tests for core/schemas.py — Pydantic model validation."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from core.schemas import Step, StepResult, StepStatus, TaskContext, TaskDefinition, TaskStatus


# ---------------------------------------------------------------------------
# Step
# ---------------------------------------------------------------------------

class TestStep:
    def test_defaults(self):
        s = Step(id="s1", name="Step 1", adapter="echo")
        assert s.max_retries == 3
        assert s.depends_on == []
        assert s.params == {}

    def test_max_retries_bounds(self):
        Step(id="s1", name="s", adapter="echo", max_retries=0)
        Step(id="s1", name="s", adapter="echo", max_retries=10)
        with pytest.raises(ValidationError):
            Step(id="s1", name="s", adapter="echo", max_retries=-1)
        with pytest.raises(ValidationError):
            Step(id="s1", name="s", adapter="echo", max_retries=11)


# ---------------------------------------------------------------------------
# TaskDefinition validators
# ---------------------------------------------------------------------------

class TestTaskDefinition:
    def _step(self, sid: str) -> Step:
        return Step(id=sid, name=sid, adapter="echo")

    def test_empty_steps_rejected(self):
        with pytest.raises(ValidationError, match="steps must not be empty"):
            TaskDefinition(name="t", steps=[])

    def test_duplicate_step_ids_rejected(self):
        with pytest.raises(ValidationError, match="step ids must be unique"):
            TaskDefinition(name="t", steps=[self._step("a"), self._step("a")])

    def test_valid_task(self):
        td = TaskDefinition(name="t", steps=[self._step("a"), self._step("b")])
        assert len(td.steps) == 2

    def test_max_task_retries_bounds(self):
        TaskDefinition(name="t", steps=[self._step("a")], max_task_retries=0)
        TaskDefinition(name="t", steps=[self._step("a")], max_task_retries=5)
        with pytest.raises(ValidationError):
            TaskDefinition(name="t", steps=[self._step("a")], max_task_retries=6)


# ---------------------------------------------------------------------------
# StepResult
# ---------------------------------------------------------------------------

class TestStepResult:
    def test_attempt_ge_1(self):
        with pytest.raises(ValidationError):
            StepResult(step_id="s1", status=StepStatus.SUCCESS, attempt=0)

    def test_success_result(self):
        r = StepResult(step_id="s1", status=StepStatus.SUCCESS, output={"x": 1}, attempt=1)
        assert r.output == {"x": 1}
        assert r.error is None


# ---------------------------------------------------------------------------
# TaskContext default
# ---------------------------------------------------------------------------

class TestTaskContext:
    def test_default_status_is_pending(self):
        td = TaskDefinition(name="t", steps=[Step(id="s1", name="s1", adapter="echo")])
        ctx = TaskContext(task=td)
        assert ctx.status == TaskStatus.PENDING
        assert ctx.results == {}
