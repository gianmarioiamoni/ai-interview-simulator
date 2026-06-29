# services/interview_evaluation/steps/signal_enrichment_step.py

from typing import Dict, List

from domain.contracts.question.question_result import QuestionResult

from services.feedback.signal_extractor import SignalExtractor
from services.execution_analysis.execution_analyzer import ExecutionAnalyzer
from infrastructure.config.evaluation import ENRICHMENT_ALPHA

from app.core.logger import get_logger

logger = get_logger(__name__)


class SignalEnrichmentStep:
    """
    Extracts per-dimension execution signals from question results and
    blends them into the base dimension scores via alpha weighting.

    Responsibilities:
    - Iterate question results and extract execution signals
    - Accumulate signals across all questions
    - Alpha-blend base scores with signal scores
    """

    def __init__(self) -> None:
        self._signal_extractor = SignalExtractor()
        self._execution_analyzer = ExecutionAnalyzer()

    # ------------------------------------------------------------------
    # PUBLIC
    # ------------------------------------------------------------------

    def extract_signals(
        self,
        question_results: List[QuestionResult],
    ) -> Dict[str, float]:
        """
        Return a dict mapping dimension key → aggregated signal (0.0–1.0).
        Returns empty dict on any extraction failure.
        """

        dimension_signals: Dict[str, float] = {}

        try:
            for qr in question_results:

                execution = qr.execution
                if not execution:
                    continue

                analysis = self._execution_analyzer.analyze(execution)

                signals = self._signal_extractor.extract(
                    execution=execution,
                    error_type=analysis.error_type,
                    analysis=analysis,
                )

                for k, v in signals.items():
                    dimension_signals[k] = dimension_signals.get(k, 0.0) + v

            dimension_signals = {
                k: round(min(1.0, v), 2) for k, v in dimension_signals.items()
            }

            logger.debug("dimension_signals: %s", dimension_signals)

        except Exception as e:
            logger.warning("signal_extraction_failed: %s", e)
            dimension_signals = {}

        return dimension_signals

    def enrich_scores(
        self,
        base_dimension_scores: Dict,
        dimension_signals: Dict[str, float],
        execution_dims: set[str] | None = None,
    ) -> Dict:
        """
        Blend base dimension scores with execution signals using ENRICHMENT_ALPHA.
        Returns a new dict with the same keys as *base_dimension_scores*.

        Enrichment is applied only to dimensions in *execution_dims* (i.e. those
        for which at least one execution-based question exists).  Dimensions absent
        from *execution_dims* pass through unchanged so that missing execution
        evidence is not penalised as if execution had completely failed.

        When *execution_dims* is None (backwards-compatible default) enrichment
        is applied to every dimension, preserving the original behaviour.
        """

        enriched_scores: Dict = {}

        for dim, base_score in base_dimension_scores.items():

            dim_key = dim.value if hasattr(dim, "value") else dim

            if execution_dims is not None and dim_key not in execution_dims:
                enriched_scores[dim] = base_score
                continue

            signal = dimension_signals.get(dim_key, 0.0)

            enriched = (
                base_score * (1 - ENRICHMENT_ALPHA) + (signal * 100) * ENRICHMENT_ALPHA
            )

            enriched_scores[dim] = round(enriched, 1)

        return enriched_scores
