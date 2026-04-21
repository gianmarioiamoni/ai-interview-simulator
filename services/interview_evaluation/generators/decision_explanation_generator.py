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

        except Exception as e:
            logger.warning(f"decision_explanation_exception: {e}")
            result = {"drivers": [], "blockers": []}

        drivers = result.get("drivers") or []
        blockers = result.get("blockers") or []

        # -----------------------------------------------------
        # FALLBACK (SEMANTICO CORRETTO)
        # -----------------------------------------------------

        if not drivers and not blockers:

            if not dimensions:
                return {
                    "drivers": ["Evaluation completed"],
                    "blockers": ["No significant issues identified"],
                }

            strongest_dim = max(dimensions, key=lambda x: x["score"])
            weakest_dim = min(dimensions, key=lambda x: x["score"])

            strongest = strongest_dim["name"]
            weakest = weakest_dim["name"]
            weakest_score = weakest_dim["score"]

            if weakest_score >= 80:
                blocker = f"Area for improvement in {weakest}"
            elif weakest_score >= 70:
                blocker = f"Moderate improvement needed in {weakest}"
            else:
                blocker = f"Weak performance in {weakest}"

            return {
                "drivers": [f"Strong performance in {strongest}"],
                "blockers": [blocker],
            }

        return result
