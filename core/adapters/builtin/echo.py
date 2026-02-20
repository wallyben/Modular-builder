from __future__ import annotations

from typing import Any

from core.schemas import Step


def echo_adapter(step: Step) -> Any:
    """Return the step's params unchanged.

    Useful as a no-op placeholder, a test fixture, or any situation where
    data simply needs to flow through the graph without transformation.

    Output shape
    ------------
    ``{"step_id": <str>, "adapter": "echo", "params": <dict>}``
    """
    return {
        "step_id": step.id,
        "adapter": "echo",
        "params": step.params,
    }
