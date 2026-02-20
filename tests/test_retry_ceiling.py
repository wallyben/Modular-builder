from __future__ import annotations

import pathlib

import pytest

from core.adapters.registry import AdapterRegistry
from core.engine import run
from core.schemas import Step, TaskDefinition, TaskStatus
from tests.utils import latest_log

LOGS = pathlib.Path("logs")


def _failing_registry() -> AdapterRegistry:
    reg = AdapterRegistry()

    def always_fail(step: Step) -> None:
        raise RuntimeError("deliberate failure")

    reg.register("fail", always_fail)
    return reg


def _task(max_retries: int) -> TaskDefinition:
    return TaskDefinition(
        name="retry-test",
        steps=[Step(id="s1", name="s1", adapter="fail", max_retries=max_retries)],
    )


class TestRetryCeiling:
    @pytest.mark.parametrize("max_retries", [0, 1, 2, 3])
    def test_final_state_is_failed(self, max_retries: int):
        ctx = run(_task(max_retries), registry=_failing_registry())
        assert ctx.status == TaskStatus.FAILED

    @pytest.mark.parametrize("max_retries", [0, 1, 2, 3])
    def test_retry_count_does_not_exceed_ceiling(self, max_retries: int):
        run(_task(max_retries), registry=_failing_registry())
        log = latest_log(LOGS)
        assert log["retry_count"] <= max_retries

    @pytest.mark.parametrize("max_retries", [0, 1, 2, 3])
    def test_attempt_equals_max_retries_plus_one(self, max_retries: int):
        ctx = run(_task(max_retries), registry=_failing_registry())
        result = ctx.results["s1"]
        assert result.attempt == max_retries + 1

    def test_zero_retries_attempt_is_one(self):
        ctx = run(_task(0), registry=_failing_registry())
        assert ctx.results["s1"].attempt == 1

    def test_error_message_captured(self):
        ctx = run(_task(0), registry=_failing_registry())
        assert "deliberate failure" in ctx.results["s1"].error
