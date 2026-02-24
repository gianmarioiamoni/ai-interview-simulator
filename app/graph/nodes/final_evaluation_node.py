# app/graph/nodes/final_evaluation_node.py

# Final evaluation node
#
# Responsibility: produces the final structured interview evaluation.

from domain.contracts.interview_state import InterviewState
from application.services.interview_evaluation_service import InterviewEvaluationService


def build_final_evaluation_node(service: InterviewEvaluationService):

    def final_evaluation_node(state: InterviewState) -> InterviewState:

        if state.interview_evaluation is not None:
            return state

        if not state.evaluations:
            return state

        evaluation = service.evaluate(
            per_question_evaluations=state.evaluations,
            interview_type=state.interview_type,
            role=state.role,
        )

        return state.model_copy(update={"interview_evaluation": evaluation})

    return final_evaluation_node
