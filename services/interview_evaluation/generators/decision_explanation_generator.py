# services/interview_evaluation/generators/decision_explanation_generator.py

import logging
import re
import json

logger = logging.getLogger(__name__)


class DecisionExplanationGenerator:

    def __init__(self, narrative_service):
        self._narrative_service = narrative_service

    def generate(self, decision, dimensions, dimension_signals=None):



        try:
            result = self._narrative_service.generate_decision_explanation(
                decision=decision,
                dimensions=dimensions,
            )

        except Exception as e:
            logger.warning(f"decision_explanation_exception: {e}")
            result = {"drivers": [], "blockers": []}

        # -----------------------------------------------------
        # NORMALIZE OUTPUT (CRITICAL)
        # -----------------------------------------------------

        drivers = result.get("drivers") or []
        blockers = result.get("blockers") or []

        # -----------------------------------------------------
        # FALLBACK
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

            if weakest_score >= 85:
                blocker = f"Area for improvement in {weakest}"
            elif weakest_score >= 75:
                blocker = f"Moderate improvement needed in {weakest}"
            else:
                blocker = f"Weak performance in {weakest}"

            return {
                "drivers": [f"Strong performance in {strongest}"],
                "blockers": [blocker],
            }

        # -----------------------------------------------------
        # ENRICH WITH RUNTIME SIGNALS
        # -----------------------------------------------------

        if dimension_signals:

            # normalize keys (enum → string)
            normalized_signals = {
                (k.value if hasattr(k, "value") else k): v
                for k, v in dimension_signals.items()
            }

            enriched_blockers = []

            for dim in dimensions:

                dim_name = dim["name"]
                dim_score = dim["score"]

                # es: "Problem Solving" → "problem_solving"
                dim_key = dim_name.lower().replace(" ", "_")

                signal_strength = normalized_signals.get(dim_key)

                if signal_strength and dim_score < 75:

                    enriched_blockers.append(
                        f"Issues in {dim_name} reflected by execution errors "
                        f"(signal strength {signal_strength})"
                    )

            if enriched_blockers:
                blockers = blockers + enriched_blockers

        # -----------------------------------------------------
        # FINAL RETURN (ALWAYS NORMALIZED)
        # -----------------------------------------------------

        return {
            "drivers": drivers,
            "blockers": blockers,
        }

