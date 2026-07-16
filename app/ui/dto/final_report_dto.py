# app/ui/dto/final_report_dto.py
# EPIC-V13-05 Phase 9/10 — FinalReportDTO sourced exclusively from Report v2.0.
# from_components deleted (R-05). from_report is the sole factory.
# Phase 10 adds NarrativeInsightDTO, CoachingObjectiveDTO optional fields.
# Phase 1 adds StudyRecommendationDTO, study_recommendations, session_id.
# EPIC-06 C1 — FeatureIdentityDTO + NarrativeInsightDTO evidence fields.
# EPIC-06 C2 — CoachingActionDTO + coaching_actions origin join.
# EPIC-06 C3 — PC-E05 projection completeness gate.

from dataclasses import dataclass
from typing import List, Dict, Optional, Sequence
from pydantic import BaseModel, Field

from app.ui.dto.dimension_score_dto import DimensionScoreDTO
from app.ui.dto.question_assessment_dto import QuestionAssessmentDTO

from app.ui.mappers.hire_decision_mapper import HireDecisionMapper
from app.ui.dto.builders.dimension_score_mapper import DimensionScoreMapper
from app.ui.dto.builders.question_assessment_mapper import QuestionAssessmentMapper

from domain.contracts.coaching.coaching_action import CoachingAction
from domain.contracts.coaching.coaching_collection import CoachingCollection
from domain.contracts.coaching.learning_objective import LearningObjective
from domain.contracts.feedback.confidence import Confidence
from domain.contracts.feature.feature_identity import FeatureIdentity
from domain.contracts.narrative.narrative_insight import NarrativeInsight
from domain.contracts.report.report import Report
from domain.contracts.user.role import RoleType
from domain.contracts.interview.interview_context_profile import InterviewContextProfile


@dataclass(frozen=True)
class FeatureIdentityDTO:
    """Presentation projection of FeatureIdentity (EPIC-06 Data Model §2.2)."""

    feature_type_id: str
    semantic_category: str
    schema_version: Optional[str] = None


@dataclass(frozen=True)
class NarrativeInsightDTO:
    """DTO for a single NarrativeInsight (EPIC-V13-05 Phase 10 + EPIC-06 C1)."""

    insight_type: str
    prose: str
    confidence: float
    source_feature_id: FeatureIdentityDTO
    is_traceable: bool


def _map_feature_identity(identity: FeatureIdentity) -> FeatureIdentityDTO:
    feature_type_id = identity.feature_type_id
    semantic_category = identity.semantic_category
    if not feature_type_id or not semantic_category:
        raise ValueError(
            "Projection contract violation (X-01): source_feature_id requires "
            "non-empty feature_type_id and semantic_category"
        )
    return FeatureIdentityDTO(
        feature_type_id=feature_type_id,
        semantic_category=semantic_category,
        schema_version=identity.schema_version,
    )


def _map_narrative_insight(insight: NarrativeInsight) -> NarrativeInsightDTO:
    if not insight.is_traceable:
        raise ValueError(
            "Projection contract violation (X-02): NarrativeInsight.is_traceable "
            "must be True"
        )
    return NarrativeInsightDTO(
        insight_type=(
            insight.insight_type.value
            if hasattr(insight.insight_type, "value")
            else str(insight.insight_type)
        ),
        prose=insight.prose,
        confidence=insight.confidence,
        source_feature_id=_map_feature_identity(insight.source_feature_id),
        is_traceable=insight.is_traceable,
    )


@dataclass(frozen=True)
class CoachingObjectiveDTO:
    """DTO for a single LearningObjective (EPIC-V13-05 Phase 10)."""
    objective_id: str
    description: str
    priority: str
    confidence: float
    feature_type: str


@dataclass(frozen=True)
class CoachingActionDTO:
    """DTO for a CoachingAction with resolved LearningObjective origin (EPIC-06 §3.3)."""

    action_id: str
    objective_id: str
    category: str
    description: str
    effort_estimate_hours: float
    is_immediate: bool
    origin_feature_type: str
    origin_supporting_observation_types: List[str]
    origin_objective_description: str


@dataclass(frozen=True)
class StudyRecommendationDTO:
    """DTO for a single StudyRecommendation (EPIC-V13-05 Phase 1 / PC-05)."""
    recommendation_id: str
    objective_id: str
    resource_type: str
    topic: str
    rationale: str
    estimated_duration_hours: float


def _map_coaching_action(
    action: CoachingAction,
    objective: LearningObjective,
) -> CoachingActionDTO:
    return CoachingActionDTO(
        action_id=action.action_id,
        objective_id=action.objective_id,
        category=(
            action.category.value
            if hasattr(action.category, "value")
            else str(action.category)
        ),
        description=action.description,
        effort_estimate_hours=action.effort_estimate_hours,
        is_immediate=action.is_immediate,
        origin_feature_type=(
            objective.feature_type.value
            if hasattr(objective.feature_type, "value")
            else str(objective.feature_type)
        ),
        origin_supporting_observation_types=[
            (
                obs_type.value
                if hasattr(obs_type, "value")
                else str(obs_type)
            )
            for obs_type in objective.supporting_observation_types
        ],
        origin_objective_description=objective.description,
    )


def _map_coaching_actions(collection: CoachingCollection) -> List[CoachingActionDTO]:
    mapped: List[CoachingActionDTO] = []
    for action in collection.actions:
        objective = collection.objective_by_id(action.objective_id)
        if objective is None:
            raise ValueError(
                "Snapshot integrity violation (X-03): CoachingAction "
                f"{action.action_id!r} objective_id {action.objective_id!r} "
                "does not resolve on the same coaching_snapshot"
            )
        mapped.append(_map_coaching_action(action, objective))
    return mapped


def _assert_explainability_projection_complete(
    insights: Sequence[NarrativeInsightDTO],
    actions: Sequence[CoachingActionDTO],
) -> None:
    """PC-E05 — fail-fast gate for required explainability fields on present items.

    Empty collections are valid (X-07 / EC-V-01 empty-set rule).
    """
    for insight in insights:
        identity = insight.source_feature_id
        if identity is None:
            raise ValueError(
                "Projection contract violation (X-01): NarrativeInsightDTO "
                "missing source_feature_id"
            )
        if not identity.feature_type_id or not identity.semantic_category:
            raise ValueError(
                "Projection contract violation (X-01): source_feature_id requires "
                "non-empty feature_type_id and semantic_category"
            )
        if insight.is_traceable is not True:
            raise ValueError(
                "Projection contract violation (X-02): NarrativeInsightDTO.is_traceable "
                "must be True"
            )

    for action in actions:
        if not action.origin_feature_type:
            raise ValueError(
                "Projection contract violation (X-04): CoachingActionDTO "
                f"{action.action_id!r} missing origin_feature_type"
            )
        if action.origin_supporting_observation_types is None:
            raise ValueError(
                "Projection contract violation (X-04): CoachingActionDTO "
                f"{action.action_id!r} missing origin_supporting_observation_types"
            )
        if not action.origin_objective_description:
            raise ValueError(
                "Projection contract violation (X-04): CoachingActionDTO "
                f"{action.action_id!r} missing origin_objective_description"
            )


def _safe_role_type(role_str: str) -> RoleType:
    try:
        return RoleType(role_str)
    except ValueError:
        return RoleType.OTHER


class FinalReportDTO(BaseModel):

    overall_score: float
    raw_score: float
    adjusted_score: float
    hiring_probability: float
    hire_decision: str
    decision_explanation: Dict[str, List[str]]
    dimension_signals: Dict[str, float]

    percentile_rank: float
    percentile_explanation: str

    executive_summary: str

    gating_triggered: bool
    gating_reason: Optional[str]

    weighted_breakdown: Dict[str, float]

    dimension_scores: List[DimensionScoreDTO]
    question_assessments: List[QuestionAssessmentDTO]

    improvement_suggestions: List[str]

    # Coaching sections (V1.0)
    went_well: List[str] = Field(default_factory=list)
    held_you_back: List[Dict] = Field(default_factory=list)
    knowledge_gaps: List[Dict] = Field(default_factory=list)
    next_strategy: List[Dict] = Field(default_factory=list)

    total_tokens_used: int

    confidence: Confidence

    role: RoleType

    seniority_level: str

    context_profile: InterviewContextProfile

    # Phase 10 — new optional sections (additive, default empty)
    narrative_insights: List[NarrativeInsightDTO] = Field(default_factory=list)
    coaching_objectives: List[CoachingObjectiveDTO] = Field(default_factory=list)

    # EPIC-06 C2 — coaching actions with resolved origin (may be empty)
    coaching_actions: List[CoachingActionDTO] = Field(default_factory=list)

    # Phase 1 — study recommendations + replay session identity (EPIC-05 Data Model §2.2)
    study_recommendations: List[StudyRecommendationDTO] = Field(default_factory=list)
    session_id: str

    @classmethod
    def from_report(cls, report: Report) -> "FinalReportDTO":
        """Build FinalReportDTO exclusively from Report v2.0 (ADR-033, R-05, EPIC-V13-05 Phase 9).

        No InterviewState reads. No SessionHistory reads.
        """
        scoring = report.scoring
        narrative = report.scoring_narrative

        dimension_scores = DimensionScoreMapper().map(scoring.scoring_dimensions)

        question_assessments = [
            QuestionAssessmentMapper.to_dto(r) for r in report.question_assessments
        ]

        total_tokens = (
            report.generation_metadata.total_tokens_used
            if report.generation_metadata is not None
            else 0
        )

        narrative_insights = [
            _map_narrative_insight(i) for i in report.narrative.insights
        ]

        collection = report.coaching_snapshot.collection

        coaching_objectives = [
            CoachingObjectiveDTO(
                objective_id=obj.objective_id,
                description=obj.description,
                priority=obj.priority.value if hasattr(obj.priority, "value") else str(obj.priority),
                confidence=obj.confidence,
                feature_type=obj.feature_type.value if hasattr(obj.feature_type, "value") else str(obj.feature_type),
            )
            for obj in collection.objectives
        ]

        coaching_actions = _map_coaching_actions(collection)

        _assert_explainability_projection_complete(
            narrative_insights, coaching_actions
        )

        study_recommendations = [
            StudyRecommendationDTO(
                recommendation_id=rec.recommendation_id,
                objective_id=rec.objective_id,
                resource_type=(
                    rec.resource_type.value
                    if hasattr(rec.resource_type, "value")
                    else str(rec.resource_type)
                ),
                topic=rec.topic,
                rationale=rec.rationale,
                estimated_duration_hours=rec.estimated_duration_hours,
            )
            for rec in collection.recommendations
        ]

        return cls(
            overall_score=scoring.overall_score,
            raw_score=scoring.raw_score or 0.0,
            adjusted_score=scoring.adjusted_score or scoring.overall_score,
            hiring_probability=scoring.hiring_probability,
            hire_decision=HireDecisionMapper.to_label(scoring.hire_decision),
            decision_explanation=scoring.decision_explanation,
            dimension_signals=scoring.dimension_signals,
            percentile_rank=scoring.percentile_rank,
            percentile_explanation=scoring.percentile_explanation,
            executive_summary=narrative.executive_summary,
            gating_triggered=scoring.gating_triggered,
            gating_reason=scoring.gating_reason,
            weighted_breakdown=scoring.weighted_breakdown,
            dimension_scores=dimension_scores,
            question_assessments=question_assessments,
            improvement_suggestions=list(narrative.improvement_suggestions),
            went_well=list(narrative.went_well),
            held_you_back=[item.to_dict() for item in narrative.held_you_back],
            knowledge_gaps=[item.to_dict() for item in narrative.knowledge_gaps],
            next_strategy=[item.to_dict() for item in narrative.next_strategy],
            total_tokens_used=total_tokens,
            confidence=scoring.confidence,
            role=_safe_role_type(report.role),
            seniority_level=report.seniority,
            context_profile=report.context_profile,
            narrative_insights=narrative_insights,
            coaching_objectives=coaching_objectives,
            coaching_actions=coaching_actions,
            study_recommendations=study_recommendations,
            session_id=report.session_id,
        )
