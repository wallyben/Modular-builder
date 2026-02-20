from __future__ import annotations

from core.schemas import Step, TaskDefinition


def single_step_task(adapter: str = "echo", params: dict | None = None) -> TaskDefinition:
    return TaskDefinition(
        name="fixture-single",
        steps=[Step(id="s1", name="s1", adapter=adapter, params=params or {})],
    )


def linear_task(adapters: list[str] | None = None) -> TaskDefinition:
    adapters = adapters or ["echo", "echo", "echo"]
    steps = [
        Step(
            id=f"s{i}",
            name=f"s{i}",
            adapter=a,
            depends_on=[f"s{i - 1}"] if i > 0 else [],
        )
        for i, a in enumerate(adapters)
    ]
    return TaskDefinition(name="fixture-linear", steps=steps)


def always_fail_task(max_retries: int = 2) -> TaskDefinition:
    return TaskDefinition(
        name="fixture-fail",
        steps=[Step(id="s1", name="s1", adapter="fail", max_retries=max_retries)],
    )
