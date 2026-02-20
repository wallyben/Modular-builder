from __future__ import annotations

import logging
import os
import subprocess
import tempfile
from typing import Any, Callable, Dict, List

from core.artifact_validator import ArtifactValidator
from core.buildspec import BuildSpec
from core.schemas import (
    Step,
    StepResult,
    StepStatus,
    TaskContext,
    TaskDefinition,
    TaskStatus,
)
from core.state import (
    all_steps_resolved,
    is_task_terminal,
    resolve_runnable_steps,
    transition_task,
    validate_step_transition,
)

_LOG = logging.getLogger(__name__)

_BUILD_MAX_RETRIES = 3  # mirrors Step.max_retries default


# ---------------------------------------------------------------------------
# ToolRegistry — minimal callable registry for build-time tools
# ---------------------------------------------------------------------------

class ToolRegistry:
    def __init__(self) -> None:
        self._tools: Dict[str, Callable[..., Any]] = {}

    def register(self, name: str, fn: Callable[..., Any]) -> None:
        self._tools[name] = fn

    def call(self, name: str, **kwargs: Any) -> Any:
        if name not in self._tools:
            raise KeyError(f"Tool not registered: '{name}'")
        return self._tools[name](**kwargs)


# ---------------------------------------------------------------------------
# Default build tools
# ---------------------------------------------------------------------------

def _tool_generate_file(path: str, content: str) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w") as fh:
        fh.write(content)


def _module_stub(name: str, description: str) -> str:
    return f'"""{description}"""\n\n\ndef placeholder():\n    pass\n'


def _run_pytest(directory: str) -> int:
    result = subprocess.run(
        ["pytest", directory, "--tb=short", "-q"],
        capture_output=True,
        text=True,
    )
    _LOG.debug("pytest stdout: %s", result.stdout)
    _LOG.debug("pytest stderr: %s", result.stderr)
    return result.returncode


# ---------------------------------------------------------------------------
# BuildEngine
# ---------------------------------------------------------------------------

class BuildEngine:
    def __init__(self, max_retries: int = _BUILD_MAX_RETRIES) -> None:
        self.max_retries = max_retries

    def build(self, buildspec: BuildSpec, output_dir: str = "") -> Dict[str, Any]:
        _LOG.info("BUILD START project=%s language=%s", buildspec.project_name, buildspec.language)

        registry = ToolRegistry()
        registry.register("generate_file", _tool_generate_file)

        # PLAN
        if not output_dir:
            output_dir = tempfile.mkdtemp(prefix=f"build_{buildspec.project_name}_")
        _LOG.info("PLAN modules=%d output_dir=%s", len(buildspec.modules), output_dir)

        # GENERATE FILES
        generated: List[str] = []
        for module in buildspec.modules:
            path = os.path.join(output_dir, f"{module.name}.py")
            content = _module_stub(module.name, module.description)
            registry.call("generate_file", path=path, content=content)
            generated.append(path)
            _LOG.info("GENERATED file=%s", path)

        if len(generated) > buildspec.max_files:
            _LOG.error(
                "FAILED max_files exceeded: generated=%d limit=%d",
                len(generated), buildspec.max_files,
            )
            return {
                "status": "FAILED",
                "reason": "max_files exceeded",
                "output_dir": output_dir,
                "files": generated,
            }

        # SKIP TESTS — still run validation
        if not buildspec.test_required:
            validator = ArtifactValidator(output_dir, generated, last_pytest_exit_code=0)
            validator.validate_file_count(buildspec.max_files)
            validator.validate_required_modules(buildspec.modules)
            validator.validate_tests_pass(test_required=False)
            if not validator.validate_build_integrity():
                _LOG.error("FAILED validation after no-test run")
                return {
                    "status": "FAILED",
                    "reason": "artifact validation failed",
                    "output_dir": output_dir,
                    "files": generated,
                }
            _LOG.info("DONE tests_required=False")
            return {"status": "DONE", "output_dir": output_dir, "files": generated}

        # RUN TESTS → VALIDATE → PATCH → RE-RUN TESTS
        exit_code = 1
        for attempt in range(1, self.max_retries + 1):
            _LOG.info("RUN TESTS attempt=%d/%d", attempt, self.max_retries)
            exit_code = _run_pytest(output_dir)

            _LOG.info("VALIDATE attempt=%d", attempt)
            validator = ArtifactValidator(output_dir, generated, last_pytest_exit_code=exit_code)
            validator.validate_file_count(buildspec.max_files)
            validator.validate_required_modules(buildspec.modules)
            validator.validate_tests_pass(buildspec.test_required)
            integrity_ok = validator.validate_build_integrity()

            if exit_code == 0 and integrity_ok:
                _LOG.info("DONE tests_passed=True attempt=%d", attempt)
                return {"status": "DONE", "output_dir": output_dir, "files": generated}

            _LOG.warning("TESTS/VALIDATE FAILED exit_code=%d integrity=%s attempt=%d", exit_code, integrity_ok, attempt)

            if attempt < self.max_retries:
                _LOG.info("PATCH attempt=%d", attempt)
                for path in generated:
                    with open(path, "a") as fh:
                        fh.write(f"\n# patch-{attempt}: stub reconciliation\n")

        _LOG.error("FAILED after %d attempts", self.max_retries)
        return {
            "status": "FAILED",
            "reason": f"tests/validation failed after {self.max_retries} attempts",
            "output_dir": output_dir,
            "files": generated,
        }


# ---------------------------------------------------------------------------
# Stub adapter — replaced by real adapter registry in Phase 1B+
# ---------------------------------------------------------------------------

def _stub_adapter(step: Step) -> Any:
    return {"step": step.id, "adapter": step.adapter, "params": step.params}


# ---------------------------------------------------------------------------
# Step execution with retry ceiling
# ---------------------------------------------------------------------------

def _execute_step(step: Step) -> StepResult:
    last_error: str = ""
    max_attempts = step.max_retries + 1

    for attempt in range(1, max_attempts + 1):
        try:
            output = _stub_adapter(step)
            return StepResult(
                step_id=step.id,
                status=StepStatus.SUCCESS,
                output=output,
                attempt=attempt,
            )
        except Exception as exc:
            last_error = str(exc)

    return StepResult(
        step_id=step.id,
        status=StepStatus.FAILED,
        error=last_error,
        attempt=max_attempts,
    )


# ---------------------------------------------------------------------------
# Deterministic state loop
# ---------------------------------------------------------------------------

def run(task_def: TaskDefinition) -> TaskContext:
    ctx = TaskContext(task=task_def)
    ctx = transition_task(ctx, TaskStatus.RUNNING)

    step_map: Dict[str, Step] = {s.id: s for s in task_def.steps}

    while not is_task_terminal(ctx):
        runnable = resolve_runnable_steps(ctx)

        if not runnable:
            if all_steps_resolved(ctx):
                failed = [
                    r for r in ctx.results.values()
                    if r.status == StepStatus.FAILED
                ]
                if failed:
                    ctx = transition_task(ctx, TaskStatus.FAILED)
                else:
                    ctx = transition_task(ctx, TaskStatus.SUCCESS)
            else:
                ctx = transition_task(ctx, TaskStatus.FAILED)
            break

        for step_id in runnable:
            step = step_map[step_id]

            pending_result = StepResult(
                step_id=step_id,
                status=StepStatus.RUNNING,
                attempt=1,
            )
            validate_step_transition(StepStatus.PENDING, StepStatus.RUNNING)
            updated_results = {**ctx.results, step_id: pending_result}
            ctx = ctx.model_copy(update={"results": updated_results})

            result = _execute_step(step)

            validate_step_transition(StepStatus.RUNNING, result.status)
            updated_results = {**ctx.results, step_id: result}
            ctx = ctx.model_copy(update={"results": updated_results})

    return ctx
