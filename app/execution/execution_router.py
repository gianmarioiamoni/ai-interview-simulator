# app/execution/execution_router.py

from domain.contracts.question import Question, QuestionType
from domain.contracts.execution_result import ExecutionResult

from app.execution.python_executor import PythonExecutor
from app.execution.sql_executor import SQLExecutor


class ExecutionRouter:
    # Routes execution requests to the correct execution engine.

    def __init__(self):

        self._python_executor = PythonExecutor()
        self._sql_executor = SQLExecutor()

    def execute(
        self,
        question: Question,
        answer: str,
    ) -> ExecutionResult:

        if question.type == QuestionType.CODING:
            return self._python_executor.execute(question, answer)

        if question.type == QuestionType.DATABASE:
            return self._sql_executor.execute(question, answer)

        raise ValueError(
            f"ExecutionRouter cannot execute question type: {question.type}"
        )
