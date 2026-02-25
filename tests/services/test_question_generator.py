# Tests for QuestionGenerator

from unittest.mock import MagicMock, patch

from services.question_intelligence.question_generator import (
    QuestionGenerator,
)
from domain.contracts.role import Role
from domain.contracts.role import RoleType
from domain.contracts.interview_area import InterviewArea


def test_generate_parses_and_validates_output():
    mock_llm = MagicMock()

    mock_llm.invoke.return_value.content = """
    [
        {"text": "Explain REST principles.", "difficulty": 3},
        {"text": "Describe CAP theorem trade-offs.", "difficulty": 4}
    ]
    """

    with patch(
        "services.question_intelligence.question_generator.get_llm",
        return_value=mock_llm,
    ):
        generator = QuestionGenerator()

        results = generator.generate(
            role=Role(type=RoleType.BACKEND_ENGINEER),
            level="mid",
            interview_type="technical",
            area=InterviewArea.TECH_CASE_STUDY,
            n=2,
        )

        assert len(results) == 2
        assert results[0].difficulty == 3
        assert results[1].difficulty == 4
