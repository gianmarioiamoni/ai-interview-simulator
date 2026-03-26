# app/graph/nodes/evaluation_node.py

# EvaluationNode
#
# - Computes evaluation from execution result
# - Pure domain logic (no external services)
# - Produces updated InterviewState with evaluation + feedback bundle

from domain.contracts.interview_state import InterviewState
from domain.contracts.question import QuestionType
from domain.contracts.question_evaluation import QuestionEvaluation

from app.contracts.feedback_bundle import (
    FeedbackBundle,
    FeedbackBlockResult,
    FeedbackSignal,
    FeedbackQuality,
)


class EvaluationNode:

    def __call__(self, state: InterviewState) -> InterviewState:

        question = state.current_question

        # ---------------------------------------------------------
        # Safety guards
        # ---------------------------------------------------------

        if question is None:
            return state

        if question.type not in (QuestionType.CODING, QuestionType.DATABASE):
            return state

        result = state.get_result_for_question(question.id)

        if result is None:
            return state

        if result.execution is None:
            return state

        # Avoid re-evaluation (BUT allow bundle creation if missing)
        if result.evaluation is not None and getattr(
            state, "last_feedback_bundle", None
        ):
            return state

        execution = result.execution

        # ---------------------------------------------------------
        # Compute score
        # ---------------------------------------------------------

        if execution.total_tests and execution.total_tests > 0:
            score = (execution.passed_tests / execution.total_tests) * 100
        else:
            score = 100 if execution.success else 0

        # ---------------------------------------------------------
        # Build evaluation
        # ---------------------------------------------------------

        evaluation = QuestionEvaluation(
            question_id=question.id,
            score=score,
            max_score=100,
            passed=execution.success,
            feedback=execution.error or "Execution evaluated automatically.",
            strengths=[],
            weaknesses=[],
            passed_tests=execution.passed_tests,
            total_tests=execution.total_tests,
            execution_status=execution.status.value,
        )

        # ---------------------------------------------------------
        # FEEDBACK BUNDLE (🔥 NEW - CRITICAL)
        # ---------------------------------------------------------

        # --- QUALITY MAPPING ---
        if execution.success:
            quality_level = "optimal"
        elif execution.passed_tests > 0:
            quality_level = "partial"
        else:
            quality_level = "incorrect"

        quality = FeedbackQuality(
            level=quality_level,
            explanation=execution.error or "Execution result analysis",
        )

        # --- SIGNALS ---
        signals = []
        if execution.error:
            signals.append(
                FeedbackSignal(
                    severity="error",
                    message=execution.error,
                )
            )

        # --- BLOCK ---
        block = FeedbackBlockResult(
            title="Execution Result",
            content=execution.error or "Execution completed",
            severity="error" if not execution.success else "info",
            confidence=0.8,
            signals=signals,
            learning=[],
            quality=quality,
        )

        # --- FINAL BUNDLE ---
        bundle = FeedbackBundle(
            blocks=[block],
            overall_severity=block.severity,
            overall_confidence=block.confidence,
            overall_quality=quality.level,  # 🔥 used by HintNode
            markdown=block.content,
        )

        # ---------------------------------------------------------
        # Immutable state update
        # ---------------------------------------------------------

        new_results = dict(state.results_by_question)

        updated_result = result.model_copy(update={"evaluation": evaluation})

        new_results[question.id] = updated_result

        return state.model_copy(
            update={
                "results_by_question": new_results,
                "last_feedback_bundle": bundle,  # 🔥 CRITICAL WRITE
            }
        )
