# services/question_intelligence/sql_question_generator.py

import json
import logging
import uuid
from typing import List
from pydantic import BaseModel, Field, ValidationError

from domain.contracts.question.question import (
    Question,
    QuestionType,
    QuestionDifficulty,
    SQLTestCase,
)
from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.user.role import RoleType
from domain.contracts.user.seniority_level import SeniorityLevel

from infrastructure.llm.llm_factory import get_llm

from services.sql_engine.sql_database import SQLDatabase
from services.sql_engine.schema_summary_generator import SchemaSummaryGenerator

logger = logging.getLogger(__name__)


# =========================================================
# DTOs (Structured Output)
# =========================================================


class GeneratedSQLTestCase(BaseModel):
    expected_query: str
    ordered: bool = True


class GeneratedSQLQuestion(BaseModel):
    prompt: str
    reference_query: str
    test_cases: List[GeneratedSQLTestCase] = Field(default_factory=list)


# =========================================================
# Generator
# =========================================================


class SQLQuestionGenerator:

    def __init__(self) -> None:
        self._llm = get_llm()
        self._schema_generator = SchemaSummaryGenerator()
        self._db = SQLDatabase()

    # -----------------------------------------------------

    def generate(
        self,
        role: RoleType,
        level: SeniorityLevel,
        n: int = 1,
    ) -> List[Question]:

        schema_summary = self._build_schema_summary()

        prompt = self._build_prompt(
            role=role.value,
            level=level.value,
            n=n,
            schema_summary=schema_summary,
        )

        response = self._llm.invoke(prompt)

        try:
            raw_data = json.loads(response.content)
        except Exception as e:
            raise ValueError(f"Invalid JSON from LLM: {e}")

        validated_items: List[GeneratedSQLQuestion] = []

        for item in raw_data:
            try:
                validated = GeneratedSQLQuestion.model_validate(item)

                if not validated.test_cases:
                    raise ValueError("SQL question must include at least one test case")

                validated_items.append(validated)

            except ValidationError as e:
                raise ValueError(f"Invalid SQL question structure: {e}")

        # -----------------------------------------------------
        # Mapping to domain Question
        # -----------------------------------------------------

        return [self._map_to_question(item) for item in validated_items]

    # =========================================================
    # INTERNALS
    # =========================================================

    def _build_schema_summary(self) -> str:

        db = self._db 
        conn = db.connection

        return self._schema_generator.generate(conn)

    # -----------------------------------------------------

    def _map_to_question(self, item: GeneratedSQLQuestion) -> Question:

        return Question(
            id=str(uuid.uuid4()),
            area=InterviewArea.TECH_DATABASE,
            type=QuestionType.DATABASE,
            prompt=item.prompt,
            difficulty=QuestionDifficulty.MEDIUM,
            # SQL core
            reference_solution=item.reference_query,
            expected_ordered=False,
            # IMPORTANT: use default DB (executor fallback)
            db_schema=self._db.get_schema_sql(),
            db_seed_data=self._db.get_seed_sql(),
            # Test cases
            sql_test_cases=[
                SQLTestCase(
                    id=f"tc_{i}",
                    expected_query=tc.expected_query,
                    ordered=False,
                )
                for i, tc in enumerate(item.test_cases)
            ],
        )

    # -----------------------------------------------------

    def _build_prompt(
        self,
        role: str,
        level: str,
        n: int,
        schema_summary: str,
    ) -> str:

        return f"""
You are a senior SQL interviewer.

Database schema:

{schema_summary}

Generate {n} SQL interview questions for a {level} {role}.

Each question MUST include:

1. A clear and unambiguous problem description
2. A correct reference SQL query
3. At least 2 test cases (query variations)

Return STRICT JSON array:

[
  {{
    "prompt": "...",
    "reference_query": "SELECT ...",
    "test_cases": [
      {{
        "expected_query": "...",
        "ordered": true
      }}
    ]
  }}
]

Rules:
- Use ONLY tables and columns from the schema
- Use SQLite-compatible SQL
- Queries MUST be executable
- Avoid ambiguous wording
- Do NOT generate schema or data
- No markdown
- Only valid JSON
- Test cases MUST validate the SAME problem.

- Do NOT change the business logic of the query
- Do NOT change filters (e.g. > 100000 must remain the same)
- Test cases should represent alternative but equivalent queries
- Variations can include:
  - different JOIN syntax
  - use of aliases
  - ordering differences
  - equivalent SQL constructs

IMPORTANT:
- Use EXACT table names from schema
- DO NOT invent tables
- DO NOT rename tables
- DO NOT assume columns

All test cases must return the SAME result as the reference query.
"""
