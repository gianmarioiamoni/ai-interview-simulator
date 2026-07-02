# domain/contracts/coaching/future_action_backlog.py
# FutureActionBacklog — ordered queue of deferred CoachingActions (ADR-025)

from __future__ import annotations

from pydantic import BaseModel, Field

from domain.contracts.coaching.coaching_action import CoachingAction


class FutureActionBacklog(BaseModel):
    """Immutable, ordered backlog of CoachingActions deferred beyond the current session.

    Invariants (ADR-025):
    - Immutable after construction.
    - Actions are ordered by insertion order; priority is expressed via
      CoachingAction.is_immediate and LearningObjective.priority.
    - No mutation of CandidateProfile.
    - No replay capability.
    """

    actions: tuple[CoachingAction, ...] = Field(default_factory=tuple)
    session_id: str = Field(..., min_length=1)
    candidate_identity_id: str = Field(..., min_length=1)
    created_at_question_index: int = Field(..., ge=0)

    model_config = {"frozen": True, "extra": "forbid"}

    @property
    def size(self) -> int:
        return len(self.actions)

    @property
    def is_empty(self) -> bool:
        return len(self.actions) == 0

    def immediate_actions(self) -> tuple[CoachingAction, ...]:
        return tuple(a for a in self.actions if a.is_immediate)

    def deferred_actions(self) -> tuple[CoachingAction, ...]:
        return tuple(a for a in self.actions if not a.is_immediate)

    def by_objective(self, objective_id: str) -> tuple[CoachingAction, ...]:
        return tuple(a for a in self.actions if a.objective_id == objective_id)

    def by_category(self, category: str) -> tuple[CoachingAction, ...]:
        return tuple(a for a in self.actions if a.category.value == category)

    def with_action(self, action: CoachingAction) -> "FutureActionBacklog":
        """Return a new backlog with action appended (immutable append)."""
        return FutureActionBacklog(
            actions=self.actions + (action,),
            session_id=self.session_id,
            candidate_identity_id=self.candidate_identity_id,
            created_at_question_index=self.created_at_question_index,
        )
