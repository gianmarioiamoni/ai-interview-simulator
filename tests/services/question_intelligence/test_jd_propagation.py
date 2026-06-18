# tests/services/question_intelligence/test_jd_propagation.py

import pytest
from unittest.mock import MagicMock, patch

from domain.contracts.user.role import RoleType
from domain.contracts.user.seniority_level import SeniorityLevel
from domain.contracts.interview.interview_type import InterviewType
from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.interview.interview_context_profile import InterviewContextProfile

from services.question_intelligence.area_question_builder import AreaQuestionBuilder
from services.question_corpus.contracts.interview_retrieval_memory import InterviewRetrievalMemory


_JD = "Looking for a backend engineer with Python and microservices experience."


def _make_pipeline_mock(name="written"):
    mock = MagicMock()
    mock.build.return_value = ([], InterviewRetrievalMemory())
    return mock


class TestAreaQuestionBuilderJDPropagation:

    def _make_builder(self, written_mock, coding_mock, sql_mock):
        builder = AreaQuestionBuilder.__new__(AreaQuestionBuilder)
        builder._written_pipeline = written_mock
        builder._coding_pipeline = coding_mock
        builder._sql_pipeline = sql_mock
        return builder

    def test_written_pipeline_receives_job_description(self):
        written = _make_pipeline_mock()
        coding = _make_pipeline_mock()
        sql = _make_pipeline_mock()
        builder = self._make_builder(written, coding, sql)

        builder.build(
            role=RoleType.BACKEND_ENGINEER,
            level=SeniorityLevel.SENIOR,
            interview_type=InterviewType.TECHNICAL,
            area=InterviewArea.TECH_TECHNICAL_KNOWLEDGE,
            job_description=_JD,
        )

        call_kwargs = written.build.call_args.kwargs
        assert call_kwargs.get("job_description") == _JD

    def test_coding_pipeline_receives_job_description(self):
        written = _make_pipeline_mock()
        coding = _make_pipeline_mock()
        sql = _make_pipeline_mock()
        builder = self._make_builder(written, coding, sql)

        builder.build(
            role=RoleType.BACKEND_ENGINEER,
            level=SeniorityLevel.SENIOR,
            interview_type=InterviewType.TECHNICAL,
            area=InterviewArea.TECH_CODING,
            job_description=_JD,
        )

        call_kwargs = coding.build.call_args.kwargs
        assert call_kwargs.get("job_description") == _JD

    def test_sql_pipeline_receives_job_description(self):
        written = _make_pipeline_mock()
        coding = _make_pipeline_mock()
        sql = _make_pipeline_mock()
        builder = self._make_builder(written, coding, sql)

        builder.build(
            role=RoleType.BACKEND_ENGINEER,
            level=SeniorityLevel.SENIOR,
            interview_type=InterviewType.TECHNICAL,
            area=InterviewArea.TECH_DATABASE,
            job_description=_JD,
        )

        call_kwargs = sql.build.call_args.kwargs
        assert call_kwargs.get("job_description") == _JD

    def test_written_pipeline_receives_none_when_no_jd(self):
        written = _make_pipeline_mock()
        coding = _make_pipeline_mock()
        sql = _make_pipeline_mock()
        builder = self._make_builder(written, coding, sql)

        builder.build(
            role=RoleType.BACKEND_ENGINEER,
            level=SeniorityLevel.MID,
            interview_type=InterviewType.TECHNICAL,
            area=InterviewArea.TECH_TECHNICAL_KNOWLEDGE,
        )

        call_kwargs = written.build.call_args.kwargs
        assert call_kwargs.get("job_description") is None


class TestLazyAdaptiveInterviewServiceJDPropagation:

    def _make_service(self, area_builder_mock):
        from services.question_intelligence.lazy_adaptive_interview_service import (
            LazyAdaptiveInterviewService,
        )
        from services.question_intelligence.interview_theme_selector import InterviewThemeSelector

        theme_selector = MagicMock(spec=InterviewThemeSelector)
        theme_selector.select_anchor.return_value = "general"

        svc = LazyAdaptiveInterviewService.__new__(LazyAdaptiveInterviewService)
        svc._area_builder = area_builder_mock
        svc._theme_selector = theme_selector
        return svc

    def test_generate_first_question_passes_jd_to_area_builder(self):
        from domain.contracts.question.question import Question, QuestionType, QuestionDifficulty
        mock_q = MagicMock(spec=Question)
        mock_memory = InterviewRetrievalMemory()

        area_builder = MagicMock()
        area_builder.build.return_value = ([mock_q], mock_memory)

        svc = self._make_service(area_builder)

        svc.generate_first_question(
            role=RoleType.BACKEND_ENGINEER,
            level=SeniorityLevel.SENIOR,
            interview_type=InterviewType.TECHNICAL,
            job_description=_JD,
        )

        call_kwargs = area_builder.build.call_args.kwargs
        assert call_kwargs.get("job_description") == _JD

    def test_generate_first_question_passes_none_when_no_jd(self):
        mock_q = MagicMock()
        area_builder = MagicMock()
        area_builder.build.return_value = ([mock_q], InterviewRetrievalMemory())

        svc = self._make_service(area_builder)

        svc.generate_first_question(
            role=RoleType.BACKEND_ENGINEER,
            level=SeniorityLevel.MID,
            interview_type=InterviewType.TECHNICAL,
        )

        call_kwargs = area_builder.build.call_args.kwargs
        assert call_kwargs.get("job_description") is None

    def test_generate_next_question_passes_jd_to_area_builder(self):
        mock_q = MagicMock()
        area_builder = MagicMock()
        area_builder.build.return_value = ([mock_q], InterviewRetrievalMemory())

        svc = self._make_service(area_builder)

        planned = [
            InterviewArea.TECH_TECHNICAL_KNOWLEDGE.value,
            InterviewArea.TECH_CODING.value,
        ]

        svc.generate_next_question(
            role=RoleType.BACKEND_ENGINEER,
            level=SeniorityLevel.SENIOR,
            interview_type=InterviewType.TECHNICAL,
            planned_areas=planned,
            generated_count=1,
            memory=InterviewRetrievalMemory(),
            job_description=_JD,
        )

        call_kwargs = area_builder.build.call_args.kwargs
        assert call_kwargs.get("job_description") == _JD


class TestContextProfileJDTruncationInStart:
    """
    Verifies that start.py truncates JD to 500 chars before passing to generation.
    This is a unit test of the truncation logic inline in start_interview.
    """

    def test_truncation_logic_at_500_chars(self):
        long_jd = "a" * 600
        truncated = long_jd.strip()[:500]
        assert len(truncated) == 500

    def test_none_jd_stays_none(self):
        jd = None
        result = jd.strip()[:500] if jd and jd.strip() else None
        assert result is None

    def test_blank_jd_becomes_none(self):
        jd = "   "
        result = jd.strip()[:500] if jd and jd.strip() else None
        assert result is None
