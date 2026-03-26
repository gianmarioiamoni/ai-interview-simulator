# app/graph/nodes/decision_node.py

# DecisionNode
#
# - Controls retry vs next step
# - Owns flow control semantics
# - Does NOT execute business logic

from domain.contracts.interview_state import InterviewState


class DecisionNode:

    def __init__(self, max_attempts: int = 3):
        self.max_attempts = max_attempts

    def __call__(self, state: InterviewState) -> InterviewState:

        question = state.current_question

        if question is None:
            return state

        result = state.get_result_for_question(question.id)

        if not result or not result.evaluation:
            return state

        attempt = state.get_attempt_for_question(question.id)

        # ---------------------------------------------------------
        # PASS → move forward
        # ---------------------------------------------------------

        if result.evaluation.passed:
            return state.model_copy(
                update={
                    "awaiting_user_input": False,
                }
            )

        # ---------------------------------------------------------
        # FAIL → retry if possible
        # ---------------------------------------------------------

        if attempt < self.max_attempts:
            return state.model_copy(
                update={
                    "awaiting_user_input": True,
                }
            )

        # ---------------------------------------------------------
        # FAIL + max attempts → move on
        # ---------------------------------------------------------

        return state.model_copy(
            update={
                "awaiting_user_input": False,
            }
        )
