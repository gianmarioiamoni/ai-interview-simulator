# domain/contracts/question_result.py

from typing import Optional
from pydantic import BaseModel

from domain.contracts.question.question import Question
from domain.contracts.question.question_evaluation import QuestionEvaluation
from domain.contracts.execution.execution_result import ExecutionResult
from domain.contracts.ai.ai_hint import AIHint
from domain.contracts.ai.hint_level import HintLevel


class QuestionResult(BaseModel):
    question_id: str

    question: Optional[Question] = None

    evaluation: Optional[QuestionEvaluation] = None
    execution: Optional[ExecutionResult] = None

    ai_hint: Optional[AIHint] = None
    hint_level: Optional[HintLevel] = None
