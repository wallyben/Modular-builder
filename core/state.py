from __future__ import annotations

from enum import Enum
from typing import Optional


class State(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    RETRYING = "RETRYING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


_TRANSITIONS: dict[State, frozenset[State]] = {
    State.PENDING:   frozenset({State.RUNNING}),
    State.RUNNING:   frozenset({State.SUCCESS, State.RETRYING, State.FAILED}),
    State.RETRYING:  frozenset({State.RUNNING, State.FAILED}),
    State.SUCCESS:   frozenset(),
    State.FAILED:    frozenset(),
}


class StateMachine:
    def __init__(self) -> None:
        self._state: State = State.PENDING
        self._attempt: int = 0

    @property
    def state(self) -> State:
        return self._state

    @property
    def attempt(self) -> int:
        return self._attempt

    def transition(self, target: State) -> None:
        allowed = _TRANSITIONS[self._state]
        if target not in allowed:
            raise InvalidTransitionError(self._state, target)
        self._state = target
        if target == State.RUNNING:
            self._attempt += 1

    def is_terminal(self) -> bool:
        return self._state in (State.SUCCESS, State.FAILED)


class InvalidTransitionError(Exception):
    def __init__(self, from_state: State, to_state: State) -> None:
        super().__init__(
            f"Invalid transition: {from_state.value} -> {to_state.value}"
        )
        self.from_state = from_state
        self.to_state = to_state
