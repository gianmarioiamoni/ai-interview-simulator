# services/interview_scoring/components/dimension_scorer.py

from typing import List, Dict
from domain.contracts.question.question import Question, QuestionType
from domain.contracts.question.question_evaluation import QuestionEvaluation
from domain.contracts.shared.performance_dimension_type import PerformanceDimensionType


AREA_TO_DIMENSION = {
    "technical_technical_knowledge": PerformanceDimensionType.TECHNICAL_DEPTH,
    "technical_database": PerformanceDimensionType.TECHNICAL_DEPTH,
    "technical_coding": PerformanceDimensionType.PROBLEM_SOLVING,
    "technical_case_study": PerformanceDimensionType.SYSTEM_DESIGN,
    "hr_background": PerformanceDimensionType.COMMUNICATION,
    "hr_technical_knowledge": PerformanceDimensionType.TECHNICAL_DEPTH,
    "hr_situational": PerformanceDimensionType.COMMUNICATION,
    "hr_brain_teaser": PerformanceDimensionType.PROBLEM_SOLVING,
    "hr_analytical": PerformanceDimensionType.PROBLEM_SOLVING,
}


class DimensionScorer:

    def compute(
        self,
        questions: List[Question],
        evaluations: List[QuestionEvaluation],
    ) -> Dict[PerformanceDimensionType, float]:

        question_map = {q.id: q for q in questions}
        dimension_map: Dict[PerformanceDimensionType, List[float]] = {}

        for ev in evaluations:

            question = question_map.get(ev.question_id)
            if not question:
                continue

            if question.type == QuestionType.WRITTEN:
                dimension = PerformanceDimensionType.COMMUNICATION
            else:
                dimension = AREA_TO_DIMENSION.get(question.area)

            if not dimension:
                continue

            dimension_map.setdefault(dimension, []).append(ev.score)

        return {
            dim: round(sum(scores) / len(scores), 1)
            for dim, scores in dimension_map.items()
            if scores
        }
