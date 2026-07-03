# tests/services/interview_pipeline/test_interview_pipeline_orchestration.py
# Orchestration tests: delegation, stage sequencing, abort behaviour

from __future__ import annotations

import pytest

from services.interview_pipeline.interview_pipeline_configuration import (
    InterviewPipelineConfiguration,
)
from services.interview_pipeline.interview_pipeline_diagnostics import InterviewPipelineStage
from services.interview_pipeline.interview_pipeline_result import InterviewPipelineResult
from tests.services.interview_pipeline.conftest import (
    CAND,
    Q_IDX,
    SESSION,
    RaisingCoachingEngine,
    RaisingKnowledgePipeline,
    RaisingNarrativeGenerator,
    make_ce_result,
    make_context,
    make_kp_result,
    make_ng_result,
    make_pipeline,
)


class TestSuccessfulDelegation:
    def test_run_delegates_to_knowledge_pipeline(self):
        pipeline, kp, _, _ = make_pipeline()
        ctx = make_context()
        pipeline.run(ctx)
        assert kp.call_count == 1

    def test_run_delegates_to_narrative_generator(self):
        pipeline, _, ng, _ = make_pipeline()
        ctx = make_context()
        pipeline.run(ctx)
        assert ng.call_count == 1

    def test_run_delegates_to_coaching_engine(self):
        pipeline, _, _, ce = make_pipeline()
        ctx = make_context()
        pipeline.run(ctx)
        assert ce.call_count == 1

    def test_run_returns_interview_pipeline_result(self):
        pipeline, _, _, _ = make_pipeline()
        result = pipeline.run(make_context())
        assert isinstance(result, InterviewPipelineResult)

    def test_successful_result_has_is_successful_true(self):
        pipeline, _, _, _ = make_pipeline()
        result = pipeline.run(make_context())
        assert result.is_successful is True

    def test_result_carries_session_id(self):
        pipeline, _, _, _ = make_pipeline()
        result = pipeline.run(make_context())
        assert result.session_id == SESSION

    def test_result_carries_candidate_identity_id(self):
        pipeline, _, _, _ = make_pipeline()
        result = pipeline.run(make_context())
        assert result.candidate_identity_id == CAND

    def test_result_carries_question_index(self):
        pipeline, _, _, _ = make_pipeline()
        result = pipeline.run(make_context())
        assert result.question_index == Q_IDX

    def test_result_has_profile_on_success(self):
        pipeline, _, _, _ = make_pipeline()
        result = pipeline.run(make_context())
        assert result.has_profile is True

    def test_diagnostics_always_present(self):
        pipeline, _, _, _ = make_pipeline()
        result = pipeline.run(make_context())
        assert result.diagnostics is not None


class TestKnowledgePipelineContextForwarding:
    def test_session_id_forwarded_to_knowledge_pipeline(self):
        pipeline, kp, _, _ = make_pipeline()
        pipeline.run(make_context(session_id=SESSION))
        assert kp.last_context.session_id == SESSION

    def test_candidate_id_forwarded_to_knowledge_pipeline(self):
        pipeline, kp, _, _ = make_pipeline()
        pipeline.run(make_context(candidate_id=CAND))
        assert kp.last_context.candidate_identity_id == CAND

    def test_signals_forwarded_to_knowledge_pipeline(self):
        from tests.services.interview_pipeline.conftest import make_signal
        sig = make_signal()
        pipeline, kp, _, _ = make_pipeline()
        pipeline.run(make_context(signals=(sig,)))
        assert sig in kp.last_context.signals

    def test_prior_profile_forwarded_to_knowledge_pipeline(self):
        from tests.services.interview_pipeline.conftest import make_candidate_profile
        prior = make_candidate_profile(questions_answered=2)
        pipeline, kp, _, _ = make_pipeline()
        pipeline.run(make_context(prior_profile=prior))
        assert kp.last_context.prior_profile is prior


class TestNarrativeGeneratorContextForwarding:
    def test_session_id_forwarded_to_narrative_generator(self):
        pipeline, _, ng, _ = make_pipeline()
        pipeline.run(make_context())
        assert ng.last_context.session_id == SESSION

    def test_interview_metadata_forwarded_to_narrative_generator(self):
        pipeline, _, ng, _ = make_pipeline()
        ctx = make_context()
        ctx_with_meta = ctx.model_copy(update={"interview_metadata": {"topic": "algo"}})
        pipeline.run(ctx_with_meta)
        assert ng.last_context.interview_metadata == {"topic": "algo"}


class TestCoachingEngineContextForwarding:
    def test_session_id_forwarded_to_coaching_engine(self):
        pipeline, _, _, ce = make_pipeline()
        pipeline.run(make_context())
        assert ce.last_context.session_id == SESSION

    def test_interview_topic_forwarded_to_coaching_engine(self):
        pipeline, _, _, ce = make_pipeline()
        pipeline.run(make_context(interview_topic="System Design"))
        assert ce.last_context.interview_topic == "System Design"

    def test_interview_role_forwarded_to_coaching_engine(self):
        pipeline, _, _, ce = make_pipeline()
        pipeline.run(make_context(interview_role="Staff Engineer"))
        assert ce.last_context.interview_role == "Staff Engineer"


class TestKnowledgePipelineAbortBehaviour:
    def test_aborts_on_kp_failure_when_configured(self):
        config = InterviewPipelineConfiguration(abort_on_knowledge_pipeline_failure=True)
        pipeline, _, ng, ce = make_pipeline(
            kp_result=make_kp_result(is_successful=False, failure_reason="kp failed"),
            configuration=config,
        )
        result = pipeline.run(make_context())
        assert result.is_successful is False
        assert ng.call_count == 0
        assert ce.call_count == 0

    def test_continues_on_kp_failure_when_not_abort_configured(self):
        config = InterviewPipelineConfiguration(abort_on_knowledge_pipeline_failure=False)
        pipeline, _, ng, ce = make_pipeline(
            kp_result=make_kp_result(is_successful=False, failure_reason="kp failed"),
            configuration=config,
        )
        result = pipeline.run(make_context())
        assert ng.call_count == 1
        assert ce.call_count == 1

    def test_failure_result_carries_failure_reason(self):
        config = InterviewPipelineConfiguration(abort_on_knowledge_pipeline_failure=True)
        pipeline, _, _, _ = make_pipeline(
            kp_result=make_kp_result(is_successful=False, failure_reason="kp exploded"),
            configuration=config,
        )
        result = pipeline.run(make_context())
        assert result.failure_reason is not None
        assert "kp exploded" in result.failure_reason

    def test_failure_diagnostics_carry_failure_stage(self):
        config = InterviewPipelineConfiguration(abort_on_knowledge_pipeline_failure=True)
        pipeline, _, _, _ = make_pipeline(
            kp_result=make_kp_result(is_successful=False),
            configuration=config,
        )
        result = pipeline.run(make_context())
        assert result.diagnostics.failure_stage == InterviewPipelineStage.KNOWLEDGE_PIPELINE


class TestNarrativeAbortBehaviour:
    def test_aborts_on_ng_failure_when_configured(self):
        config = InterviewPipelineConfiguration(abort_on_narrative_failure=True)
        pipeline, _, _, ce = make_pipeline(
            ng_result=make_ng_result(is_successful=False),
            configuration=config,
        )
        result = pipeline.run(make_context())
        assert result.is_successful is False
        assert ce.call_count == 0

    def test_continues_on_ng_failure_when_not_abort_configured(self):
        config = InterviewPipelineConfiguration(abort_on_narrative_failure=False)
        pipeline, _, _, ce = make_pipeline(
            ng_result=make_ng_result(is_successful=False),
            configuration=config,
        )
        result = pipeline.run(make_context())
        assert ce.call_count == 1


class TestCoachingAbortBehaviour:
    def test_aborts_on_ce_failure_when_configured(self):
        config = InterviewPipelineConfiguration(abort_on_coaching_failure=True)
        pipeline, _, _, _ = make_pipeline(
            ce_result=make_ce_result(is_successful=False),
            configuration=config,
        )
        result = pipeline.run(make_context())
        assert result.is_successful is False

    def test_continues_on_ce_failure_when_not_abort_configured(self):
        config = InterviewPipelineConfiguration(abort_on_coaching_failure=False)
        pipeline, _, _, _ = make_pipeline(
            ce_result=make_ce_result(is_successful=False),
            configuration=config,
        )
        result = pipeline.run(make_context())
        assert result.is_successful is True
