from __future__ import annotations

from typing import Any, Dict

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
