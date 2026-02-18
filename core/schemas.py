from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"
    ABORTED = "aborted"


class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class StepResult(BaseModel):
    step_id: str
    status: StepStatus
    output: Optional[Any] = None
    error: Optional[str] = None
    attempt: int = Field(ge=1)


class Step(BaseModel):
    id: str
    name: str
    adapter: str
    params: Dict[str, Any] = Field(default_factory=dict)
    max_retries: int = Field(default=3, ge=0, le=10)
    depends_on: List[str] = Field(default_factory=list)


class TaskDefinition(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    steps: List[Step]
    max_task_retries: int = Field(default=0, ge=0, le=5)

    @field_validator("steps")
    @classmethod
    def steps_not_empty(cls, v: List[Step]) -> List[Step]:
        if not v:
            raise ValueError("steps must not be empty")
        return v

    @field_validator("steps")
    @classmethod
    def step_ids_unique(cls, v: List[Step]) -> List[Step]:
        ids = [s.id for s in v]
        if len(ids) != len(set(ids)):
            raise ValueError("step ids must be unique")
        return v


class TaskContext(BaseModel):
    task: TaskDefinition
    status: TaskStatus = TaskStatus.PENDING
    results: Dict[str, StepResult] = Field(default_factory=dict)
    current_step_index: int = 0
    task_attempt: int = Field(default=1, ge=1)

    class Config:
        use_enum_values = False
