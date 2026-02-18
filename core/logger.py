"""
Structured JSON logging for the Modular AI Execution Engine.
Each run produces a /logs/{run_id}.json file.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


_LOG_DIR = Path(__file__).parent.parent / "logs"


def _ensure_log_dir() -> None:
    _LOG_DIR.mkdir(parents=True, exist_ok=True)


def get_log_path(run_id: str) -> str:
    """Return the absolute path to the log file for a given run_id."""
    _ensure_log_dir()
    return str(_LOG_DIR / f"{run_id}.json")


class RunLogger:
    """
    Accumulates structured log entries for a single engine run.
    Writes final JSON to /logs/{run_id}.json on flush().
    """

    def __init__(self, run_id: str, task: str, model: str) -> None:
        self._run_id = run_id
        self._log_path = get_log_path(run_id)
        self._record: dict[str, Any] = {
            "run_id": run_id,
            "task": task,
            "model": model,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "finished_at": None,
            "final_state": None,
            "retry_count": 0,
            "state_transitions": [],
            "validation_failures": [],
            "tool_calls": [],
        }

    def log_transition(self, from_state: str, to_state: str, reason: str) -> None:
        self._record["state_transitions"].append(
            {
                "from": from_state,
                "to": to_state,
                "reason": reason,
                "at": datetime.now(timezone.utc).isoformat(),
            }
        )

    def log_validation_failure(self, issue: str) -> None:
        self._record["validation_failures"].append(issue)

    def log_tool_call(self, tool_name: str, success: bool, output: str, error: str) -> None:
        self._record["tool_calls"].append(
            {
                "tool": tool_name,
                "success": success,
                "output": output,
                "error": error,
                "at": datetime.now(timezone.utc).isoformat(),
            }
        )

    def set_retry_count(self, count: int) -> None:
        self._record["retry_count"] = count

    def set_final_state(self, state: str) -> None:
        self._record["final_state"] = state
        self._record["finished_at"] = datetime.now(timezone.utc).isoformat()

    def flush(self) -> str:
        """Write log to disk and return log file path."""
        _ensure_log_dir()
        with open(self._log_path, "w", encoding="utf-8") as fh:
            json.dump(self._record, fh, indent=2)
        return self._log_path

    @property
    def log_path(self) -> str:
        return self._log_path
