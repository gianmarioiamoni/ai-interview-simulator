# app/graph/nodes/decision_node.py

from domain.contracts.interview_state import InterviewState
from domain.policies.decision_policy import DecisionPolicy
from domain.contracts.shared.action_type import ActionType


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

        decision_str = self._policy.decide(
            quality=bundle.overall_quality,
            attempts=attempts,
            max_attempts=self.max_attempts,
        )

        decision = ActionType(decision_str)

        # -----------------------------------------------------
        # 🔥 LAST QUESTION DETECTION
        # -----------------------------------------------------

        is_last_question = state.current_question_index == len(state.questions) - 1

        # -----------------------------------------------------
        # ALLOWED ACTIONS
        # -----------------------------------------------------

        if decision == ActionType.RETRY:
            allowed_actions = [ActionType.RETRY]

        elif decision == ActionType.NEXT:

            if is_last_question:
                # FINAL STEP
                if attempts < self.max_attempts:
                    allowed_actions = [ActionType.RETRY, ActionType.GENERATE_REPORT]
                else:
                    allowed_actions = [ActionType.GENERATE_REPORT]

            else:
                if attempts < self.max_attempts:
                    allowed_actions = [ActionType.RETRY, ActionType.NEXT]
                else:
                    allowed_actions = [ActionType.NEXT]

        else:
            allowed_actions = [ActionType.NEXT]

        return state.model_copy(
            update={
                "awaiting_user_input": True,
                "allowed_actions": allowed_actions,
                "last_action": None,
            }
        )
