"""
ShellTool — executes a shell command in a subprocess.
Mock-safe: designed so tests can patch subprocess.run cleanly.
"""
from __future__ import annotations

import subprocess
from typing import List

from tools.base import BaseTool


class ShellTool(BaseTool):
    """
    Executes a shell command and captures stdout/stderr.

    Payload keys:
        - command (str | list): Command string or argv list.
        - timeout (int): Seconds before timeout. Default 30.
        - cwd (str): Working directory. Optional.

    Mock injection: replace subprocess.run in tests via
        monkeypatch.setattr("tools.shell_tool.subprocess.run", ...)
    """

    @property
    def name(self) -> str:
        return "shell"

    def execute(self, payload: dict) -> dict:
        command = payload.get("command")
        if not command:
            return {"success": False, "output": "", "error": "'command' field is required"}

        timeout = int(payload.get("timeout", 30))
        cwd = payload.get("cwd") or None

        use_shell = isinstance(command, str)

        try:
            result = subprocess.run(
                command,
                shell=use_shell,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=cwd,
            )
            if result.returncode == 0:
                return {"success": True, "output": result.stdout.strip(), "error": ""}
            return {
                "success": False,
                "output": result.stdout.strip(),
                "error": result.stderr.strip(),
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "output": "", "error": "Command timed out"}
        except Exception as exc:
            return {"success": False, "output": "", "error": str(exc)}
