# services/question_intelligence/sql_response_parser.py

import json
from typing import List

from pydantic import ValidationError

from services.question_intelligence.sql_question_generator import (
    GeneratedSQLQuestion,
)
from services.sql_engine.sql_database import SQLDatabase

from app.core.logger import get_logger

logger = get_logger(__name__)


class SQLResponseParser:
    """
    Parses and validates LLM JSON output for SQL questions.

    Responsibilities:
    - JSON deserialisation
    - Schema validation via GeneratedSQLQuestion pydantic model
    - SQL execution validation against the sandbox database
    """

    def __init__(self, db: SQLDatabase) -> None:
        self._db = db

    # ------------------------------------------------------------------
    # PUBLIC
    # ------------------------------------------------------------------

    def parse(self, content: str) -> List[GeneratedSQLQuestion]:
        """Parse raw LLM text into validated GeneratedSQLQuestion objects."""

        try:
            raw_data = json.loads(content)
        except Exception as e:
            raise ValueError(f"Invalid JSON from LLM: {e}") from e

        if not isinstance(raw_data, list):
            raise ValueError("LLM response must be a JSON array")

        validated_items: List[GeneratedSQLQuestion] = []

        for item in raw_data:
            try:
                validated = GeneratedSQLQuestion.model_validate(item)

                if not validated.test_cases:
                    raise ValueError("SQL question must include at least one test case")

                validated_items.append(validated)

            except (ValidationError, ValueError) as e:
                raise ValueError(f"Invalid SQL question structure: {e}") from e

        return validated_items

    def filter_executable(
        self,
        items: List[GeneratedSQLQuestion],
    ) -> List[GeneratedSQLQuestion]:
        """Retain only items whose SQL queries execute without error on the sandbox."""

        executable: List[GeneratedSQLQuestion] = []
        errors: List[str] = []

        for item in items:
            try:
                conn = self._db.get_fresh_connection()
                cursor = conn.cursor()
                cursor.execute(item.reference_query)
                for test_case in item.test_cases:
                    cursor.execute(test_case.expected_query)
                executable.append(item)
            except Exception as e:
                logger.warning("Invalid generated SQL: %s", e)
                errors.append(str(e))

        if not executable and errors:
            raise ValueError(
                f"All {len(items)} generated SQL item(s) failed execution validation. "
                f"Errors: {'; '.join(errors[:3])}. "
                f"Ensure queries use only valid columns: "
                f"employees(id,name,department_id,salary), "
                f"departments(id,name), projects(id,name,budget), "
                f"employee_projects(employee_id,project_id)."
            )

        return executable
