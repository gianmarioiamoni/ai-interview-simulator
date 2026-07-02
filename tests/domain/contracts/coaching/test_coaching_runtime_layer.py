# tests/domain/contracts/coaching/test_coaching_runtime_layer.py
# EPIC-04 Sprint 7B — Coaching Runtime Foundation

import pytest
from pydantic import ValidationError

from domain.contracts.coaching.coaching_action import ActionCategory, CoachingAction
from domain.contracts.coaching.coaching_builder import CoachingBuilder
from domain.contracts.coaching.coaching_collection import CoachingCollection
from domain.contracts.coaching.coaching_statistics import CoachingStatistics
from domain.contracts.coaching.future_action_backlog import FutureActionBacklog
from domain.contracts.coaching.learning_objective import LearningObjective, ObjectivePriority
from domain.contracts.coaching.study_recommendation import ResourceType, StudyRecommendation
from domain.contracts.feature.feature_type import FeatureType
from domain.contracts.observation.observation_type import ObservationType


# ===========================================================================
# LearningObjective
# ===========================================================================


class TestLearningObjective:
    def test_immutable(self, objective_reasoning: LearningObjective) -> None:
        with pytest.raises(ValidationError):
            objective_reasoning.priority = ObjectivePriority.LOW  # type: ignore[misc]

    def test_confidence_bounds(self) -> None:
        with pytest.raises(Exception):
            LearningObjective(
                objective_id="x",
                feature_type=FeatureType.REASONING,
                description="d",
                priority=ObjectivePriority.LOW,
                confidence=1.5,
                detected_at_question_index=0,
                candidate_identity_id="c",
            )

    def test_fields(self, objective_reasoning: LearningObjective) -> None:
        assert objective_reasoning.feature_type == FeatureType.REASONING
        assert objective_reasoning.priority == ObjectivePriority.HIGH
        assert 0.0 <= objective_reasoning.confidence <= 1.0
        assert ObservationType.REASONING_DEPTH_LOW in objective_reasoning.supporting_observation_types


# ===========================================================================
# CoachingAction
# ===========================================================================


class TestCoachingAction:
    def test_for_objective_links_ids(
        self,
        action_for_reasoning: CoachingAction,
        objective_reasoning: LearningObjective,
    ) -> None:
        assert action_for_reasoning.objective_id == objective_reasoning.objective_id

    def test_immutable(self, action_for_reasoning: CoachingAction) -> None:
        with pytest.raises(ValidationError):
            action_for_reasoning.effort_estimate_hours = 99.0  # type: ignore[misc]

    def test_effort_must_be_positive(self, objective_reasoning: LearningObjective) -> None:
        with pytest.raises(Exception):
            CoachingAction.for_objective(
                objective=objective_reasoning,
                action_id="bad",
                category=ActionCategory.REVIEW,
                description="d",
                effort_estimate_hours=0.0,
            )

    def test_tags_default_empty(self, objective_reasoning: LearningObjective) -> None:
        action = CoachingAction.for_objective(
            objective=objective_reasoning,
            action_id="a",
            category=ActionCategory.PRACTICE,
            description="d",
            effort_estimate_hours=1.0,
        )
        assert action.tags == frozenset()


# ===========================================================================
# StudyRecommendation
# ===========================================================================


class TestStudyRecommendation:
    def test_for_objective_links_ids(
        self,
        recommendation: StudyRecommendation,
        objective_reasoning: LearningObjective,
    ) -> None:
        assert recommendation.objective_id == objective_reasoning.objective_id

    def test_immutable(self, recommendation: StudyRecommendation) -> None:
        with pytest.raises(ValidationError):
            recommendation.topic = "other"  # type: ignore[misc]

    def test_duration_must_be_positive(self, objective_reasoning: LearningObjective) -> None:
        with pytest.raises(Exception):
            StudyRecommendation.for_objective(
                objective=objective_reasoning,
                recommendation_id="r",
                resource_type=ResourceType.READING,
                topic="t",
                rationale="r",
                estimated_duration_hours=0.0,
            )


# ===========================================================================
# FutureActionBacklog
# ===========================================================================


class TestFutureActionBacklog:
    def test_empty(self) -> None:
        backlog = FutureActionBacklog(
            session_id="s1",
            candidate_identity_id="c1",
            created_at_question_index=0,
        )
        assert backlog.is_empty
        assert backlog.size == 0

    def test_with_action_returns_new(
        self,
        action_for_reasoning: CoachingAction,
        action_for_technical: CoachingAction,
    ) -> None:
        backlog = FutureActionBacklog(
            session_id="s1",
            candidate_identity_id="c1",
            created_at_question_index=0,
        )
        backlog2 = backlog.with_action(action_for_reasoning)
        assert backlog.size == 0  # original unchanged
        assert backlog2.size == 1

    def test_immediate_actions(
        self,
        action_for_reasoning: CoachingAction,
        action_for_technical: CoachingAction,
    ) -> None:
        backlog = FutureActionBacklog(
            actions=(action_for_reasoning, action_for_technical),
            session_id="s1",
            candidate_identity_id="c1",
            created_at_question_index=0,
        )
        immediate = backlog.immediate_actions()
        deferred = backlog.deferred_actions()
        assert len(immediate) == 1
        assert len(deferred) == 1
        assert immediate[0].action_id == action_for_reasoning.action_id

    def test_by_objective(
        self,
        action_for_reasoning: CoachingAction,
        action_for_technical: CoachingAction,
        objective_reasoning: LearningObjective,
    ) -> None:
        backlog = FutureActionBacklog(
            actions=(action_for_reasoning, action_for_technical),
            session_id="s1",
            candidate_identity_id="c1",
            created_at_question_index=0,
        )
        result = backlog.by_objective(objective_reasoning.objective_id)
        assert len(result) == 1
        assert result[0].action_id == action_for_reasoning.action_id

    def test_immutable(self, action_for_reasoning: CoachingAction) -> None:
        backlog = FutureActionBacklog(
            actions=(action_for_reasoning,),
            session_id="s1",
            candidate_identity_id="c1",
            created_at_question_index=0,
        )
        with pytest.raises(ValidationError):
            backlog.session_id = "other"  # type: ignore[misc]


# ===========================================================================
# CoachingCollection
# ===========================================================================


class TestCoachingCollection:
    def test_empty(self) -> None:
        c = CoachingCollection.empty()
        assert c.is_empty
        assert c.objective_count == 0

    def test_counts(self, full_collection: CoachingCollection) -> None:
        assert full_collection.objective_count == 2
        assert full_collection.action_count == 2
        assert full_collection.recommendation_count == 1

    def test_objectives_by_priority(
        self, full_collection: CoachingCollection
    ) -> None:
        critical = full_collection.objectives_by_priority(ObjectivePriority.CRITICAL)
        assert len(critical) == 1
        assert critical[0].feature_type == FeatureType.TECHNICAL_SKILL

    def test_objectives_by_feature_type(
        self, full_collection: CoachingCollection
    ) -> None:
        reasoning = full_collection.objectives_by_feature_type(FeatureType.REASONING)
        assert len(reasoning) == 1

    def test_actions_for_objective(
        self,
        full_collection: CoachingCollection,
        objective_reasoning: LearningObjective,
    ) -> None:
        acts = full_collection.actions_for_objective(objective_reasoning.objective_id)
        assert len(acts) == 1

    def test_immediate_actions(self, full_collection: CoachingCollection) -> None:
        assert len(full_collection.immediate_actions()) == 1

    def test_group_by_priority(self, full_collection: CoachingCollection) -> None:
        groups = full_collection.group_objectives_by_priority()
        assert ObjectivePriority.CRITICAL in groups
        assert ObjectivePriority.HIGH in groups

    def test_filter_objectives(self, full_collection: CoachingCollection) -> None:
        filtered = full_collection.filter_objectives(lambda o: o.confidence > 0.8)
        assert filtered.objective_count == 1

    def test_recommendations_for_objective(
        self,
        full_collection: CoachingCollection,
        objective_reasoning: LearningObjective,
    ) -> None:
        recs = full_collection.recommendations_for_objective(objective_reasoning.objective_id)
        assert len(recs) == 1

    def test_objective_by_id_missing(self, full_collection: CoachingCollection) -> None:
        assert full_collection.objective_by_id("nonexistent") is None


# ===========================================================================
# CoachingStatistics
# ===========================================================================


class TestCoachingStatistics:
    def test_empty_collection(self) -> None:
        stats = CoachingStatistics.from_collection(CoachingCollection.empty())
        assert stats.is_empty
        assert stats.total_objectives == 0
        assert stats.mean_objective_confidence == 0.0

    def test_from_collection(self, full_collection: CoachingCollection) -> None:
        stats = CoachingStatistics.from_collection(full_collection)
        assert stats.total_objectives == 2
        assert stats.total_actions == 2
        assert stats.total_recommendations == 1
        assert stats.critical_objective_count == 1
        assert stats.high_objective_count == 1
        assert stats.immediate_action_count == 1
        assert stats.distinct_feature_type_count == 2
        assert 0.0 <= stats.mean_objective_confidence <= 1.0

    def test_priority_distribution_keys(self, full_collection: CoachingCollection) -> None:
        stats = CoachingStatistics.from_collection(full_collection)
        dist = stats.priority_distribution
        assert "critical" in dist
        assert "high" in dist
        assert dist["critical"] == 1

    def test_immutable(self, full_collection: CoachingCollection) -> None:
        stats = CoachingStatistics.from_collection(full_collection)
        with pytest.raises(ValidationError):
            stats.total_objectives = 99  # type: ignore[misc]


# ===========================================================================
# CoachingBuilder
# ===========================================================================


class TestCoachingBuilder:
    def test_empty_snapshot(self) -> None:
        snap = CoachingBuilder.empty(session_id="s1", question_index=0)
        assert snap.session_id == "s1"
        assert snap.question_index == 0
        assert snap.statistics.is_empty

    def test_build_snapshot(
        self,
        objective_reasoning: LearningObjective,
        action_for_reasoning: CoachingAction,
        recommendation: StudyRecommendation,
    ) -> None:
        snap = CoachingBuilder.build(
            objectives=[objective_reasoning],
            actions=[action_for_reasoning],
            recommendations=[recommendation],
            session_id="s2",
            question_index=3,
        )
        assert snap.question_index == 3
        assert snap.statistics.total_objectives == 1
        assert snap.collection.objective_count == 1

    def test_repr(self) -> None:
        snap = CoachingBuilder.empty(session_id="sess-x", question_index=5)
        assert "sess-x" in repr(snap)
        assert "5" in repr(snap)

    def test_determinism(
        self,
        objective_reasoning: LearningObjective,
        action_for_reasoning: CoachingAction,
        recommendation: StudyRecommendation,
    ) -> None:
        kwargs = dict(
            objectives=[objective_reasoning],
            actions=[action_for_reasoning],
            recommendations=[recommendation],
            session_id="s3",
            question_index=1,
        )
        snap1 = CoachingBuilder.build(**kwargs)
        snap2 = CoachingBuilder.build(**kwargs)
        assert snap1.statistics.total_objectives == snap2.statistics.total_objectives
        assert snap1.statistics.mean_objective_confidence == snap2.statistics.mean_objective_confidence


# ===========================================================================
# Architecture / ADR-025 invariants
# ===========================================================================


class TestArchitectureInvariants:
    def test_no_candidateprofile_import(self) -> None:
        import domain.contracts.coaching.learning_objective as m
        src = m.__file__
        with open(src) as f:
            assert "CandidateProfile" not in f.read()

    def test_no_narrative_import(self) -> None:
        import domain.contracts.coaching.coaching_builder as m
        src = m.__file__
        with open(src) as f:
            content = f.read()
            assert "NarrativeEngine" not in content
            assert "generate_narrative" not in content

    def test_no_replay_references(self) -> None:
        import domain.contracts.coaching.coaching_collection as m
        src = m.__file__
        with open(src) as f:
            assert "replay" not in f.read().lower()

    def test_coaching_collection_state_isolation(
        self, full_collection: CoachingCollection
    ) -> None:
        filtered = full_collection.filter_objectives(lambda o: o.priority == ObjectivePriority.HIGH)
        assert full_collection.objective_count == 2
        assert filtered.objective_count == 1
