"""
test_tool_invocation.py
Tests for tool registration, execution, mocking, and error handling.
Covers: EchoTool, FileWriteTool, ShellTool, ToolRegistry.
"""
from __future__ import annotations

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from tools.base import BaseTool
from tools.echo_tool import EchoTool
from tools.file_write_tool import FileWriteTool
from tools.registry import ToolRegistry, build_default_registry
from tools.shell_tool import ShellTool


# ── EchoTool ──────────────────────────────────────────────────────────────────

class TestEchoTool:
    def test_echoes_message(self):
        tool = EchoTool()
        result = tool.execute({"message": "hello world"})
        assert result["success"] is True
        assert result["output"] == "hello world"
        assert result["error"] == ""

    def test_empty_message(self):
        tool = EchoTool()
        result = tool.execute({"message": ""})
        assert result["success"] is True
        assert result["output"] == ""

    def test_missing_message_key(self):
        tool = EchoTool()
        result = tool.execute({})
        assert result["success"] is True
        assert result["output"] == ""

    def test_non_string_message_fails(self):
        tool = EchoTool()
        result = tool.execute({"message": 42})
        assert result["success"] is False
        assert "string" in result["error"]

    def test_tool_name(self):
        assert EchoTool().name == "echo"

    def test_is_base_tool(self):
        assert isinstance(EchoTool(), BaseTool)


# ── FileWriteTool ─────────────────────────────────────────────────────────────

class TestFileWriteTool:
    def test_writes_file(self, tmp_path):
        tool = FileWriteTool()
        target = tmp_path / "output.txt"
        result = tool.execute({"path": str(target), "content": "hello"})
        assert result["success"] is True
        assert target.read_text() == "hello"

    def test_creates_parent_dirs(self, tmp_path):
        tool = FileWriteTool()
        target = tmp_path / "nested" / "deep" / "file.txt"
        result = tool.execute({"path": str(target), "content": "data"})
        assert result["success"] is True
        assert target.exists()

    def test_missing_path_fails(self):
        tool = FileWriteTool()
        result = tool.execute({"content": "x"})
        assert result["success"] is False
        assert "path" in result["error"]

    def test_non_string_content_fails(self):
        tool = FileWriteTool()
        result = tool.execute({"path": "/tmp/x.txt", "content": 123})
        assert result["success"] is False

    def test_tool_name(self):
        assert FileWriteTool().name == "file_write"


# ── ShellTool ─────────────────────────────────────────────────────────────────

class TestShellTool:
    def test_missing_command_fails(self):
        tool = ShellTool()
        result = tool.execute({})
        assert result["success"] is False
        assert "command" in result["error"]

    def test_tool_name(self):
        assert ShellTool().name == "shell"

    def test_successful_command_via_mock(self):
        """Mock subprocess.run to avoid real shell execution in tests."""
        tool = ShellTool()
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "hello from shell"
        mock_result.stderr = ""

        with patch("tools.shell_tool.subprocess.run", return_value=mock_result):
            result = tool.execute({"command": "echo hello"})

        assert result["success"] is True
        assert result["output"] == "hello from shell"

    def test_failed_command_via_mock(self):
        tool = ShellTool()
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "command failed"

        with patch("tools.shell_tool.subprocess.run", return_value=mock_result):
            result = tool.execute({"command": "false"})

        assert result["success"] is False
        assert result["error"] == "command failed"

    def test_timeout_returns_failure_via_mock(self):
        tool = ShellTool()
        with patch(
            "tools.shell_tool.subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd="sleep 100", timeout=1),
        ):
            result = tool.execute({"command": "sleep 100", "timeout": 1})
        assert result["success"] is False
        assert "timed out" in result["error"].lower()


# ── ToolRegistry ──────────────────────────────────────────────────────────────

class TestToolRegistry:
    def test_register_and_execute(self):
        registry = ToolRegistry()
        registry.register("echo", EchoTool())
        result = registry.execute("echo", {"message": "test"})
        assert result["success"] is True
        assert result["output"] == "test"

    def test_unregistered_tool_raises_key_error(self):
        registry = ToolRegistry()
        with pytest.raises(KeyError, match="not registered"):
            registry.execute("nonexistent", {})

    def test_list_tools(self):
        registry = ToolRegistry()
        registry.register("echo", EchoTool())
        assert "echo" in registry.list_tools()

    def test_has_tool(self):
        registry = ToolRegistry()
        registry.register("echo", EchoTool())
        assert registry.has_tool("echo") is True
        assert registry.has_tool("missing") is False

    def test_register_non_tool_raises_type_error(self):
        registry = ToolRegistry()
        with pytest.raises(TypeError):
            registry.register("bad", object())

    def test_build_default_registry_has_required_tools(self):
        registry = build_default_registry()
        assert registry.has_tool("echo")
        assert registry.has_tool("file_write")
        assert registry.has_tool("shell")

    def test_mock_tool_injection(self):
        """Demonstrate mock tool injection pattern."""
        registry = ToolRegistry()
        mock_tool = MagicMock(spec=BaseTool)
        mock_tool.name = "mock_tool"
        mock_tool.execute.return_value = {"success": True, "output": "mocked", "error": ""}
        registry.register("mock_tool", mock_tool)

        result = registry.execute("mock_tool", {"any": "payload"})
        assert result["output"] == "mocked"
        mock_tool.execute.assert_called_once_with({"any": "payload"})
