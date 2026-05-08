# app/ui/response/sections/display_section.py

from domain.contracts.interview_state import InterviewState
from domain.contracts.question.question import Question, QuestionType

from app.ui.ui_state import UIState
from app.ui.types.ui_fields import DisplayFields


class DisplaySection:

    @staticmethod
    def build(
        state: InterviewState,
        question: Question,
        ui_state: UIState,
        has_previous_answer: bool,
    ) -> DisplayFields:

        display_text = DisplaySection._build_full_text(
            state,
            question,
            ui_state,
            has_previous_answer,
        )

        return DisplaySection._map_by_question_type(
            question.type,
            display_text,
        )

    # =========================================================
    # CORE TEXT BUILDER (FIX ARCHITETTURALE)
    # =========================================================

    @staticmethod
    def _build_full_text(
        state: InterviewState,
        question: Question,
        ui_state: UIState,
        has_previous_answer: bool,
    ) -> str:

        parts: list[str] = []

        # -----------------------------------------------------
        # ALWAYS SHOW QUESTION
        # -----------------------------------------------------

        if question.prompt:
            parts.append(f"### Question\n\n{question.prompt.strip()}")

        last_answer = state.get_latest_answer_for_question(question.id)

        # -----------------------------------------------------
        # FEEDBACK → show submitted answer
        # -----------------------------------------------------

        if ui_state == UIState.FEEDBACK and last_answer:
            parts.append(f"\n\n### Your Answer\n\n{last_answer.content}")

        # -----------------------------------------------------
        # RETRY / IMPROVE → show previous answer
        # -----------------------------------------------------

        elif has_previous_answer and last_answer:
            parts.append(f"\n\n### Previous Answer\n\n{last_answer.content}")

        return "\n".join(parts)

    # =========================================================
    # MAPPING BY TYPE
    # =========================================================

    @staticmethod
    def _map_by_question_type(
        qtype: QuestionType,
        text: str,
    ) -> DisplayFields:

        return {
            "written_display": text if qtype == QuestionType.WRITTEN else "",
            "coding_display": text if qtype == QuestionType.CODING else "",
            "database_display": text if qtype == QuestionType.DATABASE else "",
        }
