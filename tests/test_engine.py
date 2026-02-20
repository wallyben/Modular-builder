"""Tests for core/engine.py — end-to-end task execution."""
from __future__ import annotations

from typing import Any

import pytest

from core.adapters import AdapterRegistry
from core.adapters.builtin.echo import echo_adapter
from core.adapters.builtin.fail import fail_adapter
from core.engine import run
from core.schemas import Step, StepStatus, TaskDefinition, TaskStatus


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_task(*steps: Step, max_task_retries: int = 0) -> TaskDefinition:
    return TaskDefinition(name="test-task", steps=list(steps), max_task_retries=max_task_retries)


def _step(
    sid: str,
    adapter: str = "echo",
    depends_on: list[str] | None = None,
    params: dict | None = None,
    max_retries: int = 0,
) -> Step:
    return Step(
        id=sid,
        name=sid,
        adapter=adapter,
        depends_on=depends_on or [],
        params=params or {},
        max_retries=max_retries,
    )


def _registry(*adapters: tuple[str, Any]) -> AdapterRegistry:
    reg = AdapterRegistry()
    for name, fn in adapters:
        reg.register(name, fn)
    return reg


# ---------------------------------------------------------------------------
# Happy-path execution
# ---------------------------------------------------------------------------

class TestRunSuccess:
    def test_single_step_succeeds(self):
        reg = _registry(("echo", echo_adapter))
        task = _make_task(_step("s1", adapter="echo"))
        ctx = run(task, registry=reg)
        assert ctx.status == TaskStatus.SUCCESS
        assert ctx.results["s1"].status == StepStatus.SUCCESS

    def test_linear_chain(self):
        reg = _registry(("echo", echo_adapter))
        task = _make_task(
            _step("a"),
            _step("b", depends_on=["a"]),
            _step("c", depends_on=["b"]),
        )
        ctx = run(task, registry=reg)
        assert ctx.status == TaskStatus.SUCCESS
        for sid in ("a", "b", "c"):
            assert ctx.results[sid].status == StepStatus.SUCCESS

    def test_parallel_steps(self):
        reg = _registry(("echo", echo_adapter))
        task = _make_task(_step("a"), _step("b"), _step("c"))
        ctx = run(task, registry=reg)
        assert ctx.status == TaskStatus.SUCCESS

    def test_diamond_dependency(self):
        """a -> b, a -> c, b+c -> d."""
        reg = _registry(("echo", echo_adapter))
        task = _make_task(
            _step("a"),
            _step("b", depends_on=["a"]),
            _step("c", depends_on=["a"]),
            _step("d", depends_on=["b", "c"]),
        )
        ctx = run(task, registry=reg)
        assert ctx.status == TaskStatus.SUCCESS
        assert ctx.results["d"].status == StepStatus.SUCCESS

    def test_output_stored_in_result(self):
        reg = _registry(("echo", echo_adapter))
        task = _make_task(_step("s1", params={"hello": "world"}))
        ctx = run(task, registry=reg)
        assert ctx.results["s1"].output["params"] == {"hello": "world"}


# ---------------------------------------------------------------------------
# Failure paths
# ---------------------------------------------------------------------------

class TestRunFailure:
    def test_single_step_fails(self):
        reg = _registry(("fail", fail_adapter))
        task = _make_task(_step("s1", adapter="fail", max_retries=0))
        ctx = run(task, registry=reg)
        assert ctx.status == TaskStatus.FAILED
        assert ctx.results["s1"].status == StepStatus.FAILED

    def test_retries_exhausted(self):
        attempts: list[int] = []

        def counting_fail(step: Step) -> None:
            attempts.append(1)
            raise RuntimeError("always fails")

        reg = _registry(("flaky", counting_fail))
        task = _make_task(_step("s1", adapter="flaky", max_retries=2))
        ctx = run(task, registry=reg)
        assert ctx.status == TaskStatus.FAILED
        assert ctx.results["s1"].attempt == 3   # 1 + 2 retries
        assert len(attempts) == 3

    def test_downstream_steps_blocked_on_failed_dep(self):
        reg = _registry(("fail", fail_adapter), ("echo", echo_adapter))
        task = _make_task(
            _step("a", adapter="fail", max_retries=0),
            _step("b", adapter="echo", depends_on=["a"]),
        )
        ctx = run(task, registry=reg)
        assert ctx.status == TaskStatus.FAILED
        # b should never have run (dep failed)
        assert "b" not in ctx.results

    def test_unknown_adapter_raises_keyerror(self):
        reg = AdapterRegistry()  # empty — nothing registered
        task = _make_task(_step("s1", adapter="nope"))
        with pytest.raises(KeyError):
            run(task, registry=reg)

    def test_error_message_propagated(self):
        reg = _registry(("fail", fail_adapter))
        task = _make_task(
            _step("s1", adapter="fail", params={"message": "custom error"}, max_retries=0)
        )
        ctx = run(task, registry=reg)
        assert "custom error" in ctx.results["s1"].error


# ---------------------------------------------------------------------------
# Retry on success within ceiling
# ---------------------------------------------------------------------------

class TestRetrySuccess:
    def test_succeeds_on_second_attempt(self):
        call_count = [0]

        def flaky(step: Step) -> dict:
            call_count[0] += 1
            if call_count[0] < 2:
                raise RuntimeError("transient")
            return {"ok": True}

        reg = _registry(("flaky", flaky))
        task = _make_task(_step("s1", adapter="flaky", max_retries=3))
        ctx = run(task, registry=reg)
        assert ctx.status == TaskStatus.SUCCESS
        assert ctx.results["s1"].attempt == 2


# ---------------------------------------------------------------------------
# Default registry is used when none provided
# ---------------------------------------------------------------------------

class TestDefaultRegistry:
    def test_echo_works_without_explicit_registry(self):
        task = _make_task(_step("s1", adapter="echo"))
        ctx = run(task)  # uses default_registry
        assert ctx.status == TaskStatus.SUCCESS
