# tests/ui/mappers/test_final_report_dto.py
# EPIC-V13-05 Phase 9/1 — FinalReportDTO.from_report() architectural tests.
# EPIC-06 C1 — NarrativeInsightDTO evidence mapping unit tests.

import inspect

from app.ui.dto.final_report_dto import (
    FeatureIdentityDTO,
    FinalReportDTO,
    NarrativeInsightDTO,
    StudyRecommendationDTO,
)
from domain.contracts.coaching.coaching_builder import CoachingBuilder
from domain.contracts.coaching.learning_objective import LearningObjective, ObjectivePriority
from domain.contracts.coaching.study_recommendation import ResourceType, StudyRecommendation
from domain.contracts.feature.feature_type import FeatureType
from domain.contracts.observation.observation_type import ObservationType
from tests.domain.contracts.report.conftest import (
    make_report,
    make_report_with_explainability,
)
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


class TestFinalReportDTOFromReport:

    def test_from_components_does_not_exist(self):
        """R-05: from_components must not exist after Phase 9."""
        assert not hasattr(FinalReportDTO, "from_components")

    def test_from_report_exists(self):
        assert hasattr(FinalReportDTO, "from_report")
        assert callable(FinalReportDTO.from_report)

    def test_from_report_returns_final_report_dto(self):
        report = make_report()
        dto = FinalReportDTO.from_report(report)
        assert isinstance(dto, FinalReportDTO)

    def test_overall_score_from_scoring(self):
        report = make_report()
        dto = FinalReportDTO.from_report(report)
        assert dto.overall_score == report.scoring.overall_score

    def test_hiring_probability_from_scoring(self):
        report = make_report()
        dto = FinalReportDTO.from_report(report)
        assert dto.hiring_probability == report.scoring.hiring_probability

    def test_executive_summary_from_scoring_narrative(self):
        report = make_report()
        dto = FinalReportDTO.from_report(report)
        assert dto.executive_summary == report.scoring_narrative.executive_summary

    def test_gating_triggered_from_scoring(self):
        report = make_report()
        dto = FinalReportDTO.from_report(report)
        assert dto.gating_triggered == report.scoring.gating_triggered

    def test_percentile_rank_from_scoring(self):
        report = make_report()
        dto = FinalReportDTO.from_report(report)
        assert dto.percentile_rank == report.scoring.percentile_rank

    def test_dimension_signals_from_scoring(self):
        report = make_report()
        dto = FinalReportDTO.from_report(report)
        assert dto.dimension_signals == report.scoring.dimension_signals

    def test_weighted_breakdown_from_scoring(self):
        report = make_report()
        dto = FinalReportDTO.from_report(report)
        assert dto.weighted_breakdown == report.scoring.weighted_breakdown

    def test_dimension_scores_mapped_from_scoring_dimensions(self):
        report = make_report()
        dto = FinalReportDTO.from_report(report)
        assert len(dto.dimension_scores) == len(report.scoring.scoring_dimensions)

    def test_went_well_from_scoring_narrative(self):
        report = make_report()
        dto = FinalReportDTO.from_report(report)
        assert dto.went_well == list(report.scoring_narrative.went_well)

    def test_improvement_suggestions_from_scoring_narrative(self):
        report = make_report()
        dto = FinalReportDTO.from_report(report)
        assert dto.improvement_suggestions == list(report.scoring_narrative.improvement_suggestions)

    def test_seniority_level_from_report(self):
        report = make_report()
        dto = FinalReportDTO.from_report(report)
        assert dto.seniority_level == report.seniority

    def test_context_profile_from_report(self):
        report = make_report()
        dto = FinalReportDTO.from_report(report)
        assert dto.context_profile is report.context_profile

    def test_confidence_from_scoring(self):
        report = make_report()
        dto = FinalReportDTO.from_report(report)
        assert dto.confidence == report.scoring.confidence

    def test_total_tokens_zero_when_no_generation_metadata(self):
        report = make_report()
        assert report.generation_metadata is None
        dto = FinalReportDTO.from_report(report)
        assert dto.total_tokens_used == 0

    def test_question_assessments_count_matches_report(self):
        report = make_report()
        dto = FinalReportDTO.from_report(report)
        assert len(dto.question_assessments) == len(report.question_assessments)

    def test_raw_score_fallback_to_zero_when_none(self):
        report = make_report()
        dto = FinalReportDTO.from_report(report)
        expected = report.scoring.raw_score if report.scoring.raw_score is not None else 0.0
        assert dto.raw_score == expected

    def test_adjusted_score_fallback_to_overall_when_none(self):
        report = make_report()
        dto = FinalReportDTO.from_report(report)
        expected = (
            report.scoring.adjusted_score
            if report.scoring.adjusted_score is not None
            else report.scoring.overall_score
        )
        assert dto.adjusted_score == expected

    def test_no_interview_state_attributes_accessed(self):
        """Structural: from_report signature takes only Report, no InterviewState."""
        sig = inspect.signature(FinalReportDTO.from_report)
        params = list(sig.parameters.keys())
        assert "state" not in params
        assert "report" in params

    def test_session_id_equals_report_session_id(self):
        """I-C02-03 / DM-FR-03: session_id mapped from Report.session_id only."""
        report = make_report(session_id="session-phase1-001")
        dto = FinalReportDTO.from_report(report)
        assert dto.session_id == report.session_id
        assert dto.session_id == "session-phase1-001"

    def test_study_recommendations_empty_when_domain_empty(self):
        """SR-03: empty list only when domain collection is empty."""
        report = make_report()
        assert report.coaching_snapshot.collection.recommendations == ()
        dto = FinalReportDTO.from_report(report)
        assert dto.study_recommendations == []

    def test_study_recommendations_mapped_from_coaching_snapshot(self):
        """PC-05 / SR-01: recommendations mapped from coaching_snapshot.collection."""
        report = make_report().model_copy(
            update={"coaching_snapshot": _make_populated_coaching_snapshot()}
        )
        dto = FinalReportDTO.from_report(report)
        assert len(dto.study_recommendations) == 1
        rec = dto.study_recommendations[0]
        assert isinstance(rec, StudyRecommendationDTO)
        domain_rec = report.coaching_snapshot.collection.recommendations[0]
        assert rec.recommendation_id == domain_rec.recommendation_id
        assert rec.objective_id == domain_rec.objective_id
        assert rec.resource_type == domain_rec.resource_type.value
        assert rec.topic == domain_rec.topic
        assert rec.rationale == domain_rec.rationale
        assert rec.estimated_duration_hours == domain_rec.estimated_duration_hours


class TestNarrativeInsightEvidenceMapping:
    """EPIC-06 C1 — NarrativeInsightDTO source_feature_id + is_traceable."""

    def test_empty_insights_remain_empty(self):
        report = make_report()
        assert report.narrative.insights == ()
        dto = FinalReportDTO.from_report(report)
        assert dto.narrative_insights == []

    def test_maps_source_feature_id_and_is_traceable(self):
        report = make_report_with_explainability()
        assert len(report.narrative.insights) >= 1
        dto = FinalReportDTO.from_report(report)
        assert len(dto.narrative_insights) == len(report.narrative.insights)
        for mapped, domain in zip(
            dto.narrative_insights, report.narrative.insights, strict=True
        ):
            assert isinstance(mapped, NarrativeInsightDTO)
            assert isinstance(mapped.source_feature_id, FeatureIdentityDTO)
            assert (
                mapped.source_feature_id.feature_type_id
                == domain.source_feature_id.feature_type_id
            )
            assert (
                mapped.source_feature_id.semantic_category
                == domain.source_feature_id.semantic_category
            )
            assert (
                mapped.source_feature_id.schema_version
                == domain.source_feature_id.schema_version
            )
            assert mapped.is_traceable is True
            assert mapped.is_traceable is domain.is_traceable
            assert mapped.prose == domain.prose
            assert mapped.confidence == domain.confidence
            assert mapped.insight_type == domain.insight_type.value

    def test_explainability_baseline_fixture_has_actions_and_objectives(self):
        """M0 fixture inventory: insights + actions + matching objectives."""
        report = make_report_with_explainability()
        assert len(report.narrative.insights) >= 1
        collection = report.coaching_snapshot.collection
        assert len(collection.objectives) >= 1
        assert len(collection.actions) >= 1
        objective_ids = {o.objective_id for o in collection.objectives}
        for action in collection.actions:
            assert action.objective_id in objective_ids
