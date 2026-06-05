# services/question_intelligence/performance_responsive_candidate_selector.py

from services.question_corpus.contracts.adaptive_retrieval_context import (
    AdaptiveRetrievalContext,
)
from services.question_corpus.contracts.retrieval_candidate import RetrievalCandidate
from services.planning.difficulty_spike_suppressor import DifficultySpikeSuppressor


class PerformanceResponsiveCandidateSelector:

    def __init__(
        self,
        spike_suppressor: DifficultySpikeSuppressor | None = None,
        max_allowed_jump: int = 2,
    ) -> None:

        self._max_allowed_jump = max_allowed_jump
        self._spike_suppressor = (
            spike_suppressor
            if spike_suppressor is not None
            else DifficultySpikeSuppressor(max_allowed_jump=max_allowed_jump)
        )

    # =====================================================
    # PUBLIC
    # =====================================================

    def select(
        self,
        pool: list[RetrievalCandidate],
        context: AdaptiveRetrievalContext,
    ) -> list[RetrievalCandidate]:

        if not pool:
            return []

        count = context.target_question_count

        if len(pool) == 1:
            return pool[:count]

        target = context.target_difficulty

        if target is None:
            return pool[:count]

        rank_index = {id(candidate): index for index, candidate in enumerate(pool)}
        selected: list[RetrievalCandidate] = []
        remaining = list(pool)
        selected_difficulties: list[int] = []

        for _ in range(min(count, len(pool))):
            pick = self._pick_best(
                remaining=remaining,
                target=target,
                selected_difficulties=selected_difficulties,
                context=context,
                rank_index=rank_index,
            )

            if pick is None:
                pick = remaining[0]

            selected.append(pick)
            remaining.remove(pick)

            difficulty = self._candidate_difficulty(pick)

            if difficulty is not None:
                selected_difficulties.append(difficulty)

        return selected

    def prioritize(
        self,
        pool: list[RetrievalCandidate],
        context: AdaptiveRetrievalContext,
    ) -> list[RetrievalCandidate]:

        if len(pool) <= 1:
            return list(pool)

        target = context.target_difficulty

        if target is None:
            return list(pool)

        previous = self._previous_difficulty([], context)

        indexed = list(enumerate(pool))
        indexed.sort(
            key=lambda pair: self._sort_key(
                candidate=pair[1],
                rank=pair[0],
                target=target,
                previous_difficulty=previous,
            ),
        )

        return [candidate for _, candidate in indexed]

    # =====================================================
    # INTERNALS
    # =====================================================

    def _pick_best(
        self,
        remaining: list[RetrievalCandidate],
        target: int,
        selected_difficulties: list[int],
        context: AdaptiveRetrievalContext,
        rank_index: dict[int, int],
    ) -> RetrievalCandidate | None:

        viable = [
            candidate
            for candidate in remaining
            if self._candidate_difficulty(candidate) is not None
        ]

        if not viable:
            return None

        previous = self._previous_difficulty(selected_difficulties, context)

        viable.sort(
            key=lambda candidate: self._sort_key(
                candidate=candidate,
                rank=rank_index[id(candidate)],
                target=target,
                previous_difficulty=previous,
            ),
        )

        return viable[0]

    def _sort_key(
        self,
        candidate: RetrievalCandidate,
        rank: int,
        target: int,
        previous_difficulty: int | None,
    ) -> tuple[int, int, int]:

        difficulty = self._candidate_difficulty(candidate)

        if difficulty is None:
            return (999, 1, rank)

        target_distance = abs(difficulty - target)
        jump = (
            abs(difficulty - previous_difficulty)
            if previous_difficulty is not None
            else 0
        )
        spike = 0 if jump <= self._max_allowed_jump else 1

        return (target_distance, spike, rank)

    def _previous_difficulty(
        self,
        selected_difficulties: list[int],
        context: AdaptiveRetrievalContext,
    ) -> int | None:

        if selected_difficulties:
            return selected_difficulties[-1]

        history = context.memory.difficulty_history

        if history:
            return history[-1]

        return None

    def _candidate_difficulty(
        self,
        candidate: RetrievalCandidate,
    ) -> int | None:

        raw = candidate.document.metadata.get("difficulty")

        try:
            return int(raw)
        except (TypeError, ValueError):
            return None
