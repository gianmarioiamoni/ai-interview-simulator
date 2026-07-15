# tests/infrastructure/longitudinal/test_longitudinal_profile_repository_impl.py
# EPIC-02 — P3/C1 — Integration tests for JsonFileLongitudinalProfileRepository
#
# Test plan (EPIC-02-IMPLEMENTATION-PLAN.md §8 integration tests):
#   - save → get round-trip: all fields equal
#   - replace-on-write semantics verified
#   - exists returns False before first save, True after
#   - serialization round-trip for tuple[LanguageCapability, ...] within LongitudinalSessionMetadata
#   - contract compliance: implementation satisfies LongitudinalProfileRepository interface
#   - error handling: get on absent candidate returns None

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from domain.contracts.language.language_capability import LanguageCapability
from domain.contracts.longitudinal.longitudinal_profile import (
    CrossSessionLanguageCapability,
    LongitudinalProfile,
    LongitudinalSessionEntry,
    LongitudinalSessionMetadata,
)
from domain.contracts.longitudinal.longitudinal_profile_repository import (
    LongitudinalProfileRepository,
)
from infrastructure.longitudinal.longitudinal_profile_repository_impl import (
    JsonFileLongitudinalProfileRepository,
)

# Import shared factory helpers from domain contract conftest
from tests.domain.contracts.longitudinal.conftest import (
    CANDIDATE_ID,
    LATER_DT,
    SESSION_ID_0,
    SESSION_ID_1,
    make_candidate_profile_snapshot,
    make_longitudinal_profile,
    make_session_entry,
    make_session_metadata,
)

FIXED_DT = datetime(2026, 7, 14, 0, 0, 0, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def repo(tmp_path: Path) -> JsonFileLongitudinalProfileRepository:
    return JsonFileLongitudinalProfileRepository(storage_dir=tmp_path / "longitudinal")


@pytest.fixture
def single_session_profile() -> LongitudinalProfile:
    return make_longitudinal_profile()


@pytest.fixture
def profile_with_language_capabilities() -> LongitudinalProfile:
    lang_cap = LanguageCapability(
        language_id="python",
        questions_answered_in_language=5,
        composite_score=0.82,
        idiomatic_usage_score=0.78,
        type_error_rate=0.12,
    )
    metadata = LongitudinalSessionMetadata(
        role="Backend Engineer",
        seniority="senior",
        interview_type="technical",
        question_count=5,
        session_language="en",
        knowledge_epoch="1",
        total_objectives=2,
        total_narrative_insights=3,
        language_capabilities=(lang_cap,),
    )
    entry = LongitudinalSessionEntry(
        session_id=SESSION_ID_0,
        interview_index=0,
        profile_snapshot=make_candidate_profile_snapshot(),
        session_metadata=metadata,
        contributed_at=FIXED_DT,
    )
    cross = CrossSessionLanguageCapability(
        language_id="python",
        session_count_in_language=1,
        total_questions_answered=5,
        mean_composite_score=0.82,
        mean_idiomatic_score=0.78,
        mean_type_error_rate=0.12,
        trend_direction="insufficient_data",
        schema_version="1.0",
    )
    return LongitudinalProfile(
        candidate_identity_id=CANDIDATE_ID,
        session_snapshots=(entry,),
        session_count=1,
        language_capability_summary=(cross,),
        knowledge_epoch="1",
        schema_version="1.0",
        created_at=FIXED_DT,
        last_updated_at=FIXED_DT,
    )


# ---------------------------------------------------------------------------
# Contract compliance
# ---------------------------------------------------------------------------


def test_repository_is_abstract_interface_implementation(
    repo: JsonFileLongitudinalProfileRepository,
) -> None:
    assert isinstance(repo, LongitudinalProfileRepository)


# ---------------------------------------------------------------------------
# exists — before any save
# ---------------------------------------------------------------------------


def test_exists_returns_false_before_any_save(
    repo: JsonFileLongitudinalProfileRepository,
) -> None:
    assert repo.exists(CANDIDATE_ID) is False


def test_get_returns_none_before_any_save(
    repo: JsonFileLongitudinalProfileRepository,
) -> None:
    assert repo.get(CANDIDATE_ID) is None


# ---------------------------------------------------------------------------
# save → exists → get round-trip
# ---------------------------------------------------------------------------


def test_exists_returns_true_after_save(
    repo: JsonFileLongitudinalProfileRepository,
    single_session_profile: LongitudinalProfile,
) -> None:
    repo.save(single_session_profile)
    assert repo.exists(CANDIDATE_ID) is True


def test_get_returns_profile_equal_to_saved(
    repo: JsonFileLongitudinalProfileRepository,
    single_session_profile: LongitudinalProfile,
) -> None:
    repo.save(single_session_profile)
    retrieved = repo.get(CANDIDATE_ID)
    assert retrieved is not None
    assert retrieved == single_session_profile


def test_round_trip_candidate_identity_id(
    repo: JsonFileLongitudinalProfileRepository,
    single_session_profile: LongitudinalProfile,
) -> None:
    repo.save(single_session_profile)
    retrieved = repo.get(CANDIDATE_ID)
    assert retrieved is not None
    assert retrieved.candidate_identity_id == single_session_profile.candidate_identity_id


def test_round_trip_session_count(
    repo: JsonFileLongitudinalProfileRepository,
    single_session_profile: LongitudinalProfile,
) -> None:
    repo.save(single_session_profile)
    retrieved = repo.get(CANDIDATE_ID)
    assert retrieved is not None
    assert retrieved.session_count == single_session_profile.session_count


def test_round_trip_schema_version(
    repo: JsonFileLongitudinalProfileRepository,
    single_session_profile: LongitudinalProfile,
) -> None:
    repo.save(single_session_profile)
    retrieved = repo.get(CANDIDATE_ID)
    assert retrieved is not None
    assert retrieved.schema_version == "1.0"


def test_round_trip_datetime_fields_are_timezone_aware(
    repo: JsonFileLongitudinalProfileRepository,
    single_session_profile: LongitudinalProfile,
) -> None:
    repo.save(single_session_profile)
    retrieved = repo.get(CANDIDATE_ID)
    assert retrieved is not None
    assert retrieved.created_at.tzinfo is not None
    assert retrieved.last_updated_at.tzinfo is not None


def test_round_trip_session_snapshots_ordering_preserved(
    repo: JsonFileLongitudinalProfileRepository,
) -> None:
    entry_0 = make_session_entry(session_id=SESSION_ID_0, interview_index=0, contributed_at=FIXED_DT)
    entry_1 = make_session_entry(session_id=SESSION_ID_1, interview_index=1, contributed_at=LATER_DT, knowledge_epoch="2")
    profile = make_longitudinal_profile(entries=(entry_0, entry_1))
    repo.save(profile)
    retrieved = repo.get(CANDIDATE_ID)
    assert retrieved is not None
    assert len(retrieved.session_snapshots) == 2
    assert retrieved.session_snapshots[0].interview_index == 0
    assert retrieved.session_snapshots[1].interview_index == 1


# ---------------------------------------------------------------------------
# Serialization round-trip for tuple[LanguageCapability, ...]
# ---------------------------------------------------------------------------


def test_round_trip_language_capabilities_in_session_metadata(
    repo: JsonFileLongitudinalProfileRepository,
    profile_with_language_capabilities: LongitudinalProfile,
) -> None:
    repo.save(profile_with_language_capabilities)
    retrieved = repo.get(CANDIDATE_ID)
    assert retrieved is not None
    assert len(retrieved.session_snapshots) == 1
    lang_caps = retrieved.session_snapshots[0].session_metadata.language_capabilities
    assert len(lang_caps) == 1
    lc = lang_caps[0]
    assert lc.language_id == "python"
    assert lc.questions_answered_in_language == 5
    assert lc.composite_score == pytest.approx(0.82)
    assert lc.idiomatic_usage_score == pytest.approx(0.78)
    assert lc.type_error_rate == pytest.approx(0.12)


def test_round_trip_language_capability_summary(
    repo: JsonFileLongitudinalProfileRepository,
    profile_with_language_capabilities: LongitudinalProfile,
) -> None:
    repo.save(profile_with_language_capabilities)
    retrieved = repo.get(CANDIDATE_ID)
    assert retrieved is not None
    assert len(retrieved.language_capability_summary) == 1
    cross = retrieved.language_capability_summary[0]
    assert cross.language_id == "python"
    assert cross.session_count_in_language == 1
    assert cross.trend_direction == "insufficient_data"


# ---------------------------------------------------------------------------
# Replace-on-write semantics
# ---------------------------------------------------------------------------


def test_replace_on_write_overwrites_previous_profile(
    repo: JsonFileLongitudinalProfileRepository,
    single_session_profile: LongitudinalProfile,
) -> None:
    repo.save(single_session_profile)

    entry_1 = make_session_entry(
        session_id=SESSION_ID_1,
        interview_index=1,
        contributed_at=LATER_DT,
        knowledge_epoch="2",
    )
    updated_profile = make_longitudinal_profile(
        entries=(
            make_session_entry(session_id=SESSION_ID_0, interview_index=0, contributed_at=FIXED_DT),
            entry_1,
        )
    )
    repo.save(updated_profile)

    retrieved = repo.get(CANDIDATE_ID)
    assert retrieved is not None
    assert retrieved.session_count == 2
    assert retrieved.knowledge_epoch == "2"


def test_replace_on_write_only_one_record_stored(
    repo: JsonFileLongitudinalProfileRepository,
    single_session_profile: LongitudinalProfile,
) -> None:
    repo.save(single_session_profile)
    repo.save(single_session_profile)
    storage_files = list((repo._storage_dir).glob("*.json"))
    assert len(storage_files) == 1


def test_exists_reflects_replaced_profile(
    repo: JsonFileLongitudinalProfileRepository,
    single_session_profile: LongitudinalProfile,
) -> None:
    repo.save(single_session_profile)
    repo.save(single_session_profile)
    assert repo.exists(CANDIDATE_ID) is True


# ---------------------------------------------------------------------------
# Multiple candidates are isolated
# ---------------------------------------------------------------------------


def test_multiple_candidates_are_independent(
    repo: JsonFileLongitudinalProfileRepository,
    single_session_profile: LongitudinalProfile,
) -> None:
    other_id = "cand-other-999"
    other_entry = make_session_entry(candidate_id=other_id)
    other_profile = make_longitudinal_profile(candidate_id=other_id, entries=(other_entry,))

    repo.save(single_session_profile)
    repo.save(other_profile)

    assert repo.exists(CANDIDATE_ID) is True
    assert repo.exists(other_id) is True
    assert repo.get(CANDIDATE_ID) is not None
    assert repo.get(other_id) is not None
    assert repo.get(CANDIDATE_ID) != repo.get(other_id)


def test_absent_candidate_does_not_affect_existing_record(
    repo: JsonFileLongitudinalProfileRepository,
    single_session_profile: LongitudinalProfile,
) -> None:
    repo.save(single_session_profile)
    assert repo.get("nonexistent-candidate") is None
    assert repo.exists(CANDIDATE_ID) is True
