# services/interview_evaluation/generators/decision_explanation_generator.py

from typing import Dict, List, Any

from app.core.logger import get_logger
from infrastructure.config.evaluation import (
    NARRATIVE_WEAKEST_BLOCKER_MILD,
    NARRATIVE_WEAKEST_BLOCKER_MODERATE,
)
from services.interview_evaluation.generators.causal_explanation_builder import (
    CausalExplanationBuilder,
)
from services.interview_evaluation.generators.signal_enrichment_builder import (
    SignalEnrichmentBuilder,
)

logger = get_logger(__name__)


class DecisionExplanationGenerator:

    def __init__(self, narrative_service) -> None:
        self._narrative_service = narrative_service
        self._causal_builder = CausalExplanationBuilder()
        self._enrichment_builder = SignalEnrichmentBuilder(self._causal_builder)

    # ---------------------------------------------------------
    # PUBLIC
    # ---------------------------------------------------------

    def generate(
        self,
        decision: str,
        dimensions: List[Dict[str, Any]],
        dimension_signals: Dict[str, float] | None = None,
    ) -> Dict[str, List[str]]:

        result = self._narrative_service.generate_decision_explanation(
            decision=decision,
            dimensions=dimensions,
            dimension_signals=dimension_signals,
        )

        raw_drivers = result.get("drivers") if isinstance(result, dict) else []
        raw_blockers = result.get("blockers") if isinstance(result, dict) else []

        drivers = self._normalize_items(raw_drivers)
        blockers = self._normalize_items(raw_blockers)

        if not drivers and not blockers:
            return self._fallback(dimensions)

        if dimension_signals:
            covered = self._covered_dimensions(blockers, dimensions)
            enriched_drivers, enriched_blockers = self._enrichment_builder.build(
                dimensions=dimensions,
                dimension_signals=dimension_signals,
                covered_dimensions=covered,
            )
            drivers = self._dedupe(drivers + enriched_drivers)[:3]
            blockers = self._dedupe(blockers + enriched_blockers)[:3]

        return {"drivers": drivers, "blockers": blockers}

    # ---------------------------------------------------------
    # PRIVATE HELPERS
    # ---------------------------------------------------------

    def _fallback(self, dimensions: List[Dict[str, Any]]) -> Dict[str, List[str]]:
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

        if weakest_score >= NARRATIVE_WEAKEST_BLOCKER_MILD:
            blocker = f"Area for improvement in {weakest}"
        elif weakest_score >= NARRATIVE_WEAKEST_BLOCKER_MODERATE:
            blocker = f"Moderate improvement needed in {weakest}"
        else:
            blocker = f"Weak performance in {weakest}"

        return {
            "drivers": [f"Strong performance in {strongest}"],
            "blockers": [blocker],
        }

    @staticmethod
    def _covered_dimensions(
        blockers: List[str],
        dimensions: List[Dict[str, Any]],
    ) -> set[str]:
        covered: set[str] = set()
        for b in blockers:
            b_lower = b.lower()
            for dim in dimensions:
                name = dim.get("name", "").lower()
                if name and name in b_lower:
                    covered.add(name)
        return covered

    @staticmethod
    def _normalize_items(items: Any) -> List[str]:
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

    @staticmethod
    def _dedupe(items: List[str]) -> List[str]:
        seen: set[str] = set()
        result = []
        for item in items:
            key = item.lower().strip()
            if key not in seen:
                seen.add(key)
                result.append(item)
        return result
