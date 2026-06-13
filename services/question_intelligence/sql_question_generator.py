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
from app.prompts.prompt_loader import PromptLoader
from app.prompts.prompt_renderer import PromptRenderer
from infrastructure.llm.metrics.llm_operation_context import LLMOperationContext
from infrastructure.llm.metrics.llm_operation_names import QUESTION_GENERATION

from services.sql_engine.sql_database import SQLDatabase

from app.core.logger import get_logger

logger = get_logger(__name__)

_SANDBOX_TABLES = (
    "employees, departments, projects, employee_projects"
)

_SANDBOX_COLUMN_WHITELIST = """
EXACT column names per table (no others exist):
  employees        : id, name, department_id, salary
  departments      : id, name
  projects         : id, name, budget
  employee_projects: employee_id, project_id

FORBIDDEN column name examples (do NOT use):
  employee_name, emp_name, dept_name, project_name, first_name, last_name,
  email, phone, title, position, hire_date, age, manager_id
"""

_SANDBOX_EXECUTION_RULES = f"""
EXECUTION CONSTRAINTS (mandatory):
- reference_query and every test case expected_query MUST be a single SELECT only
- Use ONLY sandbox tables: {_SANDBOX_TABLES}
- Use ONLY columns that exist on those tables in the provided schema
- Use SQLite-compatible SQL (not PostgreSQL-specific syntax)
- Do NOT use CREATE, ALTER, DROP, VIEW, TRIGGER, or any DDL
- Do NOT use INSERT, UPDATE, DELETE, or multi-statement SQL (no semicolon-separated statements)
- Do NOT invent tables, views, or column names
{_SANDBOX_COLUMN_WHITELIST}
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

        with LLMOperationContext.scope(QUESTION_GENERATION):
            response = self._llm.invoke(prompt)

        try:
            validated_items = self._parse_llm_response(response.content)
        except ValueError as e:
            raise ValueError(str(e)) from e

        executable_items = self._filter_executable_items(validated_items)

        return [self._map_to_question(item) for item in executable_items]

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
            with LLMOperationContext.scope(QUESTION_GENERATION):
                response = self._llm.invoke(prompt)
            validated_items = self._parse_llm_response(response.content)
            executable_items = self._filter_executable_items(validated_items)
        except ValueError as e:
            logger.warning(f"[SQL enrich] Failed enrichment: {e}")
            return None
        except Exception as e:
            logger.warning(f"[SQL enrich] Unexpected error during enrichment: {e}")
            return None

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
                error_msg = f"Invalid generated SQL: {e}"
                logger.warning(error_msg)
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

    def _build_schema_summary(self) -> str:
        return """
        Tables and their EXACT columns (use no others):
        - employees(id INTEGER, name TEXT, department_id INTEGER, salary INTEGER)
        - departments(id INTEGER, name TEXT)
        - projects(id INTEGER, name TEXT, budget INTEGER)
        - employee_projects(employee_id INTEGER, project_id INTEGER)

        Foreign keys:
        - employees.department_id → departments.id
        - employee_projects.employee_id → employees.id
        - employee_projects.project_id → projects.id
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

        template = PromptLoader.load("generation/sql_question_generation.txt")

        return PromptRenderer.render(
            template,
            {
                "n": n,
                "level": level,
                "role": role,
                "schema_summary": schema_summary,
                "theme_block": theme_block,
                "json_output_contract": self._json_output_contract(),
                "sandbox_execution_rules": _SANDBOX_EXECUTION_RULES,
            },
        )

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

        template = PromptLoader.load("generation/sql_question_enrichment.txt")

        return PromptRenderer.render(
            template,
            {
                "seed_prompt": seed_prompt,
                "level": level,
                "role": role,
                "schema_summary": schema_summary,
                "theme_block": theme_block,
                "json_output_contract": self._json_output_contract(),
                "sandbox_execution_rules": _SANDBOX_EXECUTION_RULES,
            },
        )

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
