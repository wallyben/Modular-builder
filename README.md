# Modular AI Execution Engine — Phase 1 Core

A minimal, production-grade AI execution engine with:
- Model-agnostic LLM adapter layer
- Deterministic state machine (INIT→PLAN→EXECUTE→VALIDATE→DONE/FAILED)
- Strict Pydantic schema enforcement
- Retry ceiling (max 3 attempts)
- Structured JSON logging per run
- Full pytest test suite
- CLI entry point

## Architecture

```
/adapters   LLM adapter abstraction (OpenAI, Anthropic, swappable)
/core       Engine, schemas, logger
/tools      Tool registry + built-in tools (echo, file_write, shell)
/modules    Reserved for Phase 2 modules
/tests      Full pytest suite (5 test files)
/logs       Per-run JSON logs ({run_id}.json)
main.py     CLI entry point
```

## State Machine

```
INIT → PLAN → EXECUTE → VALIDATE → DONE
                    ↑        ↓
                   PATCH (max 3 retries)
                              ↓
                           FAILED
```

## Quick Start (PowerShell — Windows)

```powershell
# 1. Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the test suite
pytest -q

# 4. Run the engine via CLI
python main.py run "Build simple test task"

# 5. Optional: use Anthropic adapter
python main.py run "Build simple test task" --adapter anthropic

# 6. List available tools
python main.py list-tools

# 7. List available adapters
python main.py list-adapters
```

## Quick Start (Linux/macOS)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest -q
python main.py run "Build simple test task"
```

## Running Tests

```bash
pytest -q
```

All tests are deterministic, use mocked tools/adapters, and require no API keys.

## Phase 1 Scope Lock

This implementation is strictly Phase 1. The following are intentionally excluded:
- Vector databases
- UI / streaming
- Memory embeddings
- External infrastructure
- Multi-agent swarm logic
- Async complexity
- Speculative features
