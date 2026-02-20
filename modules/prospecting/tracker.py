from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

_TRACKER_PATH = Path("data/outreach.jsonl")


def ensure_data_dir() -> None:
    _TRACKER_PATH.parent.mkdir(parents=True, exist_ok=True)


def record_outreach(
    company_name: str,
    email: str | None,
    status: str,
    notes: str | None = None,
) -> None:
    ensure_data_dir()
    record = {
        "company_name": company_name,
        "email": email,
        "status": status,
        "notes": notes,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    }
    with _TRACKER_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record) + "\n")


def list_outreach(status_filter: str | None = None) -> list[dict]:
    ensure_data_dir()
    if not _TRACKER_PATH.exists():
        return []
    results: list[dict] = []
    with _TRACKER_PATH.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if status_filter is None or record.get("status") == status_filter:
                results.append(record)
    return results
