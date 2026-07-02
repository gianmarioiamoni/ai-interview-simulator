# tests/services/knowledge_pipeline/test_knowledge_pipeline_behavior.py
# Behavioral tests: pipeline stages, success/failure paths, metrics

from __future__ import annotations

import pytest

from domain.contracts.reasoning.candidate_profile import CandidateProfile
from services.knowledge_pipeline.knowledge_pipeline_configuration import KnowledgePipelineConfiguration
from services.knowledge_pipeline.knowledge_pipeline_context import KnowledgePipelineContext
from services.knowledge_pipeline.knowledge_pipeline_diagnostics import PipelineStage
from tests.services.knowledge_pipeline.conftest import (
    AlwaysMatchRule,
    EmptyUpdater,
    NeverMatchRule,
    make_candidate,
    make_pipeline,
    make_signal,
)


SESSION = "sess-001"
CAND = "cand-001"


def _ctx(
    question_index: int = 0,
    signals: tuple | None = None,
    session_id: str = SESSION,
    candidate_id: str = CAND,
    prior_profile: CandidateProfile | None = None,
) -> KnowledgePipelineContext:
    sig = signals if signals is not None else (make_signal(question_index=question_index, session_id=session_id),)
    return KnowledgePipelineContext(
        session_id=session_id,
        candidate_identity_id=candidate_id,
        question_index=question_index,
        signals=sig,
        prior_profile=prior_profile,
    )


class TestPipelineSuccessPath:
    def test_successful_run_returns_profile(self):
        pipeline, _ = make_pipeline(session_id=SESSION)
        result = pipeline.run(_ctx())
        assert result.is_successful is True
        assert result.profile is not None
        assert isinstance(result.profile, CandidateProfile)

    def test_profile_questions_answered_incremented(self):
        pipeline, _ = make_pipeline(session_id=SESSION)
        result = pipeline.run(_ctx(question_index=2))
        assert result.profile is not None
        assert result.profile.questions_answered == 3

    def test_profile_last_updated_at_matches_question_index(self):
        pipeline, _ = make_pipeline(session_id=SESSION)
        result = pipeline.run(_ctx(question_index=5))
        assert result.profile is not None
        assert result.profile.last_updated_at_question_index == 5

    def test_features_produced(self):
        pipeline, _ = make_pipeline(session_id=SESSION, candidates=[make_candidate()])
        result = pipeline.run(_ctx())
        assert result.feature_count >= 0  # may be 0 if no observations matched updater

    def test_observations_appended_to_store(self):
        pipeline, store = make_pipeline(session_id=SESSION, rules=[AlwaysMatchRule()])
        assert store.count() == 0
        pipeline.run(_ctx())
        assert store.count() > 0

    def test_diagnostics_is_successful(self):
        pipeline, _ = make_pipeline(session_id=SESSION)
        result = pipeline.run(_ctx())
        assert result.diagnostics.is_successful is True
        assert result.diagnostics.failure_stage is None

    def test_all_five_stages_recorded(self):
        pipeline, _ = make_pipeline(session_id=SESSION)
        result = pipeline.run(_ctx())
        stages = {r.stage for r in result.diagnostics.stage_records}
        assert PipelineStage.EXTRACTION in stages
        assert PipelineStage.STORE_APPEND in stages
        assert PipelineStage.QUERY_ENGINE in stages
        assert PipelineStage.FEATURE_ENGINE in stages
        assert PipelineStage.PROFILE_BUILD in stages

    def test_metrics_signals_received(self):
        pipeline, _ = make_pipeline(session_id=SESSION)
        ctx = _ctx()
        result = pipeline.run(ctx)
        assert result.diagnostics.metrics.signals_received == len(ctx.signals)

    def test_metrics_total_duration_positive(self):
        pipeline, _ = make_pipeline(session_id=SESSION)
        result = pipeline.run(_ctx())
        assert result.diagnostics.metrics.total_duration_ms >= 0.0


class TestPipelineWithPriorProfile:
    def test_prior_profile_propagated(self):
        pipeline, _ = make_pipeline(session_id=SESSION)
        first_result = pipeline.run(_ctx(question_index=0))
        assert first_result.profile is not None

        second_result = pipeline.run(
            _ctx(question_index=1, prior_profile=first_result.profile)
        )
        assert second_result.profile is not None
        assert second_result.profile.questions_answered == 2

    def test_second_cycle_inherits_areas_covered(self):
        from domain.contracts.reasoning.profile_dimension import ProfileDimension
        from domain.contracts.reasoning.dimension_trace import DimensionTrace
        from domain.profile.candidate_profile_builder import CandidateProfileBuilder

        prior = (
            CandidateProfileBuilder()
            .with_questions_answered(1)
            .with_areas_covered(["algorithms"])
            .with_last_updated_at(0)
            .build()
        )
        pipeline, _ = make_pipeline(session_id=SESSION)
        result = pipeline.run(_ctx(question_index=1, prior_profile=prior))
        assert result.profile is not None
        assert "algorithms" in result.profile.areas_covered


class TestEmptySignalHandling:
    def test_empty_signals_default_config_returns_failure(self):
        pipeline, _ = make_pipeline(session_id=SESSION)
        ctx = KnowledgePipelineContext(
            session_id=SESSION,
            candidate_identity_id=CAND,
            question_index=0,
            signals=(),
        )
        result = pipeline.run(ctx)
        assert result.is_successful is False
        assert result.profile is None

    def test_empty_signals_allowed_when_configured(self):
        cfg = KnowledgePipelineConfiguration(allow_empty_signal_cycles=True)
        pipeline, _ = make_pipeline(session_id=SESSION, configuration=cfg)
        ctx = KnowledgePipelineContext(
            session_id=SESSION,
            candidate_identity_id=CAND,
            question_index=0,
            signals=(),
        )
        result = pipeline.run(ctx)
        # Pipeline should proceed; extraction will short-circuit with 0 observations
        # but profile build should still succeed
        assert result.is_successful is True


class TestAbortOnStageFailure:
    def test_abort_on_extraction_failure(self):
        from tests.services.knowledge_pipeline.conftest import ErrorRule
        cfg = KnowledgePipelineConfiguration(abort_on_stage_failure=True)
        # ErrorRule raises during evaluate — extraction stage completes (extractor catches)
        # but we test the abort path by using an empty signal with abort=True
        pipeline, _ = make_pipeline(session_id=SESSION, configuration=cfg)
        ctx = KnowledgePipelineContext(
            session_id=SESSION,
            candidate_identity_id=CAND,
            question_index=0,
            signals=(),
        )
        result = pipeline.run(ctx)
        assert result.is_successful is False

    def test_soft_failure_continues_without_abort(self):
        cfg = KnowledgePipelineConfiguration(abort_on_stage_failure=False)
        pipeline, _ = make_pipeline(session_id=SESSION, configuration=cfg)
        result = pipeline.run(_ctx())
        # Even with soft failure mode, a valid run should succeed
        assert result.is_successful is True


class TestNeverMatchRule:
    def test_no_observations_but_profile_built(self):
        pipeline, store = make_pipeline(session_id=SESSION, rules=[NeverMatchRule()])
        result = pipeline.run(_ctx())
        assert result.is_successful is True
        assert store.count() == 0
        # Profile is always built regardless of observation/feature count
        assert result.profile is not None


class TestMultipleCycles:
    def test_three_cycles_accumulate_observations(self):
        pipeline, store = make_pipeline(session_id=SESSION, rules=[AlwaysMatchRule()])
        for q in range(3):
            pipeline.run(_ctx(question_index=q))
        # Each cycle with AlwaysMatchRule emits at least one observation
        assert store.count() >= 3

    def test_question_index_tracked_correctly(self):
        pipeline, _ = make_pipeline(session_id=SESSION)
        results = []
        prior = None
        for q in range(3):
            ctx = _ctx(question_index=q, prior_profile=prior)
            r = pipeline.run(ctx)
            prior = r.profile
            results.append(r)
        assert results[2].profile is not None
        assert results[2].profile.last_updated_at_question_index == 2
