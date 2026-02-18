"""
CLI Entry Point — Modular AI Execution Engine Phase 1.

Usage:
    python main.py run "Build simple test task"

Commands:
    run <task>      Execute a task through the full engine loop
    list-tools      List all registered tools
    list-adapters   List available LLM adapters
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def _build_engine(adapter_name: str = "openai"):
    """Construct the engine with the specified adapter and default tool registry."""
    from adapters.openai_adapter import OpenAIAdapter
    from adapters.anthropic_adapter import AnthropicAdapter
    from core.engine import ExecutionEngine
    from tools.registry import build_default_registry

    adapters = {
        "openai": OpenAIAdapter(),
        "anthropic": AnthropicAdapter(),
    }
    if adapter_name not in adapters:
        print(f"[ERROR] Unknown adapter '{adapter_name}'. Choose: {list(adapters)}")
        sys.exit(1)

    registry = build_default_registry()
    return ExecutionEngine(adapter=adapters[adapter_name], registry=registry)


def cmd_run(task: str, adapter: str = "openai") -> None:
    """Trigger the full execution loop for a task."""
    if not task.strip():
        print("[ERROR] Task cannot be empty.")
        sys.exit(1)

    engine = _build_engine(adapter)
    print(f"\n[ENGINE] Starting run for task: {task!r}")
    print(f"[ENGINE] Adapter: {adapter}\n")

    result = engine.run(task)

    print("=" * 60)
    print("RUN RESULT")
    print("=" * 60)
    output = {
        "run_id": result.run_id,
        "task": result.task,
        "final_state": result.final_state.value,
        "success": result.success,
        "retry_count": result.retry_count,
        "model_used": result.model_used,
        "state_transitions": [
            {"from": t.from_state.value, "to": t.to_state.value, "reason": t.reason}
            for t in result.state_transitions
        ],
        "validation_failures": result.validation_failures,
        "tool_calls": [
            {
                "tool": tc.tool_name,
                "success": tc.success,
                "output": tc.output,
                "error": tc.error,
            }
            for tc in result.tool_calls
        ],
        "log_path": result.log_path,
    }
    print(json.dumps(output, indent=2))
    print("=" * 60)
    print(f"[ENGINE] Log saved to: {result.log_path}")

    sys.exit(0 if result.success else 1)


def cmd_list_tools() -> None:
    """Print all registered tools."""
    from tools.registry import build_default_registry

    registry = build_default_registry()
    print("Registered tools:")
    for name in registry.list_tools():
        print(f"  - {name}")


def cmd_list_adapters() -> None:
    """Print available LLM adapters."""
    print("Available adapters:")
    print("  - openai   (OpenAIAdapter  → gpt-4o)")
    print("  - anthropic (AnthropicAdapter → claude-opus-4-6)")


def main() -> None:
    args = sys.argv[1:]

    if not args or args[0] in ("-h", "--help", "help"):
        print(__doc__)
        sys.exit(0)

    command = args[0]

    if command == "run":
        if len(args) < 2:
            print("[ERROR] Usage: python main.py run <task> [--adapter openai|anthropic]")
            sys.exit(1)
        task = args[1]
        adapter = "openai"
        if "--adapter" in args:
            idx = args.index("--adapter")
            if idx + 1 < len(args):
                adapter = args[idx + 1]
        cmd_run(task, adapter)

    elif command == "list-tools":
        cmd_list_tools()

    elif command == "list-adapters":
        cmd_list_adapters()

    else:
        print(f"[ERROR] Unknown command: {command!r}")
        print("Commands: run, list-tools, list-adapters")
        sys.exit(1)


if __name__ == "__main__":
    main()
