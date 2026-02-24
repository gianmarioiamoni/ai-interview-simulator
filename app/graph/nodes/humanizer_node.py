# app/graph/nodes/humanizer_node.py

from domain.contracts.interview_state import InterviewState
from services.prompt_builders.humanizer_prompt_builder import (
    build_humanizer_prompt,
)
from app.ports.llm_port import LLMPort
from domain.contracts.question import QuestionType


def build_humanizer_node(llm: LLMPort):

    def humanizer_node(state: InterviewState) -> InterviewState:

        # 1️⃣ Feature disabilitata
        if not state.enable_humanizer:
            return state

        # 2️⃣ Nessuna domanda corrente
        if state.current_question_id is None:
            return state

        question = next(
            (q for q in state.questions if q.id == state.current_question_id),
            None,
        )

        if question is None:
            return state

        # 3️⃣ Check if this specific question was already humanized
        # We track this by checking if we already have chat_history entries
        # for this question index. Since chat_history grows with each question,
        # and questions are processed in order, we can check:
        # - If current_question_index < len(chat_history), this question was already processed
        if state.current_question_index < len(state.chat_history):
            return state

        # 4️⃣ Solo domande scritte vengono humanizzate
        if question.type != QuestionType.WRITTEN:
            state.chat_history.append(question.prompt)
            return state

        # 5️⃣ Costruzione prompt humanizer
        prompt = build_humanizer_prompt(
            question=question,
            language=state.language,
            chat_history=state.chat_history,
        )

        response = llm.invoke(prompt)

        state.chat_history.append(response.content.strip())

        return state

    return humanizer_node
