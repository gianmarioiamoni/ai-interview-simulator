# domain/contracts/observation/extraction/__init__.py
# Observation Extraction Layer — E02-M2 (ADR-016, ADR-017, ADR-021)

from domain.contracts.observation.extraction.observation_rule_priority import ObservationRulePriority
from domain.contracts.observation.extraction.observation_rule_match import ObservationRuleMatch
from domain.contracts.observation.extraction.observation_extraction_context import ObservationExtractionContext
from domain.contracts.observation.extraction.observation_rule import ObservationRule
from domain.contracts.observation.extraction.observation_rule_registry import (
    ObservationRuleRegistry,
    DuplicateRuleError,
)
from domain.contracts.observation.extraction.observation_extraction_diagnostics import (
    ObservationRuleDiagnostic,
    ObservationExtractionDiagnostics,
)
from domain.contracts.observation.extraction.observation_extraction_result import ObservationExtractionResult
from domain.contracts.observation.extraction.observation_extractor_metrics import (
    ObservationTypeCount,
    ObservationRuleMetric,
    ObservationExtractorMetrics,
)
from domain.contracts.observation.extraction.observation_extractor import ObservationExtractor

__all__ = [
    "ObservationRulePriority",
    "ObservationRuleMatch",
    "ObservationExtractionContext",
    "ObservationRule",
    "ObservationRuleRegistry",
    "DuplicateRuleError",
    "ObservationRuleDiagnostic",
    "ObservationExtractionDiagnostics",
    "ObservationExtractionResult",
    "ObservationTypeCount",
    "ObservationRuleMetric",
    "ObservationExtractorMetrics",
    "ObservationExtractor",
]
