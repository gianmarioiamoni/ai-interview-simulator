# domain/contracts/replay/replay_timeline.py
# EPIC-03 Phase 2d — ReplayTimelineEntry + ReplayTimeline: derived navigation view.
# Field specification per EPIC-03-DOMAIN-CONTRACTS.md §4.

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


class ReplayTimelineEntry(BaseModel, frozen=True, extra="forbid"):
    """One navigable position in the replay timeline.

    Derived from ReplayQuestionRecord by ReplaySessionBuilder.
    """

    position: int = Field(..., ge=0)
    question_id: str = Field(..., min_length=1)
    question_index: int = Field(..., ge=0)
    area_label: str = Field(..., min_length=1)
    question_type: str = Field(..., min_length=1)


class ReplayTimeline(BaseModel, frozen=True, extra="forbid"):
    """Ordered, derived navigation view over ReplaySession.question_results.

    Produced by ReplaySessionBuilder from question_results. Not persisted.
    total_positions, first_position, last_position, and is_empty are
    computed fields that must be consistent with entries.
    """

    entries: tuple[ReplayTimelineEntry, ...] = Field(default_factory=tuple)
    total_positions: int = Field(..., ge=0)
    first_position: int
    last_position: int
    is_empty: bool

    @model_validator(mode="after")
    def _validate_consistency(self) -> ReplayTimeline:
        n = len(self.entries)
        if self.total_positions != n:
            raise ValueError(
                f"total_positions ({self.total_positions}) must equal len(entries) ({n})."
            )
        expected_first = 0 if n > 0 else -1
        expected_last = n - 1 if n > 0 else -1
        if self.first_position != expected_first:
            raise ValueError(
                f"first_position must be {expected_first} for {n} entries, "
                f"got {self.first_position}."
            )
        if self.last_position != expected_last:
            raise ValueError(
                f"last_position must be {expected_last} for {n} entries, "
                f"got {self.last_position}."
            )
        if self.is_empty != (n == 0):
            raise ValueError(
                f"is_empty must be {n == 0} for {n} entries, got {self.is_empty}."
            )
        return self
