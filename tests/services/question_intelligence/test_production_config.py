# tests/services/question_intelligence/test_production_config.py
"""
Phase 7E-G — Production Configuration Freeze tests.

Validates that the Question Intelligence production configuration
matches the Phase 7E-F validated specification exactly.
"""

import math
import pytest

from app.settings.constants import (
    DEFAULT_INTERVIEW_LENGTH,
    DEFAULT_FOLLOWUP_RATE,
    MAX_FOLLOW_UPS_PER_INTERVIEW,
    TECHNICAL_AREA_WEIGHTS,
    TECHNICAL_AREA_CORPUS_FRACTION,
    TECHNICAL_AREA_QUESTION_COUNT,
)
from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.interview.interview_type import InterviewType
from services.humanizer.humanizer_policy_engine import HumanizerPolicyEngine
from services.question_intelligence.corpus_quota_resolver import resolve_corpus_quota


# ── Constants ─────────────────────────────────────────────────────────────────

class TestDefaultInterviewLength:
    def test_default_interview_length_is_20(self):
        assert DEFAULT_INTERVIEW_LENGTH == 20

    def test_orchestrator_source_references_constant(self):
        """The orchestrator module must import DEFAULT_INTERVIEW_LENGTH."""
        import importlib, ast, pathlib
        src = pathlib.Path(
            "services/interview_orchestration/interview_orchestrator.py"
        ).read_text()
        tree = ast.parse(src)
        imported_names = [
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
            for alias in node.names
        ]
        assert "DEFAULT_INTERVIEW_LENGTH" in imported_names


class TestFollowUpRate:
    def test_default_followup_rate_is_20_percent(self):
        assert DEFAULT_FOLLOWUP_RATE == 0.20

    def test_max_follow_ups_per_interview_is_2(self):
        assert MAX_FOLLOW_UPS_PER_INTERVIEW == 2

    def test_humanizer_policy_engine_uses_constant(self):
        engine = HumanizerPolicyEngine()
        assert engine.MAX_FOLLOW_UPS == MAX_FOLLOW_UPS_PER_INTERVIEW
        assert engine.MAX_FOLLOW_UPS == 2


# ── Area allocation ───────────────────────────────────────────────────────────

EXPECTED_WEIGHTS = {
    "technical_background":           0.10,
    "technical_technical_knowledge":  0.20,
    "technical_case_study":           0.25,
    "technical_database":             0.20,
    "technical_coding":               0.25,
}

EXPECTED_Q_COUNT = {
    "technical_background":           2,
    "technical_technical_knowledge":  4,
    "technical_case_study":           5,
    "technical_database":             4,
    "technical_coding":               5,
}


class TestTechnicalAreaWeights:
    def test_all_technical_areas_present(self):
        expected_areas = {a.value for a in InterviewType.TECHNICAL.get_areas()}
        assert set(TECHNICAL_AREA_WEIGHTS.keys()) == expected_areas

    def test_weights_sum_to_one(self):
        total = sum(TECHNICAL_AREA_WEIGHTS.values())
        assert abs(total - 1.0) < 1e-9

    @pytest.mark.parametrize("area,weight", EXPECTED_WEIGHTS.items())
    def test_area_weight_matches_spec(self, area: str, weight: float):
        assert TECHNICAL_AREA_WEIGHTS[area] == pytest.approx(weight)

    def test_question_counts_sum_to_default_length(self):
        assert sum(TECHNICAL_AREA_QUESTION_COUNT.values()) == DEFAULT_INTERVIEW_LENGTH

    @pytest.mark.parametrize("area,expected_q", EXPECTED_Q_COUNT.items())
    def test_question_count_per_area(self, area: str, expected_q: int):
        assert TECHNICAL_AREA_QUESTION_COUNT[area] == expected_q

    def test_question_counts_consistent_with_weights_and_length(self):
        """Derived counts must match floor-with-remainder distribution."""
        raw = {a: TECHNICAL_AREA_WEIGHTS[a] * DEFAULT_INTERVIEW_LENGTH
               for a in TECHNICAL_AREA_WEIGHTS}
        floored = {a: math.floor(v) for a, v in raw.items()}
        remainder = DEFAULT_INTERVIEW_LENGTH - sum(floored.values())
        for a in sorted(TECHNICAL_AREA_WEIGHTS, key=lambda x: raw[x] - floored[x], reverse=True)[:remainder]:
            floored[a] += 1
        assert floored == TECHNICAL_AREA_QUESTION_COUNT


# ── Corpus / LLM fractions ────────────────────────────────────────────────────

EXPECTED_CORPUS_FRACTIONS = {
    "technical_background":           0.50,
    "technical_technical_knowledge":  0.80,
    "technical_case_study":           0.60,
    "technical_database":             0.80,
    "technical_coding":               0.90,
}


class TestTechnicalAreaCorpusFraction:
    def test_all_technical_areas_have_fraction(self):
        expected_areas = {a.value for a in InterviewType.TECHNICAL.get_areas()}
        assert set(TECHNICAL_AREA_CORPUS_FRACTION.keys()) == expected_areas

    @pytest.mark.parametrize("area,frac", EXPECTED_CORPUS_FRACTIONS.items())
    def test_corpus_fraction_matches_spec(self, area: str, frac: float):
        assert TECHNICAL_AREA_CORPUS_FRACTION[area] == pytest.approx(frac)

    @pytest.mark.parametrize("area,frac", EXPECTED_CORPUS_FRACTIONS.items())
    def test_fraction_is_between_0_and_1(self, area: str, frac: float):
        assert 0.0 < frac <= 1.0


# ── corpus_quota helper ───────────────────────────────────────────────────────

class TestCorpusQuotaResolver:
    """resolve_corpus_quota must return the correct integer cap for each area."""

    @pytest.mark.parametrize("area_value,q_per_area,expected_quota", [
        ("technical_background",           2,  1),   # round(2 * 0.50) = 1
        ("technical_technical_knowledge",  4,  3),   # round(4 * 0.80) = 3
        ("technical_case_study",           5,  3),   # round(5 * 0.60) = 3
        ("technical_database",             4,  3),   # round(4 * 0.80) = 3
        ("technical_coding",               5,  4),   # round(5 * 0.90) = 4 (Python banker's rounding: round(4.5)=4)
    ])
    def test_corpus_quota_technical(self, area_value: str, q_per_area: int, expected_quota: int):
        area = InterviewArea(area_value)
        quota = resolve_corpus_quota(area, InterviewType.TECHNICAL, q_per_area)
        assert quota == expected_quota

    def test_corpus_quota_returns_none_for_hr(self):
        area = InterviewArea.HR_BACKGROUND
        quota = resolve_corpus_quota(area, InterviewType.HR, 4)
        assert quota is None

    @pytest.mark.parametrize("area_value", [a.value for a in InterviewType.TECHNICAL.get_areas()])
    def test_corpus_quota_at_least_one(self, area_value: str):
        area = InterviewArea(area_value)
        quota = resolve_corpus_quota(area, InterviewType.TECHNICAL, 1)
        assert quota is not None and quota >= 1

    @pytest.mark.parametrize("area_value", [a.value for a in InterviewType.TECHNICAL.get_areas()])
    def test_corpus_quota_never_exceeds_q_per_area(self, area_value: str):
        area = InterviewArea(area_value)
        for q_pa in [1, 2, 3, 4, 5, 8]:
            quota = resolve_corpus_quota(area, InterviewType.TECHNICAL, q_pa)
            assert quota is not None and quota <= q_pa


# ── WrittenQuestionPipeline corpus_quota signature ────────────────────────────

class TestWrittenPipelineCorpusQuotaSignature:
    def test_build_accepts_corpus_quota(self):
        import ast, pathlib
        src = pathlib.Path(
            "services/question_intelligence/pipelines/written_question_pipeline.py"
        ).read_text()
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "build":
                arg_names = [a.arg for a in node.args.args] + [a.arg for a in (node.args.kwonlyargs or [])]
                assert "corpus_quota" in arg_names, "corpus_quota missing from WrittenQuestionPipeline.build"
                return
        pytest.fail("build method not found in written_question_pipeline.py")

    def test_corpus_quota_default_is_none(self):
        import ast, pathlib
        src = pathlib.Path(
            "services/question_intelligence/pipelines/written_question_pipeline.py"
        ).read_text()
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "build":
                # defaults align to the last N args
                args = node.args.args
                defaults = node.args.defaults
                args_with_defaults = args[len(args) - len(defaults):]
                for arg, default in zip(args_with_defaults, defaults):
                    if arg.arg == "corpus_quota":
                        assert isinstance(default, ast.Constant) and default.value is None
                        return
                pytest.fail("corpus_quota has no default or default is not None")
        pytest.fail("build method not found")


class TestAreaQuestionBuilderCorpusQuotaSignature:
    def test_build_accepts_corpus_quota(self):
        import ast, pathlib
        src = pathlib.Path(
            "services/question_intelligence/area_question_builder.py"
        ).read_text()
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "build":
                arg_names = [a.arg for a in node.args.args]
                assert "corpus_quota" in arg_names, "corpus_quota missing from AreaQuestionBuilder.build"
                return
        pytest.fail("build method not found in area_question_builder.py")
