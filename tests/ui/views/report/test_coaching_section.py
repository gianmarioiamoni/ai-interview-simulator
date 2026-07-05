# tests/ui/views/report/test_coaching_section.py
# EPIC-V13-05 Phase 10 — render_coaching_objectives and render_study_recommendations tests.

from domain.contracts.coaching.learning_objective import LearningObjective, ObjectivePriority
from domain.contracts.coaching.study_recommendation import StudyRecommendation, ResourceType
from domain.contracts.feature.feature_type import FeatureType
from domain.contracts.observation.observation_type import ObservationType

from app.ui.views.report.sections.coaching_section import render_coaching_objectives
from app.ui.views.report.sections.study_recommendations_section import render_study_recommendations


def _make_objective(
    description: str = "Practice system design trade-offs.",
    priority: ObjectivePriority = ObjectivePriority.HIGH,
    confidence: float = 0.80,
) -> LearningObjective:
    return LearningObjective(
        objective_id="obj-test-001",
        feature_type=FeatureType.REASONING,
        description=description,
        priority=priority,
        confidence=confidence,
        supporting_observation_types=(ObservationType.REASONING_DEPTH_LOW,),
        detected_at_question_index=1,
        candidate_identity_id="cand-001",
    )


def _make_recommendation(obj: LearningObjective | None = None) -> StudyRecommendation:
    objective = obj or _make_objective()
    return StudyRecommendation.for_objective(
        objective=objective,
        recommendation_id="rec-test-001",
        resource_type=ResourceType.EXERCISE,
        topic="System Design Exercises",
        rationale="Directly addresses the identified reasoning gap.",
        estimated_duration_hours=4.0,
    )


class TestRenderCoachingObjectives:

    def test_empty_objectives_returns_empty_string(self):
        assert render_coaching_objectives({"coaching_objectives": []}) == ""

    def test_missing_key_returns_empty_string(self):
        assert render_coaching_objectives({}) == ""

    def test_renders_description(self):
        obj = _make_objective(description="Deepen causal reasoning skills.")
        html = render_coaching_objectives({"coaching_objectives": [obj]})
        assert "Deepen causal reasoning skills." in html

    def test_renders_priority(self):
        obj = _make_objective(priority=ObjectivePriority.CRITICAL)
        html = render_coaching_objectives({"coaching_objectives": [obj]})
        assert "critical" in html

    def test_renders_confidence(self):
        obj = _make_objective(confidence=0.9)
        html = render_coaching_objectives({"coaching_objectives": [obj]})
        assert "90%" in html

    def test_renders_multiple_objectives(self):
        objs = [
            _make_objective(description="Objective A"),
            LearningObjective(
                objective_id="obj-002",
                feature_type=FeatureType.TECHNICAL_SKILL,
                description="Objective B",
                priority=ObjectivePriority.MODERATE,
                confidence=0.6,
                supporting_observation_types=(),
                detected_at_question_index=2,
                candidate_identity_id="cand-001",
            ),
        ]
        html = render_coaching_objectives({"coaching_objectives": objs})
        assert "Objective A" in html
        assert "Objective B" in html

    def test_section_header_present(self):
        obj = _make_objective()
        html = render_coaching_objectives({"coaching_objectives": [obj]})
        assert "Coaching Objectives" in html


class TestRenderStudyRecommendations:

    def test_empty_recommendations_returns_empty_string(self):
        assert render_study_recommendations({"study_recommendations": []}) == ""

    def test_missing_key_returns_empty_string(self):
        assert render_study_recommendations({}) == ""

    def test_renders_topic(self):
        rec = _make_recommendation()
        html = render_study_recommendations({"study_recommendations": [rec]})
        assert "System Design Exercises" in html

    def test_renders_rationale(self):
        rec = _make_recommendation()
        html = render_study_recommendations({"study_recommendations": [rec]})
        assert "Directly addresses the identified reasoning gap." in html

    def test_renders_resource_type(self):
        rec = _make_recommendation()
        html = render_study_recommendations({"study_recommendations": [rec]})
        assert "Exercise" in html

    def test_renders_duration(self):
        rec = _make_recommendation()
        html = render_study_recommendations({"study_recommendations": [rec]})
        assert "4h" in html

    def test_section_header_present(self):
        rec = _make_recommendation()
        html = render_study_recommendations({"study_recommendations": [rec]})
        assert "Study Recommendations" in html
