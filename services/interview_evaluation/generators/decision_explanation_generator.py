# services/interview_evaluation/generators/decision_explanation_generator.py

import logging

logger = logging.getLogger(__name__)


class DecisionExplanationGenerator:

    def __init__(self, narrative_service):
        self._narrative_service = narrative_service

    def generate(self, decision, dimensions):

        try:
            return self._narrative_service.generate_decision_explanation(
                decision=decision,
                dimensions=dimensions,
            )
        except Exception:
            logger.warning("decision_explanation_generation_failed")
            return {"drivers": [], "blockers": []}
