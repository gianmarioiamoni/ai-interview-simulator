# tests/ui/views/report/test_study_recommendations_dto_path.py
# EPIC-V13-05 Phase 2 — study recommendations production path is FinalReportDTO-only.

from app.ui.dto.final_report_dto import FinalReportDTO, StudyRecommendationDTO
from app.ui.views.report.report_view_model_builder import ReportViewModelBuilder
from app.ui.views.report.sections.study_recommendations_section import (
    render_study_recommendations,
)
from domain.contracts.coaching.coaching_builder import CoachingBuilder
from domain.contracts.coaching.learning_objective import LearningObjective, ObjectivePriority
from domain.contracts.coaching.study_recommendation import ResourceType, StudyRecommendation
from domain.contracts.feature.feature_type import FeatureType
from domain.contracts.observation.observation_type import ObservationType
from tests.domain.contracts.report.conftest import make_report
from tests.domain.contracts.session_history.conftest import CANDIDATE_ID, SESSION_ID


def _make_populated_coaching_snapshot():
    objective = LearningObjective(
        objective_id="obj-1",
        feature_type=FeatureType.REASONING,
        description="Strengthen algorithmic reasoning",
        priority=ObjectivePriority.HIGH,
        confidence=0.9,
        supporting_observation_types=(ObservationType.REASONING_DEPTH_LOW,),
        detected_at_question_index=0,
        candidate_identity_id=CANDIDATE_ID,
    )
    recommendation = StudyRecommendation(
        recommendation_id="rec-1",
        objective_id=objective.objective_id,
        resource_type=ResourceType.EXERCISE,
        topic="Hash maps",
        rationale="Addresses lookup complexity gaps",
        estimated_duration_hours=2.0,
    )
    return CoachingBuilder.build(
        objectives=(objective,),
        actions=(),
        recommendations=(recommendation,),
        session_id=SESSION_ID,
        question_index=0,
    )


def _dto_with_recommendations() -> FinalReportDTO:
    report = make_report().model_copy(
        update={"coaching_snapshot": _make_populated_coaching_snapshot()}
    )
    return FinalReportDTO.from_report(report)


class TestStudyRecommendationsDtoProductionPath:

    def test_vm_reads_study_recommendations_from_dto(self):
        dto = _dto_with_recommendations()
        assert len(dto.study_recommendations) == 1

        vm = ReportViewModelBuilder().build(dto)

        assert len(vm["study_recommendations"]) == 1
        rec = vm["study_recommendations"][0]
        assert isinstance(rec, StudyRecommendationDTO)
        assert rec.topic == "Hash maps"
        assert rec.recommendation_id == dto.study_recommendations[0].recommendation_id

    def test_vm_empty_list_when_dto_recommendations_empty(self):
        dto = FinalReportDTO.from_report(make_report())
        assert dto.study_recommendations == []

        vm = ReportViewModelBuilder().build(dto)

        assert vm["study_recommendations"] == []

    def test_vm_does_not_read_domain_coaching_snapshot_fallback(self):
        """SR-02: empty DTO list must not fall through to coaching_snapshot."""
        domain_report = make_report().model_copy(
            update={"coaching_snapshot": _make_populated_coaching_snapshot()}
        )
        dto = FinalReportDTO.from_report(make_report())
        assert dto.study_recommendations == []
        assert len(domain_report.coaching_snapshot.collection.recommendations) == 1

        # Production path input is DTO; empty DTO must stay empty even if a domain
        # Report with recommendations exists elsewhere (no dual-read).
        vm = ReportViewModelBuilder().build(dto)
        assert vm["study_recommendations"] == []

    def test_section_renders_dto_recommendations(self):
        dto = _dto_with_recommendations()
        vm = ReportViewModelBuilder().build(dto)
        html = render_study_recommendations(vm)

        assert "Study Recommendations" in html
        assert "Hash maps" in html
        assert "Addresses lookup complexity gaps" in html
        assert "Exercise" in html
        assert "2h" in html

    def test_section_empty_when_dto_recommendations_empty(self):
        dto = FinalReportDTO.from_report(make_report())
        vm = ReportViewModelBuilder().build(dto)
        assert render_study_recommendations(vm) == ""

    def test_from_report_remains_sole_factory(self):
        assert hasattr(FinalReportDTO, "from_report")
        assert not hasattr(FinalReportDTO, "from_components")
