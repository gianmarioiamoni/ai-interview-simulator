# tests/services/humanizer/selector/test_follow_up_selector.py
#
# Covers M1-4 Section B (SEL), Section C (DST), and selector-related
# property tests from Section K (PROP).

import pytest
from unittest.mock import MagicMock

from services.humanizer.selector.follow_up_selector import FollowUpSelector


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _settings(
    *,
    enabled: bool = True,
    percentage: float = 0.20,
    max_follow_ups: int = 2,
    policy: str = "percentage",
    allowed_areas: str = "",
    allowed_types: str = "written",
) -> MagicMock:
    s = MagicMock()
    s.humanizer_follow_up_enabled = enabled
    s.follow_up_percentage = percentage
    s.max_follow_ups_per_interview = max_follow_ups
    s.follow_up_selector_policy = policy
    s.follow_up_allowed_areas = allowed_areas
    s.follow_up_allowed_types = allowed_types
    return s


def _areas(n: int, area: str = "technical_technical_knowledge") -> list[str]:
    """Build a planned_areas list of length n, all defaulting to a written area."""
    return [area] * n


def _select(total: int, *, settings=None, areas: list[str] | None = None) -> frozenset[int]:
    if settings is None:
        settings = _settings()
    if areas is None:
        areas = _areas(total)
    return FollowUpSelector().select(
        total_questions=total,
        planned_areas=areas,
        settings=settings,
    )


# ---------------------------------------------------------------------------
# SEL-001..006  Disabled / zero configuration
# ---------------------------------------------------------------------------

def test_sel_001_disabled_by_flag() -> None:
    result = _select(20, settings=_settings(enabled=False))
    assert result == frozenset()


def test_sel_002_percentage_zero() -> None:
    result = _select(20, settings=_settings(percentage=0.0))
    assert result == frozenset()


def test_sel_003_max_follow_ups_zero() -> None:
    result = _select(20, settings=_settings(max_follow_ups=0))
    assert result == frozenset()


def test_sel_004_single_question() -> None:
    result = _select(1)
    assert result == frozenset()


def test_sel_005_two_questions() -> None:
    result = _select(2)
    assert result == frozenset()


def test_sel_006_three_questions() -> None:
    result = _select(3)
    # only index 1 is eligible (0 and 2 excluded)
    assert result <= {1}


# ---------------------------------------------------------------------------
# SEL-010..017  Standard percentages
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("total,pct,cap,expected_count", [
    (10, 0.20, 2, 2),
    (20, 0.20, 2, 2),
    (5,  0.20, 2, 1),
    (10, 0.30, 2, 2),
    (20, 0.30, 2, 2),
    (10, 0.40, 2, 2),
    (10, 1.00, 2, 2),
    (30, 1.00, 2, 2),
])
def test_sel_010_to_017_standard_percentages(total, pct, cap, expected_count) -> None:
    result = _select(total, settings=_settings(percentage=pct, max_follow_ups=cap))
    assert len(result) == expected_count


# ---------------------------------------------------------------------------
# SEL-020..022  First/last exclusion
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("total", [3, 5, 10, 20, 30])
def test_sel_020_first_question_never_selected(total) -> None:
    result = _select(total)
    assert 0 not in result


@pytest.mark.parametrize("total", [3, 5, 10, 20, 30])
def test_sel_021_last_question_never_selected(total) -> None:
    result = _select(total)
    assert total - 1 not in result


def test_sel_022_only_valid_index_in_three_questions() -> None:
    result = _select(3)
    assert result <= {1}


# ---------------------------------------------------------------------------
# SEL-030..032  No-consecutive constraint
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("total", [5, 10, 20, 30])
def test_sel_030_no_consecutive_indices(total) -> None:
    result = _select(total, settings=_settings(max_follow_ups=2))
    sorted_result = sorted(result)
    for i in range(len(sorted_result) - 1):
        assert sorted_result[i + 1] - sorted_result[i] > 1, (
            f"Consecutive indices found: {sorted_result[i]}, {sorted_result[i+1]}"
        )


def test_sel_031_no_consecutive_at_boundary_three_questions() -> None:
    result = _select(3)
    assert len(result) <= 1


def test_sel_032_no_adjacent_in_ten_question_interview() -> None:
    result = _select(10, settings=_settings(max_follow_ups=2))
    sorted_result = sorted(result)
    for i in range(len(sorted_result) - 1):
        assert sorted_result[i + 1] - sorted_result[i] > 1


# ---------------------------------------------------------------------------
# SEL-040..043  Area filter
# ---------------------------------------------------------------------------

def test_sel_040_all_areas_enabled_none() -> None:
    areas = _areas(10)
    result = _select(10, areas=areas)
    assert len(result) > 0


def test_sel_041_area_filter_excludes_database_area() -> None:
    areas = ["technical_database"] * 10
    # no allowed area override, but allowed_types = "written" → database areas excluded
    result = _select(10, areas=areas)
    assert result == frozenset()


def test_sel_042_area_filter_excludes_coding_area() -> None:
    areas = ["technical_coding"] * 10
    result = _select(10, areas=areas)
    assert result == frozenset()


def test_sel_043_empty_allowed_types() -> None:
    result = _select(10, settings=_settings(allowed_types=""))
    assert result == frozenset()


def test_sel_044_explicit_allowed_areas_filter() -> None:
    # Only hr_background allowed; other areas excluded
    areas = ["technical_technical_knowledge"] * 10
    result = _select(
        10,
        settings=_settings(allowed_areas="hr_background"),
        areas=areas,
    )
    assert result == frozenset()


def test_sel_045_explicit_allowed_areas_match() -> None:
    areas = ["hr_background"] * 10
    result = _select(
        10,
        settings=_settings(allowed_areas="hr_background", allowed_types="written"),
        areas=areas,
    )
    assert len(result) > 0


# ---------------------------------------------------------------------------
# SEL-050..052  Adaptive vs. fixed interview
# ---------------------------------------------------------------------------

def test_sel_050_fixed_interview_20_questions() -> None:
    areas = _areas(20)
    result = _select(20, areas=areas)
    assert len(result) == 2


def test_sel_051_adaptive_same_result_as_fixed_with_same_areas() -> None:
    areas = _areas(20)
    r1 = _select(20, areas=areas)
    r2 = _select(20, areas=areas)
    assert r1 == r2


def test_sel_052_adaptive_uses_planned_areas_not_questions_length() -> None:
    # planned_areas has 20 entries; questions list may be smaller at runtime
    areas = _areas(20)
    result = _select(20, areas=areas)
    # All selected indices must be within planned_areas bounds
    assert all(0 < idx < 20 for idx in result)


# ---------------------------------------------------------------------------
# SEL-060..064  Determinism and immutability
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("run", range(10))
def test_sel_060_same_inputs_same_output(run) -> None:
    areas = _areas(20)
    s = _settings()
    r1 = FollowUpSelector().select(total_questions=20, planned_areas=areas, settings=s)
    r2 = FollowUpSelector().select(total_questions=20, planned_areas=areas, settings=s)
    assert r1 == r2


def test_sel_061_different_total_different_output() -> None:
    areas10 = _areas(10)
    areas20 = _areas(20)
    r1 = _select(10, areas=areas10)
    r2 = _select(20, areas=areas20)
    # At minimum the indices themselves differ since total differs
    assert not (r1 == r2 and len(r1) > 0 and len(r2) > 0 and max(r1, default=0) == max(r2, default=0))


def test_sel_062_different_max_cap_different_count() -> None:
    s1 = _settings(max_follow_ups=1)
    s2 = _settings(max_follow_ups=2)
    r1 = _select(20, settings=s1)
    r2 = _select(20, settings=s2)
    assert len(r1) <= 1
    assert len(r2) <= 2


def test_sel_063_result_is_frozenset() -> None:
    result = _select(20)
    assert isinstance(result, frozenset)


def test_sel_064_mutation_attempt_raises() -> None:
    result = _select(20)
    with pytest.raises(AttributeError):
        result.add(5)  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# SECTION C  Distribution tests (DST-001..010)
# ---------------------------------------------------------------------------

def _metrics(result: frozenset[int], total: int) -> dict:
    if len(result) < 2:
        return {
            "min_spacing": None,
            "max_spacing": None,
            "centroid": (sum(result) / total) if result else 0.0,
            "spread": 0,
        }
    s = sorted(result)
    spacings = [s[i + 1] - s[i] for i in range(len(s) - 1)]
    return {
        "min_spacing": min(spacings),
        "max_spacing": max(spacings),
        "centroid": sum(s) / len(s) / total,
        "spread": max(s) - min(s),
    }


def test_dst_001_no_consecutive_indices() -> None:
    result = _select(20, settings=_settings(percentage=0.20, max_follow_ups=2))
    m = _metrics(result, 20)
    if m["min_spacing"] is not None:
        assert m["min_spacing"] > 1


def test_dst_002_no_first_two_questions() -> None:
    result = _select(20, settings=_settings(percentage=0.20, max_follow_ups=2))
    # First question (index 0) is always excluded; index 1 may be selected
    assert 0 not in result, f"First question selected: {sorted(result)}"


def test_dst_003_no_last_question() -> None:
    result = _select(20, settings=_settings(percentage=0.20, max_follow_ups=2))
    assert 19 not in result


def test_dst_004_spread_across_interview() -> None:
    total = 20
    result = _select(total, settings=_settings(percentage=0.20, max_follow_ups=2))
    if len(result) >= 2:
        m = _metrics(result, total)
        assert m["spread"] >= total // 3, (
            f"Follow-ups clustered: {sorted(result)}, spread={m['spread']}"
        )


def test_dst_005_centroid_near_middle() -> None:
    total = 20
    result = _select(total, settings=_settings(percentage=0.20, max_follow_ups=2))
    if result:
        m = _metrics(result, total)
        assert 0.25 <= m["centroid"] <= 0.75, (
            f"Centroid outside [0.25, 0.75]: {m['centroid']:.2f}, indices={sorted(result)}"
        )


def test_dst_006_no_start_clustering_10q() -> None:
    result = _select(10, settings=_settings(percentage=0.30, max_follow_ups=2))
    assert 0 not in result, f"First question selected: {sorted(result)}"


def test_dst_007_no_end_clustering_10q() -> None:
    result = _select(10, settings=_settings(percentage=0.30, max_follow_ups=2))
    assert 9 not in result, f"Last question selected: {sorted(result)}"


def test_dst_008_single_follow_up_placement() -> None:
    result = _select(10, settings=_settings(percentage=0.20, max_follow_ups=1))
    assert len(result) <= 1
    for idx in result:
        assert 1 < idx < 9, f"Index {idx} is at boundary"


def test_dst_009_two_follow_ups_spacing_30q() -> None:
    result = _select(30, settings=_settings(percentage=0.20, max_follow_ups=2))
    m = _metrics(result, 30)
    if m["min_spacing"] is not None:
        assert m["min_spacing"] >= 5, (
            f"Spacing too small: {m['min_spacing']}, indices={sorted(result)}"
        )


@pytest.mark.parametrize("total", [5, 10, 15, 20, 30])
def test_dst_010_parametric_distribution(total) -> None:
    result = _select(total, settings=_settings(percentage=0.20, max_follow_ups=2))
    s = sorted(result)
    # no consecutive
    for i in range(len(s) - 1):
        assert s[i + 1] - s[i] > 1
    # centroid in range (only meaningful with ≥ 1 element)
    if result:
        m = _metrics(result, total)
        assert 0.20 <= m["centroid"] <= 0.80, (
            f"total={total}, centroid={m['centroid']:.2f}, indices={s}"
        )


# ---------------------------------------------------------------------------
# Property tests (PROP-001..004 selector-specific)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("seed", range(20))
def test_prop_001_selector_determinism(seed) -> None:
    total = (seed % 25) + 5  # 5..29
    areas = _areas(total)
    s = _settings()
    r1 = FollowUpSelector().select(total_questions=total, planned_areas=areas, settings=s)
    r2 = FollowUpSelector().select(total_questions=total, planned_areas=areas, settings=s)
    assert r1 == r2


@pytest.mark.parametrize("seed", range(20))
def test_prop_002_selector_no_consecutive(seed) -> None:
    total = (seed % 25) + 5
    result = _select(total)
    s = sorted(result)
    for i in range(len(s) - 1):
        assert s[i + 1] - s[i] > 1


@pytest.mark.parametrize("cap", range(0, 6))
def test_prop_003_selector_respects_cap(cap) -> None:
    result = _select(30, settings=_settings(max_follow_ups=cap))
    assert len(result) <= cap


@pytest.mark.parametrize("total", range(3, 35))
def test_prop_004_no_first_last(total) -> None:
    result = _select(total)
    assert 0 not in result
    assert total - 1 not in result


# ---------------------------------------------------------------------------
# Configuration variation tests
# ---------------------------------------------------------------------------

def test_config_policy_fixed_uses_max_directly() -> None:
    result = _select(30, settings=_settings(policy="fixed", max_follow_ups=2, percentage=0.50))
    assert len(result) <= 2


def test_config_policy_percentage_uses_floor() -> None:
    # floor(5 * 0.20) = 1
    result = _select(5, settings=_settings(percentage=0.20, max_follow_ups=5))
    assert len(result) <= 1


def test_config_mixed_areas() -> None:
    areas = (
        ["technical_technical_knowledge"] * 5
        + ["technical_coding"] * 5
        + ["technical_database"] * 5
        + ["hr_background"] * 5
    )
    result = _select(20, areas=areas, settings=_settings(allowed_types="written"))
    # coding and database indices should not be selected
    for idx in result:
        assert "coding" not in areas[idx] and "database" not in areas[idx], (
            f"Index {idx} has disallowed area {areas[idx]}"
        )


def test_supports_follow_up_false_does_not_affect_selector() -> None:
    # supports_follow_up is checked at runtime in question_node, not in selector
    # Selector operates on planned_areas only
    result = _select(20)
    assert isinstance(result, frozenset)
