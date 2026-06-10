# tests/services/test_question_generator.py

import json

import pytest
from unittest.mock import MagicMock

from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.interview.interview_type import InterviewType
from domain.contracts.user.role import RoleType
from domain.contracts.user.seniority_level import SeniorityLevel
from services.question_intelligence.question_generator import QuestionGenerator


def build_llm(content: str) -> MagicMock:
    llm = MagicMock()
    llm.invoke.return_value.content = content
    return llm


def test_generate_parses_and_validates_output():

    llm = build_llm(
        """
        [
            {"text": "Explain REST principles in detail.", "difficulty": 3},
            {"text": "Describe CAP theorem trade-offs.", "difficulty": 4}
        ]
        """
    )

    generator = QuestionGenerator(llm)

    results = generator.generate(
        role=RoleType.BACKEND_ENGINEER,
        level=SeniorityLevel.MID,
        interview_type=InterviewType.TECHNICAL,
        area=InterviewArea.TECH_CASE_STUDY,
        n=2,
    )

    assert len(results) == 2
    assert results[0].text == "Explain REST principles in detail."
    assert results[0].difficulty == 3
    assert results[1].difficulty == 4


def test_generate_builds_prompt_with_context():

    llm = build_llm("[]")

    generator = QuestionGenerator(llm)

    generator.generate(
        role=RoleType.BACKEND_ENGINEER,
        level=SeniorityLevel.SENIOR,
        interview_type=InterviewType.TECHNICAL,
        area=InterviewArea.TECH_TECHNICAL_KNOWLEDGE,
        n=3,
    )

    prompt = llm.invoke.call_args[0][0]

    assert "backend_engineer" in prompt
    assert "senior" in prompt
    assert "technical_technical_knowledge" in prompt
    assert "Generate 3" in prompt


def test_generate_raises_on_invalid_json():

    llm = build_llm("not valid json")

    generator = QuestionGenerator(llm)

    with pytest.raises(json.JSONDecodeError):
        generator.generate(
            role=RoleType.BACKEND_ENGINEER,
            level=SeniorityLevel.MID,
            interview_type=InterviewType.TECHNICAL,
            area=InterviewArea.TECH_CASE_STUDY,
            n=2,
        )


def test_generate_raises_on_contract_violation():

    # difficulty out of bounds must be rejected by GeneratedQuestion
    llm = build_llm('[{"text": "A valid question text.", "difficulty": 9}]')

    generator = QuestionGenerator(llm)

    with pytest.raises(Exception):
        generator.generate(
            role=RoleType.BACKEND_ENGINEER,
            level=SeniorityLevel.MID,
            interview_type=InterviewType.TECHNICAL,
            area=InterviewArea.TECH_CASE_STUDY,
            n=1,
        )
