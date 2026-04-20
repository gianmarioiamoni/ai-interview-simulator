# services/interview_evaluation/generators/executive_summary_generator.py

import logging

logger = logging.getLogger(__name__)


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
            )
        except Exception:
            logger.warning("executive_summary_generation_failed")
            return None
