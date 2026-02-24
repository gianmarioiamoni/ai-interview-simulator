# app/graph/nodes/scoring_node.py

# Responsibility:
# Extract score from EvaluationResult
# Append score to scores
# Increment current_question_index SOLO se non followup

from domain.contracts.interview_state import InterviewState


def scoring_node(state: InterviewState) -> InterviewState:
    if state.evaluation_result:
        state.scores.append(state.evaluation_result.score)

    # Advance only if not follow-up
    if not state.last_was_followup:
        state.current_question_index += 1

    return state
