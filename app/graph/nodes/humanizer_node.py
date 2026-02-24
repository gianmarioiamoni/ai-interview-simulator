# app/graph/nodes/humanizer_node.py

from domain.contracts.interview_state import InterviewState
from services.prompt_builders.humanizer_prompt_builder import (
    build_humanizer_prompt,
)
from app.ports.llm_port import LLMPort


def build_humanizer_node(llm: LLMPort):

    def humanizer_node(state: InterviewState) -> InterviewState:

        if not state.enable_humanizer:
            return state

        if state.current_question_id is None:
            return state

        question = next(
            (q for q in state.questions if q.id == state.current_question_id), None
        )

        if question is None:
            return state

        if question.type != "written":
            state.chat_history.append(question.content)
            return state

        prompt = build_humanizer_prompt(
            question=question,
            language=state.language,
            chat_history=state.chat_history,
        )

        response = llm.invoke(prompt)

        state.chat_history.append(response.content.strip())

        return state

    return humanizer_node
