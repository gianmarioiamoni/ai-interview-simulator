# domain/contracts/longitudinal/longitudinal_profile_builder.py
# EPIC-02 — P1/C2 — LongitudinalProfileBuilder (sole construction path for LongitudinalProfile)
# Governing: ADR-034, EPIC-02-DOMAIN-CONTRACTS.md §4, EPIC-02-DATA-MODEL.md §5

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from domain.contracts.language.language_capability import LanguageCapability
from domain.contracts.longitudinal.longitudinal_profile import (
    CrossSessionLanguageCapability,
    LongitudinalProfile,
    LongitudinalSessionEntry,
    LongitudinalSessionMetadata,
)
from domain.contracts.session_history.session_history import SessionHistory


class LongitudinalProfileBuilder:
    """Sole permitted construction path for LongitudinalProfile (ADR-034 Decision 1).

    Pure assembly component (P-05: Builders Assemble; Engines Compute).
    Applies no scoring, derivation, or LLM invocation.
    Receives pre-computed inputs and constructs a valid, immutable LongitudinalProfile.

    Usage:
        profile = (
            LongitudinalProfileBuilder()
            .with_prior_profile(prior)
            .with_session_history(session_history)
            .with_language_capabilities(language_caps)
            .with_current_timestamp(datetime.now(tz=timezone.utc))
            .build()
        )

    Responsibilities (DC §4.3 steps 1–10):
        1. Validate identity match (prior profile vs session history).
        2. Guard idempotency (duplicate interview_index → return prior unchanged).
        3. Assemble LongitudinalSessionEntry.
        4. Assemble session_snapshots (append + sort).
        5. Aggregate language_capability_summary (running means).
        6. Set knowledge_epoch.
        7. Set timestamps.
        8. Compute session_count.
        9. Set schema_version = "1.0".
        10. Validate and construct.

    Invariants enforced at build():
        LP-V-01 through LP-V-08, LC-V-02, LC-V-03, XC-01 through XC-05.
    """

    def __init__(self) -> None:
        self._prior_profile: Optional[LongitudinalProfile] = None
        self._session_history: Optional[SessionHistory] = None
        self._language_capabilities: tuple[LanguageCapability, ...] = ()
        self._current_timestamp: Optional[datetime] = None

    def with_prior_profile(self, prior: Optional[LongitudinalProfile]) -> "LongitudinalProfileBuilder":
        self._prior_profile = prior
        return self

    def with_session_history(self, session_history: SessionHistory) -> "LongitudinalProfileBuilder":
        self._session_history = session_history
        return self

    def with_language_capabilities(
        self, capabilities: tuple[LanguageCapability, ...]
    ) -> "LongitudinalProfileBuilder":
        self._language_capabilities = capabilities
        return self

    def with_current_timestamp(self, timestamp: datetime) -> "LongitudinalProfileBuilder":
        self._current_timestamp = timestamp
        return self

    def build(self) -> LongitudinalProfile:
        """Construct and return a valid, immutable LongitudinalProfile.

        Raises:
            ValueError: If required fields are missing, identity mismatch is detected,
                        or any invariant is violated.
        """
        # Step 0: Fail-fast on missing required inputs.
        if self._session_history is None:
            raise ValueError("session_history is required and must be set before calling build()")
        if self._current_timestamp is None:
            raise ValueError("current_timestamp is required and must be set before calling build()")

        session_history = self._session_history
        current_timestamp = self._current_timestamp
        prior = self._prior_profile

        # Step 1: Validate identity match.
        if prior is not None:
            if session_history.candidate_identity_id != prior.candidate_identity_id:
                raise ValueError(
                    f"Identity mismatch: session_history.candidate_identity_id "
                    f"({session_history.candidate_identity_id!r}) does not match "
                    f"prior_profile.candidate_identity_id ({prior.candidate_identity_id!r})"
                )

        # Step 2: Guard idempotency (LP-07).
        if prior is not None:
            existing_indices = {e.interview_index for e in prior.session_snapshots}
            if session_history.interview_index in existing_indices:
                return prior

        # Step 3: Assemble LongitudinalSessionEntry.
        coaching_stats = session_history.knowledge_snapshot.coaching_snapshot.statistics
        total_objectives: int = coaching_stats.total_objectives
        total_narrative_insights: int = session_history.knowledge_snapshot.narrative.insight_count

        session_metadata = LongitudinalSessionMetadata(
            role=session_history.interview_metadata.role,
            seniority=session_history.interview_metadata.seniority,
            interview_type=session_history.interview_metadata.interview_type,
            question_count=session_history.interview_metadata.question_count,
            session_language=session_history.interview_metadata.session_language,
            knowledge_epoch=session_history.knowledge_epoch,
            total_objectives=total_objectives,
            total_narrative_insights=total_narrative_insights,
            language_capabilities=self._language_capabilities,
        )

        new_entry = LongitudinalSessionEntry(
            session_id=session_history.session_id,
            interview_index=session_history.interview_index,
            profile_snapshot=session_history.knowledge_snapshot.profile_snapshot,
            session_metadata=session_metadata,
            contributed_at=current_timestamp,
        )

        # Step 4: Assemble session_snapshots (append + sort by interview_index ascending).
        prior_snapshots: tuple[LongitudinalSessionEntry, ...] = (
            prior.session_snapshots if prior is not None else ()
        )
        all_snapshots = tuple(
            sorted(prior_snapshots + (new_entry,), key=lambda e: e.interview_index)
        )

        # Step 5: Aggregate language_capability_summary.
        prior_lang_summary: tuple[CrossSessionLanguageCapability, ...] = (
            prior.language_capability_summary if prior is not None else ()
        )
        updated_lang_summary = self._aggregate_language_capabilities(
            prior_summary=prior_lang_summary,
            new_capabilities=self._language_capabilities,
        )

        # Step 6: Set knowledge_epoch (epoch of most recent session).
        knowledge_epoch = session_history.knowledge_epoch

        # Step 7: Set timestamps.
        created_at = prior.created_at if prior is not None else current_timestamp
        last_updated_at = current_timestamp

        # Step 8: Compute session_count.
        session_count = len(all_snapshots)

        # Steps 9 & 10: Set schema_version and construct (Pydantic validates invariants).
        return LongitudinalProfile(
            candidate_identity_id=session_history.candidate_identity_id,
            session_snapshots=all_snapshots,
            session_count=session_count,
            language_capability_summary=updated_lang_summary,
            knowledge_epoch=knowledge_epoch,
            schema_version="1.0",
            created_at=created_at,
            last_updated_at=last_updated_at,
        )

    @staticmethod
    def _aggregate_language_capabilities(
        prior_summary: tuple[CrossSessionLanguageCapability, ...],
        new_capabilities: tuple[LanguageCapability, ...],
    ) -> tuple[CrossSessionLanguageCapability, ...]:
        """Merge new session language capabilities into the prior cross-session summary.

        Applies running mean aggregation for composite, idiomatic, and type-error scores.
        Applies LC-V-03 trend_direction rule: "insufficient_data" when session_count_in_language < 2.
        If new_capabilities is empty, prior_summary is returned unchanged.
        """
        if not new_capabilities:
            return prior_summary

        # Build mutable working dict keyed by language_id.
        working: dict[str, dict] = {
            cap.language_id: {
                "session_count_in_language": cap.session_count_in_language,
                "total_questions_answered": cap.total_questions_answered,
                "mean_composite_score": cap.mean_composite_score,
                "mean_idiomatic_score": cap.mean_idiomatic_score,
                "mean_type_error_rate": cap.mean_type_error_rate,
            }
            for cap in prior_summary
        }

        for lc in new_capabilities:
            lang_id = lc.language_id
            if lang_id in working:
                entry = working[lang_id]
                n = entry["session_count_in_language"]
                entry["mean_composite_score"] = (
                    entry["mean_composite_score"] * n + lc.composite_score
                ) / (n + 1)
                entry["mean_idiomatic_score"] = (
                    entry["mean_idiomatic_score"] * n + lc.idiomatic_usage_score
                ) / (n + 1)
                entry["mean_type_error_rate"] = (
                    entry["mean_type_error_rate"] * n + lc.type_error_rate
                ) / (n + 1)
                entry["session_count_in_language"] = n + 1
                entry["total_questions_answered"] += lc.questions_answered_in_language
            else:
                working[lang_id] = {
                    "session_count_in_language": 1,
                    "total_questions_answered": lc.questions_answered_in_language,
                    "mean_composite_score": lc.composite_score,
                    "mean_idiomatic_score": lc.idiomatic_usage_score,
                    "mean_type_error_rate": lc.type_error_rate,
                }

        result = []
        for lang_id, data in working.items():
            n = data["session_count_in_language"]
            trend = _compute_language_trend(
                n=n,
                prior_entry=next((c for c in prior_summary if c.language_id == lang_id), None),
                new_capability=next((lc for lc in new_capabilities if lc.language_id == lang_id), None),
            )
            result.append(
                CrossSessionLanguageCapability(
                    language_id=lang_id,
                    session_count_in_language=n,
                    total_questions_answered=data["total_questions_answered"],
                    mean_composite_score=data["mean_composite_score"],
                    mean_idiomatic_score=data["mean_idiomatic_score"],
                    mean_type_error_rate=data["mean_type_error_rate"],
                    trend_direction=trend,
                    schema_version="1.0",
                )
            )

        return tuple(result)


def _compute_language_trend(
    n: int,
    prior_entry: Optional[CrossSessionLanguageCapability],
    new_capability: Optional[LanguageCapability],
) -> str:
    """Compute trend_direction for a CrossSessionLanguageCapability entry.

    LC-V-03: returns "insufficient_data" when n < 2.
    When n >= 2 and both prior and new capability are present, uses the
    ±0.05 composite score threshold rule (DC §2.6).
    For new languages (no prior entry), always "insufficient_data" on first session.
    """
    if n < 2 or prior_entry is None or new_capability is None:
        return "insufficient_data"

    earliest = prior_entry.mean_composite_score
    latest = new_capability.composite_score

    if latest > earliest + 0.05:
        return "improving"
    if latest < earliest - 0.05:
        return "declining"
    return "stable"
