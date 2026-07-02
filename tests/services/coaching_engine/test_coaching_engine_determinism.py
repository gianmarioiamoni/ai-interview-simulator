# tests/services/coaching_engine/test_coaching_engine_determinism.py
# Determinism tests: same inputs → structurally equivalent outputs

import pytest

from domain.contracts.feature.feature_type import FeatureType
from domain.contracts.coaching.learning_objective import ObjectivePriority
from services.coaching_engine.coaching_engine import CoachingEngine
from services.coaching_engine.coaching_context import CoachingContext
from tests.services.coaching_engine.conftest import make_feature


class TestCoachingEngineDeterminism:
    @pytest.fixture(autouse=True)
    def engine(self):
        self._engine = CoachingEngine()

    def test_same_context_same_structure(self, base_context):
        r1 = self._engine.run(base_context)
        r2 = self._engine.run(base_context)
        assert r1.objective_count == r2.objective_count
        assert r1.action_count == r2.action_count
        assert r1.recommendation_count == r2.recommendation_count
        assert r1.is_successful == r2.is_successful

    def test_same_context_same_feature_types(self, base_context):
        r1 = self._engine.run(base_context)
        r2 = self._engine.run(base_context)
        ft1 = sorted(o.feature_type.value for o in r1.snapshot.collection.objectives)
        ft2 = sorted(o.feature_type.value for o in r2.snapshot.collection.objectives)
        assert ft1 == ft2

    def test_same_context_same_priorities(self, base_context):
        r1 = self._engine.run(base_context)
        r2 = self._engine.run(base_context)
        p1 = sorted(o.priority.value for o in r1.snapshot.collection.objectives)
        p2 = sorted(o.priority.value for o in r2.snapshot.collection.objectives)
        assert p1 == p2

    def test_empty_context_always_empty(self, empty_context):
        for _ in range(3):
            result = self._engine.run(empty_context)
            assert result.objective_count == 0
            assert result.is_successful

    def test_different_feature_value_different_output(self, candidate_profile):
        f_low = make_feature(FeatureType.TECHNICAL_SKILL, "LOW", confidence=0.8)
        f_high = make_feature(FeatureType.TECHNICAL_SKILL, "HIGH", confidence=0.8)

        ctx_low = CoachingContext(
            session_id="s1",
            candidate_identity_id="cand-001",
            question_index=1,
            profile=candidate_profile,
            features=(f_low,),
        )
        ctx_high = CoachingContext(
            session_id="s1",
            candidate_identity_id="cand-001",
            question_index=1,
            profile=candidate_profile,
            features=(f_high,),
        )
        r_low = self._engine.run(ctx_low)
        r_high = self._engine.run(ctx_high)
        # LOW produces objective; HIGH does not (not weak, not gap-sensitive without gaps)
        assert r_low.objective_count > r_high.objective_count

    def test_metrics_total_includes_stage_durations(self, base_context):
        result = self._engine.run(base_context)
        m = result.diagnostics.metrics
        stage_sum = (
            m.gap_analysis_duration_ms
            + m.objective_derivation_duration_ms
            + m.action_derivation_duration_ms
            + m.recommendation_derivation_duration_ms
            + m.plan_assembly_duration_ms
        )
        assert m.total_duration_ms >= stage_sum * 0.9
