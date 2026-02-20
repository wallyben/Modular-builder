from __future__ import annotations

import pytest
from pydantic import ValidationError

from core.schemas import Step, StepResult, StepStatus, TaskContext, TaskDefinition, TaskStatus
from core.engine import run
from tests.fixtures.tasks import single_step_task


class TestStepSchema:
    def test_valid_step(self):
        s = Step(id="x", name="x", adapter="echo")
        assert s.id == "x"

    def test_unknown_fields_ignored_by_default(self):
        # Pydantic v2 ignores extra fields unless model_config forbids them
        s = Step.model_validate({"id": "x", "name": "x", "adapter": "echo", "unknown": 99})
        assert not hasattr(s, "unknown")

    def test_missing_required_field_rejected(self):
        with pytest.raises(ValidationError):
            Step(id="x", name="x")  # adapter missing

    def test_max_retries_upper_bound(self):
        with pytest.raises(ValidationError):
            Step(id="x", name="x", adapter="echo", max_retries=11)

    def test_max_retries_lower_bound(self):
        with pytest.raises(ValidationError):
            Step(id="x", name="x", adapter="echo", max_retries=-1)


class TestTaskDefinitionSchema:
    def test_empty_steps_rejected(self):
        with pytest.raises(ValidationError, match="steps must not be empty"):
            TaskDefinition(name="t", steps=[])

    def test_duplicate_step_ids_rejected(self):
        s = Step(id="dup", name="dup", adapter="echo")
        with pytest.raises(ValidationError, match="step ids must be unique"):
            TaskDefinition(name="t", steps=[s, s])

    def test_max_task_retries_upper_bound(self):
        with pytest.raises(ValidationError):
            TaskDefinition(
                name="t",
                steps=[Step(id="s1", name="s1", adapter="echo")],
                max_task_retries=6,
            )


class TestStepResultSchema:
    def test_attempt_must_be_positive(self):
        with pytest.raises(ValidationError):
            StepResult(step_id="s1", status=StepStatus.SUCCESS, attempt=0)

    def test_valid_result(self):
        r = StepResult(step_id="s1", status=StepStatus.SUCCESS, output={"k": "v"}, attempt=1)
        assert r.output == {"k": "v"}


class TestRunOutputValidation:
    def test_engine_output_is_task_context(self):
        ctx = run(single_step_task())
        assert isinstance(ctx, TaskContext)

    def test_step_result_validates_against_schema(self):
        ctx = run(single_step_task())
        for result in ctx.results.values():
            assert isinstance(result, StepResult)
            assert result.attempt >= 1

    def test_task_status_is_valid_enum(self):
        ctx = run(single_step_task())
        assert ctx.status in TaskStatus
