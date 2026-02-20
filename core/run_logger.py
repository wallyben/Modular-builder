from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

_LOGS_DIR = Path("logs")


def write_run_log(data: dict[str, Any]) -> None:
    try:
        _LOGS_DIR.mkdir(exist_ok=True)
        path = _LOGS_DIR / f"{data['run_id']}.json"
        path.write_text(json.dumps(data, indent=2, default=str))
    except Exception:
        pass
