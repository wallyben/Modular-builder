"""
Abstract base class for LLM adapters.
Adapters are swappable without modifying the engine core.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional


class LLMAdapter(ABC):
    """
    Abstract interface for all LLM backends.
    Concrete implementations must be swappable without modifying the engine.
    """

    @abstractmethod
    def generate(
        self,
        messages: List[dict],
        tools: Optional[List[dict]] = None,
        schema: Optional[dict] = None,
    ) -> dict:
        """
        Send messages to the LLM and return a structured response dict.

        Args:
            messages: List of role/content message dicts.
            tools: Optional tool definitions in provider format.
            schema: Optional JSON schema for structured output enforcement.

        Returns:
            dict with at minimum:
                - "content": str  (raw text response)
                - "model": str    (model identifier)
                - "finish_reason": str
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def model_id(self) -> str:
        """Return the canonical model identifier string."""
        raise NotImplementedError
