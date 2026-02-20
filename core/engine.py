from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from adapters.base import LLMAdapter
from adapters.openai_adapter import OpenAIAdapter
from core.adapters.registry import AdapterRegistry
from core.run_logger import write_run_log
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


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Step execution with retry ceiling
# ---------------------------------------------------------------------------

def _execute_step(step: Step, registry: AdapterRegistry) -> StepResult:
    last_error: str = ""
    max_attempts = step.max_retries + 1
    adapter = registry.get(step.adapter)

    for attempt in range(1, max_attempts + 1):
        try:
            output: Any = adapter(step)
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

def run(
    task_def: TaskDefinition,
    registry: Optional[AdapterRegistry] = None,
    llm_adapter: Optional[LLMAdapter] = None,
) -> TaskContext:
    if llm_adapter is None:
        llm_adapter = OpenAIAdapter()

    if registry is None:
        from core.adapters import default_registry  # noqa: PLC0415
        registry = default_registry

    run_id = str(uuid.uuid4())
    start_ts = _now()
    state_history: List[str] = []
    tool_calls: List[str] = []
    validation_failures: int = 0

    def _transition(ctx: TaskContext, target: TaskStatus) -> TaskContext:
        result = transition_task(ctx, target)
        state_history.append(result.status.value)
        return result

    ctx = TaskContext(task=task_def)
    state_history.append(ctx.status.value)
    ctx = _transition(ctx, TaskStatus.RUNNING)

    step_map: Dict[str, Step] = {s.id: s for s in task_def.steps}

    while not is_task_terminal(ctx):
        runnable = resolve_runnable_steps(ctx)

        if not runnable:
            if all_steps_resolved(ctx):
                failed = [r for r in ctx.results.values() if r.status == StepStatus.FAILED]
                next_status = TaskStatus.FAILED if failed else TaskStatus.SUCCESS
            else:
                next_status = TaskStatus.FAILED
            ctx = _transition(ctx, next_status)
            break

        for step_id in runnable:
            step = step_map[step_id]

            pending_result = StepResult(step_id=step_id, status=StepStatus.RUNNING, attempt=1)
            try:
                validate_step_transition(StepStatus.PENDING, StepStatus.RUNNING)
            except ValueError:
                validation_failures += 1
                raise
            ctx = ctx.model_copy(update={"results": {**ctx.results, step_id: pending_result}})

            tool_calls.append(step.adapter)
            result = _execute_step(step, registry)

            try:
                validate_step_transition(StepStatus.RUNNING, result.status)
            except ValueError:
                validation_failures += 1
                raise
            ctx = ctx.model_copy(update={"results": {**ctx.results, step_id: result}})

    retry_count = sum(max(r.attempt - 1, 0) for r in ctx.results.values())

    write_run_log({
        "run_id": run_id,
        "start_timestamp": start_ts,
        "end_timestamp": _now(),
        "model_name": type(llm_adapter).__name__,
        "state_history": state_history,
        "retry_count": retry_count,
        "tool_calls": tool_calls,
        "validation_failures": validation_failures,
        "final_state": ctx.status.value,
    })

    return ctx
