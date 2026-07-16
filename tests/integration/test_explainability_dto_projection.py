# tests/integration/test_explainability_dto_projection.py
# EPIC-06 M2 / C5 — Report fixtures → FinalReportDTO explainability completeness.
# IT-01 · IT-02 · IT-03 (DTO plane; no UI/export)

from __future__ import annotations

import pytest

from app.ui.dto.final_report_dto import (
    CoachingActionDTO,
    FeatureIdentityDTO,
    FinalReportDTO,
    NarrativeInsightDTO,
)
from domain.contracts.coaching.coaching_action import ActionCategory, CoachingAction
from domain.contracts.coaching.coaching_builder import CoachingBuilder
from tests.domain.contracts.report.conftest import (
    make_report,
    make_report_with_explainability,
)
from tests.domain.contracts.session_history.conftest import SESSION_ID


class TestExplainabilityDtoProjectionIntegration:
    """C5 — Report → from_report → DTO explainability completeness."""

    def test_it01_insights_carry_source_feature_id_and_is_traceable(self) -> None:
        report = make_report_with_explainability()
        assert len(report.narrative.insights) >= 1

        dto = FinalReportDTO.from_report(report)

        assert len(dto.narrative_insights) == len(report.narrative.insights)
        for mapped, domain in zip(
            dto.narrative_insights, report.narrative.insights, strict=True
        ):
            assert isinstance(mapped, NarrativeInsightDTO)
            assert isinstance(mapped.source_feature_id, FeatureIdentityDTO)
            assert mapped.source_feature_id.feature_type_id
            assert mapped.source_feature_id.semantic_category
            assert (
                mapped.source_feature_id.feature_type_id
                == domain.source_feature_id.feature_type_id
            )
            assert (
                mapped.source_feature_id.semantic_category
                == domain.source_feature_id.semantic_category
            )
            assert mapped.is_traceable is True
            assert mapped.is_traceable is domain.is_traceable

    def test_it02_actions_carry_required_origin_fields(self) -> None:
        report = make_report_with_explainability()
        collection = report.coaching_snapshot.collection
        assert len(collection.actions) >= 1
        assert len(collection.objectives) >= 1

        dto = FinalReportDTO.from_report(report)

        assert len(dto.coaching_actions) == len(collection.actions)
        for mapped, domain in zip(
            dto.coaching_actions, collection.actions, strict=True
        ):
            objective = collection.objective_by_id(domain.objective_id)
            assert objective is not None
            assert isinstance(mapped, CoachingActionDTO)
            assert mapped.action_id == domain.action_id
            assert mapped.objective_id == domain.objective_id
            assert mapped.origin_feature_type == objective.feature_type.value
            assert mapped.origin_supporting_observation_types == [
                t.value for t in objective.supporting_observation_types
            ]
            assert mapped.origin_objective_description == objective.description
            assert mapped.origin_feature_type
            assert mapped.origin_supporting_observation_types is not None
            assert mapped.origin_objective_description

    def test_it03_missing_objective_fail_fast(self) -> None:
        orphan = CoachingAction(
            action_id="act-orphan-it03",
            objective_id="obj-does-not-exist",
            category=ActionCategory.PRACTICE,
            description="Action without resolvable objective",
            effort_estimate_hours=1.5,
            is_immediate=False,
        )
        report = make_report().model_copy(
            update={
                "coaching_snapshot": CoachingBuilder.build(
                    objectives=(),
                    actions=(orphan,),
                    recommendations=(),
                    session_id=SESSION_ID,
                    question_index=0,
                )
            }
        )

        with pytest.raises(ValueError, match="objective_id"):
            FinalReportDTO.from_report(report)

    def test_dto_explainability_completeness_for_baseline_fixture(self) -> None:
        """Report fixture with insights + actions → complete explainability DTO."""
        report = make_report_with_explainability()
        dto = FinalReportDTO.from_report(report)

        assert len(dto.narrative_insights) >= 1
        assert len(dto.coaching_actions) >= 1

        for insight in dto.narrative_insights:
            assert insight.source_feature_id.feature_type_id
            assert insight.source_feature_id.semantic_category
            assert insight.is_traceable is True

        for action in dto.coaching_actions:
            assert action.origin_feature_type
            assert isinstance(action.origin_supporting_observation_types, list)
            assert action.origin_objective_description

    def test_empty_explainability_collections_remain_complete(self) -> None:
        report = make_report()
        dto = FinalReportDTO.from_report(report)
        assert dto.narrative_insights == []
        assert dto.coaching_actions == []
