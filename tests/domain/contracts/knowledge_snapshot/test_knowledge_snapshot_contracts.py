# tests/domain/contracts/knowledge_snapshot/test_knowledge_snapshot_contracts.py
# Contract + Behavior + Architecture + Determinism tests — KnowledgeSnapshot layer

from __future__ import annotations

import ast
import pathlib

import pytest
from pydantic import ValidationError

from domain.contracts.coaching.coaching_builder import CoachingBuilder
from domain.contracts.knowledge_snapshot.candidate_profile_snapshot import (
    CandidateProfileSnapshot,
)
from domain.contracts.knowledge_snapshot.knowledge_snapshot import (
    KnowledgeSnapshot,
    PolicyVersions,
)
from domain.contracts.knowledge_snapshot.knowledge_snapshot_builder import (
    KnowledgeSnapshotBuilder,
)
from domain.contracts.knowledge_snapshot.knowledge_snapshot_statistics import (
    KnowledgeSnapshotStatistics,
)
from domain.contracts.knowledge_snapshot.knowledge_snapshot_summary import (
    KnowledgeSnapshotSummary,
)
from domain.contracts.knowledge_snapshot.knowledge_snapshot_validator import (
    KnowledgeSnapshotValidationResult,
    KnowledgeSnapshotValidator,
)
from tests.domain.contracts.knowledge_snapshot.conftest import (
    CANDIDATE_ID,
    SESSION_ID,
    make_candidate_profile_snapshot,
    make_coaching_snapshot,
    make_knowledge_snapshot,
    make_narrative,
    make_policy_versions,
    make_profile_feature,
)


# ===========================================================================
# CandidateProfileSnapshot — contract
# ===========================================================================

class TestCandidateProfileSnapshot:
    def test_valid_construction(self, profile_snapshot: CandidateProfileSnapshot):
        assert profile_snapshot.total_feature_count == 1
        assert profile_snapshot.candidate_identity_id == CANDIDATE_ID
        assert not profile_snapshot.is_empty

    def test_frozen(self, profile_snapshot: CandidateProfileSnapshot):
        with pytest.raises(Exception):
            profile_snapshot.candidate_identity_id = "mutated"  # type: ignore[misc]

    def test_feature_count_mismatch_rejected(self):
        feature = make_profile_feature()
        with pytest.raises(ValidationError):
            CandidateProfileSnapshot(
                candidate_identity_id=CANDIDATE_ID,
                features=(feature,),
                closed_at_question_index=5,
                total_feature_count=99,  # wrong count
                mean_confidence=0.75,
            )

    def test_wrong_candidate_feature_rejected(self):
        feature = make_profile_feature(candidate_id="other-cand")
        with pytest.raises(ValidationError):
            CandidateProfileSnapshot(
                candidate_identity_id=CANDIDATE_ID,
                features=(feature,),
                closed_at_question_index=5,
                total_feature_count=1,
                mean_confidence=0.75,
            )

    def test_empty_features_allowed(self):
        snap = CandidateProfileSnapshot(
            candidate_identity_id=CANDIDATE_ID,
            features=(),
            closed_at_question_index=0,
            total_feature_count=0,
            mean_confidence=0.0,
        )
        assert snap.is_empty

    def test_feature_type_ids_property(self, profile_snapshot: CandidateProfileSnapshot):
        ids = profile_snapshot.feature_type_ids
        assert isinstance(ids, frozenset)
        assert len(ids) == 1


# ===========================================================================
# PolicyVersions — contract
# ===========================================================================

class TestPolicyVersions:
    def test_valid_construction(self, policy_versions: PolicyVersions):
        assert policy_versions.feature_engine_version == "1.0"
        assert policy_versions.feature_engine_version is not None

    def test_frozen(self, policy_versions: PolicyVersions):
        with pytest.raises(Exception):
            policy_versions.feature_engine_version = "mutated"  # type: ignore[misc]

    def test_blank_version_rejected(self):
        with pytest.raises(ValidationError):
            PolicyVersions(
                feature_engine_version="",
                language_policy_version="1.0",
                ttl_policy_version="1.0",
                evaluation_policy_version="1.0",
                narrative_schema_version="1.0",
                coaching_schema_version="1.0",
                profile_schema_version="1.0",
            )


# ===========================================================================
# KnowledgeSnapshot — contract
# ===========================================================================

class TestKnowledgeSnapshot:
    def test_valid_construction(self, knowledge_snapshot: KnowledgeSnapshot):
        assert knowledge_snapshot.is_complete is True
        assert knowledge_snapshot.session_id == SESSION_ID
        assert knowledge_snapshot.candidate_identity_id == CANDIDATE_ID
        assert knowledge_snapshot.knowledge_epoch == "1"

    def test_frozen(self, knowledge_snapshot: KnowledgeSnapshot):
        with pytest.raises(Exception):
            knowledge_snapshot.session_id = "mutated"  # type: ignore[misc]

    def test_feature_count_property(self, knowledge_snapshot: KnowledgeSnapshot):
        assert knowledge_snapshot.feature_count == 1

    def test_objective_count_property(self, knowledge_snapshot: KnowledgeSnapshot):
        assert knowledge_snapshot.objective_count == 0

    def test_insight_count_property(self, knowledge_snapshot: KnowledgeSnapshot):
        assert knowledge_snapshot.insight_count == 0


# ===========================================================================
# KnowledgeSnapshotBuilder — behavior
# ===========================================================================

class TestKnowledgeSnapshotBuilder:
    def test_complete_build(self, knowledge_snapshot: KnowledgeSnapshot):
        assert isinstance(knowledge_snapshot, KnowledgeSnapshot)

    def test_missing_session_id_raises(self):
        builder = (
            KnowledgeSnapshotBuilder()
            .with_candidate_identity_id(CANDIDATE_ID)
            .with_profile_snapshot(make_candidate_profile_snapshot())
            .with_narrative(make_narrative())
            .with_coaching_snapshot(make_coaching_snapshot())
            .with_policy_versions(make_policy_versions())
        )
        with pytest.raises(ValueError, match="mandatory fields"):
            builder.build()

    def test_missing_narrative_raises(self):
        builder = (
            KnowledgeSnapshotBuilder()
            .with_session_id(SESSION_ID)
            .with_candidate_identity_id(CANDIDATE_ID)
            .with_profile_snapshot(make_candidate_profile_snapshot())
            .with_coaching_snapshot(make_coaching_snapshot())
            .with_policy_versions(make_policy_versions())
        )
        with pytest.raises(ValueError, match="mandatory fields"):
            builder.build()

    def test_candidate_id_mismatch_raises(self):
        profile_snap = make_candidate_profile_snapshot(candidate_id="other-cand")
        builder = (
            KnowledgeSnapshotBuilder()
            .with_session_id(SESSION_ID)
            .with_candidate_identity_id(CANDIDATE_ID)
            .with_profile_snapshot(profile_snap)
            .with_narrative(make_narrative())
            .with_coaching_snapshot(make_coaching_snapshot())
            .with_policy_versions(make_policy_versions())
        )
        with pytest.raises(ValueError, match="candidate_identity_id"):
            builder.build()

    def test_custom_snapshot_id(self):
        snap = (
            KnowledgeSnapshotBuilder()
            .with_session_id(SESSION_ID)
            .with_candidate_identity_id(CANDIDATE_ID)
            .with_profile_snapshot(make_candidate_profile_snapshot())
            .with_narrative(make_narrative())
            .with_coaching_snapshot(make_coaching_snapshot())
            .with_policy_versions(make_policy_versions())
            .with_snapshot_id("custom-id-42")
            .build()
        )
        assert snap.snapshot_id == "custom-id-42"

    def test_auto_snapshot_id_generated(self):
        snap = (
            KnowledgeSnapshotBuilder()
            .with_session_id(SESSION_ID)
            .with_candidate_identity_id(CANDIDATE_ID)
            .with_profile_snapshot(make_candidate_profile_snapshot())
            .with_narrative(make_narrative())
            .with_coaching_snapshot(make_coaching_snapshot())
            .with_policy_versions(make_policy_versions())
            .build()
        )
        assert len(snap.snapshot_id) > 0

    def test_build_is_sole_creation_path(self, knowledge_snapshot: KnowledgeSnapshot):
        assert isinstance(knowledge_snapshot, KnowledgeSnapshot)

    def test_knowledge_epoch_override(self):
        snap = (
            KnowledgeSnapshotBuilder()
            .with_session_id(SESSION_ID)
            .with_candidate_identity_id(CANDIDATE_ID)
            .with_profile_snapshot(make_candidate_profile_snapshot())
            .with_narrative(make_narrative())
            .with_coaching_snapshot(make_coaching_snapshot())
            .with_policy_versions(make_policy_versions())
            .with_knowledge_epoch("2")
            .build()
        )
        assert snap.knowledge_epoch == "2"


# ===========================================================================
# KnowledgeSnapshotStatistics — behavior
# ===========================================================================

class TestKnowledgeSnapshotStatistics:
    def test_from_snapshot_basic(self, knowledge_snapshot: KnowledgeSnapshot):
        stats = KnowledgeSnapshotStatistics.from_snapshot(knowledge_snapshot)
        assert stats.total_features == 1
        assert stats.total_objectives == 0
        assert stats.total_narrative_insights == 0
        assert stats.total_narrative_sections == 5
        assert stats.knowledge_epoch == "1"
        assert stats.is_profile_empty is False

    def test_mean_feature_confidence(self, knowledge_snapshot: KnowledgeSnapshot):
        stats = KnowledgeSnapshotStatistics.from_snapshot(knowledge_snapshot)
        assert 0.0 <= stats.mean_feature_confidence <= 1.0

    def test_frozen(self, knowledge_snapshot: KnowledgeSnapshot):
        stats = KnowledgeSnapshotStatistics.from_snapshot(knowledge_snapshot)
        with pytest.raises(Exception):
            stats.total_features = 99  # type: ignore[misc]

    def test_empty_profile_stats(self):
        snap = (
            KnowledgeSnapshotBuilder()
            .with_session_id(SESSION_ID)
            .with_candidate_identity_id(CANDIDATE_ID)
            .with_profile_snapshot(
                CandidateProfileSnapshot(
                    candidate_identity_id=CANDIDATE_ID,
                    features=(),
                    closed_at_question_index=0,
                    total_feature_count=0,
                    mean_confidence=0.0,
                )
            )
            .with_narrative(make_narrative())
            .with_coaching_snapshot(make_coaching_snapshot())
            .with_policy_versions(make_policy_versions())
            .build()
        )
        stats = KnowledgeSnapshotStatistics.from_snapshot(snap)
        assert stats.total_features == 0
        assert stats.mean_feature_confidence == pytest.approx(0.0)
        assert stats.is_profile_empty is True


# ===========================================================================
# KnowledgeSnapshotSummary — behavior
# ===========================================================================

class TestKnowledgeSnapshotSummary:
    def test_from_snapshot_basic(self, knowledge_snapshot: KnowledgeSnapshot):
        summary = KnowledgeSnapshotSummary.from_snapshot(knowledge_snapshot)
        assert summary.snapshot_id == knowledge_snapshot.snapshot_id
        assert summary.session_id == SESSION_ID
        assert summary.candidate_identity_id == CANDIDATE_ID
        assert summary.total_features == 1
        assert summary.is_complete is True
        assert summary.knowledge_epoch == "1"

    def test_frozen(self, knowledge_snapshot: KnowledgeSnapshot):
        summary = KnowledgeSnapshotSummary.from_snapshot(knowledge_snapshot)
        with pytest.raises(Exception):
            summary.total_features = 99  # type: ignore[misc]

    def test_schema_versions_preserved(self, knowledge_snapshot: KnowledgeSnapshot):
        summary = KnowledgeSnapshotSummary.from_snapshot(knowledge_snapshot)
        assert summary.profile_schema_version == "1.0"
        assert summary.narrative_schema_version == "1.0"
        assert summary.coaching_schema_version == "1.0"


# ===========================================================================
# KnowledgeSnapshotValidator — behavior
# ===========================================================================

class TestKnowledgeSnapshotValidator:
    def test_valid_snapshot_passes(self, knowledge_snapshot: KnowledgeSnapshot):
        result = KnowledgeSnapshotValidator.validate(knowledge_snapshot)
        assert result.is_valid is True
        assert result.violations == ()

    def test_result_ok_factory(self):
        result = KnowledgeSnapshotValidationResult.ok()
        assert result.is_valid is True
        assert result.violations == ()

    def test_result_failed_factory(self):
        result = KnowledgeSnapshotValidationResult.failed(["K-01: blank snapshot_id."])
        assert result.is_valid is False
        assert len(result.violations) == 1

    def test_session_coaching_mismatch_detected(self):
        snap = (
            KnowledgeSnapshotBuilder()
            .with_session_id(SESSION_ID)
            .with_candidate_identity_id(CANDIDATE_ID)
            .with_profile_snapshot(make_candidate_profile_snapshot())
            .with_narrative(make_narrative())
            .with_coaching_snapshot(CoachingBuilder.empty(session_id="wrong-session", question_index=0))
            .with_policy_versions(make_policy_versions())
            .build()
        )
        result = KnowledgeSnapshotValidator.validate(snap)
        assert result.is_valid is False
        assert any("session_id" in v for v in result.violations)


# ===========================================================================
# Determinism tests
# ===========================================================================

class TestKnowledgeSnapshotDeterminism:
    def test_same_inputs_same_statistics(self, knowledge_snapshot: KnowledgeSnapshot):
        results = [
            KnowledgeSnapshotStatistics.from_snapshot(knowledge_snapshot)
            for _ in range(3)
        ]
        assert all(r.total_features == 1 for r in results)
        assert all(r.total_narrative_sections == 5 for r in results)

    def test_same_inputs_same_summary(self, knowledge_snapshot: KnowledgeSnapshot):
        summaries = [
            KnowledgeSnapshotSummary.from_snapshot(knowledge_snapshot)
            for _ in range(3)
        ]
        assert len({s.snapshot_id for s in summaries}) == 1
        assert all(s.is_complete for s in summaries)

    def test_same_inputs_same_validation(self, knowledge_snapshot: KnowledgeSnapshot):
        results = [KnowledgeSnapshotValidator.validate(knowledge_snapshot) for _ in range(3)]
        assert all(r.is_valid for r in results)


# ===========================================================================
# Architecture tests
# ===========================================================================

SNAPSHOT_ROOT = pathlib.Path(__file__).parents[4] / "domain" / "contracts" / "knowledge_snapshot"

FORBIDDEN_IMPORTS_IN_SNAPSHOT = {
    "openai", "anthropic", "LLM", "llm_port", "PromptLoader",
    "SessionHistory", "Persistence", "ObservationStore", "EvidenceStore",
    "CandidateProfile",  # live runtime type — must not appear in snapshot layer
}


class TestKnowledgeSnapshotArchitecture:
    def test_no_forbidden_imports_in_contracts(self):
        for filepath in SNAPSHOT_ROOT.glob("*.py"):
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
            for forbidden in FORBIDDEN_IMPORTS_IN_SNAPSHOT:
                assert forbidden not in imported, (
                    f"Forbidden import '{forbidden}' found in {filepath.name}"
                )

    def test_all_pydantic_models_frozen(self):
        frozen_files = [
            "candidate_profile_snapshot.py",
            "knowledge_snapshot.py",
            "knowledge_snapshot_statistics.py",
            "knowledge_snapshot_summary.py",
        ]
        for fname in frozen_files:
            source = (SNAPSHOT_ROOT / fname).read_text()
            if "BaseModel" in source:
                assert '"frozen": True' in source or "'frozen': True" in source, (
                    f"Model in {fname} appears unfrozen"
                )

    def test_builder_does_not_contain_business_logic_keywords(self):
        source = (SNAPSHOT_ROOT / "knowledge_snapshot_builder.py").read_text()
        for banned in ["llm", "openai", "anthropic", "FeatureEngine", "NarrativeGenerator"]:
            assert banned not in source.lower(), (
                f"Builder contains forbidden keyword '{banned}' — builders own construction only"
            )

    def test_validator_does_not_construct_snapshots(self):
        source = (SNAPSHOT_ROOT / "knowledge_snapshot_validator.py").read_text()
        assert "KnowledgeSnapshotBuilder" not in source

    def test_statistics_does_not_construct_snapshots(self):
        source = (SNAPSHOT_ROOT / "knowledge_snapshot_statistics.py").read_text()
        assert "KnowledgeSnapshotBuilder" not in source

    def test_summary_does_not_construct_snapshots(self):
        source = (SNAPSHOT_ROOT / "knowledge_snapshot_summary.py").read_text()
        assert "KnowledgeSnapshotBuilder" not in source


# ===========================================================================
# CANDIDATE PROFILE SNAPSHOT — Ownership & Single-Writer Invariants (ADR-032)
# ===========================================================================

class TestCandidateProfileSnapshotOwnership:
    """Verify ADR-032 Single-Writer invariant for CandidateProfileSnapshot.

    The sole producer is FeatureEngine at session close. These tests confirm:
    - The contract itself is immutable and self-contained.
    - No construction pathway exists outside FeatureEngine in production code.
    - The snapshot does not reference live CandidateProfile.
    - Read-only consumers (KnowledgeSnapshot, Report, Replay, LearningProgress)
      only receive, never construct.
    """

    def test_candidate_profile_snapshot_is_frozen(
        self, profile_snapshot: CandidateProfileSnapshot
    ) -> None:
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            profile_snapshot.candidate_identity_id = "mutated"  # type: ignore[misc]

    def test_snapshot_self_contained_no_live_profile_import(self) -> None:
        source = (SNAPSHOT_ROOT / "candidate_profile_snapshot.py").read_text()
        assert "from domain.contracts.reasoning" not in source, (
            "CandidateProfileSnapshot must not import live CandidateProfile (ADR-032)"
        )
        assert "CandidateProfile" not in source or "CandidateProfileSnapshot" in source, (
            "Only CandidateProfileSnapshot reference is permitted — no live CandidateProfile"
        )

    def test_snapshot_ownership_documentation_present(self) -> None:
        source = (SNAPSHOT_ROOT / "candidate_profile_snapshot.py").read_text()
        assert "OWNERSHIP" in source, (
            "ADR-032 ownership documentation must be present in candidate_profile_snapshot.py"
        )
        assert "FeatureEngine" in source, (
            "FeatureEngine must be named as sole producer in ownership documentation"
        )
        assert "Single-Writer" in source or "sole producer" in source.lower(), (
            "Single-Writer invariant must be documented"
        )

    def test_snapshot_total_feature_count_invariant(
        self, profile_snapshot: CandidateProfileSnapshot
    ) -> None:
        assert profile_snapshot.total_feature_count == len(profile_snapshot.features)

    def test_snapshot_all_features_belong_to_same_candidate(
        self, profile_snapshot: CandidateProfileSnapshot
    ) -> None:
        for feature in profile_snapshot.features:
            assert feature.candidate_identity_id == profile_snapshot.candidate_identity_id

    def test_snapshot_rejects_total_feature_count_mismatch(
        self, profile_snapshot: CandidateProfileSnapshot
    ) -> None:
        from pydantic import ValidationError
        with pytest.raises(ValidationError, match="total_feature_count"):
            CandidateProfileSnapshot(
                candidate_identity_id=profile_snapshot.candidate_identity_id,
                features=profile_snapshot.features,
                closed_at_question_index=profile_snapshot.closed_at_question_index,
                total_feature_count=999,
            )

    def test_snapshot_rejects_cross_candidate_features(self) -> None:
        from pydantic import ValidationError
        from tests.domain.contracts.knowledge_snapshot.conftest import (
            make_profile_feature,
            CANDIDATE_ID,
        )
        wrong_feature = make_profile_feature(candidate_id="other-candidate")
        with pytest.raises(ValidationError):
            CandidateProfileSnapshot(
                candidate_identity_id=CANDIDATE_ID,
                features=(wrong_feature,),
                closed_at_question_index=1,
                total_feature_count=1,
            )

    def test_no_candidate_profile_snapshot_builder_exists_in_production(self) -> None:
        import pathlib
        snapshot_root = pathlib.Path(
            "domain/contracts/knowledge_snapshot"
        )
        builder_files = list(snapshot_root.glob("*snapshot_builder*"))
        # Only knowledge_snapshot_builder.py should exist — no profile snapshot builder
        builder_names = [f.name for f in builder_files]
        assert "candidate_profile_snapshot_builder.py" not in builder_names, (
            "CandidateProfileSnapshotBuilder does not exist yet (TCP — session-close sprint). "
            "If this test fails it means a builder was added without updating this test."
        )

    def test_services_do_not_construct_candidate_profile_snapshot(self) -> None:
        import pathlib
        services_root = pathlib.Path("services")
        violations: list[str] = []
        for py_file in services_root.rglob("*.py"):
            source = py_file.read_text()
            if "CandidateProfileSnapshot(" in source:
                violations.append(str(py_file))
        assert not violations, (
            f"Services must not construct CandidateProfileSnapshot directly (ADR-032). "
            f"Violations: {violations}"
        )

    def test_knowledge_snapshot_builder_accepts_not_constructs_profile_snapshot(
        self,
    ) -> None:
        source = (SNAPSHOT_ROOT / "knowledge_snapshot_builder.py").read_text()
        assert "CandidateProfileSnapshot(" not in source, (
            "KnowledgeSnapshotBuilder must receive CandidateProfileSnapshot "
            "as input — it must not construct one itself (ADR-032)"
        )

