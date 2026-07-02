# domain/contracts/observation/extraction/observation_extractor.py
# ADR-016: ObservationExtractor — sole producer of Observation objects
# ADR-017: Single writer contract

from __future__ import annotations

from datetime import datetime, timezone

from domain.contracts.observation.extraction.observation_extraction_context import ObservationExtractionContext
from domain.contracts.observation.extraction.observation_extraction_diagnostics import (
    ObservationExtractionDiagnostics,
    ObservationRuleDiagnostic,
)
from domain.contracts.observation.extraction.observation_extraction_result import ObservationExtractionResult
from domain.contracts.observation.extraction.observation_extractor_metrics import (
    ObservationExtractorMetrics,
    ObservationRuleMetric,
    ObservationTypeCount,
)
from domain.contracts.observation.extraction.observation_rule import ObservationRule
from domain.contracts.observation.extraction.observation_rule_match import ObservationRuleMatch
from domain.contracts.observation.extraction.observation_rule_registry import ObservationRuleRegistry
from domain.contracts.observation.observation import Observation
from domain.contracts.observation.observation_metadata import ObservationMetadata
from domain.contracts.observation.observation_origin import ObservationOrigin
from domain.contracts.observation.observation_store import ObservationStore
from domain.contracts.observation.observation_type import ObservationType


class ObservationExtractor:
    """Sole producer of Observation objects (ADR-016 single-writer contract).

    Processes EvidenceSignals via a frozen, ordered rule registry and appends
    resulting Observations to the ObservationStore.

    Contract invariants:
    - The rule registry MUST be frozen before extract() is called.
    - Rules are applied in strict priority order (ascending value), tie-broken
      by rule_id lexicographic order — guaranteed deterministic (ADR-016).
    - Rules that raise are caught, recorded in diagnostics, and skipped; they
      do not abort the extraction cycle.
    - ObservationExtractor is the ONLY component that may call store.append().
    - No LLM calls, no I/O, no shared mutable state.
    - extract() is deterministic: same context → same Observation set.

    Metrics:
    - session_metrics() returns aggregated telemetry across all cycles.
    """

    VERSION = "1.0"

    def __init__(
        self,
        registry: ObservationRuleRegistry,
        store: ObservationStore,
    ) -> None:
        if not registry.is_frozen():
            raise RuntimeError(
                "ObservationRuleRegistry must be frozen before ObservationExtractor is constructed."
            )
        self._registry = registry
        self._store = store
        self._session_id = store.session_id()

        # Mutable metrics accumulators (internal only — never exposed directly)
        self._total_cycles: int = 0
        self._total_produced: int = 0
        self._total_evaluated: int = 0
        self._total_skipped: int = 0
        self._total_errored: int = 0
        self._rule_invocations: dict[str, int] = {}
        self._rule_skips: dict[str, int] = {}
        self._rule_errors: dict[str, int] = {}
        self._rule_matches: dict[str, int] = {}
        self._type_counts: dict[ObservationType, int] = {}

        for rule in self._registry.ordered_rules():
            rid = rule.rule_id
            self._rule_invocations[rid] = 0
            self._rule_skips[rid] = 0
            self._rule_errors[rid] = 0
            self._rule_matches[rid] = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def extract(self, context: ObservationExtractionContext) -> ObservationExtractionResult:
        """Run all rules on the context, append Observations, return result.

        Deterministic: for the same context and registry state, the output
        Observations are always identical in type, description, and confidence.

        Raises:
            ValueError: if context.session_id does not match the store session.
        """
        if context.session_id != self._session_id:
            raise ValueError(
                f"Context session_id={context.session_id!r} does not match "
                f"store session_id={self._session_id!r}"
            )

        rule_diagnostics: list[ObservationRuleDiagnostic] = []
        all_observations: list[Observation] = []

        for rule in self._registry.ordered_rules():
            rid = rule.rule_id
            self._rule_invocations[rid] += 1

            # Fast-path guard
            try:
                if not rule.applies_to(context):
                    self._rule_skips[rid] += 1
                    rule_diagnostics.append(
                        ObservationRuleDiagnostic(rule_id=rid, evaluated=False, skipped=True)
                    )
                    continue
            except Exception as exc:
                self._rule_errors[rid] += 1
                rule_diagnostics.append(
                    ObservationRuleDiagnostic(
                        rule_id=rid,
                        evaluated=False,
                        error_message=f"applies_to raised: {exc}",
                    )
                )
                continue

            # Rule evaluation
            try:
                matches = rule.evaluate(context)
            except Exception as exc:
                self._rule_errors[rid] += 1
                rule_diagnostics.append(
                    ObservationRuleDiagnostic(
                        rule_id=rid,
                        evaluated=True,
                        error_message=f"evaluate raised: {exc}",
                    )
                )
                continue

            # Convert matches to Observations
            observations_from_rule: list[Observation] = []
            for match in matches:
                obs = self._match_to_observation(match, context)
                observations_from_rule.append(obs)

            self._rule_matches[rid] += len(observations_from_rule)
            rule_diagnostics.append(
                ObservationRuleDiagnostic(
                    rule_id=rid,
                    evaluated=True,
                    match_count=len(observations_from_rule),
                )
            )
            all_observations.extend(observations_from_rule)

        # Append to store (single writer)
        for obs in all_observations:
            self._store.append(obs)
            self._type_counts[obs.observation_type] = (
                self._type_counts.get(obs.observation_type, 0) + 1
            )

        # Update session accumulators
        self._total_cycles += 1
        self._total_produced += len(all_observations)
        self._total_evaluated += sum(
            1 for d in rule_diagnostics if d.evaluated and not d.skipped
        )
        self._total_skipped += sum(1 for d in rule_diagnostics if d.skipped)
        self._total_errored += sum(1 for d in rule_diagnostics if d.error_message is not None)

        diagnostics = ObservationExtractionDiagnostics.from_rule_diagnostics(
            question_index=context.question_index,
            session_id=self._session_id,
            diagnostics=rule_diagnostics,
        )

        # Order observations deterministically: type value ASC, confidence DESC
        ordered = tuple(
            sorted(
                all_observations,
                key=lambda o: (o.observation_type.value, -o.confidence),
            )
        )

        return ObservationExtractionResult(
            observations=ordered,
            question_index=context.question_index,
            session_id=self._session_id,
            diagnostics=diagnostics,
        )

    def session_metrics(self) -> ObservationExtractorMetrics:
        """Return immutable aggregated metrics for all extraction cycles so far."""
        rule_metrics = tuple(
            ObservationRuleMetric(
                rule_id=rid,
                invocations=self._rule_invocations[rid],
                skips=self._rule_skips[rid],
                errors=self._rule_errors[rid],
                total_matches=self._rule_matches[rid],
            )
            for rid in sorted(self._rule_invocations)
        )
        type_counts = tuple(
            ObservationTypeCount(observation_type=otype, count=cnt)
            for otype, cnt in sorted(
                self._type_counts.items(), key=lambda kv: kv[0].value
            )
        )
        return ObservationExtractorMetrics(
            session_id=self._session_id,
            total_cycles=self._total_cycles,
            total_observations_produced=self._total_produced,
            total_rules_evaluated=self._total_evaluated,
            total_rules_skipped=self._total_skipped,
            total_rules_errored=self._total_errored,
            rule_metrics=rule_metrics,
            type_counts=type_counts,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _match_to_observation(
        self,
        match: ObservationRuleMatch,
        context: ObservationExtractionContext,
    ) -> Observation:
        metadata = ObservationMetadata(
            question_index=context.question_index,
            session_id=self._session_id,
            origin=ObservationOrigin.EVIDENCE_SIGNAL,
            source_ref=match.rule_id,
            extractor_version=self.VERSION,
        )
        return Observation(
            observation_type=match.observation_type,
            metadata=metadata,
            description=match.description,
            confidence=match.confidence,
            tags=match.tags,
        )
