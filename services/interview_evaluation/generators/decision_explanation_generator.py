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
        print("✅ NEW DECISION GENERATOR ACTIVE")

        # -----------------------------------------------------
        # CALL NARRATIVE SERVICE (STRUCTURED)
        # -----------------------------------------------------

        result = self._narrative_service.generate_decision_explanation(
            decision=decision,
            dimensions=dimensions,
        )

        print("🔥 USING NARRATIVE SERVICE:", type(self._narrative_service))

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

                if not signal_strength:
                    continue

                # -----------------------------------------------------
                # SIGNAL-DRIVEN EXPLANATION (CONSISTENT LOGIC)
                # -----------------------------------------------------

                if signal_strength >= 0.8:
                    enriched_blockers.append(
                        f"Strong execution issues in {dim_name} "
                        f"(high signal strength {signal_strength})"
                    )

                elif signal_strength >= 0.5:
                    enriched_blockers.append(
                        f"Noticeable execution weaknesses in {dim_name} "
                        f"(signal strength {signal_strength})"
                    )

                elif signal_strength >= 0.3:
                    enriched_blockers.append(
                        f"Minor execution issues detected in {dim_name}"
                    )

            # -----------------------------------------------------
            # DUPLICATE FILTERING (BY DIMENSION)
            # -----------------------------------------------------

            existing_blockers_text = " ".join(blockers).lower()

            filtered_blockers = []

            for b in enriched_blockers:
                # evita duplicati sulla stessa dimensione
                if not any(
                    dim.get("name", "").lower() in b.lower() for dim in dimensions
                ):
                    continue

                if b.lower() not in existing_blockers_text:
                    filtered_blockers.append(b)

            # -----------------------------------------------------
            # LIMIT BLOCKERS (UX CONTROL)
            # -----------------------------------------------------

            filtered_blockers = filtered_blockers[:2]

            if filtered_blockers:
                blockers = blockers + filtered_blockers

        # -----------------------------------------------------
        # FINAL RETURN (ALWAYS SAFE)
        # -----------------------------------------------------

        return {
            "drivers": drivers,
            "blockers": blockers,
        }
