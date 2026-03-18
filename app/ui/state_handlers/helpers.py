# app/ui/state_handlers/helpers.py

from domain.contracts.interview_state import InterviewState
from app.runtime.interview_runtime import get_runtime_evaluation_service


def ensure_final_evaluation(state: InterviewState) -> InterviewState:

    if state.final_evaluation is None:

        evaluation_service = get_runtime_evaluation_service()

        state.final_evaluation = evaluation_service.evaluate(
            per_question_evaluations=state.evaluations_list,
            questions=state.questions,
            interview_type=state.interview_type,
            role=state.role.type,
        )

    return state
