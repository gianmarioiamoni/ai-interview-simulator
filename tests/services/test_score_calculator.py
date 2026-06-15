# tests/services/test_score_calculator.py

import pytest
from domain.contracts.feedback.quality import Quality
from services.score_calculator import ScoreCalculator, compute_quality


# ---------------------------------------------------------
# compute_quality() — shared helper
# ---------------------------------------------------------


def test_compute_quality_all_pass():
    _, q = compute_quality(passed=5, total=5)
    assert q == Quality.OPTIMAL


def test_compute_quality_80_percent_boundary():
    # 4/5 = 80% → exactly at CORRECT threshold
    _, q = compute_quality(passed=4, total=5)
    assert q == Quality.CORRECT


def test_compute_quality_79_percent_is_partial():
    # 3/4 = 75% → below CORRECT (80%), above PARTIAL (50%)
    _, q = compute_quality(passed=3, total=4)
    assert q == Quality.PARTIAL


def test_compute_quality_zero_passed():
    _, q = compute_quality(passed=0, total=5)
    assert q == Quality.INCORRECT


def test_compute_quality_no_tests():
    _, q = compute_quality(passed=None, total=None)
    assert q == Quality.INCORRECT


def test_compute_quality_total_zero():
    _, q = compute_quality(passed=0, total=0)
    assert q == Quality.INCORRECT


# ---------------------------------------------------------
# ScoreCalculator delegates to compute_quality
# ---------------------------------------------------------


def test_score_calculator_matches_compute_quality():
    calc = ScoreCalculator()
    for passed, total in [(0, 5), (4, 5), (5, 5), (2, 5), (3, 4)]:
        score_c, q_c = calc.compute(passed=passed, total=total)
        score_f, q_f = compute_quality(passed=passed, total=total)
        assert score_c == score_f
        assert q_c == q_f
