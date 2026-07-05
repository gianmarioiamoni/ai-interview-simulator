# app/ui/dto/builders/question_assessment_mapper.py
# EPIC-V13-05 Phase 9 — QuestionAssessmentMapper
# Maps QuestionAssessmentRecord → QuestionAssessmentDTO (direct field copy, no computation).

from domain.contracts.report.question_assessment_record import QuestionAssessmentRecord
from app.ui.dto.question_assessment_dto import QuestionAssessmentDTO


class QuestionAssessmentMapper:
    """Maps a QuestionAssessmentRecord to a QuestionAssessmentDTO.

    This is a direct field copy — no computation, no truncation.
    Truncation is a display concern; the stored record always carries the full text.
    """

    @staticmethod
    def to_dto(record: QuestionAssessmentRecord) -> QuestionAssessmentDTO:
        return QuestionAssessmentDTO(
            question_id=record.question_id,
            area=record.area_label,
            score=record.score,
            feedback=record.feedback,
            passed_tests=record.passed_tests,
            total_tests=record.total_tests,
            execution_status=record.execution_status,
            question_prompt=record.question_prompt,
            attempts=record.attempts,
            ai_hint_explanation=record.ai_hint_explanation,
            ai_hint_suggestion=record.ai_hint_suggestion,
            strengths=list(record.strengths),
            weaknesses=list(record.weaknesses),
            follow_up_question=record.follow_up_question,
        )
