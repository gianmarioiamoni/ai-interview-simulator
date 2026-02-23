# tests/domain/contracts/test_company_profile.py

import pytest
from pydantic import ValidationError

from domain.contracts.company_profile import CompanyProfile, CompanyType


def test_company_profile_valid_standard() -> None:
    company = CompanyProfile(type=CompanyType.GOOGLE)
    assert company.type == CompanyType.GOOGLE
    assert company.custom_name is None


def test_company_profile_valid_other_with_custom_name() -> None:
    company = CompanyProfile(
        type=CompanyType.OTHER,
        custom_name="Stripe",
    )

    assert company.custom_name == "Stripe"


def test_company_profile_other_without_custom_name_invalid() -> None:
    with pytest.raises(ValidationError):
        CompanyProfile(type=CompanyType.OTHER)


def test_company_profile_standard_with_custom_name_invalid() -> None:
    with pytest.raises(ValidationError):
        CompanyProfile(
            type=CompanyType.AMAZON,
            custom_name="Invalid",
        )


def test_company_profile_is_frozen() -> None:
    company = CompanyProfile(type=CompanyType.GOOGLE)

    with pytest.raises(ValidationError):
        company.type = CompanyType.META
