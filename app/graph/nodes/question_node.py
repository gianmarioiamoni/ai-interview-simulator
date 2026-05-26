# app/graph/nodes/question_node.py

from domain.contracts.interview_state import InterviewState
from domain.contracts.question.question import QuestionType

from services.humanizer.contracts.humanizer_input import HumanizerInput
from services.humanizer.contracts.humanizer_decision import HumanizerDecision
from services.humanizer.humanizer_service import HumanizerService


def build_question_node(llm):

    humanizer_service = HumanizerService(llm=llm)

    def question_node(state: InterviewState) -> InterviewState:

        question = state.current_question

        if question is None:
            return state

        if not state.enable_humanizer:
            return state

        # ---------------------------------------------------------
        # Prevent double processing
        # ---------------------------------------------------------

        if state.current_question_index < len(state.chat_history):
            return state

        # ---------------------------------------------------------
        # Humanizer disabled
        # ---------------------------------------------------------

        if not state.enable_humanizer:

            new_history = state.chat_history + [question.prompt]

            return state.model_copy(
                update={
                    "chat_history": new_history,
                }
            )

        # ---------------------------------------------------------
        # Non written questions
        # ---------------------------------------------------------

        if question.type != QuestionType.WRITTEN:

            new_history = state.chat_history + [question.prompt]

            return state.model_copy(
                update={
                    "chat_history": new_history,
                }
            )

        # ---------------------------------------------------------
        # INPUT
        # ---------------------------------------------------------

        last_answer = None
        last_score = None

        if state.answers:
            last_answer = state.answers[-1].content

        if state.last_feedback_bundle:
            last_score = int(state.last_feedback_bundle.overall_score)

        input_data = HumanizerInput(
            current_question=question,
            language=state.language,
            chat_history=state.chat_history,
            last_answer=last_answer,
            last_answer_score=last_score,
            follow_up_count=state.follow_up_count,
            last_turn_was_follow_up=state.last_humanizer_follow_up,
        )

        # ---------------------------------------------------------
        # HUMANIZE
        # ---------------------------------------------------------

        output = humanizer_service.humanize(
            input_data=input_data,
        )

        # ---------------------------------------------------------
        # UPDATE STATE
        # ---------------------------------------------------------
        is_follow_up = output.decision == HumanizerDecision.FOLLOW_UP
        follow_up_count = state.follow_up_count + 1 if is_follow_up else state.follow_up_count

        # ---------------------------------------------------------
        # UPDATE HISTORY
        # ---------------------------------------------------------

        new_history = state.chat_history + [output.message]

        return state.model_copy(
            update={
                "chat_history": new_history,
                "follow_up_count": follow_up_count,
                "last_humanizer_follow_up": is_follow_up,
            }
        )

    return question_node
