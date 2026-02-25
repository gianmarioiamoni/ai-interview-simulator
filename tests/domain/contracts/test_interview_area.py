# tests/domain/contracts/test_interview_area.py

import pytest

from domain.contracts.interview_area import InterviewArea, InterviewType


def test_interview_area_valid_enum() -> None:
    area = InterviewArea.TECH_CODING

    assert area == InterviewArea.TECH_CODING


def test_interview_area_invalid_value() -> None:
    with pytest.raises(ValueError):
        InterviewArea("random_area")


def test_interview_type_valid_enum() -> None:
    interview_type = InterviewType.TECHNICAL

    assert interview_type == InterviewType.TECHNICAL


def test_interview_type_invalid_value() -> None:
    with pytest.raises(ValueError):
        InterviewType("random")


def test_interview_area_is_immutable() -> None:
    with pytest.raises(AttributeError):
        InterviewArea.TECH_DATABASE.value = "something"