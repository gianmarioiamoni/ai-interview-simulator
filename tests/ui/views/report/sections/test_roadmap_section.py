# tests/ui/views/report/sections/test_roadmap_section.py

import pytest

from app.ui.views.report.sections.roadmap_section import render_roadmap


def _vm(roadmap=None, improvement_suggestions=None):
    return {
        "roadmap": roadmap or [],
        "improvement_suggestions": improvement_suggestions or [],
    }


class TestRenderRoadmap:

    def test_empty_roadmap_and_no_suggestions_returns_empty_string(self):
        result = render_roadmap(_vm())
        assert result == ""

    def test_suggestions_take_priority_over_roadmap(self):
        vm = _vm(
            roadmap=[{"priority": "HIGH", "dimension": "Communication", "action": "Work on clarity"}],
            improvement_suggestions=["Focus on algorithm efficiency"],
        )
        result = render_roadmap(vm)
        assert "Focus on algorithm efficiency" in result
        assert "Communication" not in result

    def test_roadmap_fallback_rendered_when_no_suggestions(self):
        vm = _vm(
            roadmap=[{"priority": "HIGH", "dimension": "Problem Solving", "action": "Practice edge cases"}],
        )
        result = render_roadmap(vm)
        assert "Problem Solving" in result
        assert "Practice edge cases" in result
        assert "[HIGH]" in result

    def test_multiple_suggestions_all_rendered(self):
        suggestions = ["Improve time complexity", "Handle edge cases", "Refactor nested loops"]
        result = render_roadmap(_vm(improvement_suggestions=suggestions))
        for s in suggestions:
            assert s in result

    def test_heading_present_when_content_exists(self):
        result = render_roadmap(_vm(improvement_suggestions=["Some tip"]))
        assert "Improvement Roadmap" in result

    def test_heading_absent_when_empty(self):
        result = render_roadmap(_vm())
        assert "Improvement Roadmap" not in result

    def test_none_suggestions_falls_back_to_roadmap(self):
        vm = {"roadmap": [{"priority": "HIGH", "dimension": "Communication", "action": "Use STAR"}], "improvement_suggestions": None}
        result = render_roadmap(vm)
        assert "Communication" in result
