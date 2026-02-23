import pytest
from pydantic import ValidationError

from domain.contracts.coding_test_case import CodingTestCase


def test_valid_test_case():
    test_case = CodingTestCase(
        args=[2],
        kwargs={},
        expected=4,
    )

    assert test_case.args == [2]
    assert test_case.expected == 4


def test_default_args_and_kwargs():
    test_case = CodingTestCase(
        expected=10,
    )

    assert test_case.args == []
    assert test_case.kwargs == {}


def test_missing_expected_raises():
    with pytest.raises(ValidationError):
        CodingTestCase(
            args=[1],
            kwargs={},
        )


def test_immutable():
    test_case = CodingTestCase(expected=5)

    with pytest.raises(ValidationError):
        test_case.expected = 10
