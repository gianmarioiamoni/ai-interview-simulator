# domain/observation/runtime/default_observation_registry.py
# Builds and freezes the default ObservationRuleRegistry for V1.2 runtime.
# ADR-016: rule registry must be frozen before ObservationExtractor is built.

from __future__ import annotations

from domain.contracts.observation.extraction.observation_rule_registry import ObservationRuleRegistry
from domain.observation.runtime.evidence_signal_observation_rule import EvidenceSignalObservationRule


def build_default_observation_registry() -> ObservationRuleRegistry:
    """Return a frozen ObservationRuleRegistry with the default V1.2 rules."""
    registry = ObservationRuleRegistry()
    registry.register(EvidenceSignalObservationRule())
    registry.freeze()
    return registry
