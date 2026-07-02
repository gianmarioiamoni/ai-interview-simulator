# tests/domain/contracts/coaching/conftest.py
import pytest

from domain.contracts.coaching.coaching_action import ActionCategory, CoachingAction
from domain.contracts.coaching.coaching_collection import CoachingCollection
from domain.contracts.coaching.learning_objective import LearningObjective, ObjectivePriority
from domain.contracts.coaching.study_recommendation import ResourceType, StudyRecommendation
from domain.contracts.feature.feature_type import FeatureType
from domain.contracts.observation.observation_type import ObservationType


@pytest.fixture()
def objective_reasoning() -> LearningObjective:
    return LearningObjective(
        objective_id="obj-reasoning-1",
        feature_type=FeatureType.REASONING,
        description="Candidate shows shallow causal analysis",
        priority=ObjectivePriority.HIGH,
        confidence=0.75,
        supporting_observation_types=(ObservationType.REASONING_DEPTH_LOW,),
        detected_at_question_index=2,
        candidate_identity_id="cand-1",
    )


@pytest.fixture()
def objective_technical() -> LearningObjective:
    return LearningObjective(
        objective_id="obj-technical-1",
        feature_type=FeatureType.TECHNICAL_SKILL,
        description="Gap in data-structure selection",
        priority=ObjectivePriority.CRITICAL,
        confidence=0.9,
        supporting_observation_types=(ObservationType.TECHNICAL_GAP,),
        detected_at_question_index=3,
        candidate_identity_id="cand-1",
    )


@pytest.fixture()
def action_for_reasoning(objective_reasoning: LearningObjective) -> CoachingAction:
    return CoachingAction.for_objective(
        objective=objective_reasoning,
        action_id="act-1",
        category=ActionCategory.DEEP_DIVE,
        description="Work through 5 system-design trade-off exercises",
        effort_estimate_hours=3.0,
        is_immediate=True,
        tags=frozenset({"system-design", "trade-offs"}),
    )


@pytest.fixture()
def action_for_technical(objective_technical: LearningObjective) -> CoachingAction:
    return CoachingAction.for_objective(
        objective=objective_technical,
        action_id="act-2",
        category=ActionCategory.PRACTICE,
        description="Solve 10 data-structure problems on LeetCode",
        effort_estimate_hours=5.0,
        is_immediate=False,
    )


@pytest.fixture()
def recommendation(objective_reasoning: LearningObjective) -> StudyRecommendation:
    return StudyRecommendation.for_objective(
        objective=objective_reasoning,
        recommendation_id="rec-1",
        resource_type=ResourceType.CONCEPT_REVIEW,
        topic="Causal reasoning in distributed systems",
        rationale="Directly addresses shallow analysis pattern",
        estimated_duration_hours=2.0,
        tags=frozenset({"distributed-systems"}),
    )


@pytest.fixture()
def full_collection(
    objective_reasoning: LearningObjective,
    objective_technical: LearningObjective,
    action_for_reasoning: CoachingAction,
    action_for_technical: CoachingAction,
    recommendation: StudyRecommendation,
) -> CoachingCollection:
    return CoachingCollection.from_parts(
        objectives=[objective_reasoning, objective_technical],
        actions=[action_for_reasoning, action_for_technical],
        recommendations=[recommendation],
    )
