# tests/domain/contracts/longitudinal/test_longitudinal_profile_contracts.py
# P1/C1 unit tests — immutable domain contracts for LongitudinalProfile
# Covers: immutability, serialization round-trip, equality, validation invariants,
#         invalid construction, default values.
# Test IDs: LP-V-01 through LP-V-08, LC-V-01 through LC-V-05, XC-01 through XC-05.

from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from domain.contracts.language.language_capability import LanguageCapability
from domain.contracts.longitudinal.longitudinal_profile import (
    CrossSessionLanguageCapability,
    LongitudinalProfile,
    LongitudinalSessionEntry,
    LongitudinalSessionMetadata,
)
from tests.domain.contracts.longitudinal.conftest import (
    CANDIDATE_ID,
    FIXED_DT,
    LATER_DT,
    make_candidate_profile_snapshot,
    make_longitudinal_profile,
    make_session_entry,
    make_session_metadata,
)


# ===========================================================================
# CrossSessionLanguageCapability
# ===========================================================================


class TestCrossSessionLanguageCapability:

    def test_valid_single_session_insufficient_data(self) -> None:
        cap = CrossSessionLanguageCapability(
            language_id="python",
            session_count_in_language=1,
            total_questions_answered=3,
            mean_composite_score=0.8,
            mean_idiomatic_score=0.75,
            mean_type_error_rate=0.1,
            trend_direction="insufficient_data",
        )
        assert cap.language_id == "python"
        assert cap.trend_direction == "insufficient_data"
        assert cap.schema_version == "1.0"

    def test_valid_multi_session_improving(self) -> None:
        cap = CrossSessionLanguageCapability(
            language_id="typescript",
            session_count_in_language=3,
            total_questions_answered=9,
            mean_composite_score=0.9,
            mean_idiomatic_score=0.85,
            mean_type_error_rate=0.05,
            trend_direction="improving",
        )
        assert cap.trend_direction == "improving"

    def test_default_trend_direction_is_stable(self) -> None:
        cap = CrossSessionLanguageCapability(
            language_id="python",
            session_count_in_language=2,
            total_questions_answered=4,
            mean_composite_score=0.7,
            mean_idiomatic_score=0.7,
            mean_type_error_rate=0.1,
        )
        assert cap.trend_direction == "stable"

    def test_default_schema_version(self) -> None:
        cap = CrossSessionLanguageCapability(
            language_id="rust",
            session_count_in_language=2,
            total_questions_answered=2,
            mean_composite_score=0.5,
            mean_idiomatic_score=0.5,
            mean_type_error_rate=0.2,
        )
        assert cap.schema_version == "1.0"

    # LC-V-02: session_count_in_language >= 1
    def test_lc_v02_rejects_zero_session_count(self) -> None:
        with pytest.raises(ValidationError):
            CrossSessionLanguageCapability(
                language_id="python",
                session_count_in_language=0,
                total_questions_answered=0,
                mean_composite_score=0.5,
                mean_idiomatic_score=0.5,
                mean_type_error_rate=0.1,
                trend_direction="insufficient_data",
            )

    # LC-V-03: trend_direction must be "insufficient_data" when session_count_in_language < 2
    def test_lc_v03_rejects_non_insufficient_when_single_session(self) -> None:
        with pytest.raises(ValidationError, match="LC-V-03"):
            CrossSessionLanguageCapability(
                language_id="python",
                session_count_in_language=1,
                total_questions_answered=2,
                mean_composite_score=0.7,
                mean_idiomatic_score=0.6,
                mean_type_error_rate=0.1,
                trend_direction="improving",
            )

    # LC-V-04: scores in [0.0, 1.0]
    def test_lc_v04_rejects_composite_score_above_1(self) -> None:
        with pytest.raises(ValidationError):
            CrossSessionLanguageCapability(
                language_id="python",
                session_count_in_language=1,
                total_questions_answered=1,
                mean_composite_score=1.1,
                mean_idiomatic_score=0.5,
                mean_type_error_rate=0.1,
                trend_direction="insufficient_data",
            )

    def test_lc_v04_rejects_idiomatic_score_below_0(self) -> None:
        with pytest.raises(ValidationError):
            CrossSessionLanguageCapability(
                language_id="python",
                session_count_in_language=1,
                total_questions_answered=1,
                mean_composite_score=0.5,
                mean_idiomatic_score=-0.1,
                mean_type_error_rate=0.1,
                trend_direction="insufficient_data",
            )

    def test_invalid_trend_direction_rejected(self) -> None:
        with pytest.raises(ValidationError, match="trend_direction"):
            CrossSessionLanguageCapability(
                language_id="python",
                session_count_in_language=2,
                total_questions_answered=4,
                mean_composite_score=0.7,
                mean_idiomatic_score=0.7,
                mean_type_error_rate=0.1,
                trend_direction="unknown_value",
            )

    def test_extra_fields_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            CrossSessionLanguageCapability(
                language_id="python",
                session_count_in_language=1,
                total_questions_answered=1,
                mean_composite_score=0.5,
                mean_idiomatic_score=0.5,
                mean_type_error_rate=0.1,
                trend_direction="insufficient_data",
                extra_field="not_allowed",
            )

    def test_immutability(self) -> None:
        cap = CrossSessionLanguageCapability(
            language_id="python",
            session_count_in_language=1,
            total_questions_answered=1,
            mean_composite_score=0.5,
            mean_idiomatic_score=0.5,
            mean_type_error_rate=0.1,
            trend_direction="insufficient_data",
        )
        with pytest.raises((TypeError, ValidationError)):
            cap.language_id = "java"  # type: ignore[misc]

    def test_equality(self) -> None:
        kwargs = dict(
            language_id="python",
            session_count_in_language=1,
            total_questions_answered=1,
            mean_composite_score=0.5,
            mean_idiomatic_score=0.5,
            mean_type_error_rate=0.1,
            trend_direction="insufficient_data",
        )
        assert CrossSessionLanguageCapability(**kwargs) == CrossSessionLanguageCapability(**kwargs)

    def test_serialization_round_trip(self) -> None:
        cap = CrossSessionLanguageCapability(
            language_id="python",
            session_count_in_language=2,
            total_questions_answered=4,
            mean_composite_score=0.75,
            mean_idiomatic_score=0.7,
            mean_type_error_rate=0.08,
            trend_direction="stable",
        )
        serialized = cap.model_dump_json()
        restored = CrossSessionLanguageCapability.model_validate_json(serialized)
        assert restored == cap

    def test_score_boundary_values_accepted(self) -> None:
        cap = CrossSessionLanguageCapability(
            language_id="go",
            session_count_in_language=2,
            total_questions_answered=2,
            mean_composite_score=0.0,
            mean_idiomatic_score=1.0,
            mean_type_error_rate=0.0,
        )
        assert cap.mean_composite_score == 0.0
        assert cap.mean_idiomatic_score == 1.0


# ===========================================================================
# LongitudinalSessionMetadata
# ===========================================================================


class TestLongitudinalSessionMetadata:

    def test_valid_construction(self, session_metadata: LongitudinalSessionMetadata) -> None:
        assert session_metadata.role == "Backend Engineer"
        assert session_metadata.total_objectives == 2
        assert session_metadata.total_narrative_insights == 3
        assert session_metadata.language_capabilities == ()

    def test_default_total_objectives(self) -> None:
        meta = LongitudinalSessionMetadata(
            role="SWE",
            seniority="mid",
            interview_type="technical",
            question_count=3,
            session_language="en",
            knowledge_epoch="1",
        )
        assert meta.total_objectives == 0
        assert meta.total_narrative_insights == 0
        assert meta.language_capabilities == ()

    def test_immutability(self, session_metadata: LongitudinalSessionMetadata) -> None:
        with pytest.raises((TypeError, ValidationError)):
            session_metadata.role = "changed"  # type: ignore[misc]

    def test_extra_fields_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            LongitudinalSessionMetadata(
                role="SWE",
                seniority="mid",
                interview_type="technical",
                question_count=3,
                session_language="en",
                knowledge_epoch="1",
                unknown_field="bad",
            )

    def test_serialization_round_trip(self, session_metadata: LongitudinalSessionMetadata) -> None:
        serialized = session_metadata.model_dump_json()
        restored = LongitudinalSessionMetadata.model_validate_json(serialized)
        assert restored == session_metadata

    def test_with_language_capabilities(self) -> None:
        cap = LanguageCapability(
            language_id="python",
            questions_answered_in_language=2,
            composite_score=0.8,
            idiomatic_usage_score=0.75,
            type_error_rate=0.1,
        )
        meta = LongitudinalSessionMetadata(
            role="SWE",
            seniority="senior",
            interview_type="technical",
            question_count=5,
            session_language="en",
            knowledge_epoch="1",
            language_capabilities=(cap,),
        )
        assert len(meta.language_capabilities) == 1
        assert meta.language_capabilities[0].language_id == "python"

    def test_empty_role_rejected(self) -> None:
        with pytest.raises(ValidationError):
            LongitudinalSessionMetadata(
                role="",
                seniority="mid",
                interview_type="technical",
                question_count=3,
                session_language="en",
                knowledge_epoch="1",
            )


# ===========================================================================
# LongitudinalSessionEntry
# ===========================================================================


class TestLongitudinalSessionEntry:

    def test_valid_construction(self, session_entry: LongitudinalSessionEntry) -> None:
        assert session_entry.session_id == "sess-long-000"
        assert session_entry.interview_index == 0

    def test_immutability(self, session_entry: LongitudinalSessionEntry) -> None:
        with pytest.raises((TypeError, ValidationError)):
            session_entry.session_id = "changed"  # type: ignore[misc]

    def test_extra_fields_forbidden(self) -> None:
        snapshot = make_candidate_profile_snapshot()
        meta = make_session_metadata()
        with pytest.raises(ValidationError):
            LongitudinalSessionEntry(
                session_id="s-001",
                interview_index=0,
                profile_snapshot=snapshot,
                session_metadata=meta,
                contributed_at=FIXED_DT,
                unknown="bad",
            )

    def test_serialization_round_trip(self, session_entry: LongitudinalSessionEntry) -> None:
        serialized = session_entry.model_dump_json()
        restored = LongitudinalSessionEntry.model_validate_json(serialized)
        assert restored == session_entry

    def test_equality(self) -> None:
        e1 = make_session_entry()
        e2 = make_session_entry()
        assert e1 == e2

    def test_negative_interview_index_rejected(self) -> None:
        with pytest.raises(ValidationError):
            LongitudinalSessionEntry(
                session_id="s-001",
                interview_index=-1,
                profile_snapshot=make_candidate_profile_snapshot(),
                session_metadata=make_session_metadata(),
                contributed_at=FIXED_DT,
            )

    def test_empty_session_id_rejected(self) -> None:
        with pytest.raises(ValidationError):
            LongitudinalSessionEntry(
                session_id="",
                interview_index=0,
                profile_snapshot=make_candidate_profile_snapshot(),
                session_metadata=make_session_metadata(),
                contributed_at=FIXED_DT,
            )


# ===========================================================================
# LongitudinalProfile — Construction and Invariants
# ===========================================================================


class TestLongitudinalProfileValid:

    def test_valid_single_session(self, longitudinal_profile: LongitudinalProfile) -> None:
        assert longitudinal_profile.candidate_identity_id == CANDIDATE_ID
        assert longitudinal_profile.session_count == 1
        assert longitudinal_profile.schema_version == "1.0"
        assert longitudinal_profile.knowledge_epoch == "1"

    def test_default_schema_version(self) -> None:
        profile = make_longitudinal_profile()
        assert profile.schema_version == "1.0"

    def test_default_knowledge_epoch(self) -> None:
        entry = make_session_entry(knowledge_epoch="1")
        profile = LongitudinalProfile(
            candidate_identity_id=CANDIDATE_ID,
            session_snapshots=(entry,),
            session_count=1,
            created_at=FIXED_DT,
            last_updated_at=FIXED_DT,
        )
        assert profile.knowledge_epoch == "1"

    def test_default_language_capability_summary_empty(self) -> None:
        profile = make_longitudinal_profile()
        assert profile.language_capability_summary == ()

    def test_default_metadata_empty(self) -> None:
        profile = make_longitudinal_profile()
        assert profile.metadata == {}

    def test_immutability(self, longitudinal_profile: LongitudinalProfile) -> None:
        with pytest.raises((TypeError, ValidationError)):
            longitudinal_profile.candidate_identity_id = "changed"  # type: ignore[misc]

    def test_equality(self) -> None:
        p1 = make_longitudinal_profile()
        p2 = make_longitudinal_profile()
        assert p1 == p2

    def test_serialization_round_trip(self, longitudinal_profile: LongitudinalProfile) -> None:
        serialized = longitudinal_profile.model_dump_json()
        restored = LongitudinalProfile.model_validate_json(serialized)
        assert restored == longitudinal_profile

    def test_two_session_profile(self) -> None:
        e0 = make_session_entry(session_id="s-0", interview_index=0, contributed_at=FIXED_DT)
        e1 = make_session_entry(session_id="s-1", interview_index=1, contributed_at=LATER_DT)
        profile = make_longitudinal_profile(entries=(e0, e1))
        assert profile.session_count == 2
        assert profile.session_snapshots[0].interview_index == 0
        assert profile.session_snapshots[1].interview_index == 1

    def test_extra_fields_forbidden(self) -> None:
        entry = make_session_entry()
        with pytest.raises(ValidationError):
            LongitudinalProfile(
                candidate_identity_id=CANDIDATE_ID,
                session_snapshots=(entry,),
                session_count=1,
                created_at=FIXED_DT,
                last_updated_at=FIXED_DT,
                unknown_field="bad",
            )

    def test_with_language_capability_summary(self) -> None:
        lc = CrossSessionLanguageCapability(
            language_id="python",
            session_count_in_language=1,
            total_questions_answered=3,
            mean_composite_score=0.8,
            mean_idiomatic_score=0.75,
            mean_type_error_rate=0.1,
            trend_direction="insufficient_data",
        )
        profile = make_longitudinal_profile(language_capability_summary=(lc,))
        assert len(profile.language_capability_summary) == 1
        assert profile.language_capability_summary[0].language_id == "python"


# ===========================================================================
# LP-V-01: session_count == len(session_snapshots)
# ===========================================================================


class TestLPV01:

    def test_lp_v01_rejects_mismatched_count(self) -> None:
        entry = make_session_entry()
        with pytest.raises(ValidationError, match="LP-V-01"):
            LongitudinalProfile(
                candidate_identity_id=CANDIDATE_ID,
                session_snapshots=(entry,),
                session_count=2,
                created_at=FIXED_DT,
                last_updated_at=FIXED_DT,
            )

    def test_lp_v01_accepts_matching_count(self) -> None:
        entry = make_session_entry()
        profile = LongitudinalProfile(
            candidate_identity_id=CANDIDATE_ID,
            session_snapshots=(entry,),
            session_count=1,
            created_at=FIXED_DT,
            last_updated_at=FIXED_DT,
        )
        assert profile.session_count == 1


# ===========================================================================
# LP-V-02: all profile_snapshot.candidate_identity_id must match
# ===========================================================================


class TestLPV02:

    def test_lp_v02_rejects_mismatched_candidate(self) -> None:
        entry = make_session_entry(candidate_id="other-candidate")
        with pytest.raises(ValidationError, match="LP-V-02"):
            LongitudinalProfile(
                candidate_identity_id=CANDIDATE_ID,
                session_snapshots=(entry,),
                session_count=1,
                created_at=FIXED_DT,
                last_updated_at=FIXED_DT,
            )


# ===========================================================================
# LP-V-03: all interview_index values unique
# ===========================================================================


class TestLPV03:

    def test_lp_v03_rejects_duplicate_interview_index(self) -> None:
        e0 = make_session_entry(session_id="s-0", interview_index=0)
        e1 = make_session_entry(session_id="s-1", interview_index=0)
        with pytest.raises(ValidationError, match="LP-V-03"):
            LongitudinalProfile(
                candidate_identity_id=CANDIDATE_ID,
                session_snapshots=(e0, e1),
                session_count=2,
                created_at=FIXED_DT,
                last_updated_at=FIXED_DT,
            )


# ===========================================================================
# LP-V-04: session_snapshots ordered by interview_index ascending
# ===========================================================================


class TestLPV04:

    def test_lp_v04_rejects_unordered_snapshots(self) -> None:
        e0 = make_session_entry(session_id="s-0", interview_index=1)
        e1 = make_session_entry(session_id="s-1", interview_index=0)
        with pytest.raises(ValidationError, match="LP-V-04"):
            LongitudinalProfile(
                candidate_identity_id=CANDIDATE_ID,
                session_snapshots=(e0, e1),
                session_count=2,
                knowledge_epoch="1",
                created_at=FIXED_DT,
                last_updated_at=FIXED_DT,
            )


# ===========================================================================
# LP-V-05: language_id values unique in language_capability_summary
# ===========================================================================


class TestLPV05:

    def test_lp_v05_rejects_duplicate_language_id(self) -> None:
        lc1 = CrossSessionLanguageCapability(
            language_id="python",
            session_count_in_language=2,
            total_questions_answered=4,
            mean_composite_score=0.7,
            mean_idiomatic_score=0.7,
            mean_type_error_rate=0.1,
        )
        lc2 = CrossSessionLanguageCapability(
            language_id="python",
            session_count_in_language=2,
            total_questions_answered=3,
            mean_composite_score=0.6,
            mean_idiomatic_score=0.6,
            mean_type_error_rate=0.2,
        )
        entry = make_session_entry()
        with pytest.raises(ValidationError, match="LP-V-05"):
            LongitudinalProfile(
                candidate_identity_id=CANDIDATE_ID,
                session_snapshots=(entry,),
                session_count=1,
                language_capability_summary=(lc1, lc2),
                knowledge_epoch="1",
                created_at=FIXED_DT,
                last_updated_at=FIXED_DT,
            )


# ===========================================================================
# LP-V-06: last_updated_at >= created_at
# ===========================================================================


class TestLPV06:

    def test_lp_v06_rejects_last_updated_before_created(self) -> None:
        entry = make_session_entry()
        with pytest.raises(ValidationError, match="LP-V-06"):
            LongitudinalProfile(
                candidate_identity_id=CANDIDATE_ID,
                session_snapshots=(entry,),
                session_count=1,
                created_at=LATER_DT,
                last_updated_at=FIXED_DT,
            )

    def test_lp_v06_accepts_equal_timestamps(self) -> None:
        entry = make_session_entry()
        profile = LongitudinalProfile(
            candidate_identity_id=CANDIDATE_ID,
            session_snapshots=(entry,),
            session_count=1,
            created_at=FIXED_DT,
            last_updated_at=FIXED_DT,
        )
        assert profile.created_at == profile.last_updated_at


# ===========================================================================
# LP-V-07: knowledge_epoch equals epoch of highest interview_index session
# ===========================================================================


class TestLPV07:

    def test_lp_v07_rejects_wrong_epoch(self) -> None:
        entry = make_session_entry(knowledge_epoch="2")
        with pytest.raises(ValidationError, match="LP-V-07"):
            LongitudinalProfile(
                candidate_identity_id=CANDIDATE_ID,
                session_snapshots=(entry,),
                session_count=1,
                knowledge_epoch="1",
                created_at=FIXED_DT,
                last_updated_at=FIXED_DT,
            )

    def test_lp_v07_two_sessions_uses_highest_index_epoch(self) -> None:
        e0 = make_session_entry(interview_index=0, knowledge_epoch="1")
        e1 = make_session_entry(session_id="s-1", interview_index=1, knowledge_epoch="2")
        profile = LongitudinalProfile(
            candidate_identity_id=CANDIDATE_ID,
            session_snapshots=(e0, e1),
            session_count=2,
            knowledge_epoch="2",
            created_at=FIXED_DT,
            last_updated_at=LATER_DT,
        )
        assert profile.knowledge_epoch == "2"


# ===========================================================================
# LP-V-08: session_count == 0 implies empty language_capability_summary
# ===========================================================================


class TestLPV08:

    def test_lp_v08_zero_sessions_empty_language_summary_accepted(self) -> None:
        profile = LongitudinalProfile(
            candidate_identity_id=CANDIDATE_ID,
            session_snapshots=(),
            session_count=0,
            language_capability_summary=(),
            created_at=FIXED_DT,
            last_updated_at=FIXED_DT,
        )
        assert profile.session_count == 0
        assert profile.language_capability_summary == ()

    def test_lp_v08_zero_sessions_non_empty_language_summary_rejected(self) -> None:
        lc = CrossSessionLanguageCapability(
            language_id="python",
            session_count_in_language=1,
            total_questions_answered=1,
            mean_composite_score=0.5,
            mean_idiomatic_score=0.5,
            mean_type_error_rate=0.1,
            trend_direction="insufficient_data",
        )
        with pytest.raises(ValidationError, match="LP-V-08"):
            LongitudinalProfile(
                candidate_identity_id=CANDIDATE_ID,
                session_snapshots=(),
                session_count=0,
                language_capability_summary=(lc,),
                created_at=FIXED_DT,
                last_updated_at=FIXED_DT,
            )


# ===========================================================================
# XC-01 through XC-05 — Cross-contract invariants (structural, no runtime check needed for C1)
# ===========================================================================


class TestCrossContractInvariants:

    def test_xc01_candidate_identity_id_matches_across_sessions(self) -> None:
        """XC-01: profile.candidate_identity_id matches all embedded profile_snapshots."""
        entry = make_session_entry(candidate_id=CANDIDATE_ID)
        profile = make_longitudinal_profile(candidate_id=CANDIDATE_ID, entries=(entry,))
        for snap in profile.session_snapshots:
            assert snap.profile_snapshot.candidate_identity_id == profile.candidate_identity_id

    def test_xc02_interview_index_consistency(self) -> None:
        """XC-02: LongitudinalSessionEntry.interview_index preserved correctly."""
        entry = make_session_entry(interview_index=5)
        profile = LongitudinalProfile(
            candidate_identity_id=CANDIDATE_ID,
            session_snapshots=(entry,),
            session_count=1,
            knowledge_epoch="1",
            created_at=FIXED_DT,
            last_updated_at=FIXED_DT,
        )
        assert profile.session_snapshots[0].interview_index == 5

    def test_xc03_profile_snapshot_value_embedded(self) -> None:
        """XC-03: profile_snapshot is embedded by value (not reference)."""
        snap = make_candidate_profile_snapshot()
        entry = make_session_entry()
        profile = make_longitudinal_profile(entries=(entry,))
        assert profile.session_snapshots[0].profile_snapshot == snap

    def test_xc04_session_count_not_exceeds_snapshots(self) -> None:
        """XC-04: session_count equals len(session_snapshots) — covered by LP-V-01."""
        profile = make_longitudinal_profile()
        assert profile.session_count == len(profile.session_snapshots)

    def test_xc05_no_replay_import_in_module(self) -> None:
        """XC-05: longitudinal_profile module does not import any replay contract."""
        import importlib
        import sys
        mod = sys.modules.get("domain.contracts.longitudinal.longitudinal_profile")
        if mod is None:
            mod = importlib.import_module("domain.contracts.longitudinal.longitudinal_profile")
        source_file = mod.__file__ or ""
        with open(source_file) as f:
            content = f.read()
        assert "replay" not in content.lower(), (
            "XC-05: longitudinal_profile must not import any replay contract"
        )


# ===========================================================================
# Serialization — datetime UTC handling
# ===========================================================================


class TestDatetimeSerialization:

    def test_datetime_serializes_with_utc_timezone(self) -> None:
        entry = make_session_entry()
        profile = make_longitudinal_profile(entries=(entry,))
        data = json.loads(profile.model_dump_json())
        assert data["created_at"].endswith("Z") or "+00:00" in data["created_at"]

    def test_utc_datetime_accepted_in_session_entry(self) -> None:
        utc_dt = datetime(2026, 7, 14, 0, 0, 0, tzinfo=timezone.utc)
        entry = LongitudinalSessionEntry(
            session_id="s-001",
            interview_index=0,
            profile_snapshot=make_candidate_profile_snapshot(),
            session_metadata=make_session_metadata(),
            contributed_at=utc_dt,
        )
        assert entry.contributed_at.tzinfo is not None
