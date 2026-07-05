# domain/contracts/report/question_assessment_record.py
# EPIC-V13-01 Phase 8 — QuestionAssessmentRecord (Report-layer projection of QuestionResultRecord)
# EPIC-01-DOMAIN-CONTRACTS §4. ADR-033.

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


class QuestionAssessmentRecord(BaseModel):
    """Report-layer immutable projection of QuestionResultRecord.

    Assembled by ReportBuilder from SessionHistory.question_results.
    Carries exactly the fields needed to populate QuestionAssessmentDTO from Report alone.
    Field set is identical to QuestionResultRecord — no transformation at assembly time.

    Invariants (mirror V-QRR-01 through V-QRR-03):
    - V-QAR-01: len(report.question_assessments) == report.question_count (enforced in ReportBuilder)
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

    @model_validator(mode="after")
    def _validate_coding_test_pair(self) -> "QuestionAssessmentRecord":
        if (self.passed_tests is None) != (self.total_tests is None):
            raise ValueError(
                "passed_tests and total_tests must both be set or both be None (V-QRR-01)"
            )
        return self

    @model_validator(mode="after")
    def _validate_test_counts(self) -> "QuestionAssessmentRecord":
        if self.passed_tests is not None and self.total_tests is not None:
            if self.passed_tests > self.total_tests:
                raise ValueError(
                    f"passed_tests ({self.passed_tests}) must not exceed "
                    f"total_tests ({self.total_tests}) (V-QRR-02)"
                )
        return self

    @model_validator(mode="after")
    def _validate_hint_pair(self) -> "QuestionAssessmentRecord":
        if self.ai_hint_suggestion is not None and self.ai_hint_explanation is None:
            raise ValueError(
                "ai_hint_explanation must be set when ai_hint_suggestion is present (V-QRR-03)"
            )
        return self
