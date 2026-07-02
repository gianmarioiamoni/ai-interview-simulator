# tests/domain/contracts/narrative/test_narrative_contracts.py
# Contract + Behavior + Integration + Architecture + Determinism tests

from __future__ import annotations

import ast
import pathlib

import pytest
from pydantic import ValidationError

from domain.contracts.feature.feature_identity import FeatureIdentity
from domain.contracts.feature.feature_type import FeatureType
from domain.contracts.narrative.narrative import Narrative
from domain.contracts.narrative.narrative_builder import NarrativeBuilder
from domain.contracts.narrative.narrative_collection import NarrativeCollection
from domain.contracts.narrative.narrative_insight import NarrativeInsight
from domain.contracts.narrative.narrative_insight_type import NarrativeInsightType
from domain.contracts.narrative.narrative_section import NarrativeSection
from domain.contracts.narrative.narrative_section_type import NarrativeSectionType
from domain.contracts.narrative.narrative_statistics import NarrativeStatistics
from domain.contracts.narrative.narrative_summary import NarrativeSummary
from tests.domain.contracts.narrative.conftest import (
    REASONING_ID,
    TECHNICAL_ID,
    make_insight,
    make_narrative,
    make_section,
)


# ===========================================================================
# NarrativeSection — contract
# ===========================================================================

class TestNarrativeSection:
    def test_valid_construction(self):
        s = make_section(NarrativeSectionType.STRENGTHS)
        assert s.section_type == NarrativeSectionType.STRENGTHS
        assert s.is_evidence_grounded is True
        assert len(s.feature_references) >= 1

    def test_frozen(self):
        s = make_section(NarrativeSectionType.STRENGTHS)
        with pytest.raises(Exception):
            s.prose = "mutated"  # type: ignore[misc]

    def test_empty_feature_references_rejected(self):
        with pytest.raises(ValidationError):
            NarrativeSection(
                section_type=NarrativeSectionType.STRENGTHS,
                prose="Some prose.",
                feature_references=(),
                confidence_context="ok",
            )

    def test_is_evidence_grounded_false_rejected(self):
        with pytest.raises(ValidationError):
            NarrativeSection(
                section_type=NarrativeSectionType.STRENGTHS,
                prose="Prose.",
                feature_references=(REASONING_ID,),
                confidence_context="ok",
                is_evidence_grounded=False,
            )

    def test_multiple_feature_references_allowed(self):
        s = NarrativeSection(
            section_type=NarrativeSectionType.WEAKNESSES,
            prose="Prose.",
            feature_references=(REASONING_ID, TECHNICAL_ID),
            confidence_context="ok",
        )
        assert len(s.feature_references) == 2

    def test_all_section_types_constructible(self):
        for stype in NarrativeSectionType:
            s = make_section(stype)
            assert s.section_type == stype


# ===========================================================================
# NarrativeInsight — contract
# ===========================================================================

class TestNarrativeInsight:
    def test_valid_construction(self):
        ins = make_insight()
        assert ins.is_traceable is True
        assert ins.confidence == pytest.approx(0.85)

    def test_frozen(self):
        ins = make_insight()
        with pytest.raises(Exception):
            ins.prose = "mutated"  # type: ignore[misc]

    def test_is_traceable_false_rejected(self):
        with pytest.raises(ValidationError):
            NarrativeInsight(
                insight_type=NarrativeInsightType.STRENGTH_SIGNAL,
                prose="Prose.",
                source_feature_id=REASONING_ID,
                confidence=0.8,
                is_traceable=False,
            )

    def test_confidence_out_of_range_rejected(self):
        with pytest.raises(ValidationError):
            NarrativeInsight(
                insight_type=NarrativeInsightType.ANOMALY,
                prose="Prose.",
                source_feature_id=REASONING_ID,
                confidence=1.5,
            )

    def test_all_insight_types_constructible(self):
        for itype in NarrativeInsightType:
            ins = make_insight(insight_type=itype)
            assert ins.insight_type == itype

    def test_confidence_boundary_values(self):
        for v in [0.0, 0.5, 1.0]:
            ins = make_insight(confidence=v)
            assert ins.confidence == pytest.approx(v)


# ===========================================================================
# Narrative — contract + invariants
# ===========================================================================

class TestNarrative:
    def test_complete_narrative_construction(self, complete_narrative: Narrative):
        assert complete_narrative.is_complete is True
        assert len(complete_narrative.all_sections) == 5

    def test_all_sections_canonical_order(self, complete_narrative: Narrative):
        sections = complete_narrative.all_sections
        assert sections[0].section_type == NarrativeSectionType.EXECUTIVE_SUMMARY
        assert sections[1].section_type == NarrativeSectionType.STRENGTHS
        assert sections[2].section_type == NarrativeSectionType.WEAKNESSES
        assert sections[3].section_type == NarrativeSectionType.GROWTH
        assert sections[4].section_type == NarrativeSectionType.RECOMMENDATIONS

    def test_section_type_mismatch_rejected(self):
        wrong_section = make_section(NarrativeSectionType.WEAKNESSES)
        with pytest.raises(ValidationError):
            Narrative(
                executive_summary=wrong_section,  # wrong type
                strengths=make_section(NarrativeSectionType.STRENGTHS),
                weaknesses=make_section(NarrativeSectionType.WEAKNESSES),
                growth_areas=make_section(NarrativeSectionType.GROWTH),
                recommendations=make_section(NarrativeSectionType.RECOMMENDATIONS),
            )

    def test_insights_default_empty(self, complete_narrative: Narrative):
        assert complete_narrative.insight_count == 0

    def test_insights_stored(self):
        ins = make_insight()
        n = make_narrative(insights=[ins])
        assert n.insight_count == 1

    def test_frozen_after_construction(self, complete_narrative: Narrative):
        with pytest.raises(Exception):
            complete_narrative.schema_version = "mutated"  # type: ignore[misc]

    def test_schema_version_default(self, complete_narrative: Narrative):
        assert complete_narrative.schema_version == "1.0"


# ===========================================================================
# NarrativeBuilder — behavior
# ===========================================================================

class TestNarrativeBuilder:
    def test_complete_build(self, complete_narrative: Narrative):
        assert complete_narrative is not None

    def test_missing_section_raises(self):
        builder = (
            NarrativeBuilder()
            .with_executive_summary(make_section(NarrativeSectionType.EXECUTIVE_SUMMARY))
            .with_strengths(make_section(NarrativeSectionType.STRENGTHS))
        )
        with pytest.raises(ValueError, match="mandatory sections"):
            builder.build()

    def test_wrong_section_type_in_slot_raises(self):
        wrong = make_section(NarrativeSectionType.WEAKNESSES)
        builder = NarrativeBuilder()
        with pytest.raises(ValueError):
            builder.with_executive_summary(wrong)

    def test_with_insights_fluent(self):
        ins1 = make_insight(NarrativeInsightType.STRENGTH_SIGNAL)
        ins2 = make_insight(NarrativeInsightType.RISK_SIGNAL)
        n = (
            NarrativeBuilder()
            .with_executive_summary(make_section(NarrativeSectionType.EXECUTIVE_SUMMARY))
            .with_strengths(make_section(NarrativeSectionType.STRENGTHS))
            .with_weaknesses(make_section(NarrativeSectionType.WEAKNESSES))
            .with_growth_areas(make_section(NarrativeSectionType.GROWTH))
            .with_recommendations(make_section(NarrativeSectionType.RECOMMENDATIONS))
            .with_insights([ins1, ins2])
            .build()
        )
        assert n.insight_count == 2

    def test_schema_version_override(self):
        n = (
            NarrativeBuilder()
            .with_executive_summary(make_section(NarrativeSectionType.EXECUTIVE_SUMMARY))
            .with_strengths(make_section(NarrativeSectionType.STRENGTHS))
            .with_weaknesses(make_section(NarrativeSectionType.WEAKNESSES))
            .with_growth_areas(make_section(NarrativeSectionType.GROWTH))
            .with_recommendations(make_section(NarrativeSectionType.RECOMMENDATIONS))
            .with_schema_version("2.0")
            .build()
        )
        assert n.schema_version == "2.0"

    def test_build_is_sole_creation_path(self):
        # NarrativeBuilder.build() must return a Narrative
        n = make_narrative()
        assert isinstance(n, Narrative)


# ===========================================================================
# NarrativeCollection — behavior
# ===========================================================================

class TestNarrativeCollection:
    def test_from_list(self):
        insights = [make_insight(NarrativeInsightType.STRENGTH_SIGNAL) for _ in range(3)]
        col = NarrativeCollection.from_list(insights)
        assert col.size == 3

    def test_is_empty(self):
        assert NarrativeCollection().is_empty is True

    def test_by_type_filter(self):
        col = NarrativeCollection.from_list([
            make_insight(NarrativeInsightType.STRENGTH_SIGNAL),
            make_insight(NarrativeInsightType.RISK_SIGNAL),
            make_insight(NarrativeInsightType.STRENGTH_SIGNAL),
        ])
        strengths = col.by_type(NarrativeInsightType.STRENGTH_SIGNAL)
        assert strengths.size == 2

    def test_with_min_confidence(self):
        col = NarrativeCollection.from_list([
            make_insight(confidence=0.3),
            make_insight(confidence=0.7),
            make_insight(confidence=0.9),
        ])
        high = col.with_min_confidence(0.6)
        assert high.size == 2

    def test_by_feature_type_id(self):
        col = NarrativeCollection.from_list([
            make_insight(source_feature_id=REASONING_ID),
            make_insight(source_feature_id=TECHNICAL_ID),
        ])
        reasoning_only = col.by_feature_type_id(REASONING_ID.feature_type_id)
        assert reasoning_only.size == 1

    def test_insight_types_frozenset(self):
        col = NarrativeCollection.from_list([
            make_insight(NarrativeInsightType.STRENGTH_SIGNAL),
            make_insight(NarrativeInsightType.ANOMALY),
        ])
        types = col.insight_types()
        assert NarrativeInsightType.STRENGTH_SIGNAL in types
        assert NarrativeInsightType.ANOMALY in types

    def test_frozen(self):
        col = NarrativeCollection()
        with pytest.raises(Exception):
            col.insights = ()  # type: ignore[misc]


# ===========================================================================
# NarrativeStatistics — behavior
# ===========================================================================

class TestNarrativeStatistics:
    def test_from_narrative_complete(self):
        n = make_narrative(with_insights=True)
        stats = NarrativeStatistics.from_narrative(n)
        assert stats.total_sections == 5
        assert stats.is_complete is True
        assert stats.total_insights == 1

    def test_unique_feature_ids(self):
        n = make_narrative(with_insights=True)
        stats = NarrativeStatistics.from_narrative(n)
        assert len(stats.unique_feature_ids) >= 1

    def test_confidence_distribution(self):
        ins = make_insight(confidence=0.6)
        n = make_narrative(insights=[ins])
        stats = NarrativeStatistics.from_narrative(n)
        assert stats.mean_insight_confidence == pytest.approx(0.6)
        assert stats.min_insight_confidence == pytest.approx(0.6)
        assert stats.max_insight_confidence == pytest.approx(0.6)

    def test_zero_insights(self):
        n = make_narrative()
        stats = NarrativeStatistics.from_narrative(n)
        assert stats.total_insights == 0
        assert stats.mean_insight_confidence == pytest.approx(0.0)

    def test_insight_type_counts(self):
        n = make_narrative(insights=[
            make_insight(NarrativeInsightType.STRENGTH_SIGNAL),
            make_insight(NarrativeInsightType.STRENGTH_SIGNAL),
            make_insight(NarrativeInsightType.RISK_SIGNAL),
        ])
        stats = NarrativeStatistics.from_narrative(n)
        counts = {r.insight_type: r.count for r in stats.insight_type_counts}
        assert counts[NarrativeInsightType.STRENGTH_SIGNAL] == 2
        assert counts[NarrativeInsightType.RISK_SIGNAL] == 1


# ===========================================================================
# NarrativeSummary — behavior
# ===========================================================================

class TestNarrativeSummary:
    def test_from_narrative_basic(self, complete_narrative: Narrative):
        summary = NarrativeSummary.from_narrative(complete_narrative)
        assert summary.total_sections == 5
        assert summary.is_complete is True
        assert summary.total_insights == 0

    def test_from_narrative_with_insights(self):
        n = make_narrative(with_insights=True)
        summary = NarrativeSummary.from_narrative(n)
        assert summary.total_insights == 1
        assert NarrativeInsightType.STRENGTH_SIGNAL in summary.insight_types_present

    def test_sections_present(self, complete_narrative: Narrative):
        summary = NarrativeSummary.from_narrative(complete_narrative)
        assert summary.sections_present == frozenset(NarrativeSectionType)

    def test_unique_feature_ids_referenced(self, complete_narrative: Narrative):
        summary = NarrativeSummary.from_narrative(complete_narrative)
        assert summary.unique_feature_ids_referenced >= 1

    def test_frozen(self, complete_narrative: Narrative):
        summary = NarrativeSummary.from_narrative(complete_narrative)
        with pytest.raises(Exception):
            summary.total_sections = 99  # type: ignore[misc]


# ===========================================================================
# Determinism tests
# ===========================================================================

class TestNarrativeDeterminism:
    def test_same_inputs_same_statistics(self):
        stats_list = [NarrativeStatistics.from_narrative(make_narrative(with_insights=True)) for _ in range(3)]
        assert all(s.total_sections == 5 for s in stats_list)
        assert all(s.total_insights == 1 for s in stats_list)
        assert all(s.is_complete for s in stats_list)

    def test_same_inputs_same_summary(self):
        summaries = [NarrativeSummary.from_narrative(make_narrative()) for _ in range(3)]
        assert len({s.total_sections for s in summaries}) == 1
        assert all(s.is_complete for s in summaries)

    def test_collection_filter_deterministic(self):
        insights = [make_insight(confidence=0.5), make_insight(confidence=0.9)]
        for _ in range(3):
            col = NarrativeCollection.from_list(insights)
            high = col.with_min_confidence(0.7)
            assert high.size == 1


# ===========================================================================
# Architecture tests
# ===========================================================================

NARRATIVE_CONTRACT_ROOT = pathlib.Path(__file__).parents[4] / "domain" / "contracts" / "narrative"

FORBIDDEN_IMPORTS = {
    "openai", "anthropic", "LLM", "llm_port", "PromptLoader",
    "CoachingAction", "CoachingPlan", "SessionHistory", "Persistence",
    "ObservationStore", "EvidenceStore",
}


class TestNarrativeArchitecture:
    def test_no_forbidden_imports_in_contracts(self):
        for filepath in NARRATIVE_CONTRACT_ROOT.glob("*.py"):
            source = filepath.read_text()
            tree = ast.parse(source)
            imported: set[str] = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imported.add(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imported.add(node.module)
                    for alias in node.names:
                        imported.add(alias.name)
            for forbidden in FORBIDDEN_IMPORTS:
                assert forbidden not in imported, (
                    f"Forbidden import '{forbidden}' found in {filepath.name}"
                )

    def test_narrative_does_not_import_candidate_profile(self):
        """NarrativeBuilder and Narrative must never import CandidateProfile."""
        for fname in ("narrative_builder.py", "narrative.py"):
            fpath = NARRATIVE_CONTRACT_ROOT / fname
            source = fpath.read_text()
            tree = ast.parse(source)
            imported: set[str] = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imported.add(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    for alias in node.names:
                        imported.add(alias.name)
            assert "CandidateProfile" not in imported, (
                f"CandidateProfile import found in {fname} — N-01/N-02 violation"
            )

    def test_no_prose_generation_in_contracts(self):
        """Contracts must not call any LLM-like function."""
        for filepath in NARRATIVE_CONTRACT_ROOT.glob("*.py"):
            source = filepath.read_text()
            for banned in ["llm.generate", "openai.chat", "anthropic.messages"]:
                assert banned not in source

    def test_all_contracts_frozen(self):
        """All Pydantic models must have frozen=True."""
        for filepath in NARRATIVE_CONTRACT_ROOT.glob("*.py"):
            source = filepath.read_text()
            if "class Narrative" in source and "BaseModel" in source:
                assert '"frozen": True' in source or "'frozen': True" in source, (
                    f"Model in {filepath.name} appears unfrozen"
                )
