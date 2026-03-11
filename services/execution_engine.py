# services/execution_engine.py

from domain.contracts.question import QuestionType
from domain.contracts.question import Question
from domain.contracts.execution_result import ExecutionResult

from services.coding_engine.coding_executor import CodingExecutor
from services.sql_engine.sql_executor import SQLExecutor


class ExecutionEngine:

    def __init__(self):

        self._coding_executor = CodingExecutor()
        self._sql_executor = SQLExecutor()

    def execute(
        self,
        question: Question,
        user_answer: str,
    ) -> ExecutionResult:

        if question.type == QuestionType.CODING:

            return self._coding_executor.execute(
                question,
                user_answer,
            )

        if question.type == QuestionType.DATABASE:

            return self._sql_executor.execute(
                question,
                user_answer,
            )

        raise ValueError(f"Unsupported execution type: {question.type}")
