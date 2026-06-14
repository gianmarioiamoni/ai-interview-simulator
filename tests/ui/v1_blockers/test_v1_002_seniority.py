# tests/ui/v1_blockers/test_v1_002_seniority.py

import pytest

from domain.contracts.interview_state.factory import InterviewStateFactoryMixin
from domain.contracts.interview_state import InterviewState
from domain.contracts.user.role import RoleType
from domain.contracts.user.seniority_level import SeniorityLevel
from domain.contracts.interview.interview_type import InterviewType
from domain.contracts.question.question import Question, QuestionType, QuestionDifficulty
from domain.contracts.interview.interview_area import InterviewArea


def _make_question() -> Question:
    return Question(
        id="q1",
        prompt="Explain dependency injection.",
        type=QuestionType.WRITTEN,
        area=InterviewArea.TECH_BACKGROUND,
        difficulty=QuestionDifficulty.MEDIUM,
    )


class TestSeniorityOnState:
    def test_create_initial_stores_seniority_junior(self):
        state = InterviewState.create_initial(
            role_type=RoleType.BACKEND_ENGINEER,
            interview_type=InterviewType.TECHNICAL,
            company="Acme",
            language="en",
            questions=[_make_question()],
            interview_id="s1",
            seniority_level="junior",
            interview_length=20,
        )
        assert state.seniority_level == "junior"

    def test_create_initial_stores_seniority_mid(self):
        state = InterviewState.create_initial(
            role_type=RoleType.BACKEND_ENGINEER,
            interview_type=InterviewType.TECHNICAL,
            company="Acme",
            language="en",
            questions=[_make_question()],
            interview_id="s2",
            seniority_level="mid",
            interview_length=20,
        )
        assert state.seniority_level == "mid"

    def test_create_initial_stores_seniority_senior(self):
        state = InterviewState.create_initial(
            role_type=RoleType.BACKEND_ENGINEER,
            interview_type=InterviewType.TECHNICAL,
            company="Acme",
            language="en",
            questions=[_make_question()],
            interview_id="s3",
            seniority_level="senior",
            interview_length=20,
        )
        assert state.seniority_level == "senior"

    def test_default_seniority_is_mid(self):
        state = InterviewState.create_initial(
            role_type=RoleType.BACKEND_ENGINEER,
            interview_type=InterviewType.TECHNICAL,
            company="Acme",
            language="en",
            questions=[_make_question()],
            interview_id="s4",
        )
        assert state.seniority_level == "mid"

    def test_seniority_level_enum_resolution(self):
        for level in SeniorityLevel:
            resolved = SeniorityLevel(level.value)
            assert resolved == level


class TestSeniorityNotHardcoded:
    def test_adaptive_navigation_node_uses_state_seniority(self):
        from app.graph.nodes.adaptive_navigation_node import AdaptiveNavigationNode

        node = AdaptiveNavigationNode(seniority_level=SeniorityLevel.JUNIOR)
        assert node._seniority_level == SeniorityLevel.JUNIOR

    def test_adaptive_navigation_node_defaults_none(self):
        from app.graph.nodes.adaptive_navigation_node import AdaptiveNavigationNode

        node = AdaptiveNavigationNode()
        assert node._seniority_level is None

    def test_configure_navigation_node_passes_seniority(self):
        from app.graph.nodes.navigation_node import configure_navigation_node, _default_navigation_node
        import app.graph.nodes.navigation_node as nav_module

        configure_navigation_node(seniority_level=SeniorityLevel.SENIOR)
        assert nav_module._default_navigation_node._seniority_level == SeniorityLevel.SENIOR
