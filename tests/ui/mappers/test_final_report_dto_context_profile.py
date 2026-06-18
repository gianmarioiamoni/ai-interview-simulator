# tests/ui/mappers/test_final_report_dto_context_profile.py

import pytest

from domain.contracts.feedback.confidence import Confidence
from domain.contracts.interview.hire_decision import HireDecision
from domain.contracts.interview.interview_context_profile import InterviewContextProfile
from domain.contracts.interview.interview_evaluation import InterviewEvaluation
from domain.contracts.interview.interview_level import InterviewLevel
from domain.contracts.shared.performance_dimension import PerformanceDimension

from app.ui.mappers.interview_state_mapper import InterviewStateMapper

from tests.factories.interview_state_factory import build_state_with_execution


def _build_evaluation() -> InterviewEvaluation:
    return InterviewEvaluation(
        overall_score=80.0,
        raw_score=80.0,
        adjusted_score=80.0,
        executive_summary="Good performance.",
        performance_dimensions=[
            PerformanceDimension(
                name="technical_accuracy",
                score=80.0,
                justification="Correct.",
            )
        ],
        dimension_scores={"technical_accuracy": 80.0},
        dimension_signals={"technical_accuracy": 0.8},
        level=InterviewLevel.STRONG,
        hire_decision=HireDecision.LEAN_HIRE,
        decision_explanation={"strengths": ["good"]},
        hiring_probability=70.0,
        percentile_rank=75.0,
        percentile_explanation="Above average.",
        gating_triggered=False,
        gating_reason=None,
        weighted_breakdown={"technical_accuracy": 40.0},
        per_question_assessment=[],
        improvement_suggestions=[],
        confidence=Confidence(base=0.8, final=0.85),
    )


class TestFinalReportDTOContextProfile:

    def test_report_carries_context_profile_from_state(self):
        profile = InterviewContextProfile(
            job_description="Backend engineer at Big Corp",
            company_description="Fast-growing startup",
        )
        state = build_state_with_execution(passed_tests=2, total_tests=2)
        state = state.model_copy(update={
            "interview_evaluation": _build_evaluation(),
            "context_profile": profile,
        })

        report = InterviewStateMapper().to_final_report_dto(state)

        assert report.context_profile.job_description == "Backend engineer at Big Corp"
        assert report.context_profile.company_description == "Fast-growing startup"

    def test_report_context_profile_defaults_when_not_set(self):
        state = build_state_with_execution(passed_tests=2, total_tests=2)
        state = state.model_copy(update={"interview_evaluation": _build_evaluation()})

        report = InterviewStateMapper().to_final_report_dto(state)

        assert report.context_profile.job_description is None
        assert report.context_profile.company_description is None

    def test_report_context_profile_partial_jd_only(self):
        profile = InterviewContextProfile(job_description="JD only")
        state = build_state_with_execution(passed_tests=2, total_tests=2)
        state = state.model_copy(update={
            "interview_evaluation": _build_evaluation(),
            "context_profile": profile,
        })

        report = InterviewStateMapper().to_final_report_dto(state)

        assert report.context_profile.job_description == "JD only"
        assert report.context_profile.company_description is None

    def test_report_existing_fields_unaffected(self):
        state = build_state_with_execution(passed_tests=2, total_tests=2)
        state = state.model_copy(update={
            "interview_evaluation": _build_evaluation(),
            "seniority_level": "senior",
        })

        report = InterviewStateMapper().to_final_report_dto(state)

        assert report.overall_score == 80.0
        assert report.seniority_level == "senior"
        assert report.context_profile is not None
