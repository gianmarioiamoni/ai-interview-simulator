# app/ui/mappers/interview_state_mapper.py

from typing import List, Optional, Dict

from domain.contracts.interview_state import InterviewState
from domain.contracts.interview_progress import InterviewProgress
from domain.contracts.question import Question
from domain.contracts.question_evaluation import QuestionEvaluation

from app.ui.dto.question_dto import QuestionDTO
from app.ui.dto.interview_session_dto import InterviewSessionDTO
from app.ui.dto.final_report_dto import FinalReportDTO
from app.ui.dto.dimension_score_dto import DimensionScoreDTO
from app.ui.dto.question_assessment_dto import QuestionAssessmentDTO


class InterviewStateMapper:
    # Maps InterviewState (domain layer) into UI-safe DTOs.
    # Contains no business logic.

    # ---------------------------------------------------------
    # DTO session
    # ---------------------------------------------------------

    def to_session_dto(self, state: InterviewState) -> InterviewSessionDTO:

        is_completed = state.progress == InterviewProgress.COMPLETED

        if is_completed:
            return InterviewSessionDTO(
                session_id=state.interview_id,
                current_question=None,
                is_completed=True,
                current_area=None,
            )

        current_question = self._extract_current_question(state)

        if current_question is None:
            return InterviewSessionDTO(
                session_id=state.interview_id,
                current_question=None,
                is_completed=False,
                current_area=None,
            )

        question_dto = self._map_question(
            question=current_question,
            index=state.current_question_index + 1,
            total=len(state.questions),
        )

        return InterviewSessionDTO(
            session_id=state.interview_id,
            current_question=question_dto,
            is_completed=False,
            current_area=current_question.area,
        )

    # ---------------------------------------------------------
    # Final repor
    # ---------------------------------------------------------

    def to_final_report_dto(self, state: InterviewState) -> FinalReportDTO:

        question_assessments = [
            QuestionAssessmentDTO(
                question_id=ev.question_id,
                score=ev.score,
                feedback=ev.feedback,
            )
            for ev in state.evaluations
        ]

        dimension_scores = self._aggregate_dimension_scores(
            state.questions,
            state.evaluations,
        )

        improvement_suggestions = self._aggregate_weaknesses(state.evaluations)

        overall_score = state.final_evaluation.overall_score

        return FinalReportDTO(
            overall_score=overall_score,
            hiring_probability=state.final_evaluation.hiring_probability,
            dimension_scores=dimension_scores,
            question_assessments=question_assessments,
            improvement_suggestions=improvement_suggestions,
            total_tokens_used=0,
        )

    # ---------------------------------------------------------
    # Private helpers
    # ---------------------------------------------------------

    def _extract_current_question(self, state: InterviewState) -> Optional[Question]:

        if not state.questions:
            return None

        if state.current_question_index >= len(state.questions):
            return None

        return state.questions[state.current_question_index]

    def _map_question(
        self,
        question: Question,
        index: int,
        total: int,
    ) -> QuestionDTO:

        return QuestionDTO(
            question_id=question.id,
            text=question.prompt,
            question_type=question.type.value,
            area=question.area,
            index=index,
            total=total,
        )

    def _aggregate_dimension_scores(
        self,
        questions: List[Question],
        evaluations: List[QuestionEvaluation],
    ) -> List[DimensionScoreDTO]:

        # Map question_id -> area
        question_area_map: Dict[str, str] = {q.id: q.area for q in questions}

        dimension_map: Dict[str, List[float]] = {}

        for ev in evaluations:
            area = question_area_map.get(ev.question_id)
            if area is None:
                continue

            dimension_map.setdefault(area, []).append(ev.score)

        result: List[DimensionScoreDTO] = []

        for area, scores in dimension_map.items():
            average = sum(scores) / len(scores)
            result.append(
                DimensionScoreDTO(
                    name=area,
                    score=average,
                    max_score=100.0,
                )
            )

        return result

    def _aggregate_weaknesses(
        self,
        evaluations: List[QuestionEvaluation],
    ) -> List[str]:

        weaknesses: List[str] = []

        for ev in evaluations:
            weaknesses.extend(ev.weaknesses)

        # Remove duplicates while preserving order
        seen = set()
        unique_weaknesses = []
        for w in weaknesses:
            if w not in seen:
                seen.add(w)
                unique_weaknesses.append(w)

        return unique_weaknesses
