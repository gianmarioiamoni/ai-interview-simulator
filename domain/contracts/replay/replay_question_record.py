# domain/contracts/replay/replay_question_record.py
# EPIC-03 Phase 2c — ReplayQuestionRecord: per-question replay projection artifact.
# Field specification per EPIC-03-DATA-MODEL.md §4 (RG-03 resolution applied).

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, model_validator


class ReplayQuestionRecord(BaseModel, frozen=True, extra="forbid"):
    """Per-question data record embedded in ReplaySession.question_results.

    Replay-layer projection of QuestionResultRecord — stripped of persistence
    artifacts (schema_version). candidate_answer is sourced from TranscriptEntry
    (joined by question_id), not directly from QuestionResultRecord.

    Validators V-RQR-01 through V-RQR-04 per EPIC-03-DOMAIN-CONTRACTS.md §2.4.
    """

    question_id: str = Field(..., min_length=1)
    question_index: int = Field(..., ge=0)
    question_type: str = Field(..., min_length=1)
    area_label: str = Field(..., min_length=1)
    question_prompt: str = Field(..., min_length=1)
    candidate_answer: str = ""
    score: float = Field(..., ge=0.0, le=100.0)
    max_score: float = Field(..., gt=0.0)
    feedback: str = Field(..., min_length=1)
    strengths: tuple[str, ...] = Field(default_factory=tuple)
    weaknesses: tuple[str, ...] = Field(default_factory=tuple)
    follow_up_question: Optional[str] = None
    execution_status: Optional[str] = None
    passed_tests: Optional[int] = Field(default=None, ge=0)
    total_tests: Optional[int] = Field(default=None, gt=0)
    ai_hint_explanation: Optional[str] = None
    ai_hint_suggestion: Optional[str] = None
    attempts: int = Field(..., ge=1)

    # ------------------------------------------------------------------
    # Model validators
    # ------------------------------------------------------------------

    @model_validator(mode="after")
    def _validate_v_rqr_01(self) -> ReplayQuestionRecord:
        """V-RQR-01: max_score > 0.0 (enforced by Field gt=0.0; verified here for explicitness)."""
        if self.max_score <= 0.0:
            raise ValueError("V-RQR-01: max_score must be > 0.0.")
        return self

    @model_validator(mode="after")
    def _validate_v_rqr_02(self) -> ReplayQuestionRecord:
        """V-RQR-02: score >= 0.0 and score <= max_score."""
        if self.score > self.max_score:
            raise ValueError(
                f"V-RQR-02: score ({self.score}) must not exceed max_score ({self.max_score})."
            )
        return self

    @model_validator(mode="after")
    def _validate_v_rqr_04(self) -> ReplayQuestionRecord:
        """V-RQR-04: passed_tests, total_tests, execution_status are co-present for coding questions."""
        coding_fields = (self.passed_tests, self.total_tests, self.execution_status)
        none_count = sum(1 for f in coding_fields if f is None)
        if none_count not in (0, 3):
            raise ValueError(
                "V-RQR-04: passed_tests, total_tests, and execution_status must all be "
                "present or all be None (coding question co-presence invariant)."
            )
        return self

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def is_coding_question(self) -> bool:
        return self.execution_status is not None

    @property
    def has_hint(self) -> bool:
        return self.ai_hint_explanation is not None

    @property
    def score_ratio(self) -> float:
        return self.score / self.max_score
