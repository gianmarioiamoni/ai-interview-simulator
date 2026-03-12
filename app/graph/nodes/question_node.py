# app/graph/nodes/question_node.py

from domain.contracts.interview_state import InterviewState
from domain.contracts.question import QuestionType
from services.prompt_builders.humanizer_prompt_builder import build_humanizer_prompt


def build_question_node(llm):

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

            state.chat_history.append(question.prompt)
            return state

        # ---------------------------------------------------------
        # Non written questions
        # ---------------------------------------------------------

        if question.type != QuestionType.WRITTEN:

            state.chat_history.append(question.prompt)
            return state

        # ---------------------------------------------------------
        # Humanize question
        # ---------------------------------------------------------

        prompt = build_humanizer_prompt(
            question=question,
            language=state.language,
            chat_history=state.chat_history,
        )

        response = llm.invoke(prompt)

        state.chat_history.append(response.content.strip())

        return state

    return question_node
