import pytest
from pydantic import ValidationError

from domain.contracts.role import Role, RoleType


def test_role_valid_standard() -> None:
    role = Role(type=RoleType.BACKEND_ENGINEER)
    assert role.type == RoleType.BACKEND_ENGINEER
    assert role.custom_name is None


def test_role_valid_other_with_custom_name() -> None:
    role = Role(type=RoleType.OTHER, custom_name="Blockchain Engineer")
    assert role.custom_name == "Blockchain Engineer"


def test_role_other_without_custom_name_invalid() -> None:
    with pytest.raises(ValidationError):
        Role(type=RoleType.OTHER)


def test_role_standard_with_custom_name_invalid() -> None:
    with pytest.raises(ValidationError):
        Role(
            type=RoleType.BACKEND_ENGINEER,
            custom_name="Should not exist",
        )


def test_role_is_frozen() -> None:
    role = Role(type=RoleType.BACKEND_ENGINEER)

    with pytest.raises(ValidationError):
        role.type = RoleType.DEVOPS_ENGINEER
