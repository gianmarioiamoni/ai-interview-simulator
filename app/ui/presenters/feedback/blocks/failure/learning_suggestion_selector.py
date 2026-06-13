# app/ui/presenters/feedback/blocks/failure/learning_suggestion_selector.py

from app.contracts.feedback_bundle import LearningSuggestion
from domain.contracts.feedback.error_type import ErrorType

_RUNTIME_SUGGESTION = LearningSuggestion(
    topic="Runtime debugging",
    action="Validate input types and ensure safe access to data structures",
)

_LOGIC_EDGE_SUGGESTION = LearningSuggestion(
    topic="Edge cases",
    action="Review how your solution handles boundary inputs (empty, single values, zero)",
)

_LOGIC_CORE_SUGGESTION = LearningSuggestion(
    topic="Algorithm correctness",
    action="Check your core logic and verify intermediate steps",
)

_DEFAULT_SUGGESTION = LearningSuggestion(
    topic="Debugging",
    action="Analyze failing test cases step-by-step",
)


class LearningSuggestionSelector:
    """
    Selects the appropriate learning suggestion based on error type and
    whether an edge-case pattern was detected. Stateless.
    """

    def select(self, error_type: ErrorType, is_edge_case: bool) -> list[LearningSuggestion]:
        if error_type == ErrorType.RUNTIME:
            return [_RUNTIME_SUGGESTION]

        if error_type == ErrorType.LOGIC:
            suggestion = _LOGIC_EDGE_SUGGESTION if is_edge_case else _LOGIC_CORE_SUGGESTION
            return [suggestion]

        return [_DEFAULT_SUGGESTION]
