# tests/services/question_corpus/test_adaptive_retrieval_policy_seniority.py

import pytest
from unittest.mock import MagicMock

from services.question_corpus.retrieval.adaptive_retrieval_policy import AdaptiveRetrievalPolicy
from services.question_corpus.contracts.adaptive_retrieval_context import AdaptiveRetrievalContext
from services.question_corpus.contracts.interview_retrieval_memory import InterviewRetrievalMemory


def _make_context(seniority: str) -> AdaptiveRetrievalContext:
    return AdaptiveRetrievalContext(
        current_role="backend_engineer",
        seniority=seniority,
        target_area="tech_technical_knowledge",
        target_question_count=5,
        target_difficulty=3,
        memory=InterviewRetrievalMemory(),
    )


class TestAdaptiveRetrievalPolicySeniorityWidening:

    def test_junior_all_stages_use_junior(self):
        policy = AdaptiveRetrievalPolicy()
        stages = policy.build_relaxation_stages(_make_context("junior"))

        for stage in stages:
            assert stage.seniority == "junior", f"Expected junior, got {stage.seniority}"

    def test_mid_all_stages_use_mid(self):
        policy = AdaptiveRetrievalPolicy()
        stages = policy.build_relaxation_stages(_make_context("mid"))

        for stage in stages:
            assert stage.seniority == "mid", f"Expected mid, got {stage.seniority}"

    def test_senior_early_stages_use_senior_only(self):
        policy = AdaptiveRetrievalPolicy()
        stages = policy.build_relaxation_stages(_make_context("senior"))

        assert stages[0].seniority == "senior"
        assert stages[1].seniority == "senior"

    def test_senior_late_stages_widen_to_mid(self):
        policy = AdaptiveRetrievalPolicy()
        stages = policy.build_relaxation_stages(_make_context("senior"))

        assert "mid" in stages[2].seniority
        assert "senior" in stages[2].seniority
        assert "mid" in stages[3].seniority
        assert "senior" in stages[3].seniority

    def test_staff_early_stages_use_staff_only(self):
        policy = AdaptiveRetrievalPolicy()
        stages = policy.build_relaxation_stages(_make_context("staff"))

        assert stages[0].seniority == "staff"
        assert stages[1].seniority == "staff"

    def test_staff_late_stages_widen_to_senior(self):
        policy = AdaptiveRetrievalPolicy()
        stages = policy.build_relaxation_stages(_make_context("staff"))

        assert "senior" in stages[2].seniority
        assert "staff" in stages[2].seniority

    def test_no_stage_has_none_seniority(self):
        policy = AdaptiveRetrievalPolicy()
        for seniority in ("junior", "mid", "senior", "staff"):
            stages = policy.build_relaxation_stages(_make_context(seniority))
            for stage in stages:
                assert stage.seniority is not None, (
                    f"Seniority must never be None at any relaxation stage for {seniority}"
                )

    def test_four_relaxation_stages_returned(self):
        policy = AdaptiveRetrievalPolicy()
        stages = policy.build_relaxation_stages(_make_context("senior"))
        assert len(stages) == 4
