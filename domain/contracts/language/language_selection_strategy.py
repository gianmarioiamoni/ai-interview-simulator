# domain/contracts/language/language_selection_strategy.py

from enum import Enum


class LanguageSelectionStrategy(str, Enum):
    """Algorithm used to assign a programming language to each coding question
    in a mixed-mode session (ADR-019 Section E, ADR-028).

    Only DETERMINISTIC_ALTERNATING is active in V1.2. All others are
    reserved extension points for future versions — no domain redesign required.
    """

    # V1.2 active — strict 50/50 alternation; deterministic for a given session
    DETERMINISTIC_ALTERNATING = "deterministic_alternating"

    # Reserved V1.3+ — probabilistic selection with configurable weights
    WEIGHTED_RANDOM = "weighted_random"

    # Reserved V1.3+ — candidate selects language per question
    CANDIDATE_PREFERENCE = "candidate_preference"

    # Reserved V1.3+ — adapts selection based on performance signals
    ADAPTIVE = "adaptive"
