# app/graph/nodes/evaluation_aggregate_node.py

from services.interview_evaluation_service import InterviewEvaluationService


class EvaluationAggregateNode:

    def __init__(self, service: InterviewEvaluationService):
        self._service = service

    def __call__(self, state):

        # ---------------------------------------------------------
        # IDENTITY / GUARDS
        # ---------------------------------------------------------

        # Already computed → no-op (idempotent)
        if state.interview_evaluation is not None:
            return state

        # Not finished → skip
        if not state.is_completed:
            return state

        # ---------------------------------------------------------
        # SOURCE OF TRUTH: QuestionResult
        # ---------------------------------------------------------

        question_results = list(state.results_by_question.values())

        if not question_results:
            raise ValueError("Cannot compute interview evaluation without results")

        # ---------------------------------------------------------
        # EVALUATION
        # ---------------------------------------------------------

        interview_eval = self._service.evaluate(
            question_results=question_results,
            questions=state.questions,
            interview_type=state.interview_type,
            role=state.role.type,
        )

        # ---------------------------------------------------------
        # STATE UPDATE
        # ---------------------------------------------------------

        return state.model_copy(update={"interview_evaluation": interview_eval})
