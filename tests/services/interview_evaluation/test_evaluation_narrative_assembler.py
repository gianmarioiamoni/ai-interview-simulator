# tests/services/interview_evaluation/test_evaluation_narrative_assembler.py

from __future__ import annotations

import json
from unittest.mock import Mock

import pytest

from domain.contracts.interview.interview_type import InterviewType
from domain.contracts.question.question_evaluation import QuestionEvaluation
from domain.contracts.report.scoring_narrative import ScoringNarrative
from domain.contracts.report.scoring_narrative_item import ScoringNarrativeItem
from domain.contracts.shared.performance_dimension_type import PerformanceDimensionType
from domain.contracts.user.role import RoleType

from services.interview_evaluation.assemblers.evaluation_narrative_assembler import (
    AssemblerResult,
    EvaluationNarrativeAssembler,
)
from services.narrative_service import NarrativeService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_evaluation(qid: str = "q1", score: float = 75.0) -> QuestionEvaluation:
    return QuestionEvaluation(
        question_id=qid,
        score=score,
        max_score=100.0,
        feedback="Good.",
        strengths=["clarity"],
        weaknesses=["depth"],
        passed=score >= 60,
    )


def _make_scoring_mock() -> Mock:
    scoring = Mock()
    scoring.percentile = 65.0
    scoring.confidence = 0.75
    scoring.hiring_probability = 60.0
    return scoring


_SENTINEL = object()


def _make_llm_narrative(
    went_well=_SENTINEL,
    held_you_back=_SENTINEL,
    knowledge_gaps=_SENTINEL,
    next_strategy=_SENTINEL,
) -> Mock:
    """Return an LLM mock that returns a valid narrative JSON string."""
    payload = {
        "dimension_justifications": {
            "Technical Depth": "Showed solid understanding.",
        },
        "improvement_suggestions": ["Practice more system design."],
        "went_well": went_well if went_well is not _SENTINEL else ["Good problem decomposition."],
        "held_you_back": held_you_back if held_you_back is not _SENTINEL else [
            {
                "behaviour": "Did not consider edge cases.",
                "why_it_matters": "Edge cases indicate thoroughness.",
                "impact": "Lowered score in problem solving.",
            }
        ],
        "knowledge_gaps": knowledge_gaps if knowledge_gaps is not _SENTINEL else [
            {
                "category": "Distributed Systems",
                "concept": "Consistent hashing",
                "why_it_matters": "Core to distributed caching.",
                "interview_impact": "System design questions.",
            }
        ],
        "next_strategy": next_strategy if next_strategy is not _SENTINEL else [
            {
                "priority": "System Design",
                "why": "Needed for senior roles.",
                "expected_improvement": "Better architecture answers.",
                "impact": "High",
            }
        ],
    }

    class FakeLLMResponse(str):
        @property
        def content(self) -> str:
            return str(self)

    llm = Mock()
    llm.invoke.return_value = FakeLLMResponse(json.dumps(payload))
    return llm


def _make_assembler(llm: Mock | None = None) -> EvaluationNarrativeAssembler:
    if llm is None:
        llm = _make_llm_narrative()
    narrative_service = Mock(spec=NarrativeService)
    narrative_service.generate_executive_summary.return_value = "Solid overall performance."
    narrative_service.generate_decision_explanation.return_value = "Decision explanation."
    return EvaluationNarrativeAssembler(llm=llm, narrative_service=narrative_service)


def _run_assemble(assembler: EvaluationNarrativeAssembler, **overrides) -> AssemblerResult:
    from domain.contracts.interview.hire_decision import HireDecision
    defaults = dict(
        dimension_scores={PerformanceDimensionType.TECHNICAL_DEPTH: 75.0},
        dimension_signals={"technical_depth": 0.6},
        hire_decision=HireDecision.LEAN_HIRE,
        overall_score=75.0,
        scoring=_make_scoring_mock(),
        evaluations=[_make_evaluation()],
        interview_type=InterviewType.TECHNICAL,
        role=RoleType.BACKEND_ENGINEER,
    )
    defaults.update(overrides)
    return assembler.assemble(**defaults)


# ---------------------------------------------------------------------------
# AssemblerResult structure
# ---------------------------------------------------------------------------


class TestAssemblerResultType:
    def test_returns_assembler_result(self):
        result = _run_assemble(_make_assembler())
        assert isinstance(result, AssemblerResult)

    def test_scoring_narrative_is_present(self):
        result = _run_assemble(_make_assembler())
        assert isinstance(result.scoring_narrative, ScoringNarrative)

    def test_executive_summary_non_empty(self):
        result = _run_assemble(_make_assembler())
        assert result.executive_summary.strip()


# ---------------------------------------------------------------------------
# ScoringNarrative construction
# ---------------------------------------------------------------------------


class TestScoringNarrativeConstruction:
    def test_executive_summary_set_on_scoring_narrative(self):
        result = _run_assemble(_make_assembler())
        assert result.scoring_narrative.executive_summary == result.executive_summary

    def test_went_well_is_tuple_of_strings(self):
        result = _run_assemble(_make_assembler())
        assert isinstance(result.scoring_narrative.went_well, tuple)
        for item in result.scoring_narrative.went_well:
            assert isinstance(item, str)

    def test_held_you_back_contains_scoring_narrative_items(self):
        result = _run_assemble(_make_assembler())
        for item in result.scoring_narrative.held_you_back:
            assert isinstance(item, ScoringNarrativeItem)

    def test_knowledge_gaps_contains_scoring_narrative_items(self):
        result = _run_assemble(_make_assembler())
        for item in result.scoring_narrative.knowledge_gaps:
            assert isinstance(item, ScoringNarrativeItem)

    def test_next_strategy_contains_scoring_narrative_items(self):
        result = _run_assemble(_make_assembler())
        for item in result.scoring_narrative.next_strategy:
            assert isinstance(item, ScoringNarrativeItem)

    def test_held_you_back_field_mapping(self):
        result = _run_assemble(_make_assembler())
        items = result.scoring_narrative.held_you_back
        assert len(items) >= 1
        item = items[0]
        assert item.category == "held_you_back"
        assert "edge cases" in item.description.lower()
        assert item.why_it_matters
        assert item.context_detail

    def test_knowledge_gap_field_mapping(self):
        result = _run_assemble(_make_assembler())
        items = result.scoring_narrative.knowledge_gaps
        assert len(items) >= 1
        item = items[0]
        assert item.category == "Distributed Systems"
        assert "consistent hashing" in item.description.lower()
        assert item.why_it_matters

    def test_next_strategy_field_mapping(self):
        result = _run_assemble(_make_assembler())
        items = result.scoring_narrative.next_strategy
        assert len(items) >= 1
        item = items[0]
        assert item.category == "System Design"
        assert item.description
        assert item.why_it_matters

    def test_improvement_suggestions_are_strings(self):
        result = _run_assemble(_make_assembler())
        for s in result.scoring_narrative.improvement_suggestions:
            assert isinstance(s, str)


# ---------------------------------------------------------------------------
# Empty / malformed LLM output handling
# ---------------------------------------------------------------------------


class TestAssemblerFallbacks:
    def test_empty_coaching_sections_produce_empty_tuples(self):
        llm = _make_llm_narrative(
            went_well=[],
            held_you_back=[],
            knowledge_gaps=[],
            next_strategy=[],
        )
        result = _run_assemble(_make_assembler(llm))
        sn = result.scoring_narrative
        assert sn.went_well == ()
        assert sn.held_you_back == ()
        assert sn.knowledge_gaps == ()
        assert sn.next_strategy == ()

    def test_malformed_held_you_back_items_are_skipped(self):
        """Non-dict items in coaching sections are skipped gracefully."""
        llm = _make_llm_narrative(
            held_you_back=["not a dict", 42],
        )
        result = _run_assemble(_make_assembler(llm))
        assert result.scoring_narrative.held_you_back == ()

    def test_scoring_narrative_is_immutable(self):
        result = _run_assemble(_make_assembler())
        with pytest.raises((TypeError, Exception)):
            result.scoring_narrative.executive_summary = "mutated"  # type: ignore[misc]
