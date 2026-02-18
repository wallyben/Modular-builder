from __future__ import annotations

from typing import FrozenSet, Tuple

from core.schemas import StepStatus, TaskContext, TaskStatus


_VALID_TASK_TRANSITIONS: dict[TaskStatus, FrozenSet[TaskStatus]] = {
    TaskStatus.PENDING:   frozenset({TaskStatus.RUNNING}),
    TaskStatus.RUNNING:   frozenset({TaskStatus.SUCCESS, TaskStatus.FAILED, TaskStatus.RETRYING}),
    TaskStatus.RETRYING:  frozenset({TaskStatus.RUNNING, TaskStatus.ABORTED}),
    TaskStatus.SUCCESS:   frozenset(),
    TaskStatus.FAILED:    frozenset(),
    TaskStatus.ABORTED:   frozenset(),
}

_TERMINAL_TASK_STATES: FrozenSet[TaskStatus] = frozenset({
    TaskStatus.SUCCESS,
    TaskStatus.FAILED,
    TaskStatus.ABORTED,
})

_VALID_STEP_TRANSITIONS: dict[StepStatus, FrozenSet[StepStatus]] = {
    StepStatus.PENDING:  frozenset({StepStatus.RUNNING, StepStatus.SKIPPED}),
    StepStatus.RUNNING:  frozenset({StepStatus.SUCCESS, StepStatus.FAILED}),
    StepStatus.SUCCESS:  frozenset(),
    StepStatus.FAILED:   frozenset(),
    StepStatus.SKIPPED:  frozenset(),
}


def transition_task(ctx: TaskContext, target: TaskStatus) -> TaskContext:
    allowed = _VALID_TASK_TRANSITIONS.get(ctx.status, frozenset())
    if target not in allowed:
        raise ValueError(
            f"Invalid task transition: {ctx.status} -> {target}"
        )
    return ctx.model_copy(update={"status": target})


def is_task_terminal(ctx: TaskContext) -> bool:
    return ctx.status in _TERMINAL_TASK_STATES


def validate_step_transition(current: StepStatus, target: StepStatus) -> None:
    allowed = _VALID_STEP_TRANSITIONS.get(current, frozenset())
    if target not in allowed:
        raise ValueError(
            f"Invalid step transition: {current} -> {target}"
        )


def resolve_runnable_steps(ctx: TaskContext) -> Tuple[str, ...]:
    completed = {
        sid
        for sid, r in ctx.results.items()
        if r.status == StepStatus.SUCCESS
    }
    skipped = {
        sid
        for sid, r in ctx.results.items()
        if r.status == StepStatus.SKIPPED
    }
    done = completed | skipped

    runnable = []
    for step in ctx.task.steps:
        if step.id in ctx.results:
            continue
        if all(dep in done for dep in step.depends_on):
            runnable.append(step.id)

    return tuple(runnable)


def all_steps_resolved(ctx: TaskContext) -> bool:
    terminal = {StepStatus.SUCCESS, StepStatus.FAILED, StepStatus.SKIPPED}
    resolved = {
        sid
        for sid, r in ctx.results.items()
        if r.status in terminal
    }
    return len(resolved) == len(ctx.task.steps)
