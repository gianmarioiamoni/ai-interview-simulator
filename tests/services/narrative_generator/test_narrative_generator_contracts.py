# tests/services/narrative_generator/test_narrative_generator_contracts.py
# Contract tests — NarrativeGenerationContext, Result, Metrics, Diagnostics

from __future__ import annotations

import pytest

from domain.contracts.feature.feature_type import FeatureType
from domain.contracts.narrative.narrative_section_type import NarrativeSectionType
from services.narrative_generator.narrative_generation_context import NarrativeGenerationContext
from services.narrative_generator.narrative_generation_diagnostics import (
    NarrativeGenerationDiagnostics,
    NarrativeStage,
    StageAuditRecord,
)
from services.narrative_generator.narrative_generation_metrics import NarrativeGenerationMetrics
from services.narrative_generator.narrative_generation_result import NarrativeGenerationResult
from tests.services.narrative_generator.conftest import (
    make_context,
    make_feature,
    make_feature_collection,
    make_profile,
)


class TestNarrativeGenerationContext:
    def test_immutable(self, empty_context: NarrativeGenerationContext) -> None:
        with pytest.raises(Exception):
            empty_context.session_id = "mutated"  # type: ignore[misc]

    def test_default_schema_version(self, empty_context: NarrativeGenerationContext) -> None:
        assert empty_context.schema_version == "1.0"

    def test_empty_features_allowed(self) -> None:
        ctx = make_context(features=make_feature_collection([]))
        assert ctx.features.is_empty

    def test_session_id_required(self) -> None:
        with pytest.raises(Exception):
            make_context(session_id="")

    def test_candidate_id_required(self) -> None:
        with pytest.raises(Exception):
            make_context(candidate_identity_id="")

    def test_question_index_non_negative(self) -> None:
        with pytest.raises(Exception):
            make_context(question_index=-1)

    def test_profile_not_mutated_by_context_creation(self) -> None:
        profile = make_profile(questions_answered=5)
        ctx = make_context(profile=profile)
        assert ctx.profile.questions_answered == 5

    def test_knowledge_gap_areas_defaults_to_empty_tuple(self) -> None:
        ctx = NarrativeGenerationContext(
            session_id="s",
            candidate_identity_id="c",
            question_index=0,
            profile=make_profile(),
            features=make_feature_collection(),
        )
        assert ctx.knowledge_gap_areas == ()


class TestNarrativeGenerationMetrics:
    def test_immutable(self) -> None:
        m = NarrativeGenerationMetrics(
            session_id="s",
            candidate_identity_id="c",
            question_index=0,
        )
        with pytest.raises(Exception):
            m.session_id = "x"  # type: ignore[misc]

    def test_defaults(self) -> None:
        m = NarrativeGenerationMetrics(
            session_id="s",
            candidate_identity_id="c",
            question_index=0,
        )
        assert m.total_duration_ms == 0.0
        assert m.features_received == 0
        assert m.sections_built == 0
        assert m.insights_built == 0

    def test_non_negative_constraints(self) -> None:
        with pytest.raises(Exception):
            NarrativeGenerationMetrics(
                session_id="s",
                candidate_identity_id="c",
                question_index=0,
                total_duration_ms=-1.0,
            )


class TestNarrativeGenerationDiagnostics:
    def _make_metrics(self) -> NarrativeGenerationMetrics:
        return NarrativeGenerationMetrics(
            session_id="s",
            candidate_identity_id="c",
            question_index=0,
        )

    def test_successful_factory(self) -> None:
        diag = NarrativeGenerationDiagnostics.successful(
            session_id="s",
            candidate_identity_id="c",
            question_index=0,
            stage_records=(),
            metrics=self._make_metrics(),
        )
        assert diag.is_successful
        assert diag.failure_stage is None
        assert diag.failure_reason is None

    def test_failed_factory(self) -> None:
        diag = NarrativeGenerationDiagnostics.failed(
            session_id="s",
            candidate_identity_id="c",
            question_index=0,
            stage_records=(),
            metrics=self._make_metrics(),
            failure_stage=NarrativeStage.SECTION_BUILD,
            failure_reason="error",
        )
        assert not diag.is_successful
        assert diag.failure_stage == NarrativeStage.SECTION_BUILD
        assert diag.failure_reason == "error"

    def test_immutable(self) -> None:
        diag = NarrativeGenerationDiagnostics.successful(
            session_id="s",
            candidate_identity_id="c",
            question_index=0,
            stage_records=(),
            metrics=self._make_metrics(),
        )
        with pytest.raises(Exception):
            diag.is_successful = False  # type: ignore[misc]


class TestNarrativeGenerationResult:
    def _make_diag(self, success: bool = True) -> NarrativeGenerationDiagnostics:
        m = NarrativeGenerationMetrics(
            session_id="s",
            candidate_identity_id="c",
            question_index=0,
        )
        if success:
            return NarrativeGenerationDiagnostics.successful(
                session_id="s",
                candidate_identity_id="c",
                question_index=0,
                stage_records=(),
                metrics=m,
            )
        return NarrativeGenerationDiagnostics.failed(
            session_id="s",
            candidate_identity_id="c",
            question_index=0,
            stage_records=(),
            metrics=m,
            failure_stage=NarrativeStage.SECTION_BUILD,
            failure_reason="fail",
        )

    def test_has_narrative_false_when_none(self) -> None:
        r = NarrativeGenerationResult(
            session_id="s",
            candidate_identity_id="c",
            question_index=0,
            narrative=None,
            diagnostics=self._make_diag(success=False),
            is_successful=False,
            failure_reason="fail",
        )
        assert not r.has_narrative

    def test_immutable(self) -> None:
        r = NarrativeGenerationResult(
            session_id="s",
            candidate_identity_id="c",
            question_index=0,
            diagnostics=self._make_diag(),
        )
        with pytest.raises(Exception):
            r.session_id = "x"  # type: ignore[misc]
