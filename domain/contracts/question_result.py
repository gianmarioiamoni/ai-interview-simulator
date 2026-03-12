# domain/contracts/question_result.py

from typing import Optional
from pydantic import BaseModel

from domain.contracts.execution_result import ExecutionResult
from domain.contracts.question_evaluation import QuestionEvaluation


class QuestionResult(BaseModel):

    question_id: str

    evaluation: Optional[QuestionEvaluation] = None

    execution: Optional[ExecutionResult] = None
