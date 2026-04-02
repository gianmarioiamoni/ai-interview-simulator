# app/graph/nodes/evaluation_node.py

from domain.contracts.interview_state import InterviewState
from domain.contracts.question import QuestionType
from domain.contracts.question_evaluation import QuestionEvaluation


class EvaluationNode:

    def __call__(self, state: InterviewState) -> InterviewState:

        question = state.current_question

        if question is None:
            return state

        if question.type not in (QuestionType.CODING, QuestionType.DATABASE):
            return state

        result = state.get_result_for_question(question.id)

        if result is None or result.execution is None:
            return state

        execution = result.execution

        # ---------------------------------------------------------
        # Compute evaluation (always safe)
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
        # STATE UPDATE (ONLY evaluation)
        # ---------------------------------------------------------

        new_results = dict(state.results_by_question)

        updated_result = result.model_copy(update={"evaluation": evaluation})
        new_results[question.id] = updated_result

        return state.model_copy(
            update={
                "results_by_question": new_results,
            }
        )
