# services/interview_evaluation/generators/decision_explanation_generator.py

import logging

logger = logging.getLogger(__name__)


class DecisionExplanationGenerator:

    def __init__(self, narrative_service):
        self._narrative_service = narrative_service

    def generate(self, decision, dimensions):

        try:
            result = self._narrative_service.generate_decision_explanation(
                decision=decision,
                dimensions=dimensions,
            )

        except Exception:
            logger.warning("decision_explanation_generation_failed")
            result = {"drivers": [], "blockers": []}

        # -----------------------------------------------------
        # FALLBACK (CRUCIALE)
        # -----------------------------------------------------

        drivers = result.get("drivers") or []
        blockers = result.get("blockers") or []

        if not drivers and not blockers:

            strongest = max(dimensions, key=lambda x: x["score"])["name"] if dimensions else None
            weakest = min(dimensions, key=lambda x: x["score"])["name"] if dimensions else None
    
            return {
                "drivers": [f"Strong performance in {strongest}"] if strongest else ["Evaluation completed"],
                "blockers": [f"Weak performance in {weakest}"] if weakest else ["No significant strengths identified"],
            }

        return result
