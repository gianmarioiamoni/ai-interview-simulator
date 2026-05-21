# services/retrieval/retrieval_session_memory.py

from collections import deque


class RetrievalSessionMemory:

    # =====================================================
    # CONSTRUCTOR
    # =====================================================

    def __init__(
        self,
        max_history: int = 50,
    ) -> None:

        self._history = deque(maxlen=max_history)

    # =====================================================
    # PUBLIC
    # =====================================================

    def remember(
        self,
        question: str,
    ) -> None:

        normalized = self._normalize(question)

        self._history.append(normalized)

    def has_seen(
        self,
        question: str,
    ) -> bool:

        normalized = self._normalize(question)

        return normalized in self._history

    def get_recent_questions(
        self,
    ) -> list[str]:

        return list(self._history)

    def clear(
        self,
    ) -> None:

        self._history.clear()

    # =====================================================
    # INTERNALS
    # =====================================================

    def _normalize(
        self,
        question: str,
    ) -> str:

        return question.strip().lower()
