"""
EchoTool — safe, deterministic tool for tests.
Echoes back the 'message' field from the payload.
"""
from __future__ import annotations

from tools.base import BaseTool


class EchoTool(BaseTool):
    """
    Deterministic identity tool.
    Returns the input message verbatim. Zero side effects.
    Used as the canonical test tool.
    """

    @property
    def name(self) -> str:
        return "echo"

    def execute(self, payload: dict) -> dict:
        message = payload.get("message", "")
        if not isinstance(message, str):
            return {
                "success": False,
                "output": "",
                "error": "'message' field must be a string",
            }
        return {
            "success": True,
            "output": message,
            "error": "",
        }
