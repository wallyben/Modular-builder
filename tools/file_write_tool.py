"""
FileWriteTool — writes content to a file path.
Validates path and content before writing.
"""
from __future__ import annotations

import os
from pathlib import Path

from tools.base import BaseTool


class FileWriteTool(BaseTool):
    """
    Writes string content to a file at the specified path.
    Creates parent directories if they do not exist.

    Payload keys:
        - path (str): Absolute or relative file path.
        - content (str): String content to write.
    """

    @property
    def name(self) -> str:
        return "file_write"

    def execute(self, payload: dict) -> dict:
        file_path = payload.get("path", "")
        content = payload.get("content", "")

        if not file_path:
            return {"success": False, "output": "", "error": "'path' field is required"}
        if not isinstance(content, str):
            return {"success": False, "output": "", "error": "'content' must be a string"}

        try:
            target = Path(file_path)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            return {
                "success": True,
                "output": f"File written: {target.resolve()}",
                "error": "",
            }
        except OSError as exc:
            return {"success": False, "output": "", "error": str(exc)}
