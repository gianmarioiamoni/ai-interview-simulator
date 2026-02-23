import pytest
from pydantic import ValidationError

from domain.contracts.interview_area import InterviewArea, InterviewType


def test_interview_area_valid() -> None:
    area = InterviewArea(
        id="tech-1",
        name="System Design",
        interview_type=InterviewType.TECHNICAL,
    )

    assert area.interview_type == InterviewType.TECHNICAL


def test_interview_area_invalid_empty_name() -> None:
    with pytest.raises(ValidationError):
        InterviewArea(
            id="tech-1",
            name="",
            interview_type=InterviewType.TECHNICAL,
        )


def test_interview_area_invalid_type() -> None:
    with pytest.raises(ValidationError):
        InterviewArea(
            id="tech-1",
            name="System Design",
            interview_type="random",
        )


def test_interview_area_is_frozen() -> None:
    area = InterviewArea(
        id="tech-1",
        name="System Design",
        interview_type=InterviewType.TECHNICAL,
    )

    with pytest.raises(ValidationError):
        area.name = "Changed"
