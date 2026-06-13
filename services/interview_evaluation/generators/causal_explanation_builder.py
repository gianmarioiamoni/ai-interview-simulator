# services/interview_evaluation/generators/causal_explanation_builder.py

"""
Builds a single causal explanation sentence for a scoring dimension.

Owns the domain vocabulary that maps dimension names, scores, and signal
strengths to human-readable causal sentences. Extracted from
DecisionExplanationGenerator to give this domain logic a single home.
"""

from infrastructure.config.evaluation import (
    NARRATIVE_CAUSAL_SIGNAL_STRONG,
    NARRATIVE_CAUSAL_SIGNAL_SUPPORTED,
    NARRATIVE_CAUSAL_SIGNAL_PARTIAL,
    NARRATIVE_CAUSAL_SCORE_WEAK,
    NARRATIVE_CAUSAL_SCORE_GAPS,
)

_DIMENSION_BASE_CAUSES: dict[str, str] = {
    "system design": "limited architectural reasoning and lack of structured system trade-offs",
    "technical depth": "insufficient depth in core technical concepts and incomplete understanding of underlying mechanisms",
    "problem solving": "inconsistent reasoning and gaps in handling edge cases",
    "communication": "lack of clarity and structured explanation of ideas",
}

_DEFAULT_BASE_CAUSE = "inconsistent performance"


class CausalExplanationBuilder:
    """
    Produces a causal explanation sentence for a single dimension.

    Stateless — safe to share across requests.
    """

    def build(
        self,
        dim_name: str,
        dim_score: float,
        signal_strength: float | None,
    ) -> str:
        base_cause = self._base_cause(dim_name)
        evidence = self._evidence(signal_strength)
        sentence = self._score_sentence(dim_name, dim_score, base_cause)

        if evidence:
            sentence += f", {evidence}"

        return sentence

    # ------------------------------------------------------------------
    # PRIVATE
    # ------------------------------------------------------------------

    @staticmethod
    def _base_cause(dim_name: str) -> str:
        dim_lower = dim_name.lower()
        for keyword, cause in _DIMENSION_BASE_CAUSES.items():
            if keyword in dim_lower:
                return cause
        return _DEFAULT_BASE_CAUSE

    @staticmethod
    def _evidence(signal_strength: float | None) -> str | None:
        if signal_strength is None:
            return None
        if signal_strength >= NARRATIVE_CAUSAL_SIGNAL_STRONG:
            return "strongly reinforced by execution failures"
        if signal_strength >= NARRATIVE_CAUSAL_SIGNAL_SUPPORTED:
            return "supported by execution inconsistencies"
        if signal_strength >= NARRATIVE_CAUSAL_SIGNAL_PARTIAL:
            return "partially reflected in execution signals"
        return None

    @staticmethod
    def _score_sentence(dim_name: str, dim_score: float, base_cause: str) -> str:
        if dim_score < NARRATIVE_CAUSAL_SCORE_WEAK:
            return f"{dim_name} is weak due to {base_cause}"
        if dim_score < NARRATIVE_CAUSAL_SCORE_GAPS:
            return f"{dim_name} shows gaps due to {base_cause}"
        return f"{dim_name} is solid, though some limitations remain in {base_cause}"
