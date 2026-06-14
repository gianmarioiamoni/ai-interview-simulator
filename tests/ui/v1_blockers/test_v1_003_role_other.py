# tests/ui/v1_blockers/test_v1_003_role_other.py

import pytest
from pydantic import ValidationError

from domain.contracts.user.role import Role, RoleType
from domain.contracts.interview_state import InterviewState
from domain.contracts.interview.interview_type import InterviewType
from domain.contracts.question.question import Question, QuestionType, QuestionDifficulty
from domain.contracts.interview.interview_area import InterviewArea


def _validate(role, role_custom_name, interview_type, seniority, interview_length, company, language) -> bool:
    """Pure logic mirror of InputValidator.validate without gradio dependency."""
    role_valid = role is not None
    if role == "other":
        role_valid = bool(role_custom_name and role_custom_name.strip())

    return (
        role_valid
        and interview_type is not None
        and seniority is not None
        and interview_length is not None
        and company is not None
        and company.strip() != ""
        and language is not None
    )


def _make_question() -> Question:
    return Question(
        id="q1",
        prompt="Describe your engineering philosophy.",
        type=QuestionType.WRITTEN,
        area=InterviewArea.TECH_BACKGROUND,
        difficulty=QuestionDifficulty.MEDIUM,
    )


class TestRoleModelValidation:
    def test_other_without_custom_name_raises(self):
        with pytest.raises(ValidationError):
            Role(type=RoleType.OTHER, custom_name=None)

    def test_other_with_custom_name_valid(self):
        role = Role(type=RoleType.OTHER, custom_name="Platform Engineer")
        assert role.custom_name == "Platform Engineer"

    def test_non_other_with_custom_name_raises(self):
        with pytest.raises(ValidationError):
            Role(type=RoleType.BACKEND_ENGINEER, custom_name="Something")

    def test_non_other_without_custom_name_valid(self):
        role = Role(type=RoleType.BACKEND_ENGINEER)
        assert role.custom_name is None


class TestCreateInitialWithOther:
    def test_create_initial_other_with_custom_name(self):
        state = InterviewState.create_initial(
            role_type=RoleType.OTHER,
            role_custom_name="Site Reliability Engineer",
            interview_type=InterviewType.TECHNICAL,
            company="Acme",
            language="en",
            questions=[_make_question()],
            interview_id="s1",
        )
        assert state.role.type == RoleType.OTHER
        assert state.role.custom_name == "Site Reliability Engineer"

    def test_create_initial_other_without_custom_name_raises(self):
        with pytest.raises(ValidationError):
            InterviewState.create_initial(
                role_type=RoleType.OTHER,
                role_custom_name=None,
                interview_type=InterviewType.TECHNICAL,
                company="Acme",
                language="en",
                questions=[_make_question()],
                interview_id="s2",
            )

    def test_create_initial_other_empty_string_raises(self):
        with pytest.raises(ValidationError):
            InterviewState.create_initial(
                role_type=RoleType.OTHER,
                role_custom_name="",
                interview_type=InterviewType.TECHNICAL,
                company="Acme",
                language="en",
                questions=[_make_question()],
                interview_id="s3",
            )

    def test_create_initial_standard_role_no_custom_name(self):
        state = InterviewState.create_initial(
            role_type=RoleType.BACKEND_ENGINEER,
            role_custom_name=None,
            interview_type=InterviewType.TECHNICAL,
            company="Acme",
            language="en",
            questions=[_make_question()],
            interview_id="s4",
        )
        assert state.role.type == RoleType.BACKEND_ENGINEER
        assert state.role.custom_name is None


class TestValidationLogicWithOther:
    def test_other_role_without_custom_name_invalid(self):
        assert not _validate("other", "", "TECHNICAL", "mid", 20, "Acme", "en")

    def test_other_role_none_custom_name_invalid(self):
        assert not _validate("other", None, "TECHNICAL", "mid", 20, "Acme", "en")

    def test_other_role_with_custom_name_valid(self):
        assert _validate("other", "Platform Engineer", "TECHNICAL", "mid", 20, "Acme", "en")

    def test_standard_role_without_custom_name_valid(self):
        assert _validate("backend_engineer", None, "TECHNICAL", "mid", 20, "Acme", "en")

    def test_missing_role_invalid(self):
        assert not _validate(None, None, "TECHNICAL", "mid", 20, "Acme", "en")

    def test_missing_company_invalid(self):
        assert not _validate("backend_engineer", None, "TECHNICAL", "mid", 20, "", "en")

    def test_missing_seniority_invalid(self):
        assert not _validate("backend_engineer", None, "TECHNICAL", None, 20, "Acme", "en")

    def test_missing_interview_length_invalid(self):
        assert not _validate("backend_engineer", None, "TECHNICAL", "mid", None, "Acme", "en")

    def test_all_valid_returns_true(self):
        assert _validate("backend_engineer", None, "TECHNICAL", "mid", 20, "Acme", "en")
