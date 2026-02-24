# app/graph/nodes/scoring_node.py

from domain.contracts.interview_state import InterviewState
from domain.contracts.execution_result import ExecutionStatus


def scoring_node(state: InterviewState) -> InterviewState:
    # Nothing to score
    if not state.questions:
        return state

    # Written questions
    if state.evaluations:
        last_evaluation = state.evaluations[-1]

        # Prevent double scoring of same question
        if state.current_question_id == last_evaluation.question_id:
            state.total_score += last_evaluation.score

    # Coding / SQL questions
    elif state.execution_results:
        last_execution = state.execution_results[-1]

        if state.current_question_id == last_execution.question_id:

            if last_execution.status == ExecutionStatus.SUCCESS:
                state.total_score += 100.0

            elif last_execution.status == ExecutionStatus.FAILED_TESTS:
                if last_execution.total_tests > 0:
                    ratio = last_execution.passed_tests / last_execution.total_tests
                    state.total_score += ratio * 100.0

            else:
                state.total_score += 0.0

    # Move pointer only if not follow-up
    if not state.last_was_follow_up:
        state.current_question_index += 1

        if state.current_question_index < len(state.questions):
            state.current_question_id = state.questions[state.current_question_index].id
        else:
            state.current_question_id = None

    return state
