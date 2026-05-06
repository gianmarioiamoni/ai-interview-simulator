# app/ui/response/sections/display_section.py

from domain.contracts.interview_state import InterviewState
from domain.contracts.question.question import QuestionType

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

        print("\n=== DISPLAY SECTION DEBUG ===")
        print("area:", question.area)
        print("type:", question.type)
        print("ui_state:", ui_state)
        print("has_previous_answer:", has_previous_answer)

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

        display_text = prefix + (content or "")

        print("content:", content)
        print("display_text:", display_text)
        print("=============================\n")

        return DisplaySection._map_by_question_type(
            question.type,
            display_text,
        )

    @staticmethod
    def _resolve_content(
        state: InterviewState,
        question: QuestionDTO,
        ui_state: UIState,
        has_previous_answer: bool,
    ) -> str:

        last_answer = state.get_latest_answer_for_question(question.question_id)

        is_feedback = ui_state == UIState.FEEDBACK

        if is_feedback or has_previous_answer:
            if last_answer:
                return last_answer.content
            return ""

        print("QUESTION TEXT:", question.text)
        return question.text or ""

    @staticmethod
    def _resolve_prefix(
        ui_state: UIState,
        has_previous_answer: bool,
    ) -> str:

        # FEEDBACK
        if ui_state == UIState.FEEDBACK:
            return "### Your Answer\n\n"

        # IMPROVE
        if has_previous_answer:
            return "### Improve Your Answer\n\n"

        # QUESTION
        return ""

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
