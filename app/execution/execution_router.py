# app/execution/execution_router.py

import logging

from domain.contracts.question import Question, QuestionType
from domain.contracts.execution_result import ExecutionResult

from app.execution.python_executor import PythonExecutor
from app.execution.sql_executor import SQLExecutor


logger = logging.getLogger(__name__)


class ExecutionRouter:

    def __init__(self):

        self._python_executor = PythonExecutor()
        self._sql_executor = SQLExecutor()

    def execute(
        self,
        question: Question,
        answer: str,
    ) -> ExecutionResult:

        logger.info(f"Routing execution for question {question.id}")

        if question.type == QuestionType.CODING:
            return self._python_executor.execute(question, answer)

        if question.type == QuestionType.DATABASE:
            return self._sql_executor.execute(question, answer)

        raise ValueError(
            f"ExecutionRouter cannot execute question type: {question.type}"
        )
