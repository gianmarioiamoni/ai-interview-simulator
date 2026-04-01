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

        # 🔥 FIX: get answer ONLY for current question
        last_answer = state.last_answer

        if last_answer and last_answer.question_id == question.question_id:
            answer_for_current = last_answer
        else:
            answer_for_current = None

        is_feedback = ui_state == UIState.FEEDBACK

        # -----------------------------------------------------
        # SHOW ANSWER (feedback / retry)
        # -----------------------------------------------------

        if is_feedback or has_previous_answer:
            if answer_for_current:
                return answer_for_current.content
            return ""

        # -----------------------------------------------------
        # SHOW QUESTION
        # -----------------------------------------------------

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
