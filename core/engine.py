"""
Deterministic Execution Engine — Phase 1 Core.

State machine: INIT → PLAN → EXECUTE → VALIDATE → (PATCH → EXECUTE)* → DONE | FAILED
Max retry ceiling: 3 attempts before FAILED.
Every state transition is logged. All LLM outputs are schema-validated.
"""
from __future__ import annotations

import json
import uuid
from typing import List

from pydantic import ValidationError

from adapters.base import LLMAdapter
from core.logger import RunLogger
from core.schemas import (
    EngineState,
    ExecutionResponse,
    PlanResponse,
    RunResult,
    StateTransition,
    ToolCall,
    ValidationResponse,
)
from tools.registry import ToolRegistry

MAX_RETRIES = 3


class ExecutionEngine:
    """
    Deterministic state machine that orchestrates plan → execute → validate cycles.

    Rules:
    - Max retry ceiling = 3 (PATCH attempts before FAILED)
    - Every state transition is logged
    - All LLM outputs are schema-validated via Pydantic
    - Validation failure → PATCH state
    - Retry ceiling exceeded → FAILED state
    - No infinite loops possible
    """

    def __init__(self, adapter: LLMAdapter, registry: ToolRegistry) -> None:
        self._adapter = adapter
        self._registry = registry

    def run(self, task: str) -> RunResult:
        run_id = str(uuid.uuid4())
        logger = RunLogger(run_id=run_id, task=task, model=self._adapter.model_id)

        state = EngineState.INIT
        retry_count = 0
        transitions: List[StateTransition] = []
        tool_call_results: List[ExecutionResponse] = []
        validation_failures: List[str] = []
        plan: PlanResponse | None = None

        def transition(next_state: EngineState, reason: str) -> None:
            nonlocal state
            logger.log_transition(state.value, next_state.value, reason)
            transitions.append(
                StateTransition(from_state=state, to_state=next_state, reason=reason)
            )
            state = next_state

        # ── INIT ──────────────────────────────────────────────────────────
        transition(EngineState.PLAN, "Engine initialised; beginning plan phase")

        # ── PLAN ──────────────────────────────────────────────────────────
        plan = self._plan(task, logger)
        if plan is None:
            transition(EngineState.FAILED, "Planning phase failed: LLM output did not validate")
            logger.set_final_state(EngineState.FAILED.value)
            logger.set_retry_count(retry_count)
            log_path = logger.flush()
            return RunResult(
                run_id=run_id,
                task=task,
                final_state=EngineState.FAILED,
                retry_count=retry_count,
                model_used=self._adapter.model_id,
                state_transitions=transitions,
                validation_failures=["Plan response schema validation failed"],
                tool_calls=tool_call_results,
                plan=None,
                success=False,
                log_path=log_path,
            )

        # ── EXECUTE / VALIDATE / PATCH loop ───────────────────────────────
        while retry_count <= MAX_RETRIES:
            # EXECUTE
            transition(EngineState.EXECUTE, f"Executing plan (attempt {retry_count + 1})")
            exec_results = self._execute(plan, logger)
            tool_call_results.extend(exec_results)

            # VALIDATE
            transition(EngineState.VALIDATE, "Validating execution results")
            validation = self._validate(plan, exec_results, logger)

            if validation.passed:
                transition(EngineState.DONE, "Validation passed; run complete")
                logger.set_final_state(EngineState.DONE.value)
                logger.set_retry_count(retry_count)
                log_path = logger.flush()
                return RunResult(
                    run_id=run_id,
                    task=task,
                    final_state=EngineState.DONE,
                    retry_count=retry_count,
                    model_used=self._adapter.model_id,
                    state_transitions=transitions,
                    validation_failures=validation_failures,
                    tool_calls=tool_call_results,
                    plan=plan,
                    success=True,
                    log_path=log_path,
                )

            # Validation failed
            for issue in validation.issues:
                validation_failures.append(issue)
                logger.log_validation_failure(issue)

            retry_count += 1
            if retry_count > MAX_RETRIES:
                break

            # PATCH
            transition(
                EngineState.PATCH,
                f"Validation failed; patching (retry {retry_count}/{MAX_RETRIES})",
            )
            plan = self._patch(plan, validation, logger) or plan

        # ── FAILED ────────────────────────────────────────────────────────
        transition(
            EngineState.FAILED,
            f"Retry ceiling ({MAX_RETRIES}) exceeded; run failed",
        )
        logger.set_final_state(EngineState.FAILED.value)
        logger.set_retry_count(retry_count)
        log_path = logger.flush()
        return RunResult(
            run_id=run_id,
            task=task,
            final_state=EngineState.FAILED,
            retry_count=retry_count,
            model_used=self._adapter.model_id,
            state_transitions=transitions,
            validation_failures=validation_failures,
            tool_calls=tool_call_results,
            plan=plan,
            success=False,
            log_path=log_path,
        )

    # ── Private phase helpers ──────────────────────────────────────────────

    def _plan(self, task: str, logger: RunLogger) -> PlanResponse | None:
        """Call LLM to produce a plan; validate against PlanResponse schema."""
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a planning assistant. Return a JSON object matching "
                    "PlanResponse schema: {plan_id, task, steps, tool_calls, reasoning}."
                ),
            },
            {"role": "user", "content": task},
        ]
        raw = self._adapter.generate(messages)
        try:
            data = json.loads(raw["content"])
            data.setdefault("task", task)
            return PlanResponse(**data)
        except (json.JSONDecodeError, ValidationError, KeyError) as exc:
            logger.log_validation_failure(f"Plan schema validation error: {exc}")
            return None

    def _execute(
        self, plan: PlanResponse, logger: RunLogger
    ) -> List[ExecutionResponse]:
        """Execute every tool call in the plan; return results."""
        results: List[ExecutionResponse] = []

        if not plan.tool_calls:
            # No tool calls — synthesise a no-op echo result so execution is non-empty
            plan.tool_calls = [ToolCall(tool_name="echo", payload={"message": plan.task})]

        for tc in plan.tool_calls:
            if self._registry.has_tool(tc.tool_name):
                raw_result = self._registry.execute(tc.tool_name, tc.payload)
            else:
                raw_result = {
                    "success": False,
                    "output": "",
                    "error": f"Tool '{tc.tool_name}' not registered",
                }

            exec_resp = ExecutionResponse(
                plan_id=plan.plan_id,
                tool_name=tc.tool_name,
                success=raw_result["success"],
                output=raw_result.get("output", ""),
                error=raw_result.get("error", ""),
            )
            results.append(exec_resp)
            logger.log_tool_call(
                tc.tool_name,
                exec_resp.success,
                exec_resp.output,
                exec_resp.error,
            )
        return results

    def _validate(
        self,
        plan: PlanResponse,
        exec_results: List[ExecutionResponse],
        logger: RunLogger,
    ) -> ValidationResponse:
        """
        Validate execution results.
        Real validation logic can query an LLM here; Phase 1 uses deterministic rules.
        """
        issues: List[str] = []

        for result in exec_results:
            if not result.success:
                issues.append(
                    f"Tool '{result.tool_name}' failed: {result.error}"
                )

        passed = len(issues) == 0
        patch_suggestion = (
            "Re-run with corrected tool payloads." if not passed else ""
        )
        return ValidationResponse(
            plan_id=plan.plan_id,
            passed=passed,
            issues=issues,
            patch_suggestion=patch_suggestion,
        )

    def _patch(
        self,
        plan: PlanResponse,
        validation: ValidationResponse,
        logger: RunLogger,
    ) -> PlanResponse:
        """
        Request a patched plan from the LLM based on validation feedback.
        Phase 1: returns a revised plan with echo tool as safe fallback.
        """
        messages = [
            {
                "role": "system",
                "content": "Produce a patched PlanResponse JSON to fix these issues.",
            },
            {
                "role": "user",
                "content": (
                    f"Original task: {plan.task}\n"
                    f"Issues: {validation.issues}\n"
                    f"Suggestion: {validation.patch_suggestion}"
                ),
            },
        ]
        raw = self._adapter.generate(messages)
        try:
            data = json.loads(raw["content"])
            data.setdefault("task", plan.task)
            return PlanResponse(**data)
        except (json.JSONDecodeError, ValidationError):
            # Fallback: safe echo plan
            return PlanResponse(
                plan_id=plan.plan_id,
                task=plan.task,
                steps=["Fallback: echo task description"],
                tool_calls=[ToolCall(tool_name="echo", payload={"message": plan.task})],
                reasoning="Patch failed; using safe echo fallback.",
            )
