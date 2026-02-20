from __future__ import annotations

from core.schemas import Step


def fail_adapter(step: Step) -> None:
    """Always raise, exhausting all retries.

    Useful in tests to verify that the engine marks steps as FAILED and
    continues (or aborts) correctly.

    Optional params
    ---------------
    message : str
        Custom error message (default: ``"fail adapter: deliberate failure"``).
    """
    msg: str = step.params.get("message", "fail adapter: deliberate failure")
    raise RuntimeError(msg)
