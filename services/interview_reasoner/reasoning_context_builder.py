# services/interview_reasoner/reasoning_context_builder.py
"""ReasoningContextBuilder — sole constructor of ReasonerInput from InterviewState.

The graph (and ReasonerNode) call only `ReasoningContextBuilder.build(state)`.
They never construct ReasonerInput directly (ADR-038, TDS §17.2).

Responsibilities:
- Extract all fields needed by ReasonerInput from InterviewState.
- Apply default values for optional fields.
- Validate preconditions; raise dedicated exceptions on failure.
- Sanitize current_answer_content (max 2000 chars, control chars stripped).

Completely deterministic. No LLM calls. No side effects.
"""

from __future__ import annotations

import re

from domain.contracts.interview_state import InterviewState
from domain.contracts.reasoning.reasoner_input import ReasonerInput
from infrastructure.config.settings import settings as _settings


def _get_settings():
    return _settings
from services.interview_reasoner.context_builder_errors import (
    IncoherentQuestionHistoryError,
    InvalidEvidenceStoreError,
    MissingCandidateProfileError,
    MissingInterviewMemoryError,
)

_MAX_ANSWER_CHARS = 2000
_CONTROL_CHAR_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


class ReasoningContextBuilder:
    """Builds a ReasonerInput snapshot from an InterviewState.

    Usage::

        builder = ReasoningContextBuilder()
        reasoner_input = builder.build(state)
    """

    def build(self, state: InterviewState) -> ReasonerInput:
        """Construct and return an immutable ReasonerInput.

        Raises:
            MissingInterviewMemoryError: if interview_memory is missing.
            IncoherentQuestionHistoryError: if asked_question_ids > len(questions).
            MissingCandidateProfileError: if candidate_profile is inaccessible.
            InvalidEvidenceStoreError: if evidence_store has a negative signal count.
        """
        self._validate(state)

        settings = _get_settings()
        memory = state.interview_memory

        current_area = self._extract_current_area(state)
        current_type = self._extract_current_type(state)
        answer_content = self._extract_answer_content(state)
        feedback_quality = self._extract_feedback_quality(state)
        dimension_signals = self._extract_dimension_signals(state)
        evaluation_score = self._extract_evaluation_score(state)

        return ReasonerInput(
            session_id=state.interview_id,
            question_index=state.current_question_index,
            interview_memory=memory,
            candidate_profile_v2=state.candidate_profile_v2,
            current_question_area=current_area,
            current_question_type=current_type,
            current_answer_content=answer_content,
            current_feedback_quality=feedback_quality,
            current_dimension_signals=dimension_signals,
            current_evaluation_score=evaluation_score,
            max_follow_ups=settings.max_follow_ups_per_interview,
            follow_up_count=state.follow_up_count,
            follow_up_eligible_indices=state.follow_up_eligible_indices,
            questions_remaining=self._questions_remaining(state),
            role=self._role_name(state),
            seniority=state.seniority_level,
            interview_type=state.interview_type.value,
        )

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def _validate(self, state: InterviewState) -> None:
        # 1. InterviewMemory present
        if state.interview_memory is None:
            raise MissingInterviewMemoryError()

        # 2. Question history coherent
        n_asked = len(state.asked_question_ids)
        n_available = len(state.questions)
        if n_asked > n_available:
            raise IncoherentQuestionHistoryError(n_asked, n_available)

        # 3. CandidateProfile accessible
        try:
            _ = state.interview_memory.candidate_profile
        except AttributeError:
            raise MissingCandidateProfileError()

        # 4. EvidenceStore valid
        try:
            count = len(state.interview_memory.evidence_store.signals)
        except AttributeError:
            raise InvalidEvidenceStoreError("evidence_store is inaccessible")
        if count < 0:
            raise InvalidEvidenceStoreError(f"signal count is negative: {count}")

    # ------------------------------------------------------------------
    # Field extractors
    # ------------------------------------------------------------------

    def _extract_current_area(self, state: InterviewState) -> str | None:
        if state.last_question_context is not None:
            return state.last_question_context.question_area
        q = self._current_question(state)
        if q is not None:
            area = getattr(q, "area", None)
            if area is not None:
                return str(area.value) if hasattr(area, "value") else str(area)
        return None

    def _extract_current_type(self, state: InterviewState) -> str | None:
        if state.last_question_context is not None:
            qt = state.last_question_context.question_type
            return qt.value if hasattr(qt, "value") else str(qt)
        q = self._current_question(state)
        if q is not None:
            qt = getattr(q, "type", None)
            if qt is not None:
                return qt.value if hasattr(qt, "value") else str(qt)
        return None

    def _extract_answer_content(self, state: InterviewState) -> str | None:
        if state.last_question_context is not None:
            raw = state.last_question_context.answer_content
        else:
            raw = self._last_answer_content(state)

        if raw is None:
            return None
        sanitized = _CONTROL_CHAR_RE.sub("", raw)
        return sanitized[:_MAX_ANSWER_CHARS]

    def _extract_feedback_quality(self, state: InterviewState) -> str | None:
        if state.last_feedback_bundle is None:
            return None
        quality = state.last_feedback_bundle.overall_quality
        return quality.value if hasattr(quality, "value") else str(quality)

    def _extract_dimension_signals(self, state: InterviewState) -> dict[str, float]:
        return {
            dim.value if hasattr(dim, "value") else str(dim): float(score)
            for dim, score in state.dimension_signals.items()
        }

    def _extract_evaluation_score(self, state: InterviewState) -> float | None:
        if not state.asked_question_ids:
            return None
        last_qid = state.asked_question_ids[-1]
        result = state.results_by_question.get(last_qid)
        if result is None or result.evaluation is None:
            return None
        score = result.evaluation.score
        return float(max(0.0, min(100.0, score)))

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _current_question(self, state: InterviewState):
        idx = state.current_question_index
        if 0 <= idx < len(state.questions):
            return state.questions[idx]
        return None

    def _last_answer_content(self, state: InterviewState) -> str | None:
        if not state.answers:
            return None
        return getattr(state.answers[-1], "content", None)

    def _questions_remaining(self, state: InterviewState) -> int:
        total = len(state.questions)
        answered = len(state.asked_question_ids)
        return max(0, total - answered)

    @staticmethod
    def _role_name(state: InterviewState) -> str:
        role = state.role
        role_type = getattr(role, "type", None)
        if role_type is not None:
            return role_type.value if hasattr(role_type, "value") else str(role_type)
        return str(role)
