# tests/services/humanizer/follow_up/test_follow_up_prompt_builder.py
#
# Covers: prompt loading, rendering, placeholder substitution, contract tests.

import pytest
from unittest.mock import MagicMock, patch

from services.humanizer.follow_up.follow_up_prompt_builder import FollowUpPromptBuilder
from services.humanizer.follow_up.follow_up_prompt_input import FollowUpPromptInput


_FULL_INPUT = FollowUpPromptInput(
    question_area="technical_knowledge",
    previous_question="Explain Redis eviction policies.",
    previous_answer="I used LRU for Redis caching.",
    previous_feedback="Good high-level explanation.",
    candidate_level="senior",
    role="Backend Engineer",
    seniority="senior",
    job_description="Build distributed systems.",
    company_description="A fintech startup.",
    business_context="High-throughput trading platform.",
    follow_up_type="deep_dive",
)


class TestFollowUpPromptBuilder:

    def test_build_returns_string(self) -> None:
        result = FollowUpPromptBuilder().build(_FULL_INPUT)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_all_placeholders_substituted(self) -> None:
        result = FollowUpPromptBuilder().build(_FULL_INPUT)
        assert "{{" not in result
        assert "}}" not in result

    def test_question_area_in_output(self) -> None:
        result = FollowUpPromptBuilder().build(_FULL_INPUT)
        assert "technical_knowledge" in result

    def test_previous_question_in_output(self) -> None:
        result = FollowUpPromptBuilder().build(_FULL_INPUT)
        assert "Redis eviction policies" in result

    def test_previous_answer_in_output(self) -> None:
        result = FollowUpPromptBuilder().build(_FULL_INPUT)
        assert "LRU for Redis caching" in result

    def test_role_in_output(self) -> None:
        result = FollowUpPromptBuilder().build(_FULL_INPUT)
        assert "Backend Engineer" in result

    def test_seniority_in_output(self) -> None:
        result = FollowUpPromptBuilder().build(_FULL_INPUT)
        assert "senior" in result

    def test_follow_up_type_in_output(self) -> None:
        result = FollowUpPromptBuilder().build(_FULL_INPUT)
        assert "deep_dive" in result

    def test_output_instructs_json_only(self) -> None:
        result = FollowUpPromptBuilder().build(_FULL_INPUT)
        assert "follow_up_question" in result
        assert "reasoning" in result
        assert "topic_anchor" in result
        assert "confidence" in result

    def test_output_instructs_no_markdown(self) -> None:
        result = FollowUpPromptBuilder().build(_FULL_INPUT)
        assert "markdown" in result.lower() or "fences" in result.lower() or "```" in result

    def test_minimal_input_renders_without_error(self) -> None:
        minimal = FollowUpPromptInput(
            question_area="algorithms",
            previous_question="What is a hash map?",
            previous_answer="It stores key-value pairs.",
        )
        result = FollowUpPromptBuilder().build(minimal)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_prompt_file_not_found_raises(self) -> None:
        with patch(
            "services.humanizer.follow_up.follow_up_prompt_builder.PromptLoader.load",
            side_effect=FileNotFoundError("Prompt not found"),
        ):
            with pytest.raises(FileNotFoundError):
                FollowUpPromptBuilder().build(_FULL_INPUT)

    def test_rendering_error_propagates(self) -> None:
        from app.prompts.prompt_renderer import PromptRenderingError
        with patch(
            "services.humanizer.follow_up.follow_up_prompt_builder.PromptRenderer.render",
            side_effect=PromptRenderingError("bad template"),
        ):
            with pytest.raises(PromptRenderingError):
                FollowUpPromptBuilder().build(_FULL_INPUT)


class TestFollowUpPromptInput:

    def test_frozen_model(self) -> None:
        from pydantic import ValidationError as PydanticVE
        inp = FollowUpPromptInput(
            question_area="area",
            previous_question="q?",
            previous_answer="a",
        )
        with pytest.raises((TypeError, AttributeError, PydanticVE)):
            inp.question_area = "other"  # type: ignore[misc]

    def test_extra_fields_forbidden(self) -> None:
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            FollowUpPromptInput(  # type: ignore[call-arg]
                question_area="area",
                previous_question="q?",
                previous_answer="a",
                unknown_field="bad",
            )

    def test_required_fields_missing_raises(self) -> None:
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            FollowUpPromptInput(question_area="area")  # type: ignore[call-arg]

    def test_defaults(self) -> None:
        inp = FollowUpPromptInput(
            question_area="area",
            previous_question="q?",
            previous_answer="a",
        )
        assert inp.follow_up_type == "deep_dive"
        assert inp.previous_feedback == ""
