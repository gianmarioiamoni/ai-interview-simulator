# tests/domain/contracts/test_interview_setup.py

import pytest
from pydantic import ValidationError

from domain.contracts.interview_setup import InterviewSetup
from domain.contracts.role import Role, RoleType
from domain.contracts.company_profile import CompanyProfile, CompanyType
from domain.contracts.interview_area import InterviewType


def test_interview_setup_valid() -> None:
    setup = InterviewSetup(
        interview_type=InterviewType.TECHNICAL,
        role=Role(type=RoleType.BACKEND_ENGINEER),
        company=CompanyProfile(type=CompanyType.GOOGLE),
    )

    assert setup.language == "en"


def test_interview_setup_invalid_language() -> None:
    with pytest.raises(ValidationError):
        InterviewSetup(
            interview_type=InterviewType.HR,
            role=Role(type=RoleType.DEVOPS_ENGINEER),
            company=CompanyProfile(type=CompanyType.AMAZON),
            language="",
        )


def test_interview_setup_is_frozen() -> None:
    setup = InterviewSetup(
        interview_type=InterviewType.HR,
        role=Role(type=RoleType.QA_ENGINEER),
        company=CompanyProfile(type=CompanyType.META),
    )

    with pytest.raises(ValidationError):
        setup.language = "it"
