# app/ui/response/config/visibility_mapper.py

from domain.contracts.question import QuestionType
from app.ui.dto.question_dto import QuestionDTO
from app.ui.types.ui_fields import VisibilityFields


class VisibilityMapper:

    @staticmethod
    def map(question: QuestionDTO) -> VisibilityFields:

        return {
            "written_visible": question.type == QuestionType.WRITTEN,
            "coding_visible": question.type == QuestionType.CODING,
            "database_visible": question.type == QuestionType.DATABASE,
        }
