# tests/domain/contracts/reasoning/test_reasoner_decision.py

import pytest
from pydantic import ValidationError

from domain.contracts.reasoning.reasoner_decision import ReasonerDecision
from domain.contracts.reasoning.follow_up_recommendation import FollowUpRecommendation
from domain.contracts.reasoning.navigation_recommendation import NavigationRecommendation


def _make_decision(**overrides) -> ReasonerDecision:
    defaults = dict(session_id="sess-1", question_index=3)
    defaults.update(overrides)
    return ReasonerDecision(**defaults)


def test_skip_default_false():
    d = _make_decision()
    assert d.skip is False


def test_skip_true():
    d = _make_decision(skip=True)
    assert d.skip is True


def test_schema_version_default():
    d = _make_decision()
    assert d.schema_version == "1.0"


def test_immutable():
    d = _make_decision()
    with pytest.raises((ValidationError, TypeError)):
        d.session_id = "other"


def test_extra_fields_forbidden():
    with pytest.raises(ValidationError):
        _make_decision(free_text_explanation="something")


def test_no_recommendations_by_default():
    d = _make_decision()
    assert d.follow_up_recommendation is None
    assert d.navigation_recommendation is None


def test_follow_up_recommendation():
    rec = FollowUpRecommendation(recommended=True)
    d = _make_decision(follow_up_recommendation=rec)
    assert d.follow_up_recommendation.recommended is True


def test_navigation_recommendation():
    rec = NavigationRecommendation(deepen_current=True)
    d = _make_decision(navigation_recommendation=rec)
    assert d.navigation_recommendation.deepen_current is True


def test_session_id_non_empty():
    with pytest.raises(ValidationError):
        _make_decision(session_id="")


def test_question_index_non_negative():
    with pytest.raises(ValidationError):
        _make_decision(question_index=-1)
