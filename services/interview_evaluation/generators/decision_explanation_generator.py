# services/interview_evaluation/generators/decision_explanation_generator.py

import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class DecisionExplanationGenerator:

    def __init__(self, narrative_service):
        self._narrative_service = narrative_service

    # ---------------------------------------------------------
    # MAIN GENERATION
    # ---------------------------------------------------------

    def generate(
        self,
        decision: str,
        dimensions: List[Dict[str, Any]],
        dimension_signals: Dict[str, float] | None = None,
    ) -> Dict[str, List[str]]:

        # -----------------------------------------------------
        # CALL NARRATIVE SERVICE (STRUCTURED)
        # -----------------------------------------------------

        try:
            result = self._narrative_service.generate_decision_explanation(
                decision=decision,
                dimensions=dimensions,
            )

        except Exception as e:
            logger.warning(f"decision_explanation_exception: {e}")
            result = {"drivers": [], "blockers": []}

        # -----------------------------------------------------
        # NORMALIZE OUTPUT (DEFENSIVE)
        # -----------------------------------------------------

        drivers = result.get("drivers") if isinstance(result, dict) else []
        blockers = result.get("blockers") if isinstance(result, dict) else []

        if not isinstance(drivers, list):
            drivers = []

        if not isinstance(blockers, list):
            blockers = []

        # -----------------------------------------------------
        # FALLBACK (DETERMINISTIC)
        # -----------------------------------------------------

        if not drivers and not blockers:

            if not dimensions:
                return {
                    "drivers": ["Evaluation completed"],
                    "blockers": ["No significant issues identified"],
                }

            strongest_dim = max(dimensions, key=lambda x: x.get("score", 0))
            weakest_dim = min(dimensions, key=lambda x: x.get("score", 0))

            strongest = strongest_dim.get("name", "Unknown")
            weakest = weakest_dim.get("name", "Unknown")
            weakest_score = weakest_dim.get("score", 0)

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

            normalized_signals = {
                (k.value if hasattr(k, "value") else k): v
                for k, v in dimension_signals.items()
            }

            enriched_blockers = []

            for dim in dimensions:

                dim_name = dim.get("name")
                dim_score = dim.get("score")

                if not dim_name or dim_score is None:
                    continue

                dim_key = dim_name.lower().replace(" ", "_")
                signal_strength = normalized_signals.get(dim_key)

                # conservative threshold to avoid noise
                if signal_strength and dim_score < 75:

                    enriched_blockers.append(
                        f"Issues in {dim_name} reflected by execution signals "
                        f"(signal strength {signal_strength})"
                    )

            if enriched_blockers:
                blockers = blockers + enriched_blockers

        # -----------------------------------------------------
        # FINAL RETURN (ALWAYS SAFE)
        # -----------------------------------------------------

        return {
            "drivers": drivers,
            "blockers": blockers,
        }
