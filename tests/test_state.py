"""Tests for core/state.py — FSM transitions and dependency resolution."""
from __future__ import annotations

import pytest

from core.schemas import Step, StepResult, StepStatus, TaskContext, TaskDefinition, TaskStatus
from core.state import (
    all_steps_resolved,
    is_task_terminal,
    resolve_runnable_steps,
    transition_task,
    validate_step_transition,
)


def _make_ctx(*step_ids: str, depends: dict | None = None) -> TaskContext:
    """Build a TaskContext with steps that have no results yet."""
    depends = depends or {}
    steps = [
        Step(id=sid, name=sid, adapter="echo", depends_on=depends.get(sid, []))
        for sid in step_ids
    ]
    td = TaskDefinition(name="test", steps=steps)
    return TaskContext(task=td)


def _with_result(ctx: TaskContext, step_id: str, status: StepStatus) -> TaskContext:
    result = StepResult(step_id=step_id, status=status, attempt=1)
    return ctx.model_copy(update={"results": {**ctx.results, step_id: result}})


# ---------------------------------------------------------------------------
# Task transitions
# ---------------------------------------------------------------------------

class TestTransitionTask:
    def test_pending_to_running(self):
        ctx = _make_ctx("s1")
        ctx = transition_task(ctx, TaskStatus.RUNNING)
        assert ctx.status == TaskStatus.RUNNING

    def test_running_to_success(self):
        ctx = _make_ctx("s1")
        ctx = transition_task(ctx, TaskStatus.RUNNING)
        ctx = transition_task(ctx, TaskStatus.SUCCESS)
        assert ctx.status == TaskStatus.SUCCESS

    def test_invalid_transition_raises(self):
        ctx = _make_ctx("s1")
        with pytest.raises(ValueError, match="Invalid task transition"):
            transition_task(ctx, TaskStatus.SUCCESS)

    def test_terminal_cannot_transition(self):
        ctx = _make_ctx("s1")
        ctx = transition_task(ctx, TaskStatus.RUNNING)
        ctx = transition_task(ctx, TaskStatus.SUCCESS)
        with pytest.raises(ValueError):
            transition_task(ctx, TaskStatus.FAILED)


# ---------------------------------------------------------------------------
# is_task_terminal
# ---------------------------------------------------------------------------

class TestIsTaskTerminal:
    @pytest.mark.parametrize("status", [TaskStatus.SUCCESS, TaskStatus.FAILED, TaskStatus.ABORTED])
    def test_terminal_states(self, status: TaskStatus):
        ctx = _make_ctx("s1")
        ctx = ctx.model_copy(update={"status": status})
        assert is_task_terminal(ctx)

    @pytest.mark.parametrize("status", [TaskStatus.PENDING, TaskStatus.RUNNING, TaskStatus.RETRYING])
    def test_non_terminal_states(self, status: TaskStatus):
        ctx = _make_ctx("s1")
        ctx = ctx.model_copy(update={"status": status})
        assert not is_task_terminal(ctx)


# ---------------------------------------------------------------------------
# validate_step_transition
# ---------------------------------------------------------------------------

class TestValidateStepTransition:
    def test_pending_to_running_ok(self):
        validate_step_transition(StepStatus.PENDING, StepStatus.RUNNING)

    def test_running_to_success_ok(self):
        validate_step_transition(StepStatus.RUNNING, StepStatus.SUCCESS)

    def test_running_to_failed_ok(self):
        validate_step_transition(StepStatus.RUNNING, StepStatus.FAILED)

    def test_success_to_anything_raises(self):
        with pytest.raises(ValueError, match="Invalid step transition"):
            validate_step_transition(StepStatus.SUCCESS, StepStatus.RUNNING)


# ---------------------------------------------------------------------------
# resolve_runnable_steps
# ---------------------------------------------------------------------------

class TestResolveRunnableSteps:
    def test_no_deps_all_runnable(self):
        ctx = _make_ctx("a", "b", "c")
        assert set(resolve_runnable_steps(ctx)) == {"a", "b", "c"}

    def test_dep_blocks_step(self):
        ctx = _make_ctx("a", "b", depends={"b": ["a"]})
        assert resolve_runnable_steps(ctx) == ("a",)

    def test_dep_satisfied_by_success(self):
        ctx = _make_ctx("a", "b", depends={"b": ["a"]})
        ctx = _with_result(ctx, "a", StepStatus.SUCCESS)
        assert "b" in resolve_runnable_steps(ctx)

    def test_dep_satisfied_by_skipped(self):
        ctx = _make_ctx("a", "b", depends={"b": ["a"]})
        ctx = _with_result(ctx, "a", StepStatus.SKIPPED)
        assert "b" in resolve_runnable_steps(ctx)

    def test_failed_dep_blocks(self):
        ctx = _make_ctx("a", "b", depends={"b": ["a"]})
        ctx = _with_result(ctx, "a", StepStatus.FAILED)
        # b's dep is failed → not satisfied → not runnable
        runnable = resolve_runnable_steps(ctx)
        assert "b" not in runnable

    def test_already_in_results_excluded(self):
        ctx = _make_ctx("a", "b")
        ctx = _with_result(ctx, "a", StepStatus.SUCCESS)
        runnable = resolve_runnable_steps(ctx)
        assert "a" not in runnable
        assert "b" in runnable


# ---------------------------------------------------------------------------
# all_steps_resolved
# ---------------------------------------------------------------------------

class TestAllStepsResolved:
    def test_false_when_no_results(self):
        ctx = _make_ctx("a", "b")
        assert not all_steps_resolved(ctx)

    def test_false_when_partial(self):
        ctx = _make_ctx("a", "b")
        ctx = _with_result(ctx, "a", StepStatus.SUCCESS)
        assert not all_steps_resolved(ctx)

    def test_true_when_all_terminal(self):
        ctx = _make_ctx("a", "b")
        ctx = _with_result(ctx, "a", StepStatus.SUCCESS)
        ctx = _with_result(ctx, "b", StepStatus.FAILED)
        assert all_steps_resolved(ctx)

    def test_running_counts_as_not_resolved(self):
        ctx = _make_ctx("a")
        ctx = _with_result(ctx, "a", StepStatus.RUNNING)
        assert not all_steps_resolved(ctx)
