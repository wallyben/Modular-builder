from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def normalize_output(log: dict[str, Any]) -> dict[str, Any]:
    """Remove non-deterministic fields before snapshot comparison."""
    drop = {"run_id", "start_timestamp", "end_timestamp"}
    return {k: v for k, v in log.items() if k not in drop}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def latest_log(logs_dir: Path) -> dict[str, Any]:
    files = sorted(logs_dir.glob("*.json"), key=lambda p: p.stat().st_mtime)
    return load_json(files[-1])
