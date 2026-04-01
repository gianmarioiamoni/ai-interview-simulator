# app/ui/response/sections/display_section.py

from domain.contracts.interview_state import InterviewState
from domain.contracts.question import QuestionType

from app.ui.dto.question_dto import QuestionDTO
from app.ui.ui_state import UIState
from app.ui.types.ui_fields import DisplayFields


class DisplaySection:

    @staticmethod
    def build(
        state: InterviewState,
        question: QuestionDTO,
        ui_state: UIState,
        has_previous_answer: bool,
    ) -> DisplayFields:

        content = DisplaySection._resolve_content(
            state,
            question,
            ui_state,
            has_previous_answer,
        )

        prefix = DisplaySection._resolve_prefix(
            ui_state,
            has_previous_answer,
        )

        display_text = prefix + content

        return DisplaySection._map_by_question_type(
            question.type,
            display_text,
        )

    # =========================================================
    # CONTENT
    # =========================================================

    @staticmethod
    def _resolve_content(
        state: InterviewState,
        question: QuestionDTO,
        ui_state: UIState,
        has_previous_answer: bool,
    ) -> str:

        # ONLY get answer for current question
        last_answer = state.get_latest_answer_for_question(question.question_id)

        is_feedback = ui_state == UIState.FEEDBACK

        # show answer only if it's for the current question
        if is_feedback or has_previous_answer:
            if last_answer:
                return last_answer.content
            return ""

        # otherwise show question
        return question.text

    # =========================================================
    # PREFIX
    # =========================================================

    @staticmethod
    def _resolve_prefix(
        ui_state: UIState,
        has_previous_answer: bool,
    ) -> str:

        if ui_state == UIState.FEEDBACK:
            return "### 🧾 Your Answer\n\n"

        if has_previous_answer:
            return "### ✏️ Improve Your Answer\n\n"

        return "### 📌 Question\n\n"

    # =========================================================
    # MAPPING
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
