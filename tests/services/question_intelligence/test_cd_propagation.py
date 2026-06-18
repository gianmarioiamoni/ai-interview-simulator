# tests/services/question_intelligence/test_cd_propagation.py

import pytest
from unittest.mock import MagicMock

from domain.contracts.user.role import RoleType
from domain.contracts.user.seniority_level import SeniorityLevel
from domain.contracts.interview.interview_type import InterviewType
from domain.contracts.interview.interview_area import InterviewArea

from services.question_intelligence.area_question_builder import AreaQuestionBuilder
from services.question_corpus.contracts.interview_retrieval_memory import InterviewRetrievalMemory


_CD = "Fintech company building payment processing infrastructure at scale."


def _make_pipeline_mock():
    mock = MagicMock()
    mock.build.return_value = ([], InterviewRetrievalMemory())
    return mock


class TestAreaQuestionBuilderCDPropagation:

    def _make_builder(self, written_mock, coding_mock, sql_mock):
        builder = AreaQuestionBuilder.__new__(AreaQuestionBuilder)
        builder._written_pipeline = written_mock
        builder._coding_pipeline = coding_mock
        builder._sql_pipeline = sql_mock
        return builder

    def test_written_pipeline_receives_company_description(self):
        written = _make_pipeline_mock()
        coding = _make_pipeline_mock()
        sql = _make_pipeline_mock()
        builder = self._make_builder(written, coding, sql)

        builder.build(
            role=RoleType.BACKEND_ENGINEER,
            level=SeniorityLevel.SENIOR,
            interview_type=InterviewType.TECHNICAL,
            area=InterviewArea.TECH_TECHNICAL_KNOWLEDGE,
            company_description=_CD,
        )

        call_kwargs = written.build.call_args.kwargs
        assert call_kwargs.get("company_description") == _CD

    def test_coding_pipeline_receives_company_description(self):
        written = _make_pipeline_mock()
        coding = _make_pipeline_mock()
        sql = _make_pipeline_mock()
        builder = self._make_builder(written, coding, sql)

        builder.build(
            role=RoleType.BACKEND_ENGINEER,
            level=SeniorityLevel.SENIOR,
            interview_type=InterviewType.TECHNICAL,
            area=InterviewArea.TECH_CODING,
            company_description=_CD,
        )

        call_kwargs = coding.build.call_args.kwargs
        assert call_kwargs.get("company_description") == _CD

    def test_sql_pipeline_receives_company_description(self):
        written = _make_pipeline_mock()
        coding = _make_pipeline_mock()
        sql = _make_pipeline_mock()
        builder = self._make_builder(written, coding, sql)

        builder.build(
            role=RoleType.BACKEND_ENGINEER,
            level=SeniorityLevel.SENIOR,
            interview_type=InterviewType.TECHNICAL,
            area=InterviewArea.TECH_DATABASE,
            company_description=_CD,
        )

        call_kwargs = sql.build.call_args.kwargs
        assert call_kwargs.get("company_description") == _CD

    def test_written_pipeline_receives_none_when_no_cd(self):
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
        assert call_kwargs.get("company_description") is None


class TestLazyAdaptiveInterviewServiceCDPropagation:

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

    def test_generate_first_question_passes_cd_to_area_builder(self):
        mock_q = MagicMock()
        area_builder = MagicMock()
        area_builder.build.return_value = ([mock_q], InterviewRetrievalMemory())

        svc = self._make_service(area_builder)

        svc.generate_first_question(
            role=RoleType.BACKEND_ENGINEER,
            level=SeniorityLevel.SENIOR,
            interview_type=InterviewType.TECHNICAL,
            company_description=_CD,
        )

        call_kwargs = area_builder.build.call_args.kwargs
        assert call_kwargs.get("company_description") == _CD

    def test_generate_first_question_passes_none_when_no_cd(self):
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
        assert call_kwargs.get("company_description") is None

    def test_generate_next_question_passes_cd_to_area_builder(self):
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
            company_description=_CD,
        )

        call_kwargs = area_builder.build.call_args.kwargs
        assert call_kwargs.get("company_description") == _CD


class TestCDPromptBuilders:

    def test_question_generator_cd_block_present(self):
        from services.question_intelligence.question_generator import QuestionGenerator
        gen = QuestionGenerator.__new__(QuestionGenerator)
        block = gen._cd_block(_CD)
        assert "BUSINESS CONTEXT" in block
        assert "Fintech" in block

    def test_question_generator_cd_block_absent_when_none(self):
        from services.question_intelligence.question_generator import QuestionGenerator
        gen = QuestionGenerator.__new__(QuestionGenerator)
        assert gen._cd_block(None) == ""
        assert gen._cd_block("  ") == ""

    def test_question_generator_cd_block_truncated_at_200(self):
        from services.question_intelligence.question_generator import QuestionGenerator
        gen = QuestionGenerator.__new__(QuestionGenerator)
        long_cd = "x" * 300
        block = gen._cd_block(long_cd)
        assert "x" * 200 in block
        assert "x" * 201 not in block

    def test_coding_prompt_builder_cd_block_present(self):
        from services.question_intelligence.coding_prompt_builder import CodingPromptBuilder
        builder = CodingPromptBuilder()
        block = builder._cd_block(_CD)
        assert "COMPANY DESCRIPTION" in block
        assert "Fintech" in block

    def test_coding_prompt_builder_cd_block_absent_when_none(self):
        from services.question_intelligence.coding_prompt_builder import CodingPromptBuilder
        builder = CodingPromptBuilder()
        assert builder._cd_block(None) == ""

    def test_sql_prompt_builder_cd_block_truncated_at_200(self):
        from services.question_intelligence.sql_prompt_builder import SQLPromptBuilder
        import sqlite3
        conn = sqlite3.connect(":memory:")
        builder = SQLPromptBuilder(conn)
        long_cd = "y" * 300
        block = builder._cd_block(long_cd)
        assert "y" * 200 in block
        assert "y" * 201 not in block

    def test_sql_prompt_builder_cd_block_absent_when_none(self):
        from services.question_intelligence.sql_prompt_builder import SQLPromptBuilder
        import sqlite3
        conn = sqlite3.connect(":memory:")
        builder = SQLPromptBuilder(conn)
        assert builder._cd_block(None) == ""


class TestCDPromptTemplateRendering:

    def test_question_generation_template_renders_cd_block(self):
        from services.question_intelligence.question_generator import QuestionGenerator
        from app.prompts.prompt_loader import PromptLoader
        from app.prompts.prompt_renderer import PromptRenderer

        gen = QuestionGenerator.__new__(QuestionGenerator)
        template = PromptLoader.load("generation/question_generation.txt")
        rendered = PromptRenderer.render(
            template,
            {
                "n": 1,
                "interview_type": "technical",
                "level": "senior",
                "role": "backend_engineer",
                "area": "technical_technical_knowledge",
                "variation": "Focus on scalability",
                "theme_block": "",
                "cd_block": gen._cd_block(_CD),
                "jd_block": "",
            },
        )
        assert "BUSINESS CONTEXT" in rendered
        assert "Fintech" in rendered

    def test_cd_block_appears_before_jd_block_in_written_template(self):
        from services.question_intelligence.question_generator import QuestionGenerator
        from app.prompts.prompt_loader import PromptLoader
        from app.prompts.prompt_renderer import PromptRenderer

        gen = QuestionGenerator.__new__(QuestionGenerator)
        template = PromptLoader.load("generation/question_generation.txt")
        rendered = PromptRenderer.render(
            template,
            {
                "n": 1,
                "interview_type": "technical",
                "level": "senior",
                "role": "backend_engineer",
                "area": "technical_technical_knowledge",
                "variation": "Focus on scalability",
                "theme_block": "",
                "cd_block": gen._cd_block(_CD),
                "jd_block": "\nJOB DESCRIPTION CONTEXT (guidance only):\nSome JD\n",
            },
        )
        cd_pos = rendered.index("BUSINESS CONTEXT")
        jd_pos = rendered.index("JOB DESCRIPTION CONTEXT")
        assert cd_pos < jd_pos


class TestCDTruncationLogic:

    def test_truncation_at_200_chars(self):
        long_cd = "a" * 300
        result = long_cd.strip()[:200] if long_cd and long_cd.strip() else None
        assert len(result) == 200

    def test_none_cd_stays_none(self):
        cd = None
        result = cd.strip()[:200] if cd and cd.strip() else None
        assert result is None

    def test_blank_cd_becomes_none(self):
        cd = "   "
        result = cd.strip()[:200] if cd and cd.strip() else None
        assert result is None
