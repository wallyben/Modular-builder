from __future__ import annotations

import pytest

from core.engine import run
from core.schemas import TaskStatus
from tests.fixtures.tasks import always_fail_task, linear_task, single_step_task
from tests.utils import latest_log

import pathlib

LOGS = pathlib.Path("logs")

TERMINAL = {"success", "failed", "aborted"}


class TestStateHistory:
    def test_first_state_is_pending(self):
        run(single_step_task())
        log = latest_log(LOGS)
        assert log["state_history"][0] == "pending"

    def test_second_state_is_running(self):
        run(single_step_task())
        log = latest_log(LOGS)
        assert log["state_history"][1] == "running"

    def test_final_state_is_terminal(self):
        run(single_step_task())
        log = latest_log(LOGS)
        assert log["final_state"] in TERMINAL

    def test_state_history_length_gt_zero(self):
        run(single_step_task())
        log = latest_log(LOGS)
        assert len(log["state_history"]) > 0

    def test_success_run_ends_in_success(self):
        run(single_step_task())
        log = latest_log(LOGS)
        assert log["final_state"] == "success"

    def test_failed_run_ends_in_failed(self):
        run(always_fail_task(max_retries=0))
        log = latest_log(LOGS)
        assert log["final_state"] == "failed"


class TestStateTransitions:
    def _valid_transitions(self) -> dict[str, set[str]]:
        return {
            "pending":  {"running"},
            "running":  {"success", "failed", "retrying"},
            "retrying": {"running", "aborted"},
            "success":  set(),
            "failed":   set(),
            "aborted":  set(),
        }

    def _check_history(self, history: list[str]) -> None:
        allowed = self._valid_transitions()
        for i in range(len(history) - 1):
            src, dst = history[i], history[i + 1]
            assert dst in allowed.get(src, set()), (
                f"Invalid transition: {src} -> {dst}"
            )

    def test_no_invalid_transitions_on_success(self):
        run(single_step_task())
        log = latest_log(LOGS)
        self._check_history(log["state_history"])

    def test_no_invalid_transitions_on_failure(self):
        run(always_fail_task(max_retries=0))
        log = latest_log(LOGS)
        self._check_history(log["state_history"])

    def test_no_invalid_transitions_linear_chain(self):
        run(linear_task())
        log = latest_log(LOGS)
        self._check_history(log["state_history"])
