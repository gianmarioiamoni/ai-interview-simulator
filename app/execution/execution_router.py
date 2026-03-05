# app/execution/execution_router.py

from domain.contracts.question import QuestionType

from app.execution.python_executor import PythonExecutor
from app.execution.sql_executor import SQLExecutor


class ExecutionRouter:
    # Routes execution requests to the correct execution engine.

    def __init__(self):

        self.python_executor = PythonExecutor()
        self.sql_executor = SQLExecutor()

    def execute(self, question_type, answer):

        if question_type == QuestionType.CODING:

            return self.python_executor.execute(answer)

        if question_type == QuestionType.DATABASE:

            return self.sql_executor.execute(answer)

        raise ValueError(f"Unsupported execution type: {question_type}")
