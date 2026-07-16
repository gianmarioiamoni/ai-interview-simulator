# tests/ui/views/report/test_coaching_actions_section.py
# EPIC-06 C7 — render_coaching_actions inline origin from CoachingActionDTO (OF-01).

import pytest

from app.ui.dto.final_report_dto import CoachingActionDTO
from app.ui.views.report.sections.coaching_section import render_coaching_actions


def _make_action(
    description: str = "Practice structured trade-off analysis.",
    category: str = "practice",
    effort_estimate_hours: float = 3.0,
    is_immediate: bool = False,
    origin_feature_type: str = "reasoning",
    origin_supporting_observation_types: list[str] | None = None,
    origin_objective_description: str = "Strengthen algorithmic reasoning",
) -> CoachingActionDTO:
    if origin_supporting_observation_types is None:
        origin_supporting_observation_types = ["reasoning_depth_low"]
    return CoachingActionDTO(
        action_id="act-001",
        objective_id="obj-001",
        category=category,
        description=description,
        effort_estimate_hours=effort_estimate_hours,
        is_immediate=is_immediate,
        origin_feature_type=origin_feature_type,
        origin_supporting_observation_types=origin_supporting_observation_types,
        origin_objective_description=origin_objective_description,
    )


class TestRenderCoachingActions:

    def test_empty_actions_returns_empty_string(self):
        assert render_coaching_actions({"coaching_actions": []}) == ""

    def test_missing_key_returns_empty_string(self):
        assert render_coaching_actions({}) == ""

    def test_renders_description(self):
        action = _make_action(description="Drill timed coding drills.")
        html = render_coaching_actions({"coaching_actions": [action]})
        assert "Drill timed coding drills." in html

    def test_renders_category(self):
        action = _make_action(category="practice")
        html = render_coaching_actions({"coaching_actions": [action]})
        assert "Practice" in html

    def test_renders_effort(self):
        action = _make_action(effort_estimate_hours=5.0)
        html = render_coaching_actions({"coaching_actions": [action]})
        assert "5h" in html

    def test_renders_immediate_badge(self):
        action = _make_action(is_immediate=True)
        html = render_coaching_actions({"coaching_actions": [action]})
        assert "Immediate" in html

    def test_section_header_present(self):
        html = render_coaching_actions({"coaching_actions": [_make_action()]})
        assert "Coaching Actions" in html

    def test_renders_origin_feature_type(self):
        action = _make_action(origin_feature_type="reasoning")
        html = render_coaching_actions({"coaching_actions": [action]})
        assert "Origin:" in html
        assert "Reasoning" in html

    def test_renders_origin_supporting_observation_types(self):
        action = _make_action(
            origin_supporting_observation_types=["reasoning_depth_low", "coverage_gap"]
        )
        html = render_coaching_actions({"coaching_actions": [action]})
        assert "Supporting observations:" in html
        assert "Reasoning Depth Low" in html
        assert "Coverage Gap" in html

    def test_renders_empty_supporting_observations_as_none(self):
        action = _make_action(origin_supporting_observation_types=[])
        html = render_coaching_actions({"coaching_actions": [action]})
        assert "Supporting observations:" in html
        assert "None" in html

    def test_renders_origin_objective_description(self):
        action = _make_action(
            origin_objective_description="Strengthen algorithmic reasoning"
        )
        html = render_coaching_actions({"coaching_actions": [action]})
        assert "Objective:" in html
        assert "Strengthen algorithmic reasoning" in html

    def test_origin_rendered_under_each_action(self):
        actions = [
            _make_action(
                description="Action A",
                origin_feature_type="reasoning",
                origin_objective_description="Objective A",
            ),
            CoachingActionDTO(
                action_id="act-002",
                objective_id="obj-002",
                category="study",
                description="Action B",
                effort_estimate_hours=2.0,
                is_immediate=False,
                origin_feature_type="communication",
                origin_supporting_observation_types=["clarity_low"],
                origin_objective_description="Objective B",
            ),
        ]
        html = render_coaching_actions({"coaching_actions": actions})
        assert html.count("Origin:") == 2
        assert "Action A" in html
        assert "Action B" in html
        assert "Objective A" in html
        assert "Objective B" in html

    def test_missing_origin_feature_type_fails_fast(self):
        class _BrokenAction:
            description = "Broken"
            category = "practice"
            effort_estimate_hours = 1.0
            is_immediate = False
            origin_feature_type = ""
            origin_supporting_observation_types = ["reasoning_depth_low"]
            origin_objective_description = "Objective"

        with pytest.raises(ValueError, match="origin_feature_type"):
            render_coaching_actions({"coaching_actions": [_BrokenAction()]})

    def test_missing_origin_supporting_observation_types_fails_fast(self):
        class _BrokenAction:
            description = "Broken"
            category = "practice"
            effort_estimate_hours = 1.0
            is_immediate = False
            origin_feature_type = "reasoning"
            origin_supporting_observation_types = None
            origin_objective_description = "Objective"

        with pytest.raises(ValueError, match="origin_supporting_observation_types"):
            render_coaching_actions({"coaching_actions": [_BrokenAction()]})

    def test_missing_origin_objective_description_fails_fast(self):
        class _BrokenAction:
            description = "Broken"
            category = "practice"
            effort_estimate_hours = 1.0
            is_immediate = False
            origin_feature_type = "reasoning"
            origin_supporting_observation_types = []
            origin_objective_description = ""

        with pytest.raises(ValueError, match="origin_objective_description"):
            render_coaching_actions({"coaching_actions": [_BrokenAction()]})
