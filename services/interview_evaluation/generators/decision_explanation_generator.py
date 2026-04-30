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
        # CALL NARRATIVE SERVICE
        # -----------------------------------------------------

        result = self._narrative_service.generate_decision_explanation(
            decision=decision,
            dimensions=dimensions,
            dimension_signals=dimension_signals,
        )

        print("🔥 USING NARRATIVE SERVICE:", type(self._narrative_service))

        # -----------------------------------------------------
        # NORMALIZE OUTPUT (CRITICAL)
        # -----------------------------------------------------

        raw_drivers = result.get("drivers") if isinstance(result, dict) else []
        raw_blockers = result.get("blockers") if isinstance(result, dict) else []

        drivers = self._normalize_items(raw_drivers)
        existing_drivers_text = " ".join(drivers).lower()

        filtered_drivers = [
            d for d in enriched_drivers 
            if d.lower() not in existing_drivers_text
        ]

        drivers = drivers + filtered_drivers[:2]

        blockers = self._normalize_items(raw_blockers)

        # -----------------------------------------------------
        # FALLBACK
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
        # ENRICH WITH SIGNALS (CAUSAL + DEDUP)
        # -----------------------------------------------------

        if dimension_signals:

            normalized_signals = {
                (k.value.lower() if hasattr(k, "value") else str(k).lower()): v
                for k, v in dimension_signals.items()
            }

            # -------------------------------------------------
            # DETECT COVERED DIMENSIONS (LLM already used)
            # -------------------------------------------------

            covered_dimensions = set()

            for b in blockers:
                b_lower = b.lower()
                for dim in dimensions:
                    name = dim.get("name", "").lower()
                    if name and name in b_lower:
                        covered_dimensions.add(name)

            # -------------------------------------------------
            # BUILD ENRICHMENT
            # -------------------------------------------------

            enriched_blockers = []
            enriched_drivers = []

            for dim in dimensions:

                dim_name = dim.get("name")
                dim_score = dim.get("score")

                if not dim_name or dim_score is None:
                    continue

                dim_key = dim_name.lower().replace(" ", "_")

                # skip if already covered by LLM
                if dim_name.lower() in covered_dimensions:
                    continue

                signal_strength = normalized_signals.get(dim_key)

                # -------------------------------------------------
                # DRIVER ENRICHMENT 
                # -------------------------------------------------
                if signal_strength and signal_strength >= 0.8 and dim_score >= 85:
                    enriched_drivers.append(
                        f"Consistent strong execution in {dim_name}"
                    )

                # trigger only if meaningful
                if dim_score < 75 or (signal_strength and signal_strength >= 0.7):

                    explanation = self._build_causal_explanation(
                        dim_name,
                        dim_score,
                        signal_strength,
                    )

                    enriched_blockers.append(explanation)


            # -------------------------------------------------
            # FILTER DUPLICATES (TEXT LEVEL)
            # -------------------------------------------------

            existing_blockers_text = " ".join(blockers).lower()

            filtered_blockers = [
                b for b in enriched_blockers if b.lower() not in existing_blockers_text
            ]

            # -------------------------------------------------
            # LIMIT (UX)
            # -------------------------------------------------

            filtered_blockers = filtered_blockers[:2]

            if filtered_blockers:
                blockers = blockers + filtered_blockers

        # -----------------------------------------------------
        # FINAL
        # -----------------------------------------------------

        return {
            "drivers": drivers,
            "blockers": blockers,
        }

    # ---------------------------------------------------------
    # NORMALIZATION
    # ---------------------------------------------------------

    def _normalize_items(self, items: Any) -> List[str]:

        if not isinstance(items, list):
            return []

        normalized = []

        for item in items:

            if isinstance(item, str):
                normalized.append(item)

            elif isinstance(item, dict):
                text = item.get("justification") or item.get("text")
                if text:
                    normalized.append(text)

        return normalized

    # ---------------------------------------------------------
    # CAUSAL EXPLANATION BUILDER
    # ---------------------------------------------------------

    def _build_causal_explanation(
        self,
        dim_name: str,
        dim_score: float,
        signal_strength: float | None,
    ) -> str:

        dim_lower = dim_name.lower()

        if "system design" in dim_lower:
            base_cause = "limited architectural reasoning and lack of structured system trade-offs"
        elif "technical depth" in dim_lower:
            base_cause = "insufficient depth in core technical concepts and incomplete understanding of underlying mechanisms"
        elif "problem solving" in dim_lower:
            base_cause = "inconsistent reasoning and gaps in handling edge cases"
        elif "communication" in dim_lower:
            base_cause = "lack of clarity and structured explanation of ideas"
        else:
            base_cause = "inconsistent performance"

        if signal_strength and signal_strength >= 0.8:
            evidence = "strongly reinforced by execution failures"
        elif signal_strength and signal_strength >= 0.5:
            evidence = "supported by execution inconsistencies"
        elif signal_strength and signal_strength >= 0.3:
            evidence = "partially reflected in execution signals"
        else:
            evidence = None

        if dim_score < 70:
            sentence = f"{dim_name} is weak due to {base_cause}"
        elif dim_score < 80:
            sentence = f"{dim_name} shows gaps due to {base_cause}"
        else:
            sentence = (
                f"{dim_name} is solid, though some limitations remain in {base_cause}"
            )

        if evidence:
            sentence += f", {evidence}"

        return sentence
