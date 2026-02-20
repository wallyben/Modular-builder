from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from core.schemas import Step


@runtime_checkable
class Adapter(Protocol):
    """Callable protocol every adapter must satisfy.

    An adapter receives a fully-resolved ``Step`` and returns arbitrary output
    that is stored in ``StepResult.output``.  Raising any exception signals
    failure; the engine's retry logic will handle re-attempts up to
    ``step.max_retries``.
    """

    def __call__(self, step: Step) -> Any: ...
