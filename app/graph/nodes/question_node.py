# app/graph/nodes/question_node.py

from domain.contracts.interview_state import InterviewState
from domain.contracts.question import QuestionType
from services.prompt_builders.humanizer_prompt_builder import build_humanizer_prompt
from infrastructure.llm.llm_factory import get_llm


llm = get_llm()


def question_node(state: InterviewState) -> InterviewState:

    question = state.current_question

    if question is None:
        return state

    # ---------------------------------------------------------
    # Humanizer disabled
    # ---------------------------------------------------------

    if not state.enable_humanizer:
        state.awaiting_user_input = True
        return state

    # ---------------------------------------------------------
    # Prevent double humanization
    # ---------------------------------------------------------

    if state.current_question_index < len(state.chat_history):
        state.awaiting_user_input = True
        return state

    # ---------------------------------------------------------
    # Only written questions are humanized
    # ---------------------------------------------------------

    if question.type != QuestionType.WRITTEN:

        state.chat_history.append(question.prompt)
        state.awaiting_user_input = True
        return state

    # ---------------------------------------------------------
    # Build humanizer prompt
    # ---------------------------------------------------------

    prompt = build_humanizer_prompt(
        question=question,
        language=state.language,
        chat_history=state.chat_history,
    )

    response = llm.invoke(prompt)

    state.chat_history.append(response.content.strip())

    state.awaiting_user_input = True

    return state
