# services/question_intelligence/sql_prompt_builder.py

from app.prompts.prompt_loader import PromptLoader
from app.prompts.prompt_renderer import PromptRenderer


_SANDBOX_TABLES = "employees, departments, projects, employee_projects"

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

_SCHEMA_SUMMARY = """
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

_JSON_OUTPUT_CONTRACT = """
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


class SQLPromptBuilder:
    """
    Builds LLM prompts for SQL question generation and enrichment.
    Owns all sandbox schema constants and output contract definitions.
    """

    # ------------------------------------------------------------------
    # PUBLIC
    # ------------------------------------------------------------------

    def build_generation_prompt(
        self,
        role: str,
        level: str,
        n: int,
        theme_guidance: str | None = None,
    ) -> str:

        template = PromptLoader.load("generation/sql_question_generation.txt")

        return PromptRenderer.render(
            template,
            {
                "n": n,
                "level": level,
                "role": role,
                "schema_summary": _SCHEMA_SUMMARY,
                "theme_block": self._theme_block(theme_guidance),
                "json_output_contract": _JSON_OUTPUT_CONTRACT,
                "sandbox_execution_rules": _SANDBOX_EXECUTION_RULES,
            },
        )

    def build_enrichment_prompt(
        self,
        seed_prompt: str,
        role: str,
        level: str,
        theme_guidance: str | None = None,
    ) -> str:

        template = PromptLoader.load("generation/sql_question_enrichment.txt")

        return PromptRenderer.render(
            template,
            {
                "seed_prompt": seed_prompt,
                "level": level,
                "role": role,
                "schema_summary": _SCHEMA_SUMMARY,
                "theme_block": self._theme_block(theme_guidance),
                "json_output_contract": _JSON_OUTPUT_CONTRACT,
                "sandbox_execution_rules": _SANDBOX_EXECUTION_RULES,
            },
        )

    # ------------------------------------------------------------------
    # PRIVATE
    # ------------------------------------------------------------------

    def _theme_block(self, theme_guidance: str | None) -> str:
        if theme_guidance:
            return f"\nTHEME GUIDANCE:\n{theme_guidance}\n"
        return ""
