# services/question_intelligence/cross_interview_pick_tracker.py

"""
Encapsulates the cross-interview pick-count state previously held in the
module-level `_CROSS_INTERVIEW_PICK_COUNTS` dict.

The tracker exposes a read-only `counts` property that returns the live
internal dict. This allows callers that previously held a direct reference
to the module-level dict (e.g. tests) to continue reading and writing
through the same dict object without any code changes.
"""


class CrossInterviewPickTracker:
    """
    Tracks how many times each document has been selected as the first question
    across different interview sessions.

    Used by the canonical fresh-start selection path to rotate picks across
    interviews so that no single document is always chosen first.
    """

    def __init__(self) -> None:
        self._counts: dict[str, int] = {}

    # ------------------------------------------------------------------
    # READ
    # ------------------------------------------------------------------

    def get(self, doc_id: str) -> int:
        """Return the pick count for doc_id (0 if never picked)."""
        return self._counts.get(doc_id, 0)

    @property
    def counts(self) -> dict[str, int]:
        """
        Live reference to the internal counts dict.

        Exposing the live dict (not a copy) preserves the behavior of any
        external code that holds a reference to the same object and reads or
        writes it directly — specifically the compat alias
        `_CROSS_INTERVIEW_PICK_COUNTS` in constrained_equivalence_band.py.
        """
        return self._counts

    def snapshot(self) -> dict[str, int]:
        """Return a shallow copy of the current counts (safe to inspect)."""
        return dict(self._counts)

    # ------------------------------------------------------------------
    # WRITE
    # ------------------------------------------------------------------

    def increment(self, doc_id: str) -> None:
        """Increment the pick count for doc_id by 1."""
        self._counts[doc_id] = self._counts.get(doc_id, 0) + 1

    def reset(self) -> None:
        """Clear all pick counts (equivalent to the former reset_cross_interview_pick_counts())."""
        self._counts.clear()
