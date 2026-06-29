# services/interview_evaluation/generators/executive_summary_generator.py

from app.core.logger import get_logger

logger = get_logger(__name__)


class ExecutiveSummaryGenerator:

    def __init__(self, narrative_service):
        self._narrative_service = narrative_service

    def generate(
        self,
        decision,
        overall_score,
        strongest,
        weakest,
        percentile,
        strongest_score,
        weakest_score,
        context_profile=None,
        evaluations=None,
        seniority_level: str = "mid",
        role: str = "backend engineer",
    ):

        try:
            return self._narrative_service.generate_executive_summary(
                decision=decision,
                overall_score=overall_score,
                strongest=strongest,
                weakest=weakest,
                percentile=percentile,
                strongest_score=strongest_score,
                weakest_score=weakest_score,
                context_profile=context_profile,
                evaluations=evaluations,
                seniority_level=seniority_level,
                role=role,
            )
        except Exception as e:
            logger.exception("executive_summary_generation_failed")
            return None
