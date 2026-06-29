# tests/services/test_signal_enrichment_step.py

import pytest

from domain.contracts.shared.performance_dimension_type import PerformanceDimensionType
from infrastructure.config.evaluation import ENRICHMENT_ALPHA
from services.interview_evaluation.steps.signal_enrichment_step import SignalEnrichmentStep

TD = PerformanceDimensionType.TECHNICAL_DEPTH
PS = PerformanceDimensionType.PROBLEM_SOLVING
SD = PerformanceDimensionType.SYSTEM_DESIGN
CM = PerformanceDimensionType.COMMUNICATION


def _step() -> SignalEnrichmentStep:
    return SignalEnrichmentStep()


def _expected_enriched(base: float, signal: float) -> float:
    return round(base * (1 - ENRICHMENT_ALPHA) + signal * 100 * ENRICHMENT_ALPHA, 1)


# ------------------------------------------------------------------
# Case 1 — execution_dims = {} → all scores pass through unchanged
# ------------------------------------------------------------------

class TestNoExecutionDims:

    def test_all_dims_unchanged_when_execution_dims_empty(self):
        base = {TD: 80.0, PS: 75.0, SD: 70.0, CM: 65.0}
        signals = {}
        step = _step()

        result = step.enrich_scores(base, signals, execution_dims=set())

        assert result[TD] == 80.0
        assert result[PS] == 75.0
        assert result[SD] == 70.0
        assert result[CM] == 65.0

    def test_perfect_scores_unchanged_when_no_execution_dims(self):
        base = {TD: 100.0, PS: 100.0}
        result = _step().enrich_scores(base, {}, execution_dims=set())
        assert result[TD] == 100.0
        assert result[PS] == 100.0

    def test_zero_scores_unchanged_when_no_execution_dims(self):
        base = {PS: 0.0}
        result = _step().enrich_scores(base, {}, execution_dims=set())
        assert result[PS] == 0.0


# ------------------------------------------------------------------
# Case 2 — dim in execution_dims → existing alpha formula applies
# ------------------------------------------------------------------

class TestExecutionDimEnriched:

    def test_alpha_formula_applied_when_dim_in_execution_dims(self):
        base = {PS: 80.0}
        signals = {"problem_solving": 0.6}
        result = _step().enrich_scores(base, signals, execution_dims={"problem_solving"})
        assert result[PS] == _expected_enriched(80.0, 0.6)

    def test_zero_signal_in_execution_dim_applies_penalty(self):
        base = {PS: 80.0}
        signals = {"problem_solving": 0.0}
        result = _step().enrich_scores(base, signals, execution_dims={"problem_solving"})
        assert result[PS] == _expected_enriched(80.0, 0.0)
        assert result[PS] < 80.0

    def test_perfect_signal_boosts_score(self):
        base = {PS: 80.0}
        signals = {"problem_solving": 1.0}
        result = _step().enrich_scores(base, signals, execution_dims={"problem_solving"})
        assert result[PS] == _expected_enriched(80.0, 1.0)
        assert result[PS] > 80.0

    def test_formula_byte_identical_to_original_for_execution_dims(self):
        base = {TD: 75.0, PS: 88.0}
        signals = {"technical_depth": 0.40, "problem_solving": 0.60}
        exec_dims = {"technical_depth", "problem_solving"}

        step = _step()
        result = step.enrich_scores(base, signals, execution_dims=exec_dims)

        assert result[TD] == _expected_enriched(75.0, 0.40)
        assert result[PS] == _expected_enriched(88.0, 0.60)


# ------------------------------------------------------------------
# Case 3 — Mixed interview: written dims pass through, exec dims enriched
# ------------------------------------------------------------------

class TestMixedInterview:

    def test_written_dims_pass_through_exec_dims_enriched(self):
        base = {TD: 85.0, PS: 88.0, SD: 82.0, CM: 80.0}
        signals = {"problem_solving": 0.60, "technical_depth": 0.40}
        exec_dims = {"problem_solving", "technical_depth"}

        result = _step().enrich_scores(base, signals, execution_dims=exec_dims)

        # Execution dims: enriched
        assert result[TD] == _expected_enriched(85.0, 0.40)
        assert result[PS] == _expected_enriched(88.0, 0.60)
        # Written-only dims: unchanged
        assert result[SD] == 82.0
        assert result[CM] == 80.0

    def test_written_dim_not_penalised_by_zero_signal(self):
        base = {CM: 70.0}
        signals = {}
        result = _step().enrich_scores(base, signals, execution_dims=set())
        assert result[CM] == 70.0  # no penalty applied


# ------------------------------------------------------------------
# Case 4 — Coding-heavy: behaviour identical to previous implementation
# ------------------------------------------------------------------

class TestCodingHeavy:

    def test_coding_heavy_result_matches_original_formula(self):
        base = {PS: 90.0}
        signals = {"problem_solving": 1.0}
        exec_dims = {"problem_solving"}

        result_b = _step().enrich_scores(base, signals, execution_dims=exec_dims)
        result_original = _step().enrich_scores(base, signals, execution_dims=None)

        assert result_b[PS] == result_original[PS]

    def test_all_dims_enriched_when_execution_dims_is_none(self):
        base = {PS: 90.0, TD: 80.0}
        signals = {"problem_solving": 1.0, "technical_depth": 0.5}

        result_b = _step().enrich_scores(base, signals, execution_dims={"problem_solving", "technical_depth"})
        result_orig = _step().enrich_scores(base, signals, execution_dims=None)

        assert result_b[PS] == result_orig[PS]
        assert result_b[TD] == result_orig[TD]


# ------------------------------------------------------------------
# Backward compat — execution_dims=None preserves original behaviour
# ------------------------------------------------------------------

class TestBackwardCompat:

    def test_none_execution_dims_applies_enrichment_to_all(self):
        base = {TD: 80.0}
        signals = {}
        result = _step().enrich_scores(base, signals, execution_dims=None)
        assert result[TD] == _expected_enriched(80.0, 0.0)
        assert result[TD] < 80.0
