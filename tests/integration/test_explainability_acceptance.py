# tests/integration/test_explainability_acceptance.py
# EPIC-06 M4 / C10 — IT-06 end-to-end fixture acceptance (R-07).
# Epic-level behavioral coverage: every insight/action surfaces required fields
# on DTO → UI HTML → export HTML/JSON paths (R-01, R-02, R-07).

from __future__ import annotations

import json
import os
import tempfile

from app.ui.dto.final_report_dto import FinalReportDTO
from app.ui.views.report.report_renderer import ReportRenderer
from app.ui.views.report.report_view_model_builder import ReportViewModelBuilder
from app.ui.views.report_view import build_report_markdown
from domain.contracts.coaching.coaching_action import ActionCategory, CoachingAction
from domain.contracts.coaching.coaching_builder import CoachingBuilder
from domain.contracts.coaching.learning_objective import (
    LearningObjective,
    ObjectivePriority,
)
from domain.contracts.feature.feature_identity import FeatureIdentity
from domain.contracts.feature.feature_type import FeatureType
from domain.contracts.narrative.narrative_insight_type import NarrativeInsightType
from domain.contracts.observation.observation_type import ObservationType
from domain.contracts.report.report_builder import ReportBuilder
from services.report_export_service import ReportExportService
from tests.domain.contracts.narrative.conftest import (
    REASONING_ID,
    TECHNICAL_ID,
    make_insight,
    make_narrative,
)
from tests.domain.contracts.report.conftest import (
    CANDIDATE_ID,
    FIXED_REPORT_DT,
    REPORT_ID,
    SESSION_ID,
    make_report,
    make_report_with_explainability,
    make_session_history,
)

COMMUNICATION_ID = FeatureIdentity.for_type(FeatureType.COMMUNICATION)


def _make_acceptance_report():
    """Multi-insight / multi-action acceptance fixture for R-07."""
    insights = [
        make_insight(
            insight_type=NarrativeInsightType.STRENGTH_SIGNAL,
            prose="Acceptance insight A — strong causal reasoning.",
            source_feature_id=REASONING_ID,
            confidence=0.91,
        ),
        make_insight(
            insight_type=NarrativeInsightType.RISK_SIGNAL,
            prose="Acceptance insight B — technical coverage risk.",
            source_feature_id=TECHNICAL_ID,
            confidence=0.77,
        ),
        make_insight(
            insight_type=NarrativeInsightType.GROWTH_OPPORTUNITY,
            prose="Acceptance insight C — communication growth.",
            source_feature_id=COMMUNICATION_ID,
            confidence=0.68,
        ),
    ]
    objectives = (
        LearningObjective(
            objective_id="obj-accept-1",
            feature_type=FeatureType.REASONING,
            description="Strengthen causal reasoning depth",
            priority=ObjectivePriority.HIGH,
            confidence=0.88,
            supporting_observation_types=(ObservationType.REASONING_DEPTH_LOW,),
            detected_at_question_index=0,
            candidate_identity_id=CANDIDATE_ID,
        ),
        LearningObjective(
            objective_id="obj-accept-2",
            feature_type=FeatureType.COMMUNICATION,
            description="Improve structured verbal clarity",
            priority=ObjectivePriority.MODERATE,
            confidence=0.74,
            supporting_observation_types=(
                ObservationType.COMMUNICATION_WEAK,
                ObservationType.COMMUNICATION_GAP,
            ),
            detected_at_question_index=1,
            candidate_identity_id=CANDIDATE_ID,
        ),
    )
    actions = (
        CoachingAction.for_objective(
            objective=objectives[0],
            action_id="act-accept-1",
            category=ActionCategory.DEEP_DIVE,
            description="Complete five causal-reasoning trade-off drills",
            effort_estimate_hours=3.0,
            is_immediate=True,
        ),
        CoachingAction.for_objective(
            objective=objectives[1],
            action_id="act-accept-2",
            category=ActionCategory.PRACTICE,
            description="Record two structured explanation walkthroughs",
            effort_estimate_hours=2.0,
            is_immediate=False,
        ),
    )
    history = make_session_history(
        session_id=SESSION_ID,
        candidate_id=CANDIDATE_ID,
    )
    return (
        ReportBuilder()
        .with_session_history(history)
        .with_narrative(make_narrative(insights=insights))
        .with_coaching_snapshot(
            CoachingBuilder.build(
                objectives=objectives,
                actions=actions,
                recommendations=(),
                session_id=SESSION_ID,
                question_index=0,
            )
        )
        .with_report_id(REPORT_ID)
        .with_created_at(FIXED_REPORT_DT)
        .build()
    )


def _assert_insight_surfaces_in_html(html: str, insight) -> None:
    feature_label = insight.source_feature_id.feature_type_id.replace("_", " ").title()
    category_label = insight.source_feature_id.semantic_category.replace(
        "_", " "
    ).title()
    assert insight.prose in html
    assert "Evidence:" in html
    assert feature_label in html
    assert category_label in html
    assert "Traceable" in html


def _assert_action_surfaces_in_html(html: str, action) -> None:
    origin_feature_label = action.origin_feature_type.replace("_", " ").title()
    assert action.description in html
    assert "Origin:" in html
    assert "Supporting observations:" in html
    assert "Objective:" in html
    assert action.origin_objective_description in html
    assert origin_feature_label in html
    for obs in action.origin_supporting_observation_types:
        assert obs.replace("_", " ").title() in html


class TestExplainabilityAcceptance:
    """C10 — IT-06 epic acceptance: every insight/action surfaces required fields."""

    def test_it06_baseline_fixture_surfaces_every_item_in_ui_and_export(self) -> None:
        report = make_report_with_explainability()
        dto = FinalReportDTO.from_report(report)
        assert len(dto.narrative_insights) >= 1
        assert len(dto.coaching_actions) >= 1

        ui_html = build_report_markdown(dto)
        export_html = ReportExportService().build_export_html(dto)
        renderer_html = ReportRenderer().render(ReportViewModelBuilder().build(dto))

        for html in (ui_html, export_html, renderer_html):
            for insight in dto.narrative_insights:
                _assert_insight_surfaces_in_html(html, insight)
            for action in dto.coaching_actions:
                _assert_action_surfaces_in_html(html, action)

        assert ui_html in export_html

    def test_it06_multi_item_acceptance_fixture_surfaces_every_item(self) -> None:
        report = _make_acceptance_report()
        dto = FinalReportDTO.from_report(report)

        assert len(dto.narrative_insights) == 3
        assert len(dto.coaching_actions) == 2

        for insight in dto.narrative_insights:
            assert insight.source_feature_id.feature_type_id
            assert insight.source_feature_id.semantic_category
            assert insight.is_traceable is True

        for action in dto.coaching_actions:
            assert action.origin_feature_type
            assert isinstance(action.origin_supporting_observation_types, list)
            assert action.origin_objective_description

        ui_html = build_report_markdown(dto)
        export_html = ReportExportService().build_export_html(dto)

        for html in (ui_html, export_html):
            for insight in dto.narrative_insights:
                _assert_insight_surfaces_in_html(html, insight)
            for action in dto.coaching_actions:
                _assert_action_surfaces_in_html(html, action)

        assert ui_html in export_html

    def test_it06_export_json_surfaces_every_required_field(self) -> None:
        dto = FinalReportDTO.from_report(_make_acceptance_report())
        service = ReportExportService()

        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "report.json")
            service.export_json(dto, path)
            with open(path, encoding="utf-8") as handle:
                data = json.load(handle)

        assert len(data["narrative_insights"]) == len(dto.narrative_insights)
        for raw, mapped in zip(
            data["narrative_insights"], dto.narrative_insights, strict=True
        ):
            assert raw["source_feature_id"]["feature_type_id"] == (
                mapped.source_feature_id.feature_type_id
            )
            assert raw["source_feature_id"]["semantic_category"] == (
                mapped.source_feature_id.semantic_category
            )
            assert raw["is_traceable"] is True

        assert len(data["coaching_actions"]) == len(dto.coaching_actions)
        for raw, mapped in zip(
            data["coaching_actions"], dto.coaching_actions, strict=True
        ):
            assert raw["origin_feature_type"] == mapped.origin_feature_type
            assert (
                raw["origin_supporting_observation_types"]
                == mapped.origin_supporting_observation_types
            )
            assert (
                raw["origin_objective_description"]
                == mapped.origin_objective_description
            )

    def test_it06_empty_collections_remain_valid(self) -> None:
        dto = FinalReportDTO.from_report(make_report())
        assert dto.narrative_insights == []
        assert dto.coaching_actions == []

        ui_html = build_report_markdown(dto)
        export_html = ReportExportService().build_export_html(dto)

        assert "Evidence:" not in ui_html
        assert "Evidence:" not in export_html
        assert "Coaching Actions" not in ui_html
        assert "Coaching Actions" not in export_html
        assert ui_html in export_html

    def test_from_report_remains_sole_factory_on_acceptance_path(self) -> None:
        dto = FinalReportDTO.from_report(_make_acceptance_report())
        assert hasattr(FinalReportDTO, "from_report")
        assert not hasattr(FinalReportDTO, "from_components")
        assert isinstance(dto, FinalReportDTO)
