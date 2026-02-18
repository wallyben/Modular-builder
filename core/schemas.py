"""
Strict Pydantic schemas for the Modular AI Execution Engine.
No optional ambiguous fields. No untyped dicts.
"""
from __future__ import annotations

from enum import Enum
from typing import List
from pydantic import BaseModel, Field
import uuid


class EngineState(str, Enum):
    INIT = "INIT"
    PLAN = "PLAN"
    EXECUTE = "EXECUTE"
    VALIDATE = "VALIDATE"
    PATCH = "PATCH"
    DONE = "DONE"
    FAILED = "FAILED"


class ToolCall(BaseModel):
    tool_name: str = Field(..., description="Name of tool to invoke")
    payload: dict = Field(..., description="Arguments for the tool")


class PlanResponse(BaseModel):
    plan_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task: str = Field(..., description="Original task description")
    steps: List[str] = Field(..., description="Ordered list of plan steps")
    tool_calls: List[ToolCall] = Field(default_factory=list)
    reasoning: str = Field(..., description="Rationale for the plan")


class ExecutionResponse(BaseModel):
    plan_id: str = Field(..., description="Associated plan ID")
    tool_name: str = Field(..., description="Tool that was invoked")
    success: bool = Field(..., description="Whether execution succeeded")
    output: str = Field(..., description="Raw output from tool")
    error: str = Field(default="", description="Error message if failed")


class ValidationResponse(BaseModel):
    plan_id: str = Field(..., description="Associated plan ID")
    passed: bool = Field(..., description="Whether validation passed")
    issues: List[str] = Field(default_factory=list, description="Validation issues found")
    patch_suggestion: str = Field(default="", description="Suggested fix if validation failed")


class StateTransition(BaseModel):
    from_state: EngineState
    to_state: EngineState
    reason: str = Field(..., description="Why this transition occurred")


class RunResult(BaseModel):
    run_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task: str = Field(..., description="Original task")
    final_state: EngineState = Field(..., description="Terminal state of the run")
    retry_count: int = Field(default=0, description="Number of retries attempted")
    model_used: str = Field(..., description="LLM model identifier used")
    state_transitions: List[StateTransition] = Field(default_factory=list)
    validation_failures: List[str] = Field(default_factory=list)
    tool_calls: List[ExecutionResponse] = Field(default_factory=list)
    plan: PlanResponse | None = Field(default=None)
    success: bool = Field(..., description="Whether the run completed successfully")
    log_path: str = Field(default="", description="Path to structured log file")
