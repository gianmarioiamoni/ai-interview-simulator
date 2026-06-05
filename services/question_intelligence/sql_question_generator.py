# services/question_intelligence/sql_question_generator.py

import json
import uuid
from typing import List

from pydantic import BaseModel, Field, ValidationError

from domain.contracts.question.question import (
    Question,
    QuestionType,
    QuestionDifficulty,
    SQLTestCase,
)
from domain.contracts.question.question_provenance import QuestionProvenance
from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.user.role import RoleType
from domain.contracts.user.seniority_level import SeniorityLevel

from app.ports.llm_port import LLMPort

from services.sql_engine.sql_database import SQLDatabase

from app.core.logger import get_logger

logger = get_logger(__name__)

_SANDBOX_TABLES = (
    "employees, departments, projects, employee_projects"
)

_SANDBOX_EXECUTION_RULES = f"""
EXECUTION CONSTRAINTS (mandatory):
- reference_query and every test case expected_query MUST be a single SELECT only
- Use ONLY sandbox tables: {_SANDBOX_TABLES}
- Use ONLY columns that exist on those tables in the provided schema
- Use SQLite-compatible SQL (not PostgreSQL-specific syntax)
- Do NOT use CREATE, ALTER, DROP, VIEW, TRIGGER, or any DDL
- Do NOT use INSERT, UPDATE, DELETE, or multi-statement SQL (no semicolon-separated statements)
- Do NOT invent tables, views, or column names
"""


# =========================================================
# DTOs
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

    def __init__(self, llm: LLMPort) -> None:
        self._llm = llm
        self._db = SQLDatabase()

    # -----------------------------------------------------

    def generate(
        self,
        role: RoleType,
        level: SeniorityLevel,
        n: int = 1,
        theme_guidance: str | None = None,
    ) -> List[Question]:

        schema_summary = self._build_schema_summary()

        prompt = self._build_generation_prompt(
            role=role.value,
            level=level.value,
            n=n,
            schema_summary=schema_summary,
            theme_guidance=theme_guidance,
        )

        response = self._llm.invoke(prompt)

        try:
            validated_items = self._parse_llm_response(response.content)
        except ValueError as e:
            raise ValueError(str(e)) from e

        executable_items = self._filter_executable_items(validated_items)

        return [
            self._map_to_question(item)
            for item in executable_items
        ]

    # -----------------------------------------------------

    def enrich_from_prompt(
        self,
        seed_prompt: str,
        role: RoleType,
        level: SeniorityLevel,
        provenance: QuestionProvenance | None = None,
        theme_guidance: str | None = None,
    ) -> Question | None:

        schema_summary = self._build_schema_summary()

        prompt = self._build_enrichment_prompt(
            seed_prompt=seed_prompt,
            role=role.value,
            level=level.value,
            schema_summary=schema_summary,
            theme_guidance=theme_guidance,
        )

        try:
            response = self._llm.invoke(prompt)
            validated_items = self._parse_llm_response(response.content)
        except (ValueError, Exception) as e:
            logger.warning(f"[SQL enrich] Failed to parse enrichment response: {e}")
            return None

        executable_items = self._filter_executable_items(validated_items)

        if not executable_items:
            logger.warning("[SQL enrich] No executable SQL after enrichment validation")
            return None

        return self._map_to_question(
            executable_items[0],
            provenance=provenance,
        )

    # =========================================================
    # INTERNALS
    # =========================================================

    def _parse_llm_response(
        self,
        content: str,
    ) -> List[GeneratedSQLQuestion]:

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

    def _filter_executable_items(
        self,
        items: List[GeneratedSQLQuestion],
    ) -> List[GeneratedSQLQuestion]:

        executable: List[GeneratedSQLQuestion] = []

        for item in items:
            try:
                conn = self._db.get_fresh_connection()
                cursor = conn.cursor()
                cursor.execute(item.reference_query)
                for test_case in item.test_cases:
                    cursor.execute(test_case.expected_query)
                executable.append(item)
            except Exception as e:
                logger.warning(f"Invalid generated SQL: {e}")

        return executable

    def _build_schema_summary(self) -> str:
        return """
        Tables:
        - employees(id, name, department_id, salary)
        - departments(id, name)
        - projects(id, name, budget)
        - employee_projects(employee_id, project_id)
        """

    # -----------------------------------------------------

    def _map_to_question(
        self,
        item: GeneratedSQLQuestion,
        provenance: QuestionProvenance | None = None,
    ) -> Question:

        return Question(
            id=str(uuid.uuid4()),
            area=InterviewArea.TECH_DATABASE,
            type=QuestionType.DATABASE,
            prompt=item.prompt,
            difficulty=QuestionDifficulty.MEDIUM,
            reference_solution=item.reference_query,
            expected_ordered=False,
            db_schema=self._db.get_schema_sql(),
            db_seed_data=self._db.get_seed_sql(),
            provenance=provenance,
            sql_test_cases=[
                SQLTestCase(
                    id=f"tc_{i}",
                    expected_query=tc.expected_query,
                    ordered=tc.ordered,
                )
                for i, tc in enumerate(item.test_cases)
            ],
        )

    # -----------------------------------------------------

    def _build_generation_prompt(
        self,
        role: str,
        level: str,
        n: int,
        schema_summary: str,
        theme_guidance: str | None = None,
    ) -> str:

        theme_block = ""

        if theme_guidance:
            theme_block = f"\nTHEME GUIDANCE:\n{theme_guidance}\n"

        return f"""
You are a senior SQL interviewer.

Database schema:

{schema_summary}

Generate {n} SQL interview questions for a {level} {role}.
{theme_block}

Each question MUST include:

1. A clear and unambiguous problem description
2. A correct reference SQL query
3. At least 2 test cases (query variations)

{self._json_output_contract()}

Rules:
- Use ONLY tables and columns from the schema
- Use SQLite-compatible SQL
- Queries MUST be executable
- Avoid ambiguous wording
- Do NOT generate schema or data
- No markdown
- Only valid JSON

{_SANDBOX_EXECUTION_RULES}

Test cases:
- Must represent equivalent queries
- Must return the SAME result as reference
- Allowed variations:
  - JOIN syntax
  - aliases
  - ordering

"""

    def _build_enrichment_prompt(
        self,
        seed_prompt: str,
        role: str,
        level: str,
        schema_summary: str,
        theme_guidance: str | None = None,
    ) -> str:

        theme_block = ""

        if theme_guidance:
            theme_block = f"\nTHEME GUIDANCE:\n{theme_guidance}\n"

        return f"""
You are a senior SQL interviewer.

Database schema:

{schema_summary}

Reframe the following interview question into ONE executable SQLite problem
for a {level} {role} candidate.
{theme_block}

Seed question (conceptual — adapt to the schema above):
{seed_prompt}

Each output item MUST include:

1. A clear and unambiguous problem description (rewritten for this schema only)
2. A correct reference SQL query runnable on the schema
3. At least 2 test cases (query variations)

{self._json_output_contract()}

Rules:
- Queries MUST be executable on the provided schema and seed data
- Do NOT generate schema or data
- No markdown
- Only valid JSON
- Return exactly 1 question in the array

{_SANDBOX_EXECUTION_RULES}

Test cases:
- Must represent equivalent queries
- Must return the SAME result as reference
- Allowed variations: JOIN syntax, aliases, ordering

"""

    def _json_output_contract(self) -> str:

        return """
Return STRICT JSON array:

[
  {
    "prompt": "...",
    "reference_query": "SELECT ...",
    "test_cases": [
      {
        "expected_query": "...",
        "ordered": true
      }
    ]
  }
]
"""
