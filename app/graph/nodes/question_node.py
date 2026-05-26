# app/graph/nodes/question_node.py

from domain.contracts.interview_state import InterviewState
from domain.contracts.question.question import QuestionType

from services.humanizer.contracts.humanizer_input import HumanizerInput
from services.humanizer.humanizer_service import HumanizerService


def build_question_node(llm):

    humanizer_service = HumanizerService(
        llm=llm,
    )

    def question_node(state: InterviewState) -> InterviewState:

        question = state.current_question

        if question is None:
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

        input_data = HumanizerInput(
            current_question=question,
            language=state.language,
            chat_history=state.chat_history,
        )

        # ---------------------------------------------------------
        # HUMANIZE
        # ---------------------------------------------------------

        output = humanizer_service.humanize(
            input_data=input_data,
        )

        # ---------------------------------------------------------
        # UPDATE HISTORY
        # ---------------------------------------------------------

        new_history = state.chat_history + [output.message]

        return state.model_copy(
            update={
                "chat_history": new_history,
            }
        )

    return question_node
