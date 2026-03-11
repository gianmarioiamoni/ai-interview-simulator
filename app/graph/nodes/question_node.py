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

    # Humanize written questions
    if state.enable_humanizer and question.type == QuestionType.WRITTEN:

        prompt = build_humanizer_prompt(
            question=question,
            language=state.language,
            chat_history=state.chat_history,
        )

        response = llm.invoke(prompt)

        state.chat_history.append(response.content.strip())

    state.awaiting_user_input = True

    return state
