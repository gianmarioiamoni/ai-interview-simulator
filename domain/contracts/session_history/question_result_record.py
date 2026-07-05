# domain/contracts/session_history/question_result_record.py

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


class QuestionResultRecord(BaseModel):
    """Immutable closure-time persistence record for a single question result.

    Captured by session_close_node from live InterviewState. Sole persistence
    form of QuestionResult — the live runtime artifact is not persisted.

    question_prompt stores the full question text; truncation is a display
    concern and must never be applied at persistence time (R-15).
    """

    model_config = {"frozen": True, "extra": "forbid"}

    question_id: str = Field(min_length=1)
    question_index: int = Field(ge=0)
    question_type: str = Field(min_length=1)
    area_label: str = Field(min_length=1)
    question_prompt: str = Field(min_length=1)

    score: float = Field(ge=0.0, le=100.0)
    max_score: float = Field(gt=0.0)
    feedback: str = Field(min_length=1)
    strengths: tuple[str, ...] = Field(default_factory=tuple)
    weaknesses: tuple[str, ...] = Field(default_factory=tuple)
    follow_up_question: str | None = None

    # Coding-only fields
    passed_tests: int | None = Field(default=None, ge=0)
    total_tests: int | None = Field(default=None, gt=0)
    execution_status: str | None = None

    attempts: int = Field(ge=1)

    ai_hint_explanation: str | None = None
    ai_hint_suggestion: str | None = None

    schema_version: str = Field(default="1.0", min_length=1)

    # ------------------------------------------------------------------
    # Invariants
    # ------------------------------------------------------------------

    @model_validator(mode="after")
    def _validate_coding_test_pair(self) -> "QuestionResultRecord":
        # V-QRR-01: passed_tests and total_tests must both be present or both None
        if (self.passed_tests is None) != (self.total_tests is None):
            raise ValueError(
                "passed_tests and total_tests must both be set or both be None (V-QRR-01)"
            )
        return self

    @model_validator(mode="after")
    def _validate_test_counts(self) -> "QuestionResultRecord":
        # V-QRR-02: passed_tests <= total_tests
        if self.passed_tests is not None and self.total_tests is not None:
            if self.passed_tests > self.total_tests:
                raise ValueError(
                    f"passed_tests ({self.passed_tests}) must not exceed "
                    f"total_tests ({self.total_tests}) (V-QRR-02)"
                )
        return self

    @model_validator(mode="after")
    def _validate_hint_pair(self) -> "QuestionResultRecord":
        # V-QRR-03: if ai_hint_suggestion is set, ai_hint_explanation must also be set
        if self.ai_hint_suggestion is not None and self.ai_hint_explanation is None:
            raise ValueError(
                "ai_hint_explanation must be set when ai_hint_suggestion is present (V-QRR-03)"
            )
        return self
