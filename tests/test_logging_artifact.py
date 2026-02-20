from __future__ import annotations

import json
import pathlib

import pytest

from core.engine import run
from tests.fixtures.tasks import always_fail_task, single_step_task

LOGS = pathlib.Path("logs")

REQUIRED_KEYS = {
    "run_id",
    "start_timestamp",
    "end_timestamp",
    "model_name",
    "state_history",
    "retry_count",
    "tool_calls",
    "validation_failures",
    "final_state",
}


def _run_and_find_log() -> dict:
    before = {p.name for p in LOGS.glob("*.json")}
    run(single_step_task())
    after = {p.name for p in LOGS.glob("*.json")}
    new = after - before
    assert len(new) == 1, f"Expected 1 new log file, got {len(new)}"
    return json.loads((LOGS / next(iter(new))).read_text())


class TestLoggingArtifact:
    def test_log_file_created(self):
        before = set(LOGS.glob("*.json"))
        run(single_step_task())
        after = set(LOGS.glob("*.json"))
        assert len(after) > len(before)

    def test_log_file_named_by_run_id(self):
        log = _run_and_find_log()
        run_id = log["run_id"]
        assert (LOGS / f"{run_id}.json").exists()

    def test_all_required_keys_present(self):
        log = _run_and_find_log()
        missing = REQUIRED_KEYS - log.keys()
        assert not missing, f"Missing keys: {missing}"

    def test_run_id_is_string(self):
        log = _run_and_find_log()
        assert isinstance(log["run_id"], str)
        assert len(log["run_id"]) == 36  # uuid4 canonical form

    def test_state_history_is_list(self):
        log = _run_and_find_log()
        assert isinstance(log["state_history"], list)

    def test_tool_calls_is_list(self):
        log = _run_and_find_log()
        assert isinstance(log["tool_calls"], list)

    def test_retry_count_is_int(self):
        log = _run_and_find_log()
        assert isinstance(log["retry_count"], int)

    def test_validation_failures_is_int(self):
        log = _run_and_find_log()
        assert isinstance(log["validation_failures"], int)

    def test_final_state_success(self):
        log = _run_and_find_log()
        assert log["final_state"] == "success"

    def test_final_state_failed(self):
        before = {p.name for p in LOGS.glob("*.json")}
        run(always_fail_task(max_retries=0))
        after = {p.name for p in LOGS.glob("*.json")}
        new_name = next(iter(after - before))
        log = json.loads((LOGS / new_name).read_text())
        assert log["final_state"] == "failed"

    def test_log_is_valid_json(self):
        before = {p.name for p in LOGS.glob("*.json")}
        run(single_step_task())
        after = {p.name for p in LOGS.glob("*.json")}
        new_name = next(iter(after - before))
        raw = (LOGS / new_name).read_text()
        parsed = json.loads(raw)
        assert isinstance(parsed, dict)

    def test_model_name_is_string(self):
        log = _run_and_find_log()
        assert isinstance(log["model_name"], str)
        assert log["model_name"]  # non-empty
