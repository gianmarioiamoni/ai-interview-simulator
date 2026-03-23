# app/ui/response/config/editor_mapper.py

from domain.contracts.question import QuestionType

from app.ui.dto.question_dto import QuestionDTO
from app.ui.ui_state import UIState
from app.ui.types.ui_fields import EditorVisibilityFields


class EditorMapper:

    @staticmethod
    def map(
        question: QuestionDTO,
        ui_state: UIState,
    ) -> EditorVisibilityFields:

        show_editor = ui_state != UIState.FEEDBACK

        return {
            "written_editor_visible": (
                question.type == QuestionType.WRITTEN and show_editor
            ),
            "coding_editor_visible": (
                question.type == QuestionType.CODING and show_editor
            ),
            "database_editor_visible": (
                question.type == QuestionType.DATABASE and show_editor
            ),
        }
