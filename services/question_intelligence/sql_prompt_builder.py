# services/question_intelligence/sql_prompt_builder.py

import sqlite3

from app.prompts.prompt_loader import PromptLoader
from app.prompts.prompt_renderer import PromptRenderer
from infrastructure.config.settings import settings
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

    def __init__(
        self,
        connection: sqlite3.Connection,
        vocabulary_hint: tuple[str, ...] = (),
    ) -> None:
        generator = SchemaSummaryGenerator()
        self._schema_summary = generator.generate(connection)
        self._sandbox_tables = self._extract_table_names(connection)
        self._sandbox_execution_rules = self._build_execution_rules()
        self._vocabulary_hint = vocabulary_hint
        self._sandbox_table_list: list[str] = [
            t.strip() for t in self._sandbox_tables.split(",") if t.strip()
        ]

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
        difficulty_label: str | None = None,
        scenario_anchor: str | None = None,
        job_description: str | None = None,
        company_description: str | None = None,
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
                "difficulty_target_block": self._difficulty_target_block(difficulty_label),
                "scenario_focus_block": self._scenario_focus_block(scenario_anchor),
                "cd_block": self._cd_block(company_description),
                "jd_block": self._jd_block(job_description),
                "vocabulary_block": self._vocabulary_block(),
                "schema_coverage_block": self._schema_coverage_block(),
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
        job_description: str | None = None,
        company_description: str | None = None,
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
                "cd_block": self._cd_block(company_description),
                "jd_block": self._jd_block(job_description),
                "vocabulary_block": self._vocabulary_block(),
                "schema_coverage_block": self._schema_coverage_block(),
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

    def _jd_block(self, job_description: str | None) -> str:
        if not job_description or not job_description.strip():
            return ""
        truncated = job_description.strip()[:settings.job_description_max_chars]
        return f"\nJOB DESCRIPTION CONTEXT (guidance only — do not override domain or difficulty):\n{truncated}\n"

    def _cd_block(self, company_description: str | None) -> str:
        if not company_description or not company_description.strip():
            return ""
        truncated = company_description.strip()[:settings.company_description_max_chars]
        return f"\nBUSINESS CONTEXT (scenario framing only — do not change domain, difficulty, or seniority):\n{truncated}\n"

    def _domain_focus_block(self, domains: list[str] | None) -> str:
        if domains:
            joined = ", ".join(domains)
            return (
                f"\nDOMAIN FOCUS (mandatory):\n"
                f"Generate questions that specifically test: {joined}.\n"
                f"Do NOT generate generic employee/department/salary questions unless they directly exercise the domain(s) above.\n"
            )
        return ""

    def _difficulty_target_block(self, difficulty_label: str | None) -> str:
        if difficulty_label:
            return f"\nDIFFICULTY TARGET:\n{difficulty_label.upper()}\n"
        return ""

    def _scenario_focus_block(self, scenario_anchor: str | None) -> str:
        if scenario_anchor:
            return f"\nSCENARIO FOCUS:\n{scenario_anchor}\n"
        return ""

    def _vocabulary_block(self) -> str:
        if not self._vocabulary_hint:
            return ""
        terms = ", ".join(self._vocabulary_hint)
        return (
            f"\nBUSINESS VOCABULARY (incorporate where natural — do not force):\n"
            f"{terms}\n"
            f"Frame the problem description using these domain concepts when appropriate.\n"
        )

    def _schema_coverage_block(self) -> str:
        if not self._sandbox_table_list:
            return ""
        tables = ", ".join(self._sandbox_table_list)
        return (
            f"\nSCHEMA COVERAGE GUIDANCE:\n"
            f"Available tables: {tables}\n"
            f"- Avoid repeatedly querying the same table in isolation\n"
            f"- Prefer questions that JOIN multiple tables or exercise less-used tables\n"
            f"- Vary the focal table across questions to maximise schema coverage\n"
        )
