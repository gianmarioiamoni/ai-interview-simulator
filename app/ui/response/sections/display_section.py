# app/ui/response/sections/display_section.py

from domain.contracts.interview_state import InterviewState
from domain.contracts.question import QuestionType

from app.ui.dto.question_dto import QuestionDTO
from app.ui.ui_state import UIState
from app.ui.types.ui_fields import DisplayFields

from app.ui.response.formatters.markdown_formatter import MarkdownFormatter


class DisplaySection:

    @staticmethod
    def build(
        state: InterviewState,
        question: QuestionDTO,
        ui_state: UIState,
        error_hint: str,
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

        if error_hint and has_previous_answer:
            prefix += MarkdownFormatter.error_block(error_hint)

        display_text = prefix + content

        return DisplaySection._map_by_question_type(
            question.type,
            display_text,
        )

    # =========================================================
    # CONTENT RESOLUTION
    # =========================================================

    @staticmethod
    def _resolve_content(
        state: InterviewState,
        question: QuestionDTO,
        ui_state: UIState,
        has_previous_answer: bool,
    ) -> str:

        last_answer = state.last_answer

        is_feedback = ui_state == UIState.FEEDBACK

        if is_feedback or has_previous_answer:
            if last_answer:
                return last_answer.content
            return ""

        return question.text

    # =========================================================
    # PREFIX RESOLUTION
    # =========================================================

    @staticmethod
    def _resolve_prefix(
        ui_state: UIState,
        has_previous_answer: bool,
    ) -> str:

        if ui_state == UIState.FEEDBACK:
            return "### Your Answer\n\n"

        if has_previous_answer:
            return "### Fix Your Previous Answer\n\n"

        return "### Question\n\n"

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
