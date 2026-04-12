# app/graph/nodes/hint_node.py

from domain.contracts.feedback.feedback.quality import Quality
from domain.contracts.interview_state import InterviewState
from domain.contracts.ai_hint import AIHintInput, AIHint
from domain.contracts.execution_result import ExecutionResult
from domain.contracts.test_execution_result import TestStatus
from domain.contracts.hint_level import HintLevel
from domain.policies.hint_policy import HintPolicy
from domain.contracts.question import QuestionType

from services.ai_hint_engine.ai_hint_service import AIHintService
from services.hint_rules.sql_hint_rules import SQLHintRules


class HintNode:

    def __init__(self, hint_service: AIHintService) -> None:
        self._hint_service = hint_service
        self._policy = HintPolicy()

    def __call__(self, state: InterviewState) -> InterviewState:

        question = state.current_question
        if not question:
            return state

        answer = state.get_latest_answer_for_question(question.id)
        if not answer:
            return state

        result = state.get_result_for_question(question.id)
        if not result:
            return state

        execution = result.execution
        if not execution:
            return state

        # -----------------------------------------------------
        # IDEMPOTENCY
        # -----------------------------------------------------

        if result.ai_hint is not None and result.hint_level is not None:
            return state

        # -----------------------------------------------------
        # CONTEXT
        # -----------------------------------------------------

        attempts = state.get_attempt_for_question(question.id)

        passed = execution.passed_tests or 0
        total = execution.total_tests or 0

        if execution.success:
            quality = Quality.CORRECT
        elif total > 0 and passed > 0:
            quality = Quality.PARTIAL
        else:
            quality = Quality.INCORRECT

        # -----------------------------------------------------
        # HINT LEVEL
        # -----------------------------------------------------

        hint_level = self._policy.resolve(
            quality=quality,
            attempts=attempts,
            has_error=bool(execution.error),
        )

        if hint_level == HintLevel.NONE:
            return state

        # =====================================================
        # RULE-BASED HINTS (SQL FIRST)
        # =====================================================

        if question.type == QuestionType.DATABASE:

            rule_hints = SQLHintRules.generate(answer.content)

            if rule_hints:

                ai_hint = AIHint(
                    explanation="Your SQL query can be improved.",
                    suggestion="\n".join(rule_hints),
                )

                new_results = dict(state.results_by_question)

                updated = result.model_copy(
                    update={
                        "ai_hint": ai_hint,
                        "hint_level": hint_level,
                    }
                )

                new_results[question.id] = updated

                return state.model_copy(update={"results_by_question": new_results})

        # -----------------------------------------------------
        # SIGNALS EXTRACTION
        # -----------------------------------------------------

        error = execution.error
        failed_tests = self._extract_execution_signals(execution)

        # -----------------------------------------------------
        # AI INPUT
        # -----------------------------------------------------

        hint_input = AIHintInput(
            error=error,
            user_code=answer.content[:1000],
            failed_tests=failed_tests,
            question=question.prompt,
            hint_level=hint_level,
        )

        # -----------------------------------------------------
        # AI GENERATION (LLM fallback)
        # -----------------------------------------------------

        try:
            ai_hint = self._hint_service.generate_hint(
                hint_input,
                level=hint_level.value,
            )
        except Exception:
            ai_hint = None

        # -----------------------------------------------------
        # STATE UPDATE
        # -----------------------------------------------------

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
    # INTERNAL
    # ---------------------------------------------------------

    def _extract_execution_signals(self, execution: ExecutionResult) -> str:

        if not execution or not execution.test_results:
            return "None"

        failed = [t for t in execution.test_results if t.status != TestStatus.PASSED]

        if not failed:
            return "None"

        lines = []

        for t in failed[:2]:

            # Readable input representation
            if t.args:
                input_repr = t.args[0] if len(t.args) == 1 else t.args
            else:
                input_repr = "[]"

            lines.append(
                f"Input: {input_repr} | Expected: {t.expected} | Actual: {t.actual} | Error: {t.error}"
            )

        return "\n".join(lines)
