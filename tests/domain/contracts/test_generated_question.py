# Tests for GeneratedQuestion contract

import pytest
from pydantic import ValidationError

from domain.contracts.generated_question import GeneratedQuestion


def test_valid_generated_question():
    q = GeneratedQuestion(
        text="Explain the difference between REST and GraphQL.",
        difficulty=3,
    )

    assert q.difficulty == 3


def test_invalid_difficulty():
    with pytest.raises(ValidationError):
        GeneratedQuestion(
            text="Explain something.",
            difficulty=10,
        )


def test_text_too_short():
    with pytest.raises(ValidationError):
        GeneratedQuestion(
            text="Too short",
            difficulty=3,
        )
