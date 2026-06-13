# services/question_intelligence/equivalence_band_scoring.py

"""
Pure scoring helpers for ConstrainedEquivalenceBand.

All functions here are stateless and side-effect-free. They accept only their
immediate inputs — no global state, no module-level mutable structures.
"""

import hashlib

from services.question_corpus.contracts.adaptive_retrieval_context import (
    AdaptiveRetrievalContext,
)
from services.question_corpus.contracts.retrieval_candidate import RetrievalCandidate


def candidate_score(candidate: RetrievalCandidate) -> float:
    """Return the best available score for a retrieval candidate."""
    return float(candidate.adaptive_score or candidate.final_score)


def candidate_difficulty(candidate: RetrievalCandidate) -> int | None:
    """Extract the integer difficulty from candidate metadata; return None if absent."""
    raw = candidate.document.metadata.get("difficulty")
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def score_floor(best_score: float, band_pct: float) -> float:
    """Return the minimum score a candidate must exceed to be within the equivalence band."""
    margin = max(0.01, best_score * band_pct)
    return best_score - margin


def adaptive_tier(
    candidate: RetrievalCandidate,
    target: int,
    previous_difficulty: int | None,
    max_allowed_jump: int,
) -> tuple[int, int]:
    """
    Return a (target_distance, spike) tuple that encodes how well a candidate
    matches the desired difficulty target without producing a jarring difficulty jump.

    target_distance — |candidate.difficulty − target|; lower is better
    spike          — 1 if the jump from previous_difficulty exceeds max_allowed_jump
    """
    difficulty = candidate_difficulty(candidate)

    if difficulty is None:
        return (999, 1)

    target_distance = abs(difficulty - target)
    jump = abs(difficulty - previous_difficulty) if previous_difficulty is not None else 0
    spike = 0 if jump <= max_allowed_jump else 1

    return (target_distance, spike)


def historical_usage_ids(context: AdaptiveRetrievalContext) -> set[str]:
    """Return the union of all question IDs used in the current session and prior interviews."""
    return {
        *context.memory.asked_question_ids,
        *context.already_used_question_ids,
    }


def rotation_index(seed: str, size: int) -> int:
    """
    Derive a deterministic index in [0, size) from an arbitrary seed string via SHA-256.

    The same seed always produces the same index, ensuring reproducible rotation
    across runs with identical role/level/theme/query inputs.
    """
    digest = hashlib.sha256(seed.encode()).hexdigest()
    return int(digest[:12], 16) % size
