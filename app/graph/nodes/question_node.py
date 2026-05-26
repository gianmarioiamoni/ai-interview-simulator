# app/graph/nodes/question_node.py

from domain.contracts.interview_state import InterviewState
from domain.contracts.question.question import QuestionType

from services.humanizer.builders.humanizer_prompt_builder import HumanizerPromptBuilder
from services.humanizer.contracts.humanizer_input import HumanizerInput
from services.humanizer.contracts.humanizer_decision import HumanizerDecision


def build_question_node(llm):

    prompt_builder = HumanizerPromptBuilder()

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
        # Build humanizer input
        # ---------------------------------------------------------

        input_data = HumanizerInput(
            current_question=question,
            language=state.language,
            chat_history=state.chat_history,
        )

        # ---------------------------------------------------------
        # Transitional plain-question mode
        # ---------------------------------------------------------

        prompt = prompt_builder.build(
            input_data=input_data,
            decision=HumanizerDecision.PLAIN_QUESTION,
        )

        # ---------------------------------------------------------
        # Invoke LLM
        # ---------------------------------------------------------

        response = llm.invoke(prompt)

        new_message = response.content.strip()

        new_history = state.chat_history + [new_message]

        return state.model_copy(
            update={
                "chat_history": new_history,
            }
        )

    return question_node
