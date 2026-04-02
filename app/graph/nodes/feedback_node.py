# app/graph/nodes/feedback_node.py

from domain.contracts.interview_state import InterviewState
from app.ui.presenters.feedback.feedback_builder import FeedbackBuilder


class FeedbackNode:

    def __init__(self):
        self._builder = FeedbackBuilder()

    def __call__(self, state: InterviewState) -> InterviewState:

        question = state.current_question
        if question is None:
            return state

        result = state.get_result_for_question(question.id)
        if not result:
            return state

        execution = result.execution
        evaluation = result.evaluation

        # -----------------------------------------------------
        # USE NEW FEEDBACK SYSTEM
        # -----------------------------------------------------

        bundle = self._builder.build(
            state=state,
            result=result,
            evaluation=evaluation,
            execution=execution,
        )

        return state.model_copy(update={"last_feedback_bundle": bundle})
