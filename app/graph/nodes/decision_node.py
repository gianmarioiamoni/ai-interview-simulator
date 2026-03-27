# app/graph/nodes/decision_node.py

from domain.contracts.interview_state import InterviewState


class DecisionNode:

    def __init__(self, max_attempts: int = 3):
        self.max_attempts = max_attempts

    def __call__(self, state: InterviewState) -> InterviewState:

        question = state.current_question

        if question is None:
            return state

        result = state.get_result_for_question(question.id)

        if not result:
            return state

        evaluation = result.evaluation
        execution = result.execution

        attempts = state.get_attempt_for_question(question.id)

        # ---------------------------------------------------------
        # PASS → NEXT
        # ---------------------------------------------------------

        if evaluation:
            passed = evaluation.passed
        elif execution:
            passed = execution.success
        else:
            return state

        if passed:
            return state.model_copy(
                update={
                    "awaiting_user_input": False,
                    "last_action": "next",
                }
            )

        # ---------------------------------------------------------
        # FAIL → RETRY
        # ---------------------------------------------------------

        if attempts < self.max_attempts:
            return state.model_copy(
                update={
                    "awaiting_user_input": True,
                    "last_action": "retry",
                }
            )

        # ---------------------------------------------------------
        # FAIL → COMPLETE (no more retries)
        # ---------------------------------------------------------

        return state.model_copy(
            update={
                "awaiting_user_input": False,
                "last_action": "next",  # continua comunque
            }
        )
