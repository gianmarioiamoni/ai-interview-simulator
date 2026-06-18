# tests/domain/contracts/test_interview_context_profile.py

import pytest
from pydantic import ValidationError

from domain.contracts.interview.interview_context_profile import InterviewContextProfile
from domain.contracts.interview_state import InterviewState
from domain.contracts.user.role import Role, RoleType


class TestInterviewContextProfile:

    def test_default_is_empty(self):
        profile = InterviewContextProfile()
        assert profile.job_description is None
        assert profile.company_description is None

    def test_accepts_job_description(self):
        profile = InterviewContextProfile(job_description="Senior backend engineer role at FAANG.")
        assert profile.job_description == "Senior backend engineer role at FAANG."
        assert profile.company_description is None

    def test_accepts_company_description(self):
        profile = InterviewContextProfile(company_description="Fast-growing startup in FinTech.")
        assert profile.company_description == "Fast-growing startup in FinTech."
        assert profile.job_description is None

    def test_accepts_both_fields(self):
        profile = InterviewContextProfile(
            job_description="JD text",
            company_description="CD text",
        )
        assert profile.job_description == "JD text"
        assert profile.company_description == "CD text"

    def test_is_frozen(self):
        profile = InterviewContextProfile(job_description="JD")
        with pytest.raises(Exception):
            profile.job_description = "new"

    def test_rejects_extra_fields(self):
        with pytest.raises(ValidationError):
            InterviewContextProfile(unknown_field="x")

    def test_serialization_roundtrip(self):
        profile = InterviewContextProfile(job_description="JD", company_description="CD")
        restored = InterviewContextProfile.model_validate(profile.model_dump())
        assert restored == profile


class TestInterviewStateContextProfile:

    def _base(self) -> dict:
        return {
            "interview_id": "test-1",
            "role": Role(type=RoleType.BACKEND_ENGINEER),
            "company": "Acme",
            "language": "en",
        }

    def test_state_has_default_context_profile(self):
        state = InterviewState(**self._base())
        assert state.context_profile is not None
        assert state.context_profile.job_description is None
        assert state.context_profile.company_description is None

    def test_state_accepts_context_profile(self):
        profile = InterviewContextProfile(job_description="Backend role", company_description="Big Corp")
        state = InterviewState(**self._base(), context_profile=profile)
        assert state.context_profile.job_description == "Backend role"
        assert state.context_profile.company_description == "Big Corp"

    def test_state_serializes_context_profile(self):
        profile = InterviewContextProfile(job_description="JD text")
        state = InterviewState(**self._base(), context_profile=profile)
        data = state.model_dump()
        assert data["context_profile"]["job_description"] == "JD text"
        assert data["context_profile"]["company_description"] is None

    def test_state_create_initial_with_context_profile(self):
        from domain.contracts.user.role import RoleType
        from domain.contracts.interview.interview_type import InterviewType

        profile = InterviewContextProfile(job_description="JD", company_description="CD")
        state = InterviewState.create_initial(
            role_type=RoleType.BACKEND_ENGINEER,
            interview_type=InterviewType.TECHNICAL,
            company="TestCo",
            language="en",
            questions=[],
            interview_id="sid-1",
            context_profile=profile,
        )
        assert state.context_profile.job_description == "JD"
        assert state.context_profile.company_description == "CD"

    def test_state_create_initial_without_context_profile_defaults(self):
        from domain.contracts.user.role import RoleType
        from domain.contracts.interview.interview_type import InterviewType

        state = InterviewState.create_initial(
            role_type=RoleType.BACKEND_ENGINEER,
            interview_type=InterviewType.TECHNICAL,
            company="TestCo",
            language="en",
            questions=[],
            interview_id="sid-2",
        )
        assert state.context_profile.job_description is None
        assert state.context_profile.company_description is None

    def test_state_copy_preserves_context_profile(self):
        profile = InterviewContextProfile(job_description="JD")
        state = InterviewState(**self._base(), context_profile=profile)
        copied = state.model_copy(update={"company": "NewCo"})
        assert copied.context_profile.job_description == "JD"
