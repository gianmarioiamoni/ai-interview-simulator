# services/question_intelligence/sql_prompt_builder.py

import sqlite3

from app.prompts.prompt_loader import PromptLoader
from app.prompts.prompt_renderer import PromptRenderer
from services.sql_engine.schema_summary_generator import SchemaSummaryGenerator


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

    Receives schema information dynamically via the constructor, derived from
    the live SQLDatabase through SchemaSummaryGenerator. No hardcoded schema
    constants are stored here.
    """

    def __init__(self, connection: sqlite3.Connection) -> None:
        generator = SchemaSummaryGenerator()
        self._schema_summary = generator.generate(connection)
        self._sandbox_tables = self._extract_table_names(connection)
        self._sandbox_execution_rules = self._build_execution_rules()

    # ------------------------------------------------------------------
    # PUBLIC
    # ------------------------------------------------------------------

    def build_generation_prompt(
        self,
        role: str,
        level: str,
        n: int,
        theme_guidance: str | None = None,
        domains: list[str] | None = None,
    ) -> str:

        template = PromptLoader.load("generation/sql_question_generation.txt")

        return PromptRenderer.render(
            template,
            {
                "n": n,
                "level": level,
                "role": role,
                "schema_summary": self._schema_summary,
                "theme_block": self._theme_block(theme_guidance),
                "domain_focus_block": self._domain_focus_block(domains),
                "json_output_contract": _JSON_OUTPUT_CONTRACT,
                "sandbox_execution_rules": self._sandbox_execution_rules,
            },
        )

    def build_enrichment_prompt(
        self,
        seed_prompt: str,
        role: str,
        level: str,
        theme_guidance: str | None = None,
        domains: list[str] | None = None,
        expected_topics: list[str] | None = None,
        difficulty_label: str | None = None,
    ) -> str:

        template = PromptLoader.load("generation/sql_question_enrichment.txt")

        return PromptRenderer.render(
            template,
            {
                "seed_prompt": seed_prompt,
                "level": level,
                "role": role,
                "schema_summary": self._schema_summary,
                "theme_block": self._theme_block(theme_guidance),
                "domain_constraint_block": self._domain_constraint_block(domains),
                "expected_topics_block": self._expected_topics_block(expected_topics),
                "difficulty_block": self._difficulty_block(difficulty_label),
                "json_output_contract": _JSON_OUTPUT_CONTRACT,
                "sandbox_execution_rules": self._sandbox_execution_rules,
            },
        )

    # ------------------------------------------------------------------
    # PRIVATE
    # ------------------------------------------------------------------

    def _extract_table_names(self, connection: sqlite3.Connection) -> str:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT name FROM sqlite_master
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
            """
        )
        return ", ".join(row[0] for row in cursor.fetchall())

    def _build_execution_rules(self) -> str:
        return f"""
EXECUTION CONSTRAINTS (mandatory):
- reference_query and every test case expected_query MUST be a single SELECT only
- Use ONLY sandbox tables: {self._sandbox_tables}
- Use ONLY columns that exist on those tables in the provided schema
- Use SQLite-compatible SQL (not PostgreSQL-specific syntax)
- Do NOT use CREATE, ALTER, DROP, VIEW, TRIGGER, or any DDL
- Do NOT use INSERT, UPDATE, DELETE, or multi-statement SQL (no semicolon-separated statements)
- Do NOT invent tables, views, or column names
"""

    def _theme_block(self, theme_guidance: str | None) -> str:
        if theme_guidance:
            return f"\nTHEME GUIDANCE:\n{theme_guidance}\n"
        return ""

    def _domain_constraint_block(self, domains: list[str] | None) -> str:
        if domains:
            joined = ", ".join(domains)
            return (
                f"\nDOMAIN CONSTRAINT (mandatory):\n"
                f"The generated question MUST test one or more of the following SQL concepts: {joined}.\n"
                f"The question prompt MUST require the candidate to use these concepts directly.\n"
                f"Do NOT generate a question about a different SQL topic.\n"
            )
        return ""

    def _expected_topics_block(self, expected_topics: list[str] | None) -> str:
        if expected_topics:
            joined = ", ".join(expected_topics)
            return f"\nREQUIRED KEYWORDS (preferred — use in question wording when possible):\n{joined}\n"
        return ""

    def _difficulty_block(self, difficulty_label: str | None) -> str:
        if difficulty_label:
            return f"\nDIFFICULTY: {difficulty_label.upper()}\n"
        return ""

    def _domain_focus_block(self, domains: list[str] | None) -> str:
        if domains:
            joined = ", ".join(domains)
            return (
                f"\nDOMAIN FOCUS (mandatory):\n"
                f"Generate questions that specifically test: {joined}.\n"
                f"Do NOT generate generic employee/department/salary questions unless they directly exercise the domain(s) above.\n"
            )
        return ""
