from __future__ import annotations

import json
import pathlib

from core.adapters.registry import AdapterRegistry
from core.adapters.builtin.echo import echo_adapter
from core.engine import run
from core.schemas import Step, TaskDefinition
from tests.utils import latest_log, normalize_output

LOGS = pathlib.Path("logs")
SNAPSHOTS = pathlib.Path("tests/snapshots")


def _snapshot_task() -> TaskDefinition:
    return TaskDefinition(
        name="snapshot-task",
        steps=[
            Step(id="s1", name="s1", adapter="echo", params={"key": "value"}),
            Step(id="s2", name="s2", adapter="echo", depends_on=["s1"]),
        ],
    )


def _snapshot_registry() -> AdapterRegistry:
    reg = AdapterRegistry()
    reg.register("echo", echo_adapter)
    return reg


class TestRegressionSnapshot:
    def test_snapshot_file_exists(self):
        assert (SNAPSHOTS / "run_001.json").exists()

    def test_normalized_output_matches_snapshot(self):
        run(_snapshot_task(), registry=_snapshot_registry())
        log = latest_log(LOGS)
        actual = normalize_output(log)
        expected = json.loads((SNAPSHOTS / "run_001.json").read_text())
        assert actual == expected

    def test_normalize_removes_run_id(self):
        log = {"run_id": "abc", "final_state": "success"}
        assert "run_id" not in normalize_output(log)

    def test_normalize_removes_timestamps(self):
        log = {
            "start_timestamp": "2026-01-01T00:00:00+00:00",
            "end_timestamp": "2026-01-01T00:00:01+00:00",
            "final_state": "success",
        }
        normalized = normalize_output(log)
        assert "start_timestamp" not in normalized
        assert "end_timestamp" not in normalized

    def test_normalize_preserves_stable_fields(self):
        log = {
            "run_id": "x",
            "start_timestamp": "t",
            "end_timestamp": "t",
            "final_state": "success",
            "retry_count": 0,
            "tool_calls": ["echo"],
            "validation_failures": 0,
            "state_history": ["pending", "running", "success"],
            "model_name": "OpenAIAdapter",
        }
        normalized = normalize_output(log)
        assert normalized["final_state"] == "success"
        assert normalized["retry_count"] == 0
        assert normalized["tool_calls"] == ["echo"]
        assert normalized["model_name"] == "OpenAIAdapter"
