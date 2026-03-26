# app/graph/nodes/hint_node.py

# HintNode
#
# - Generates AI hint based on evaluation + execution signals
# - Owns hint_level decision logic
# - Updates state immutably

from domain.contracts.interview_state import InterviewState
from domain.contracts.ai_hint import AIHintInput
from domain.contracts.hint_level import HintLevel
from domain.contracts.execution_result import ExecutionResult
from domain.contracts.test_execution_result import TestStatus

from services.ai_hint_engine.ai_hint_service import AIHintService


class HintNode:

    def __init__(self, hint_service: AIHintService) -> None:
        self._hint_service = hint_service

    def __call__(self, state: InterviewState) -> InterviewState:

        question = state.current_question
        answer = state.last_answer

        if question is None or answer is None:
            return state

        result = state.get_result_for_question(question.id)

        if not result:
            return state

        # Avoid duplicate generation
        if result.ai_hint is not None and result.hint_level is not None:
            return state

        attempt = state.get_attempt_for_question(question.id)

        bundle = getattr(state, "last_feedback_bundle", None)
        quality = (
            bundle.overall_quality if bundle and bundle.overall_quality else "unknown"
        )

        execution = result.execution

        # ---------------------------------------------------------
        # Signals extraction
        # ---------------------------------------------------------

        error = execution.error if execution else None
        failed_tests = self._extract_execution_signals(execution)

        # ---------------------------------------------------------
        # Hint level (🔥 updated logic)
        # ---------------------------------------------------------

        hint_level = self._resolve_hint_level(
            attempt,
            quality,
            execution,
        )

        # ---------------------------------------------------------
        # AI Hint generation
        # ---------------------------------------------------------

        user_code = answer.content

        hint_input = AIHintInput(
            error=error,
            user_code=user_code[:1000],
            failed_tests=failed_tests,
            question=question.prompt,
            hint_level=hint_level,
        )

        try:
            ai_hint = self._hint_service.generate_hint(
                hint_input,
                level=hint_level.value,
            )
        except Exception:
            ai_hint = None

        # ---------------------------------------------------------
        # State update (IMMUTABLE)
        # ---------------------------------------------------------

        new_results = dict(state.results_by_question)

        updated = result.model_copy(
            update={
                "ai_hint": ai_hint,
                "hint_level": hint_level,
            }
        )

        new_results[question.id] = updated

        return state.model_copy(update={"results_by_question": new_results})

    # ---------------------------------------------------------
    # INTERNAL LOGIC
    # ---------------------------------------------------------

    def _resolve_hint_level(
        self,
        attempt: int,
        quality: str,
        execution: ExecutionResult,
    ) -> HintLevel:

        # ---------------------------------------------------------
        # 1. ERROR dominates (runtime / execution failure)
        # ---------------------------------------------------------

        if execution and execution.error:
            if attempt <= 1:
                return HintLevel.TARGETED
            return HintLevel.SOLUTION

        # ---------------------------------------------------------
        # 2. QUALITY-DRIVEN LOGIC
        # ---------------------------------------------------------

        if quality == "incorrect":
            if attempt == 0:
                return HintLevel.NONE
            if attempt == 1:
                return HintLevel.BASIC
            if attempt == 2:
                return HintLevel.TARGETED
            return HintLevel.SOLUTION

        if quality == "partial":
            if attempt <= 1:
                return HintLevel.BASIC
            return HintLevel.TARGETED

        if quality in ("correct", "optimal"):
            return HintLevel.NONE

        if quality == "inefficient":
            return HintLevel.BASIC

        # ---------------------------------------------------------
        # 3. FALLBACK (unknown / missing bundle)
        # ---------------------------------------------------------

        if attempt >= 2:
            return HintLevel.BASIC

        return HintLevel.NONE

    # ---------------------------------------------------------

    def _extract_execution_signals(self, execution: ExecutionResult) -> str:

        if not execution or not execution.test_results:
            return "None"

        failed = [t for t in execution.test_results if t.status != TestStatus.PASSED]

        if not failed:
            return "None"

        return "\n".join(
            [
                f"Input: {t.args} | Expected: {t.expected} | Actual: {t.actual}"
                for t in failed[:2]
            ]
        )
