# app/graph/nodes/progression_node.py

from domain.contracts.interview_state import InterviewState
from domain.contracts.question import Question


def build_progression_node():

    def progression_node(state: InterviewState) -> InterviewState:

        question = state.current_question
        last_eval = state.evaluations[-1] if state.evaluations else None

        if question is None or last_eval is None:
            return state

        # ---------------------------------------------------------
        # FOLLOW-UP LOGIC
        # ---------------------------------------------------------

        clarification_needed = getattr(last_eval, "clarification_needed", False)
        follow_up_question = getattr(last_eval, "follow_up_question", None)

        can_generate_followup = (
            clarification_needed
            and state.follow_up_count < 2
            and not state.last_was_follow_up
            and follow_up_question
        )

        if can_generate_followup:

            followup = Question(
                id=f"{question.id}_followup_{state.follow_up_count + 1}",
                area=question.area,
                type=question.type,
                prompt=follow_up_question,
                difficulty=question.difficulty,
            )

            new_questions = (
                state.questions[: state.current_question_index + 1]
                + [followup]
                + state.questions[state.current_question_index + 1 :]
            )

            return state.model_copy(
                update={
                    "questions": new_questions,
                    "current_question_index": state.current_question_index + 1,
                    "follow_up_count": state.follow_up_count + 1,
                    "last_was_follow_up": True,
                }
            )

        # ---------------------------------------------------------
        # NORMAL PROGRESSION
        # ---------------------------------------------------------

        next_index = state.current_question_index + 1

        return state.model_copy(
            update={
                "current_question_index": next_index,
                "last_was_follow_up": False,
            }
        )

    return progression_node
