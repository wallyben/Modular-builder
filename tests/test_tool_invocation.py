from __future__ import annotations

import pathlib
from typing import Any

from core.adapters.registry import AdapterRegistry
from core.engine import run
from core.schemas import Step, TaskDefinition, TaskStatus
from tests.utils import latest_log

LOGS = pathlib.Path("logs")


def _mock_registry(name: str, calls: list) -> AdapterRegistry:
    reg = AdapterRegistry()

    def mock_tool(step: Step) -> dict[str, Any]:
        calls.append(step.id)
        return {"mocked": True, "step_id": step.id}

    reg.register(name, mock_tool)
    return reg


def _task(adapter: str, step_id: str = "s1") -> TaskDefinition:
    return TaskDefinition(
        name="tool-test",
        steps=[Step(id=step_id, name=step_id, adapter=adapter)],
    )


class TestToolInvocation:
    def test_mock_tool_is_called(self):
        calls: list = []
        reg = _mock_registry("mock_tool", calls)
        run(_task("mock_tool"), registry=reg)
        assert calls == ["s1"]

    def test_mock_tool_output_stored_in_result(self):
        calls: list = []
        reg = _mock_registry("mock_tool", calls)
        ctx = run(_task("mock_tool"), registry=reg)
        assert ctx.results["s1"].output == {"mocked": True, "step_id": "s1"}

    def test_tool_name_recorded_in_log(self):
        calls: list = []
        reg = _mock_registry("mock_tool", calls)
        run(_task("mock_tool"), registry=reg)
        log = latest_log(LOGS)
        assert "mock_tool" in log["tool_calls"]

    def test_multiple_tools_all_recorded(self):
        calls: list = []
        reg = AdapterRegistry()

        def make_tool(label: str):
            def tool(step: Step) -> dict:
                calls.append(label)
                return {"label": label}
            return tool

        reg.register("tool_a", make_tool("tool_a"))
        reg.register("tool_b", make_tool("tool_b"))

        task = TaskDefinition(
            name="multi-tool",
            steps=[
                Step(id="a", name="a", adapter="tool_a"),
                Step(id="b", name="b", adapter="tool_b", depends_on=["a"]),
            ],
        )
        run(task, registry=reg)
        log = latest_log(LOGS)
        assert "tool_a" in log["tool_calls"]
        assert "tool_b" in log["tool_calls"]

    def test_task_succeeds_with_mock_tool(self):
        calls: list = []
        reg = _mock_registry("mock_tool", calls)
        ctx = run(_task("mock_tool"), registry=reg)
        assert ctx.status == TaskStatus.SUCCESS
