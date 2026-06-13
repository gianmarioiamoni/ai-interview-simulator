# services/interview_evaluation/generators/signal_enrichment_builder.py

"""
Enriches driver and blocker lists using per-dimension signal data.

Extracted from DecisionExplanationGenerator to isolate the signal-reading
loop and its two enrichment policies (driver threshold, blocker threshold)
from the main orchestration flow.
"""

from typing import Dict, List, Any

from infrastructure.config.evaluation import (
    NARRATIVE_DRIVER_SIGNAL_THRESHOLD,
    NARRATIVE_DRIVER_SCORE_THRESHOLD,
    NARRATIVE_BLOCKER_SCORE_THRESHOLD,
    NARRATIVE_BLOCKER_SIGNAL_THRESHOLD,
    NARRATIVE_BLOCKER_SIGNAL_SCORE_THRESHOLD,
)
from services.interview_evaluation.generators.causal_explanation_builder import (
    CausalExplanationBuilder,
)


class SignalEnrichmentBuilder:
    """
    Produces supplementary driver and blocker strings by cross-referencing
    dimension scores with signal-strength data.

    Stateless — depends only on injected CausalExplanationBuilder.
    """

    def __init__(self, causal_builder: CausalExplanationBuilder) -> None:
        self._causal_builder = causal_builder

    def build(
        self,
        dimensions: List[Dict[str, Any]],
        dimension_signals: Dict[str, float],
        covered_dimensions: set[str],
    ) -> tuple[List[str], List[str]]:
        """
        Return (enriched_drivers, enriched_blockers) for uncovered dimensions.

        covered_dimensions — dimension names (lowercased) already represented
        in the existing blocker list; these are skipped to avoid duplication.
        """
        normalized_signals = {
            (k.value.lower() if hasattr(k, "value") else str(k).lower()): v
            for k, v in dimension_signals.items()
        }

        enriched_drivers: List[str] = []
        enriched_blockers: List[str] = []

        for dim in dimensions:
            dim_name = dim.get("name")
            dim_score = dim.get("score")

            if not dim_name or dim_score is None:
                continue

            if dim_name.lower() in covered_dimensions:
                continue

            dim_key = dim_name.lower().replace(" ", "_")
            signal_strength = normalized_signals.get(dim_key)

            if (
                signal_strength
                and signal_strength >= NARRATIVE_DRIVER_SIGNAL_THRESHOLD
                and dim_score >= NARRATIVE_DRIVER_SCORE_THRESHOLD
            ):
                enriched_drivers.append(
                    f"Consistent strong execution in {dim_name}"
                )

            if dim_score < NARRATIVE_BLOCKER_SCORE_THRESHOLD or (
                signal_strength
                and signal_strength >= NARRATIVE_BLOCKER_SIGNAL_THRESHOLD
                and dim_score < NARRATIVE_BLOCKER_SIGNAL_SCORE_THRESHOLD
            ):
                enriched_blockers.append(
                    self._causal_builder.build(dim_name, dim_score, signal_strength)
                )

        return enriched_drivers, enriched_blockers
