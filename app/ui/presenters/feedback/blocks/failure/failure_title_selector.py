# app/ui/presenters/feedback/blocks/failure/failure_title_selector.py

from domain.contracts.feedback.error_type import ErrorType

_TITLE_MAP: dict[ErrorType, tuple[str, str]] = {
    ErrorType.LOGIC: (
        "Logic Errors Detected",
        "Your solution produces incorrect results.",
    ),
    ErrorType.RUNTIME: (
        "Runtime Errors in Tests",
        "Your code fails during execution for some inputs.",
    ),
}

_DEFAULT_TITLE = "Test Failures Detected"
_DEFAULT_MESSAGE = "Some test cases failed."


class FailureTitleSelector:
    """Maps error_type to (title, message) pair. Stateless."""

    def select(self, error_type: ErrorType) -> tuple[str, str]:
        return _TITLE_MAP.get(error_type, (_DEFAULT_TITLE, _DEFAULT_MESSAGE))
