from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class EngineConfig(BaseModel):
    max_retries: int = Field(default=3, ge=0, le=10)
    adapter: str = Field(default="stub")

    model_config = {"frozen": True, "extra": "forbid"}


class TaskInput(BaseModel):
    task_id: str = Field(..., min_length=1)
    payload: Dict[str, Any] = Field(default_factory=dict)
    config: EngineConfig = Field(default_factory=EngineConfig)

    model_config = {"frozen": True, "extra": "forbid"}

    @field_validator("task_id")
    @classmethod
    def task_id_no_whitespace(cls, v: str) -> str:
        if v != v.strip():
            raise ValueError("task_id must not have leading/trailing whitespace")
        return v


class AttemptRecord(BaseModel):
    attempt: int
    error: Optional[str] = None
    result: Optional[Any] = None

    model_config = {"frozen": True, "extra": "forbid"}


class TaskOutput(BaseModel):
    task_id: str
    status: str
    result: Optional[Any] = None
    attempts: List[AttemptRecord] = Field(default_factory=list)
    error: Optional[str] = None

    model_config = {"frozen": True, "extra": "forbid"}
