# tests/domain/policies/test_hint_policy.py

from domain.policies.hint_policy import HintPolicy
from domain.contracts.hint_level import HintLevel


def test_hint_level_error_progression():

    policy = HintPolicy()

    level1 = policy.resolve(
        quality="incorrect",
        attempts=1,
        has_error=True,
    )

    level2 = policy.resolve(
        quality="incorrect",
        attempts=2,
        has_error=True,
    )

    assert level1 == HintLevel.TARGETED
    assert level2 == HintLevel.SOLUTION


def test_hint_respects_quality_correct():

    policy = HintPolicy()

    level = policy.resolve(
        quality="correct",
        attempts=1,
        has_error=False,
    )

    assert level == HintLevel.NONE


def test_hint_unknown_quality_fallback():

    policy = HintPolicy()

    level = policy.resolve(
        quality="unknown",
        attempts=2,
        has_error=False,
    )

    assert level == HintLevel.NONE


def test_hint_partial_progression():

    policy = HintPolicy()

    level1 = policy.resolve(
        quality="partial",
        attempts=1,
        has_error=False,
    )

    level2 = policy.resolve(
        quality="partial",
        attempts=2,
        has_error=False,
    )

    level3 = policy.resolve(
        quality="partial",
        attempts=3,
        has_error=False,
    )

    assert level1 == HintLevel.BASIC
    assert level2 == HintLevel.TARGETED
    assert level3 == HintLevel.SOLUTION
