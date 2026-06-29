# services/humanizer/follow_up/follow_up_parse_error.py

from __future__ import annotations


class FollowUpParseError(Exception):
    """Raised by FollowUpParser on any contract violation.

    ADR-019: STRICT parser — no silent failures, no partial parsing.
    """

    def __init__(self, reason: str, raw: str = "") -> None:
        super().__init__(reason)
        self.reason = reason
        self.raw = raw
