from __future__ import annotations

from typing import Any, Callable, Optional

from core.schemas import AttemptRecord, EngineConfig, TaskInput, TaskOutput
from core.state import State, StateMachine


AdapterFn = Callable[[dict[str, Any]], Any]


def _stub_adapter(payload: dict[str, Any]) -> Any:
    return {"echo": payload}


_ADAPTER_REGISTRY: dict[str, AdapterFn] = {
    "stub": _stub_adapter,
}


def run(task: TaskInput) -> TaskOutput:
    config: EngineConfig = task.config
    adapter: AdapterFn = _ADAPTER_REGISTRY.get(config.adapter, _stub_adapter)

    sm = StateMachine()
    attempts: list[AttemptRecord] = []
    result: Optional[Any] = None
    last_error: Optional[str] = None

    sm.transition(State.RUNNING)

    while not sm.is_terminal():
        current_attempt = sm.attempt

        try:
            result = adapter(dict(task.payload))
            attempts.append(AttemptRecord(attempt=current_attempt, result=result))
            sm.transition(State.SUCCESS)

        except Exception as exc:
            last_error = str(exc)
            attempts.append(AttemptRecord(attempt=current_attempt, error=last_error))

            if sm.attempt >= config.max_retries + 1:
                sm.transition(State.FAILED)
            else:
                sm.transition(State.RETRYING)
                sm.transition(State.RUNNING)

    return TaskOutput(
        task_id=task.task_id,
        status=sm.state.value,
        result=result if sm.state == State.SUCCESS else None,
        attempts=attempts,
        error=last_error if sm.state == State.FAILED else None,
    )
