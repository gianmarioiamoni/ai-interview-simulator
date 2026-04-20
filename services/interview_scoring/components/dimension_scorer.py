# services/interview_scoring/components/dimension_scorer.py

from typing import List, Dict

from domain.contracts.question.question import Question
from domain.contracts.question.question_evaluation import QuestionEvaluation
from domain.contracts.shared.performance_dimension_type import PerformanceDimensionType
from domain.contracts.interview.interview_area import InterviewArea


AREA_TO_DIMENSION = {
    # TECH
    InterviewArea.TECH_TECHNICAL_KNOWLEDGE: PerformanceDimensionType.TECHNICAL_DEPTH,
    InterviewArea.TECH_DATABASE: PerformanceDimensionType.TECHNICAL_DEPTH,
    InterviewArea.TECH_CODING: PerformanceDimensionType.PROBLEM_SOLVING,
    InterviewArea.TECH_CASE_STUDY: PerformanceDimensionType.SYSTEM_DESIGN,
    InterviewArea.TECH_BACKGROUND: PerformanceDimensionType.TECHNICAL_DEPTH,
    # HR
    InterviewArea.HR_TECHNICAL_KNOWLEDGE: PerformanceDimensionType.TECHNICAL_DEPTH,
    InterviewArea.HR_SITUATIONAL: PerformanceDimensionType.COMMUNICATION,
    InterviewArea.HR_BRAIN_TEASER: PerformanceDimensionType.PROBLEM_SOLVING,
    InterviewArea.HR_ANALYTICAL: PerformanceDimensionType.PROBLEM_SOLVING,
    InterviewArea.HR_BACKGROUND: PerformanceDimensionType.COMMUNICATION,
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

            dimension = AREA_TO_DIMENSION.get(question.area)

            if not dimension:
                continue

            dimension_map.setdefault(dimension, []).append(ev.score)

        
        return {
            dim: round(sum(scores) / len(scores), 1)
            for dim, scores in dimension_map.items()
            if scores
        }
