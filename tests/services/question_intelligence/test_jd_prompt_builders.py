# tests/services/question_intelligence/test_jd_prompt_builders.py

import pytest
from unittest.mock import patch, MagicMock

from domain.contracts.user.role import RoleType
from domain.contracts.user.seniority_level import SeniorityLevel
from domain.contracts.interview.interview_type import InterviewType
from domain.contracts.interview.interview_area import InterviewArea

from services.question_intelligence.question_generator import QuestionGenerator
from services.question_intelligence.coding_prompt_builder import CodingPromptBuilder


_SHORT_JD = "Looking for a senior backend engineer with Python and PostgreSQL experience."
_LONG_JD = "x" * 600


class TestQuestionGeneratorJDBlock:

    def test_jd_block_present_when_provided(self):
        gen = QuestionGenerator.__new__(QuestionGenerator)
        block = gen._jd_block(_SHORT_JD)
        assert "JOB DESCRIPTION CONTEXT" in block
        assert _SHORT_JD in block

    def test_jd_block_empty_when_none(self):
        gen = QuestionGenerator.__new__(QuestionGenerator)
        assert gen._jd_block(None) == ""

    def test_jd_block_empty_when_blank(self):
        gen = QuestionGenerator.__new__(QuestionGenerator)
        assert gen._jd_block("   ") == ""

    def test_jd_block_truncated_at_500_chars(self):
        gen = QuestionGenerator.__new__(QuestionGenerator)
        block = gen._jd_block(_LONG_JD)
        assert len(block) < 700  # well under 600 + header
        assert "x" * 500 in block
        assert "x" * 501 not in block

    def test_jd_block_guidance_note_present(self):
        gen = QuestionGenerator.__new__(QuestionGenerator)
        block = gen._jd_block(_SHORT_JD)
        assert "guidance only" in block
        assert "do not override domain" in block

    @patch("services.question_intelligence.question_generator.PromptRenderer.render")
    @patch("services.question_intelligence.question_generator.PromptLoader.load")
    def test_generate_passes_jd_block_to_template(self, mock_load, mock_render):
        mock_load.return_value = "template"
        mock_render.return_value = "rendered"

        llm = MagicMock()
        llm.invoke.return_value = MagicMock(content='[{"text":"Explain indexing in databases","difficulty":3}]')
        gen = QuestionGenerator(llm)

        gen.generate(
            role=RoleType.BACKEND_ENGINEER,
            level=SeniorityLevel.SENIOR,
            interview_type=InterviewType.TECHNICAL,
            area=InterviewArea.TECH_TECHNICAL_KNOWLEDGE,
            n=1,
            job_description=_SHORT_JD,
        )

        _, context = mock_render.call_args[0]
        assert "jd_block" in context
        assert "JOB DESCRIPTION CONTEXT" in context["jd_block"]

    @patch("services.question_intelligence.question_generator.PromptRenderer.render")
    @patch("services.question_intelligence.question_generator.PromptLoader.load")
    def test_generate_jd_block_empty_when_no_jd(self, mock_load, mock_render):
        mock_load.return_value = "template"
        mock_render.return_value = "rendered"

        llm = MagicMock()
        llm.invoke.return_value = MagicMock(content='[{"text":"Explain indexing in databases","difficulty":3}]')
        gen = QuestionGenerator(llm)

        gen.generate(
            role=RoleType.BACKEND_ENGINEER,
            level=SeniorityLevel.MID,
            interview_type=InterviewType.TECHNICAL,
            area=InterviewArea.TECH_TECHNICAL_KNOWLEDGE,
            n=1,
        )

        _, context = mock_render.call_args[0]
        assert context["jd_block"] == ""


class TestCodingPromptBuilderJDBlock:

    def test_jd_block_present_in_generation_prompt(self):
        builder = CodingPromptBuilder()
        block = builder._jd_block(_SHORT_JD)
        assert "JOB DESCRIPTION CONTEXT" in block
        assert _SHORT_JD in block

    def test_jd_block_empty_when_none(self):
        builder = CodingPromptBuilder()
        assert builder._jd_block(None) == ""

    def test_jd_block_truncated_at_500_chars(self):
        builder = CodingPromptBuilder()
        block = builder._jd_block(_LONG_JD)
        assert "x" * 500 in block
        assert "x" * 501 not in block

    @patch("services.question_intelligence.coding_prompt_builder.PromptRenderer.render")
    @patch("services.question_intelligence.coding_prompt_builder.PromptLoader.load")
    def test_build_generation_prompt_passes_jd_block(self, mock_load, mock_render):
        mock_load.return_value = "template"
        mock_render.return_value = "rendered"
        builder = CodingPromptBuilder()

        builder.build_generation_prompt(
            role="backend_engineer",
            level="senior",
            n=1,
            job_description=_SHORT_JD,
        )

        _, context = mock_render.call_args[0]
        assert "jd_block" in context
        assert "JOB DESCRIPTION CONTEXT" in context["jd_block"]

    @patch("services.question_intelligence.coding_prompt_builder.PromptRenderer.render")
    @patch("services.question_intelligence.coding_prompt_builder.PromptLoader.load")
    def test_build_enrichment_prompt_passes_jd_block(self, mock_load, mock_render):
        mock_load.return_value = "template"
        mock_render.return_value = "rendered"
        builder = CodingPromptBuilder()

        builder.build_enrichment_prompt(
            seed_prompt="Write a binary search",
            role="backend_engineer",
            level="mid",
            job_description=_SHORT_JD,
        )

        _, context = mock_render.call_args[0]
        assert "jd_block" in context
        assert "JOB DESCRIPTION CONTEXT" in context["jd_block"]

    @patch("services.question_intelligence.coding_prompt_builder.PromptRenderer.render")
    @patch("services.question_intelligence.coding_prompt_builder.PromptLoader.load")
    def test_build_generation_prompt_no_jd_empty_block(self, mock_load, mock_render):
        mock_load.return_value = "template"
        mock_render.return_value = "rendered"
        builder = CodingPromptBuilder()

        builder.build_generation_prompt(role="backend_engineer", level="mid", n=1)

        _, context = mock_render.call_args[0]
        assert context["jd_block"] == ""


class TestSQLPromptBuilderJDBlock:

    def _make_builder(self):
        from services.question_intelligence.sql_prompt_builder import SQLPromptBuilder
        import sqlite3
        conn = sqlite3.connect(":memory:")
        conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, name TEXT)")
        return SQLPromptBuilder(conn)

    @patch("services.question_intelligence.sql_prompt_builder.PromptRenderer.render")
    @patch("services.question_intelligence.sql_prompt_builder.PromptLoader.load")
    def test_build_generation_prompt_passes_jd_block(self, mock_load, mock_render):
        mock_load.return_value = "template"
        mock_render.return_value = "rendered"
        builder = self._make_builder()

        builder.build_generation_prompt(
            role="backend_engineer",
            level="senior",
            n=1,
            job_description=_SHORT_JD,
        )

        _, context = mock_render.call_args[0]
        assert "jd_block" in context
        assert "JOB DESCRIPTION CONTEXT" in context["jd_block"]

    @patch("services.question_intelligence.sql_prompt_builder.PromptRenderer.render")
    @patch("services.question_intelligence.sql_prompt_builder.PromptLoader.load")
    def test_build_enrichment_prompt_passes_jd_block(self, mock_load, mock_render):
        mock_load.return_value = "template"
        mock_render.return_value = "rendered"
        builder = self._make_builder()

        builder.build_enrichment_prompt(
            seed_prompt="Write a join query",
            role="backend_engineer",
            level="senior",
            job_description=_SHORT_JD,
        )

        _, context = mock_render.call_args[0]
        assert "jd_block" in context
        assert "JOB DESCRIPTION CONTEXT" in context["jd_block"]

    @patch("services.question_intelligence.sql_prompt_builder.PromptRenderer.render")
    @patch("services.question_intelligence.sql_prompt_builder.PromptLoader.load")
    def test_no_jd_empty_block(self, mock_load, mock_render):
        mock_load.return_value = "template"
        mock_render.return_value = "rendered"
        builder = self._make_builder()

        builder.build_generation_prompt(role="backend_engineer", level="mid", n=1)

        _, context = mock_render.call_args[0]
        assert context["jd_block"] == ""

    @patch("services.question_intelligence.sql_prompt_builder.PromptRenderer.render")
    @patch("services.question_intelligence.sql_prompt_builder.PromptLoader.load")
    def test_jd_truncated_at_500_chars(self, mock_load, mock_render):
        mock_load.return_value = "template"
        mock_render.return_value = "rendered"
        builder = self._make_builder()

        builder.build_generation_prompt(
            role="backend_engineer",
            level="mid",
            n=1,
            job_description=_LONG_JD,
        )

        _, context = mock_render.call_args[0]
        assert "x" * 500 in context["jd_block"]
        assert "x" * 501 not in context["jd_block"]
