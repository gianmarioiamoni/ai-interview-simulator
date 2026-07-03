# tests/services/interview_pipeline/test_interview_pipeline_failure_handling.py
# Failure handling tests: exceptions, partial results, diagnostics audit trail

from __future__ import annotations

import pytest

from services.interview_pipeline.interview_pipeline_configuration import (
    InterviewPipelineConfiguration,
)
from services.interview_pipeline.interview_pipeline_diagnostics import InterviewPipelineStage
from tests.services.interview_pipeline.conftest import (
    RaisingCoachingEngine,
    RaisingKnowledgePipeline,
    RaisingNarrativeGenerator,
    make_ce_result,
    make_context,
    make_kp_result,
    make_ng_result,
    make_pipeline,
    StubCoachingEngine,
    StubKnowledgePipeline,
    StubNarrativeGenerator,
    SESSION,
    CAND,
    Q_IDX,
)
from services.session_close.session_close_pipeline import SessionClosePipeline


class TestExceptionHandling:
    def test_knowledge_pipeline_exception_does_not_propagate(self):
        pipeline, _, _, _ = make_pipeline(kp_stub=RaisingKnowledgePipeline())
        result = pipeline.run(make_context())
        assert result is not None

    def test_knowledge_pipeline_exception_marks_as_failed(self):
        config = InterviewPipelineConfiguration(abort_on_knowledge_pipeline_failure=True)
        from services.interview_pipeline.interview_pipeline import InterviewPipeline
        ng = StubNarrativeGenerator(make_ng_result())
        ce = StubCoachingEngine(make_ce_result())
        pipeline = InterviewPipeline(
            knowledge_pipeline=RaisingKnowledgePipeline(),  # type: ignore[arg-type]
            narrative_generator=ng,  # type: ignore[arg-type]
            coaching_engine=ce,  # type: ignore[arg-type]
            session_close_pipeline=SessionClosePipeline(),
            configuration=config,
        )
        result = pipeline.run(make_context())
        assert result.is_successful is False

    def test_narrative_exception_does_not_propagate(self):
        pipeline, _, _, _ = make_pipeline(ng_stub=RaisingNarrativeGenerator())
        result = pipeline.run(make_context())
        assert result is not None

    def test_coaching_engine_exception_does_not_propagate(self):
        pipeline, _, _, _ = make_pipeline(ce_stub=RaisingCoachingEngine())
        result = pipeline.run(make_context())
        assert result is not None


class TestDiagnosticsAuditTrail:
    def test_successful_run_produces_stage_records(self):
        pipeline, _, _, _ = make_pipeline()
        result = pipeline.run(make_context())
        assert len(result.diagnostics.stage_records) > 0

    def test_knowledge_pipeline_stage_record_present(self):
        pipeline, _, _, _ = make_pipeline()
        result = pipeline.run(make_context())
        stages = [r.stage for r in result.diagnostics.stage_records]
        assert InterviewPipelineStage.KNOWLEDGE_PIPELINE in stages

    def test_narrative_stage_record_present(self):
        pipeline, _, _, _ = make_pipeline()
        result = pipeline.run(make_context())
        stages = [r.stage for r in result.diagnostics.stage_records]
        assert InterviewPipelineStage.NARRATIVE_GENERATOR in stages

    def test_coaching_stage_record_present(self):
        pipeline, _, _, _ = make_pipeline()
        result = pipeline.run(make_context())
        stages = [r.stage for r in result.diagnostics.stage_records]
        assert InterviewPipelineStage.COACHING_ENGINE in stages

    def test_session_close_stage_record_present(self):
        pipeline, _, _, _ = make_pipeline()
        result = pipeline.run(make_context())
        stages = [r.stage for r in result.diagnostics.stage_records]
        assert InterviewPipelineStage.SESSION_CLOSE in stages

    def test_metrics_always_present(self):
        pipeline, _, _, _ = make_pipeline()
        result = pipeline.run(make_context())
        assert result.diagnostics.metrics is not None

    def test_total_duration_non_negative(self):
        pipeline, _, _, _ = make_pipeline()
        result = pipeline.run(make_context())
        assert result.diagnostics.metrics.total_duration_ms >= 0.0

    def test_signals_received_matches_context(self):
        from tests.services.interview_pipeline.conftest import make_signal
        sigs = (make_signal(), make_signal())
        pipeline, _, _, _ = make_pipeline()
        result = pipeline.run(make_context(signals=sigs))
        assert result.diagnostics.metrics.signals_received == 2

    def test_kp_failure_stage_record_marks_not_completed(self):
        config = InterviewPipelineConfiguration(abort_on_knowledge_pipeline_failure=True)
        pipeline, _, _, _ = make_pipeline(
            kp_result=make_kp_result(is_successful=False),
            configuration=config,
        )
        result = pipeline.run(make_context())
        kp_records = [r for r in result.diagnostics.stage_records
                      if r.stage == InterviewPipelineStage.KNOWLEDGE_PIPELINE]
        assert len(kp_records) == 1
        assert kp_records[0].completed is False
