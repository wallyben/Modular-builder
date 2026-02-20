from __future__ import annotations

from typing import Any, Dict, Optional

from core.adapters.registry import AdapterRegistry
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
# Step execution with retry ceiling
# ---------------------------------------------------------------------------

def _execute_step(step: Step, registry: AdapterRegistry) -> StepResult:
    """Run *step* via its registered adapter, retrying up to ``max_retries``."""
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
) -> TaskContext:
    """Execute *task_def* and return the final :class:`TaskContext`.

    Parameters
    ----------
    task_def:
        The task to execute, including all steps and their dependency graph.
    registry:
        Adapter registry to resolve step adapters from.  Defaults to
        ``core.adapters.default_registry`` (contains all built-ins).

    Returns
    -------
    TaskContext
        Final context whose ``status`` is one of ``SUCCESS``, ``FAILED``, or
        ``ABORTED``.
    """
    if registry is None:
        # Lazy import avoids a circular-import at module level; the import
        # triggers built-in registration exactly once.
        from core.adapters import default_registry  # noqa: PLC0415
        registry = default_registry

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
                next_status = TaskStatus.FAILED if failed else TaskStatus.SUCCESS
            else:
                # Deadlock — unresolved steps with no runnable candidates
                next_status = TaskStatus.FAILED
            ctx = transition_task(ctx, next_status)
            break

        for step_id in runnable:
            step = step_map[step_id]

            # Mark step as RUNNING
            pending_result = StepResult(
                step_id=step_id,
                status=StepStatus.RUNNING,
                attempt=1,
            )
            validate_step_transition(StepStatus.PENDING, StepStatus.RUNNING)
            ctx = ctx.model_copy(update={"results": {**ctx.results, step_id: pending_result}})

            # Execute and record final result
            result = _execute_step(step, registry)
            validate_step_transition(StepStatus.RUNNING, result.status)
            ctx = ctx.model_copy(update={"results": {**ctx.results, step_id: result}})

    return ctx
