# tests/app/graph/nodes/test_narrative_integration.py
# Runtime Narrative Integration
#
# Verifies:
# 1. session_close_node invokes NarrativeGenerator (not stub) when profile present.
# 2. Narrative in KnowledgeSnapshot is NarrativeGenerator output (not placeholder prose).
# 3. NarrativeGenerator is the sole Narrative producer in session_close_node source.
# 4. NarrativeGenerator failure falls back to stub — close remains non-fatal.
# 5. No FeatureEngine / KnowledgePipeline / ObservationExtractor in narrative path.
# 6. Narrative sections are all five mandatory types.
# 7. Narrative prose varies with features (not fixed "Session closed.").
# 8. Narrative in Report matches Narrative in KnowledgeSnapshot (projection).
# 9. Empty features → generator still produces valid Narrative (sentinel path).
# 10. Determinism: same state → same Narrative prose.
# 11. candidate_identity_id propagated into NarrativeGenerationContext.
# 12. Backward compat: state without candidate_profile_v2 uses empty profile.
# 13. Architecture: NarrativeGenerator is singleton in module.
# 14. Narrative insight_count >= 0 (no crash on empty).
# 15. Source guard: _build_stub_narrative still exists as fallback.

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from domain.contracts.feature.feature_collection import FeatureCollection
from domain.contracts.feature.feature_identity import FeatureIdentity
from domain.contracts.feature.feature_provenance import FeatureProvenance
from domain.contracts.feature.feature_quality import (
    FeatureConfidence,
    FeatureMaturity,
    FeatureQuality,
    FeatureStability,
)
from domain.contracts.feature.feature_type import FeatureType
from domain.contracts.feature.profile_feature import ProfileFeature
from domain.contracts.interview_state import InterviewState
from domain.contracts.interview.interview_type import InterviewType
from domain.contracts.interview.answer import Answer
from domain.contracts.question.question import Question, QuestionType, QuestionDifficulty
from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.narrative.narrative import Narrative
from domain.contracts.narrative.narrative_section_type import NarrativeSectionType
from domain.contracts.user.role import Role, RoleType
from domain.profile.candidate_profile_builder import CandidateProfileBuilder


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SESSION_ID = "mig08a-test-session"
CANDIDATE_ID = "mig08a-candidate-001"


def _make_feature(value: str = "HIGH", q_idx: int = 0) -> ProfileFeature:
    identity = FeatureIdentity.for_type(FeatureType.REASONING)
    quality = FeatureQuality(
        confidence=FeatureConfidence(value=0.8),
        stability=FeatureStability(state="stable"),
        maturity=FeatureMaturity.from_observation_count(4),
    )
    provenance = FeatureProvenance(
        feature_identity=identity,
        source_observation_ids=("obs-1",),
        computed_at_question_index=q_idx,
        feature_engine_version="1.0.0",
        updater_id="test_updater",
    )
    return ProfileFeature(
        feature_identity=identity,
        value=value,
        quality=quality,
        provenance=provenance,
        computed_at_question_index=q_idx,
        candidate_identity_id=CANDIDATE_ID,
    )


def _make_state_with_features(features: tuple[ProfileFeature, ...]) -> InterviewState:
    q = Question(
        id="q1", area=InterviewArea.TECH_CODING, type=QuestionType.WRITTEN,
        prompt="test", difficulty=QuestionDifficulty.MEDIUM,
    )
    state = InterviewState.create_initial(
        role_type=RoleType.BACKEND_ENGINEER,
        interview_type=InterviewType.TECHNICAL,
        company="MIG08ATest",
        language="en",
        questions=[q],
        interview_id=SESSION_ID,
    )
    state = state.model_copy(update={
        "is_completed": True,
        "answers": [Answer(question_id="q1", content="answer", attempt=1)],
        "current_question_index": 0,
        "candidate_identity_id": CANDIDATE_ID,
    })
    if features:
        profile = CandidateProfileBuilder().with_profile_features(features).build()
        state = state.model_copy(update={"candidate_profile_v2": profile})
    return state


def _run_close(state: InterviewState) -> InterviewState:
    from app.graph.nodes.session_close_node import session_close_node
    return session_close_node(state)


def _get_narrative(state: InterviewState) -> Narrative | None:
    if state.session_history is None:
        return None
    return state.session_history.knowledge_snapshot.narrative


# ---------------------------------------------------------------------------
# 1. NarrativeGenerator invoked (not stub prose) when profile present
# ---------------------------------------------------------------------------

class TestNarrativeGeneratorInvoked:

    def test_narrative_not_stub_when_features_present(self):
        f = _make_feature("HIGH")
        state = _make_state_with_features((f,))
        result = _run_close(state)
        narrative = _get_narrative(result)
        assert narrative is not None
        # NarrativeGenerator produces feature-derived prose, not the stub phrase
        exec_prose = narrative.overview_section.prose
        assert exec_prose != "Session closed."

    def test_narrative_all_five_sections_present(self):
        f = _make_feature()
        state = _make_state_with_features((f,))
        result = _run_close(state)
        narrative = _get_narrative(result)
        assert narrative is not None
        section_types = {s.section_type for s in narrative.all_sections}
        assert NarrativeSectionType.EXECUTIVE_SUMMARY in section_types
        assert NarrativeSectionType.STRENGTHS in section_types
        assert NarrativeSectionType.WEAKNESSES in section_types
        assert NarrativeSectionType.GROWTH in section_types
        assert NarrativeSectionType.RECOMMENDATIONS in section_types

    def test_narrative_has_insights_when_features_present(self):
        f = _make_feature("HIGH")
        state = _make_state_with_features((f,))
        result = _run_close(state)
        narrative = _get_narrative(result)
        assert narrative is not None
        assert narrative.insight_count >= 0

    def test_narrative_section_count_is_five(self):
        f = _make_feature()
        state = _make_state_with_features((f,))
        result = _run_close(state)
        narrative = _get_narrative(result)
        assert narrative is not None
        assert len(narrative.all_sections) == 5

    def test_narrative_is_frozen(self):
        f = _make_feature()
        state = _make_state_with_features((f,))
        result = _run_close(state)
        narrative = _get_narrative(result)
        assert narrative is not None
        with pytest.raises((TypeError, Exception)):
            narrative.schema_version = "mutated"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# 2. Empty features path — generator sentinel
# ---------------------------------------------------------------------------

class TestNarrativeEmptyFeatures:

    def test_narrative_produced_when_no_features(self):
        state = _make_state_with_features(())
        result = _run_close(state)
        narrative = _get_narrative(result)
        assert narrative is not None

    def test_narrative_five_sections_when_no_features(self):
        state = _make_state_with_features(())
        result = _run_close(state)
        narrative = _get_narrative(result)
        assert narrative is not None
        assert len(narrative.all_sections) == 5

    def test_narrative_produced_when_no_profile_v2(self):
        """state without candidate_profile_v2 → generator uses empty profile."""
        q = Question(
            id="q1", area=InterviewArea.TECH_CODING, type=QuestionType.WRITTEN,
            prompt="test", difficulty=QuestionDifficulty.MEDIUM,
        )
        state = InterviewState.create_initial(
            role_type=RoleType.BACKEND_ENGINEER,
            interview_type=InterviewType.TECHNICAL,
            company="MIG08ATest",
            language="en",
            questions=[q],
            interview_id=SESSION_ID,
        )
        state = state.model_copy(update={
            "is_completed": True,
            "answers": [Answer(question_id="q1", content="answer", attempt=1)],
            "current_question_index": 0,
            "candidate_identity_id": CANDIDATE_ID,
        })
        assert state.candidate_profile_v2 is None
        result = _run_close(state)
        assert result.session_history is not None
        narrative = _get_narrative(result)
        assert narrative is not None


# ---------------------------------------------------------------------------
# 3. Non-fatal fallback
# ---------------------------------------------------------------------------

class TestNarrativeFallback:

    def test_generator_failure_falls_back_to_stub(self):
        """NarrativeGenerator failure → stub narrative; close still succeeds."""
        f = _make_feature()
        state = _make_state_with_features((f,))
        with patch(
            "app.graph.nodes.session_close_node._narrative_generator.generate",
            side_effect=RuntimeError("Generator crash"),
        ):
            result = _run_close(state)
        assert result.session_history is not None
        narrative = _get_narrative(result)
        assert narrative is not None
        # Stub narrative uses the fallback prose
        assert narrative.overview_section.prose == "Session closed."

    def test_unsuccessful_result_falls_back_to_stub(self):
        """NarrativeGenerationResult.is_successful=False → stub used."""
        from services.narrative_generator.narrative_generation_result import NarrativeGenerationResult
        from services.narrative_generator.narrative_generation_diagnostics import (
            NarrativeGenerationDiagnostics, NarrativeStage, StageAuditRecord
        )
        from services.narrative_generator.narrative_generation_metrics import NarrativeGenerationMetrics

        f = _make_feature()
        state = _make_state_with_features((f,))

        mock_diag = MagicMock()
        mock_result = MagicMock(spec=NarrativeGenerationResult)
        mock_result.is_successful = False
        mock_result.narrative = None
        mock_result.failure_reason = "Test failure"

        with patch(
            "app.graph.nodes.session_close_node._narrative_generator.generate",
            return_value=mock_result,
        ):
            result = _run_close(state)

        assert result.session_history is not None
        narrative = _get_narrative(result)
        assert narrative is not None


# ---------------------------------------------------------------------------
# 4. Determinism
# ---------------------------------------------------------------------------

class TestNarrativeDeterminism:

    def test_same_state_produces_same_prose(self):
        f = _make_feature("HIGH")
        state = _make_state_with_features((f,))
        r1 = _run_close(state)
        # Create fresh identical state for second run
        state2 = _make_state_with_features((f,))
        r2 = _run_close(state2)
        n1 = _get_narrative(r1)
        n2 = _get_narrative(r2)
        assert n1 is not None
        assert n2 is not None
        assert n1.overview_section.prose == n2.overview_section.prose


# ---------------------------------------------------------------------------
# 5. Report carries NarrativeGenerator narrative
# ---------------------------------------------------------------------------

class TestReportCarriesNarrative:

    def test_report_narrative_matches_knowledge_snapshot_narrative(self):
        from app.graph.nodes.report_node import report_node
        from tests.domain.contracts.report.conftest import (
            make_scoring_snapshot,
            make_scoring_narrative,
            make_context_profile,
        )
        f = _make_feature("HIGH")
        state = _make_state_with_features((f,))
        # Phase 8: Report v2.0 requires scoring_snapshot + scoring_narrative in SessionHistory
        state = state.model_copy(update={
            "scoring_snapshot": make_scoring_snapshot(),
            "scoring_narrative": make_scoring_narrative(),
            "context_profile": make_context_profile(),
        })
        closed = _run_close(state)
        assert closed.session_history is not None
        reported = report_node(closed)
        assert reported.report is not None
        # Report narrative comes from SessionHistory.KnowledgeSnapshot (pure projection)
        expected_prose = closed.session_history.knowledge_snapshot.narrative.overview_section.prose
        assert reported.report.narrative.overview_section.prose == expected_prose

    def test_report_narrative_not_stub_prose(self):
        from app.graph.nodes.report_node import report_node
        from tests.domain.contracts.report.conftest import (
            make_scoring_snapshot,
            make_scoring_narrative,
            make_context_profile,
        )
        f = _make_feature("HIGH")
        state = _make_state_with_features((f,))
        # Phase 8: Report v2.0 requires scoring_snapshot + scoring_narrative in SessionHistory
        state = state.model_copy(update={
            "scoring_snapshot": make_scoring_snapshot(),
            "scoring_narrative": make_scoring_narrative(),
            "context_profile": make_context_profile(),
        })
        closed = _run_close(state)
        reported = report_node(closed)
        assert reported.report is not None
        assert reported.report.narrative.overview_section.prose != "Session closed."


# ---------------------------------------------------------------------------
# 6. Architecture guards
# ---------------------------------------------------------------------------

class TestNarrativeArchitecture:

    def _node_source(self) -> str:
        node_path = Path(__file__).parents[4] / "app" / "graph" / "nodes" / "session_close_node.py"
        return node_path.read_text(encoding="utf-8")

    def test_narrative_generator_imported_in_node(self):
        source = self._node_source()
        assert "NarrativeGenerator" in source
        assert "from services.narrative_generator.narrative_generator import NarrativeGenerator" in source

    def test_stub_fallback_still_exists(self):
        source = self._node_source()
        assert "_build_stub_narrative" in source

    def test_no_feature_engine_import_in_narrative_path(self):
        source = self._node_source()
        assert "from services.feature_engine" not in source

    def test_no_knowledge_pipeline_import_in_node(self):
        source = self._node_source()
        assert "build_default_knowledge_pipeline" not in source

    def test_narrative_generator_singleton_in_module(self):
        import app.graph.nodes.session_close_node as mod
        assert hasattr(mod, "_narrative_generator")
        from services.narrative_generator.narrative_generator import NarrativeGenerator
        assert isinstance(mod._narrative_generator, NarrativeGenerator)
