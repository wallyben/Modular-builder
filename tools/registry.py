"""
ToolRegistry — central registry for all available tools.
Tools are registered by name and executed by name.
"""
from __future__ import annotations

from typing import Dict

from tools.base import BaseTool


class ToolRegistry:
    """
    Registry that maps tool names to BaseTool instances.

    Usage:
        registry = ToolRegistry()
        registry.register("echo", EchoTool())
        result = registry.execute("echo", {"message": "hello"})
    """

    def __init__(self) -> None:
        self._tools: Dict[str, BaseTool] = {}

    def register(self, name: str, tool: BaseTool) -> None:
        """Register a tool under the given name."""
        if not isinstance(tool, BaseTool):
            raise TypeError(f"Tool '{name}' must be an instance of BaseTool")
        self._tools[name] = tool

    def execute(self, name: str, payload: dict) -> dict:
        """
        Execute a registered tool by name.

        Returns:
            Tool result dict with 'success', 'output', 'error' keys.

        Raises:
            KeyError: If tool name is not registered.
        """
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' is not registered. Available: {list(self._tools)}")
        return self._tools[name].execute(payload)

    def list_tools(self) -> list[str]:
        """Return list of registered tool names."""
        return list(self._tools.keys())

    def has_tool(self, name: str) -> bool:
        """Return True if tool is registered."""
        return name in self._tools


def build_default_registry() -> ToolRegistry:
    """
    Construct and return the default tool registry with all built-in tools.
    Import here to avoid circular imports.
    """
    from tools.echo_tool import EchoTool
    from tools.file_write_tool import FileWriteTool
    from tools.shell_tool import ShellTool

    registry = ToolRegistry()
    registry.register("echo", EchoTool())
    registry.register("file_write", FileWriteTool())
    registry.register("shell", ShellTool())
    return registry
