# app/graph/nodes/decision_node.py

from domain.contracts.interview_state import InterviewState
from domain.policies.decision_policy import DecisionPolicy


class DecisionNode:

    def __init__(self, max_attempts: int = 3):
        self.max_attempts = max_attempts
        self._policy = DecisionPolicy()

    def __call__(self, state: InterviewState) -> InterviewState:

        question = state.current_question
        if not question:
            return state

        attempts = state.get_attempt_for_question(question.id)
        bundle = getattr(state, "last_feedback_bundle", None)

        if not bundle:
            return state

        action = self._policy.decide(
            quality=bundle.overall_quality,
            attempts=attempts,
            max_attempts=self.max_attempts,
        )

        return state.model_copy(
            update={
                "awaiting_user_input": action == "retry",
                "last_action": action,
            }
        )
