# tests/services/narrative_generator/test_narrative_generator_failure_handling.py
# Failure handling tests — error capture, abort paths, diagnostics

from __future__ import annotations

import pytest

from domain.contracts.feature.feature_collection import FeatureCollection
from domain.contracts.reasoning.candidate_profile import CandidateProfile
from services.narrative_generator.narrative_generation_context import NarrativeGenerationContext
from services.narrative_generator.narrative_generation_diagnostics import NarrativeStage
from services.narrative_generator.narrative_generator import NarrativeGenerator
from tests.services.narrative_generator.conftest import (
    make_context,
    make_feature,
    make_feature_collection,
    make_profile,
)


@pytest.fixture
def generator() -> NarrativeGenerator:
    return NarrativeGenerator()


class TestFailureHandling:
    def test_result_always_returned_never_raises(self, generator: NarrativeGenerator) -> None:
        ctx = make_context(features=make_feature_collection([make_feature()]))
        result = generator.generate(ctx)
        assert result is not None

    def test_diagnostics_always_present(self, generator: NarrativeGenerator, rich_context) -> None:
        result = generator.generate(rich_context)
        assert result.diagnostics is not None

    def test_diagnostics_always_present_on_success(
        self, generator: NarrativeGenerator, empty_context
    ) -> None:
        result = generator.generate(empty_context)
        assert result.diagnostics is not None
        assert result.diagnostics.is_successful

    def test_stage_records_populated(self, generator: NarrativeGenerator, rich_context) -> None:
        result = generator.generate(rich_context)
        assert len(result.diagnostics.stage_records) > 0

    def test_all_stages_completed_on_success(self, generator: NarrativeGenerator, rich_context) -> None:
        result = generator.generate(rich_context)
        assert result.is_successful
        for record in result.diagnostics.stage_records:
            assert record.completed

    def test_failure_reason_none_on_success(self, generator: NarrativeGenerator, rich_context) -> None:
        result = generator.generate(rich_context)
        assert result.failure_reason is None

    def test_narrative_none_when_failed(self) -> None:
        from services.narrative_generator.narrative_generation_diagnostics import (
            NarrativeGenerationDiagnostics,
        )
        from services.narrative_generator.narrative_generation_metrics import (
            NarrativeGenerationMetrics,
        )
        from services.narrative_generator.narrative_generation_result import (
            NarrativeGenerationResult,
        )

        m = NarrativeGenerationMetrics(
            session_id="s",
            candidate_identity_id="c",
            question_index=0,
        )
        diag = NarrativeGenerationDiagnostics.failed(
            session_id="s",
            candidate_identity_id="c",
            question_index=0,
            stage_records=(),
            metrics=m,
            failure_stage=NarrativeStage.SECTION_BUILD,
            failure_reason="boom",
        )
        r = NarrativeGenerationResult(
            session_id="s",
            candidate_identity_id="c",
            question_index=0,
            narrative=None,
            diagnostics=diag,
            is_successful=False,
            failure_reason="boom",
        )
        assert not r.has_narrative
        assert r.failure_reason == "boom"

    def test_metrics_reflect_feature_count(
        self, generator: NarrativeGenerator, rich_context
    ) -> None:
        result = generator.generate(rich_context)
        assert result.diagnostics.metrics.features_received == rich_context.features.size

    def test_metrics_sections_built_on_success(
        self, generator: NarrativeGenerator, rich_context
    ) -> None:
        result = generator.generate(rich_context)
        assert result.diagnostics.metrics.sections_built == 5

    def test_metrics_insights_built_matches_narrative(
        self, generator: NarrativeGenerator, rich_context
    ) -> None:
        result = generator.generate(rich_context)
        assert result.diagnostics.metrics.insights_built == result.narrative.insight_count

    def test_total_duration_non_negative(
        self, generator: NarrativeGenerator, rich_context
    ) -> None:
        result = generator.generate(rich_context)
        assert result.diagnostics.metrics.total_duration_ms >= 0.0
