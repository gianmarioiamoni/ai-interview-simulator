# tests/ui/replay/test_replay_coaching_panel.py

from __future__ import annotations

from app.ui.replay.panels.replay_coaching_panel import ReplayCoachingPanel
from tests.domain.contracts.knowledge_snapshot.conftest import make_coaching_snapshot
from tests.ui.replay.conftest import (
    make_narrative_with_insights,
    make_populated_coaching_snapshot,
    make_replay_session,
)


def test_renders_labelled_sections_with_content() -> None:
    session = make_replay_session(
        narrative=make_narrative_with_insights(),
        coaching_snapshot=make_populated_coaching_snapshot(),
    )
    model = ReplayCoachingPanel(session).render()

    assert model.section_a_label == "Session Narrative"
    assert model.section_b_label == "Study Plan"
    assert model.overview_label == "Knowledge Overview"
    assert model.overview_prose == "Test prose."
    assert model.narrative_empty_label is None
    assert len(model.narrative_insights) == 1
    assert len(model.coaching_objectives) == 1
    assert model.coaching_empty_label is None
    assert len(model.coaching_recommendations) == 1


def test_empty_insights_and_objectives_show_neutral_indicators() -> None:
    session = make_replay_session(coaching_snapshot=make_coaching_snapshot())
    model = ReplayCoachingPanel(session).render()

    assert model.narrative_insights == ()
    assert model.narrative_empty_label == "No narrative insights recorded"
    assert model.coaching_objectives == ()
    assert model.coaching_empty_label == "No coaching objectives recorded"
    assert model.coaching_recommendations == ()
