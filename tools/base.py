"""
Abstract base class for all tools.
Every tool must be mockable for testing via dependency injection.
"""
from __future__ import annotations

from abc import ABC, abstractmethod


class BaseTool(ABC):
    """
    Interface every registered tool must implement.
    Tools receive a payload dict and return a result dict.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique registry key for this tool."""
        raise NotImplementedError

    @abstractmethod
    def execute(self, payload: dict) -> dict:
        """
        Run the tool with the given payload.

        Returns:
            dict with at minimum:
                - "success": bool
                - "output": str
                - "error": str  (empty string on success)
        """
        raise NotImplementedError
