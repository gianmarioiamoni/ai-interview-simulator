# app/graph/nodes/evaluation_node.py

from domain.contracts.interview_state import InterviewState
from domain.contracts.question.question import QuestionType
from domain.contracts.question.question_evaluation import QuestionEvaluation
from domain.contracts.shared.action_type import ActionType

from app.ui.dto.builders.dimension_mapper import DimensionMapper
from app.ui.constants.loader_steps import LoaderStep

class EvaluationNode:

    def __call__(self, state: InterviewState) -> InterviewState:

        if state.intent == ActionType.GENERATE_REPORT:
            return state

        working_state = state.model_copy(
            update={"current_step": LoaderStep.ANALYZING}
        )

        question = state.current_question

        if question is None:
            return working_state

        if question.type not in (QuestionType.CODING, QuestionType.DATABASE):
            return working_state

        result = state.get_result_for_question(question.id)

        if result is None or result.execution is None:
            return working_state

        execution = result.execution

        # ---------------------------------------------------------
        # Compute evaluation
        # ---------------------------------------------------------

        if execution.total_tests and execution.total_tests > 0:
            score = (execution.passed_tests / execution.total_tests) * 100
        else:
            score = 100 if execution.success else 0

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
        # DIMENSION SIGNALS UPDATE
        # ---------------------------------------------------------

        dimension_mapper = DimensionMapper()

        error_type = execution.error_type if hasattr(execution, "error_type") else None

        dimension = dimension_mapper.map(error_type, execution)

        current_signals = dict(getattr(state, "dimension_signals", {}) or {})

        if dimension:
            current_signals[dimension] = current_signals.get(dimension, 0) + 1

        # ---------------------------------------------------------
        # STATE UPDATE
        # ---------------------------------------------------------

        new_results = dict(state.results_by_question)

        updated_result = result.model_copy(
            update={
                "evaluation": evaluation,
                "question": result.question or question,
            }
        )

        new_results[question.id] = updated_result

        return working_state.model_copy(
            update={
                "results_by_question": new_results,
                "dimension_signals": current_signals,
            }
        )
