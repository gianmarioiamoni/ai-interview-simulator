# tests/services/interview_pipeline/test_interview_pipeline_determinism.py
# Determinism tests: same inputs → same outputs

from __future__ import annotations

import pytest

from tests.services.interview_pipeline.conftest import (
    make_context,
    make_kp_result,
    make_ng_result,
    make_ce_result,
    make_pipeline,
)


class TestDeterminism:
    def test_two_runs_with_identical_context_produce_same_success_flag(self):
        pipeline, _, _, _ = make_pipeline()
        ctx = make_context()
        r1 = pipeline.run(ctx)
        r2 = pipeline.run(ctx)
        assert r1.is_successful == r2.is_successful

    def test_two_runs_preserve_session_id(self):
        pipeline, _, _, _ = make_pipeline()
        ctx = make_context()
        r1 = pipeline.run(ctx)
        r2 = pipeline.run(ctx)
        assert r1.session_id == r2.session_id

    def test_two_runs_preserve_candidate_id(self):
        pipeline, _, _, _ = make_pipeline()
        ctx = make_context()
        r1 = pipeline.run(ctx)
        r2 = pipeline.run(ctx)
        assert r1.candidate_identity_id == r2.candidate_identity_id

    def test_two_runs_preserve_question_index(self):
        pipeline, _, _, _ = make_pipeline()
        ctx = make_context()
        r1 = pipeline.run(ctx)
        r2 = pipeline.run(ctx)
        assert r1.question_index == r2.question_index

    def test_two_runs_on_failure_context_both_fail(self):
        from services.interview_pipeline.interview_pipeline_configuration import (
            InterviewPipelineConfiguration,
        )
        config = InterviewPipelineConfiguration(abort_on_knowledge_pipeline_failure=True)
        pipeline, _, _, _ = make_pipeline(
            kp_result=make_kp_result(is_successful=False),
            configuration=config,
        )
        ctx = make_context()
        r1 = pipeline.run(ctx)
        r2 = pipeline.run(ctx)
        assert r1.is_successful is False
        assert r2.is_successful is False

    def test_stage_count_is_stable_across_runs(self):
        pipeline, _, _, _ = make_pipeline()
        ctx = make_context()
        r1 = pipeline.run(ctx)
        r2 = pipeline.run(ctx)
        assert r1.stages_completed == r2.stages_completed

    def test_failure_stage_is_stable_across_runs(self):
        from services.interview_pipeline.interview_pipeline_configuration import (
            InterviewPipelineConfiguration,
        )
        config = InterviewPipelineConfiguration(abort_on_knowledge_pipeline_failure=True)
        pipeline, _, _, _ = make_pipeline(
            kp_result=make_kp_result(is_successful=False),
            configuration=config,
        )
        ctx = make_context()
        r1 = pipeline.run(ctx)
        r2 = pipeline.run(ctx)
        assert r1.diagnostics.failure_stage == r2.diagnostics.failure_stage
