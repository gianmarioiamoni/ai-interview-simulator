# app/ui/replay/panels/replay_question_panel.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.ui.replay.panels.replay_execution_result_panel import (
    ExecutionResultViewModel,
    ReplayExecutionResultPanel,
)
from domain.contracts.replay.replay_question_record import ReplayQuestionRecord


@dataclass(frozen=True)
class QuestionViewModel:
    """C-05 rendering model (EPIC-04-DATA-MODEL §4.5)."""

    question_index: int
    question_type: str
    area_label: str
    question_prompt: str
    candidate_answer: str
    answer_display: str
    score: float
    max_score: float
    score_pct: float
    feedback: str
    strengths: tuple[str, ...]
    weaknesses: tuple[str, ...]
    follow_up_question: Optional[str]
    has_hint: bool
    ai_hint_explanation: Optional[str]
    ai_hint_suggestion: Optional[str]
    attempts: int
    is_coding_question: bool
    execution_result: Optional[ExecutionResultViewModel]


class ReplayQuestionPanel:
    """C-05: per-question view; delegates coding execution to C-06."""

    NO_ANSWER_LABEL = "No answer recorded"

    def __init__(self, record: ReplayQuestionRecord) -> None:
        self._record = record

    def render(self) -> QuestionViewModel:
        record = self._record
        answer = record.candidate_answer
        answer_display = answer if answer else self.NO_ANSWER_LABEL

        strengths = record.strengths if record.strengths else ()
        weaknesses = record.weaknesses if record.weaknesses else ()

        execution_result: Optional[ExecutionResultViewModel] = None
        if record.is_coding_question:
            execution_result = ReplayExecutionResultPanel(record).render()

        return QuestionViewModel(
            question_index=record.question_index,
            question_type=record.question_type,
            area_label=record.area_label,
            question_prompt=record.question_prompt,
            candidate_answer=answer,
            answer_display=answer_display,
            score=record.score,
            max_score=record.max_score,
            score_pct=record.score_ratio * 100.0,
            feedback=record.feedback,
            strengths=strengths,
            weaknesses=weaknesses,
            follow_up_question=record.follow_up_question,
            has_hint=record.has_hint,
            ai_hint_explanation=record.ai_hint_explanation,
            ai_hint_suggestion=record.ai_hint_suggestion,
            attempts=record.attempts,
            is_coding_question=record.is_coding_question,
            execution_result=execution_result,
        )
