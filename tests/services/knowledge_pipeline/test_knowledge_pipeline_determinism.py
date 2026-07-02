# tests/services/knowledge_pipeline/test_knowledge_pipeline_determinism.py
# Determinism tests: same inputs → same outputs across multiple runs

from __future__ import annotations

import pytest

from services.knowledge_pipeline.knowledge_pipeline_context import KnowledgePipelineContext
from tests.services.knowledge_pipeline.conftest import (
    AlwaysMatchRule,
    make_candidate,
    make_pipeline,
    make_signal,
)


def _ctx(session_id: str, question_index: int = 0) -> KnowledgePipelineContext:
    return KnowledgePipelineContext(
        session_id=session_id,
        candidate_identity_id="cand-det",
        question_index=question_index,
        signals=(make_signal(question_index=question_index, session_id=session_id),),
    )


class TestPipelineDeterminism:
    def test_same_input_same_profile_questions_answered(self):
        results = []
        for run in range(3):
            sid = f"sess-det-{run}"
            pipeline, _ = make_pipeline(session_id=sid, rules=[AlwaysMatchRule()])
            r = pipeline.run(_ctx(session_id=sid))
            results.append(r)

        questions = [r.profile.questions_answered for r in results if r.profile]
        assert len(set(questions)) == 1, f"Non-deterministic questions_answered: {questions}"

    def test_same_input_same_last_updated_at(self):
        results = []
        for run in range(3):
            sid = f"sess-det-upd-{run}"
            pipeline, _ = make_pipeline(session_id=sid, rules=[AlwaysMatchRule()])
            r = pipeline.run(_ctx(session_id=sid, question_index=4))
            results.append(r)

        indices = [r.profile.last_updated_at_question_index for r in results if r.profile]
        assert len(set(indices)) == 1, f"Non-deterministic last_updated_at: {indices}"

    def test_same_input_same_is_successful(self):
        statuses = []
        for run in range(3):
            sid = f"sess-det-ok-{run}"
            pipeline, _ = make_pipeline(session_id=sid)
            r = pipeline.run(_ctx(session_id=sid))
            statuses.append(r.is_successful)
        assert all(statuses), "Pipeline success should be deterministic"

    def test_empty_signals_consistently_fails(self):
        from services.knowledge_pipeline.knowledge_pipeline_context import KnowledgePipelineContext
        statuses = []
        for run in range(3):
            sid = f"sess-empty-{run}"
            pipeline, _ = make_pipeline(session_id=sid)
            ctx = KnowledgePipelineContext(
                session_id=sid,
                candidate_identity_id="cand-det",
                question_index=0,
                signals=(),
            )
            r = pipeline.run(ctx)
            statuses.append(r.is_successful)
        assert not any(statuses), "Empty-signal failure should be deterministic"

    def test_stage_record_count_is_stable(self):
        counts = []
        for run in range(3):
            sid = f"sess-stage-{run}"
            pipeline, _ = make_pipeline(session_id=sid)
            r = pipeline.run(_ctx(session_id=sid))
            counts.append(len(r.diagnostics.stage_records))
        assert len(set(counts)) == 1, f"Stage count not deterministic: {counts}"
