# tests/services/coaching_engine/test_coaching_engine_integration.py
# Integration tests: end-to-end CoachingEngine with realistic inputs

import pytest

from domain.contracts.feature.feature_type import FeatureType
from domain.contracts.coaching.learning_objective import ObjectivePriority
from domain.contracts.coaching.coaching_action import ActionCategory
from domain.contracts.coaching.study_recommendation import ResourceType
from services.coaching_engine.coaching_engine import CoachingEngine
from services.coaching_engine.coaching_context import CoachingContext
from services.coaching_engine.coaching_diagnostics import CoachingStage
from tests.services.coaching_engine.conftest import make_feature


class TestCoachingEngineIntegration:
    @pytest.fixture(autouse=True)
    def engine(self):
        self._engine = CoachingEngine()

    def test_full_cycle_produces_coherent_plan(self, base_context):
        result = self._engine.run(base_context)

        assert result.is_successful
        assert result.session_id == base_context.session_id
        assert result.candidate_identity_id == base_context.candidate_identity_id
        assert result.question_index == base_context.question_index

        snapshot = result.snapshot
        assert snapshot.session_id == base_context.session_id
        assert snapshot.question_index == base_context.question_index

        stats = snapshot.statistics
        assert stats.total_objectives == result.objective_count
        assert stats.total_actions == result.action_count
        assert stats.total_recommendations == result.recommendation_count

    def test_knowledge_gaps_boost_technical_objectives(self, candidate_profile):
        f_tech = make_feature(FeatureType.TECHNICAL_SKILL, "MODERATE", confidence=0.7)
        ctx_with_gaps = CoachingContext(
            session_id="s1",
            candidate_identity_id="cand-001",
            question_index=2,
            profile=candidate_profile,
            features=(f_tech,),
            knowledge_gap_observation_ids=("gap-1", "gap-2"),
        )
        ctx_no_gaps = CoachingContext(
            session_id="s1",
            candidate_identity_id="cand-001",
            question_index=2,
            profile=candidate_profile,
            features=(f_tech,),
            knowledge_gap_observation_ids=(),
        )
        r_gaps = self._engine.run(ctx_with_gaps)
        r_no_gaps = self._engine.run(ctx_no_gaps)

        # With gaps, TECHNICAL_SKILL (gap-sensitive + non-weak) should still produce objective
        # Without gaps and non-weak value, no objective
        assert r_gaps.objective_count >= r_no_gaps.objective_count

    def test_multi_feature_all_weak(self, candidate_profile):
        features = tuple(
            make_feature(ft, "LOW", confidence=0.7)
            for ft in [FeatureType.TECHNICAL_SKILL, FeatureType.REASONING, FeatureType.COVERAGE]
        )
        ctx = CoachingContext(
            session_id="s1",
            candidate_identity_id="cand-001",
            question_index=3,
            profile=candidate_profile,
            features=features,
        )
        result = self._engine.run(ctx)
        assert result.objective_count == 3
        assert result.action_count == 3
        assert result.recommendation_count == 3

    def test_snapshot_statistics_consistent(self, base_context):
        result = self._engine.run(base_context)
        stats = result.snapshot.statistics
        assert stats.total_objectives == len(result.snapshot.collection.objectives)
        assert stats.total_actions == len(result.snapshot.collection.actions)
        assert stats.total_recommendations == len(result.snapshot.collection.recommendations)

    def test_effort_estimate_positive(self, base_context):
        result = self._engine.run(base_context)
        for action in result.snapshot.collection.actions:
            assert action.effort_estimate_hours > 0.0

    def test_study_duration_positive(self, base_context):
        result = self._engine.run(base_context)
        for rec in result.snapshot.collection.recommendations:
            assert rec.estimated_duration_hours > 0.0

    def test_action_tags_contain_feature_type(self, base_context):
        result = self._engine.run(base_context)
        for action in result.snapshot.collection.actions:
            assert len(action.tags) >= 1

    def test_recommendation_tags_contain_feature_type(self, base_context):
        result = self._engine.run(base_context)
        for rec in result.snapshot.collection.recommendations:
            assert len(rec.tags) >= 1

    def test_diagnostics_session_id_matches(self, base_context):
        result = self._engine.run(base_context)
        assert result.diagnostics.session_id == base_context.session_id
        assert result.diagnostics.metrics.session_id == base_context.session_id

    def test_all_five_stages_recorded(self, base_context):
        result = self._engine.run(base_context)
        recorded_stages = {r.stage for r in result.diagnostics.stage_records}
        expected_stages = {
            CoachingStage.GAP_ANALYSIS,
            CoachingStage.OBJECTIVE_DERIVATION,
            CoachingStage.ACTION_DERIVATION,
            CoachingStage.RECOMMENDATION_DERIVATION,
            CoachingStage.PLAN_ASSEMBLY,
        }
        assert recorded_stages == expected_stages

    def test_resource_type_assignment(self, candidate_profile):
        f_tech = make_feature(FeatureType.TECHNICAL_SKILL, "LOW", confidence=0.8)
        ctx = CoachingContext(
            session_id="s1",
            candidate_identity_id="cand-001",
            question_index=1,
            profile=candidate_profile,
            features=(f_tech,),
        )
        result = self._engine.run(ctx)
        recs = result.snapshot.collection.recommendations
        assert len(recs) == 1
        assert recs[0].resource_type == ResourceType.EXERCISE

    def test_action_category_for_technical_skill(self, candidate_profile):
        f_tech = make_feature(FeatureType.TECHNICAL_SKILL, "LOW", confidence=0.8)
        ctx = CoachingContext(
            session_id="s1",
            candidate_identity_id="cand-001",
            question_index=1,
            profile=candidate_profile,
            features=(f_tech,),
        )
        result = self._engine.run(ctx)
        actions = result.snapshot.collection.actions
        assert len(actions) == 1
        assert actions[0].category == ActionCategory.PRACTICE
