# app/graph/nodes/final_evaluation_node.py

# Final evaluation node
#
# Responsibility: produces the final structured interview evaluation.

from domain.contracts.interview_state import InterviewState
from services.interview_evaluation_service import InterviewEvaluationService


def build_final_evaluation_node(service: InterviewEvaluationService):

    def final_evaluation_node(state: InterviewState) -> InterviewState:

        # Already evaluated
        if state.final_evaluation is not None:
            return state

        # Nothing to evaluate
        if not state.evaluations:
            return state

        evaluation = service.evaluate(
            per_question_evaluations=state.evaluations,
            interview_type=state.interview_type.value,
            role=state.role.type.value,
        )

        return state.model_copy(update={"final_evaluation": evaluation})

    return final_evaluation_node
