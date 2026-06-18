# tests/services/question_intelligence/test_business_context_propagation.py

from unittest.mock import MagicMock, patch
import pytest

from domain.contracts.interview.business_context import BusinessContext
from domain.contracts.interview.interview_context_profile import InterviewContextProfile
from domain.contracts.interview.interview_type import InterviewType
from domain.contracts.user.role import RoleType
from domain.contracts.user.seniority_level import SeniorityLevel
from services.question_corpus.contracts.interview_retrieval_memory import (
    InterviewRetrievalMemory,
)


# =====================================================
# Helpers
# =====================================================

def _make_question():
    q = MagicMock()
    q.id = "q1"
    return q


def _make_memory():
    return InterviewRetrievalMemory()


# =====================================================
# LazyAdaptiveInterviewService propagation
# =====================================================

class TestLazyAdaptiveServicePropagation:

    def _make_service(self, area_builder):
        from services.question_intelligence.lazy_adaptive_interview_service import (
            LazyAdaptiveInterviewService,
        )
        svc = LazyAdaptiveInterviewService(area_builder=area_builder)
        return svc

    def test_generate_first_question_passes_business_context(self):
        area_builder = MagicMock()
        area_builder.build.return_value = ([_make_question()], _make_memory())

        svc = self._make_service(area_builder)
        svc._theme_selector = MagicMock()
        svc._theme_selector.select_anchor.return_value = None

        svc.generate_first_question(
            role=RoleType.BACKEND_ENGINEER,
            level=SeniorityLevel.MID,
            interview_type=InterviewType.TECHNICAL,
            company_description="Payment fintech",
            business_context=BusinessContext.FINTECH,
        )

        call_kwargs = area_builder.build.call_args.kwargs
        assert call_kwargs["business_context"] == BusinessContext.FINTECH

    def test_generate_first_question_default_none_business_context(self):
        area_builder = MagicMock()
        area_builder.build.return_value = ([_make_question()], _make_memory())

        svc = self._make_service(area_builder)
        svc._theme_selector = MagicMock()
        svc._theme_selector.select_anchor.return_value = None

        svc.generate_first_question(
            role=RoleType.BACKEND_ENGINEER,
            level=SeniorityLevel.MID,
            interview_type=InterviewType.TECHNICAL,
        )

        call_kwargs = area_builder.build.call_args.kwargs
        assert call_kwargs["business_context"] is None

    def test_generate_next_question_passes_business_context(self):
        area_builder = MagicMock()
        area_builder.build.return_value = ([_make_question()], _make_memory())

        svc = self._make_service(area_builder)

        svc.generate_next_question(
            role=RoleType.BACKEND_ENGINEER,
            level=SeniorityLevel.MID,
            interview_type=InterviewType.TECHNICAL,
            planned_areas=["technical_case_study"],
            generated_count=0,
            memory=_make_memory(),
            business_context=BusinessContext.SAAS,
        )

        call_kwargs = area_builder.build.call_args.kwargs
        assert call_kwargs["business_context"] == BusinessContext.SAAS


# =====================================================
# AreaQuestionBuilder propagation
# =====================================================

class TestAreaQuestionBuilderPropagation:

    def _make_builder(self):
        from services.question_intelligence.area_question_builder import AreaQuestionBuilder

        mock_retrieval = MagicMock()
        mock_generator = MagicMock()
        mock_coding = MagicMock()
        mock_sql = MagicMock()

        builder = AreaQuestionBuilder(
            retrieval_service=mock_retrieval,
            generator=mock_generator,
            coding_generator=mock_coding,
            sql_generator=mock_sql,
        )
        return builder

    def test_sql_pipeline_receives_business_context(self):
        from domain.contracts.interview.interview_area import InterviewArea

        builder = self._make_builder()
        builder._sql_pipeline = MagicMock()
        builder._sql_pipeline.build.return_value = ([_make_question()], _make_memory())

        builder.build(
            role=RoleType.BACKEND_ENGINEER,
            level=SeniorityLevel.MID,
            interview_type=InterviewType.TECHNICAL,
            area=InterviewArea.TECH_DATABASE,
            business_context=BusinessContext.ECOMMERCE,
        )

        call_kwargs = builder._sql_pipeline.build.call_args.kwargs
        assert call_kwargs["business_context"] == BusinessContext.ECOMMERCE

    def test_coding_pipeline_receives_business_context(self):
        from domain.contracts.interview.interview_area import InterviewArea

        builder = self._make_builder()
        builder._coding_pipeline = MagicMock()
        builder._coding_pipeline.build.return_value = ([_make_question()], _make_memory())

        builder.build(
            role=RoleType.BACKEND_ENGINEER,
            level=SeniorityLevel.MID,
            interview_type=InterviewType.TECHNICAL,
            area=InterviewArea.TECH_CODING,
            business_context=BusinessContext.FINTECH,
        )

        call_kwargs = builder._coding_pipeline.build.call_args.kwargs
        assert call_kwargs["business_context"] == BusinessContext.FINTECH

    def test_written_pipeline_receives_business_context(self):
        from domain.contracts.interview.interview_area import InterviewArea

        builder = self._make_builder()
        builder._written_pipeline = MagicMock()
        builder._written_pipeline.build.return_value = ([_make_question()], _make_memory())

        builder.build(
            role=RoleType.BACKEND_ENGINEER,
            level=SeniorityLevel.MID,
            interview_type=InterviewType.TECHNICAL,
            area=InterviewArea.TECH_CASE_STUDY,
            business_context=BusinessContext.SAAS,
        )

        call_kwargs = builder._written_pipeline.build.call_args.kwargs
        assert call_kwargs["business_context"] == BusinessContext.SAAS


# =====================================================
# QuestionIntelligenceProvider propagation
# =====================================================

class TestQuestionIntelligenceProviderPropagation:

    def test_generate_first_question_passes_business_context(self):
        from services.question_intelligence.question_intelligence_provider import (
            QuestionIntelligenceProvider,
        )

        provider = MagicMock(spec=QuestionIntelligenceProvider)
        provider.generate_first_question = MagicMock(
            return_value=([_make_question()], _make_memory(), [])
        )

        provider.generate_first_question(
            role=RoleType.BACKEND_ENGINEER,
            level=SeniorityLevel.MID,
            interview_type=InterviewType.TECHNICAL,
            business_context=BusinessContext.FINTECH,
        )

        provider.generate_first_question.assert_called_once_with(
            role=RoleType.BACKEND_ENGINEER,
            level=SeniorityLevel.MID,
            interview_type=InterviewType.TECHNICAL,
            business_context=BusinessContext.FINTECH,
        )


# =====================================================
# InterviewContextProfile in state
# =====================================================

class TestInterviewStateContextProfile:

    def test_context_profile_stores_business_context(self):
        profile = InterviewContextProfile(
            company_description="Fintech payment platform",
            business_context=BusinessContext.FINTECH,
        )
        assert profile.business_context == BusinessContext.FINTECH

    def test_context_profile_default_generic(self):
        profile = InterviewContextProfile()
        assert profile.business_context == BusinessContext.GENERIC
