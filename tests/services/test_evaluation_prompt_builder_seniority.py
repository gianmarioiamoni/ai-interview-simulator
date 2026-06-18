# tests/services/test_evaluation_prompt_builder_seniority.py

import pytest
from unittest.mock import patch, MagicMock

from domain.contracts.question.question import Question, QuestionType, QuestionDifficulty
from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.interview.answer import Answer
from domain.contracts.user.role import Role, RoleType

from services.prompt_builders.evaluation_prompt_builder import build_evaluation_prompt


def _make_question() -> Question:
    return Question(
        id="q1",
        area=InterviewArea.TECH_TECHNICAL_KNOWLEDGE,
        type=QuestionType.WRITTEN,
        prompt="Explain indexing in databases.",
        difficulty=QuestionDifficulty.MEDIUM,
    )


def _make_answer() -> Answer:
    return Answer(question_id="q1", content="An index speeds up reads.", attempt=1)


def _make_role() -> Role:
    return Role(type=RoleType.BACKEND_ENGINEER)


class TestEvaluationPromptBuilderSeniority:

    @patch("services.prompt_builders.evaluation_prompt_builder.PromptRenderer.render")
    @patch("services.prompt_builders.evaluation_prompt_builder.PromptLoader.load")
    def test_seniority_level_injected_into_context(self, mock_load, mock_render):
        mock_load.return_value = "template"
        mock_render.return_value = "rendered"

        build_evaluation_prompt(
            _make_question(),
            _make_answer(),
            role=_make_role(),
            seniority_level="senior",
        )

        _, context = mock_render.call_args[0]
        assert context["seniority_level"] == "senior"

    @patch("services.prompt_builders.evaluation_prompt_builder.PromptRenderer.render")
    @patch("services.prompt_builders.evaluation_prompt_builder.PromptLoader.load")
    def test_seniority_level_defaults_to_mid_when_none(self, mock_load, mock_render):
        mock_load.return_value = "template"
        mock_render.return_value = "rendered"

        build_evaluation_prompt(
            _make_question(),
            _make_answer(),
            role=_make_role(),
            seniority_level=None,
        )

        _, context = mock_render.call_args[0]
        assert context["seniority_level"] == "mid"

    @patch("services.prompt_builders.evaluation_prompt_builder.PromptRenderer.render")
    @patch("services.prompt_builders.evaluation_prompt_builder.PromptLoader.load")
    def test_seniority_level_junior_propagated(self, mock_load, mock_render):
        mock_load.return_value = "template"
        mock_render.return_value = "rendered"

        build_evaluation_prompt(
            _make_question(),
            _make_answer(),
            role=_make_role(),
            seniority_level="junior",
        )

        _, context = mock_render.call_args[0]
        assert context["seniority_level"] == "junior"

    @patch("services.prompt_builders.evaluation_prompt_builder.PromptRenderer.render")
    @patch("services.prompt_builders.evaluation_prompt_builder.PromptLoader.load")
    def test_backward_compat_no_seniority_arg(self, mock_load, mock_render):
        mock_load.return_value = "template"
        mock_render.return_value = "rendered"

        build_evaluation_prompt(
            _make_question(),
            _make_answer(),
            role=_make_role(),
        )

        _, context = mock_render.call_args[0]
        assert "seniority_level" in context
        assert context["seniority_level"] == "mid"
