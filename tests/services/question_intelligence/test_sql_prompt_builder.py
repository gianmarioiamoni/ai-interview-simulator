# tests/services/question_intelligence/test_sql_prompt_builder.py

import pytest

from services.sql_engine.sql_database import SQLDatabase
from services.question_intelligence.sql_prompt_builder import SQLPromptBuilder


@pytest.fixture()
def db():
    return SQLDatabase()


@pytest.fixture()
def builder(db):
    return SQLPromptBuilder(db.connection)


class TestSQLPromptBuilderSchemaSource:
    def test_schema_summary_contains_real_table_names(self, builder):
        assert "departments" in builder._schema_summary
        assert "employees" in builder._schema_summary
        assert "projects" in builder._schema_summary
        assert "employee_projects" in builder._schema_summary

    def test_schema_summary_contains_real_columns(self, builder):
        assert "salary" in builder._schema_summary
        assert "department_id" in builder._schema_summary
        assert "budget" in builder._schema_summary

    def test_sandbox_tables_derived_from_db(self, builder):
        assert "employees" in builder._sandbox_tables
        assert "departments" in builder._sandbox_tables

    def test_no_hardcoded_schema_constant(self):
        import services.question_intelligence.sql_prompt_builder as mod

        assert not hasattr(mod, "_SCHEMA_SUMMARY"), (
            "_SCHEMA_SUMMARY hardcoded constant must not exist"
        )
        assert not hasattr(mod, "_SANDBOX_TABLES"), (
            "_SANDBOX_TABLES hardcoded constant must not exist"
        )
        assert not hasattr(mod, "_SANDBOX_COLUMN_WHITELIST"), (
            "_SANDBOX_COLUMN_WHITELIST hardcoded constant must not exist"
        )
        assert not hasattr(mod, "_SANDBOX_EXECUTION_RULES"), (
            "_SANDBOX_EXECUTION_RULES hardcoded constant must not exist"
        )


class TestSQLPromptBuilderGenerationPrompt:
    def test_generation_prompt_contains_schema(self, builder):
        prompt = builder.build_generation_prompt(role="backend", level="mid", n=2)
        assert "employees" in prompt
        assert "departments" in prompt

    def test_generation_prompt_contains_execution_rules(self, builder):
        prompt = builder.build_generation_prompt(role="backend", level="mid", n=1)
        assert "EXECUTION CONSTRAINTS" in prompt
        assert "SELECT" in prompt

    def test_generation_prompt_with_theme(self, builder):
        prompt = builder.build_generation_prompt(
            role="backend", level="senior", n=1, theme_guidance="aggregation queries"
        )
        assert "aggregation queries" in prompt


class TestSQLPromptBuilderEnrichmentPrompt:
    def test_enrichment_prompt_contains_schema(self, builder):
        prompt = builder.build_enrichment_prompt(
            seed_prompt="List all employees", role="backend", level="junior"
        )
        assert "employees" in prompt
        assert "departments" in prompt

    def test_enrichment_prompt_contains_execution_rules(self, builder):
        prompt = builder.build_enrichment_prompt(
            seed_prompt="Find top earners", role="backend", level="senior"
        )
        assert "EXECUTION CONSTRAINTS" in prompt

    def test_enrichment_prompt_with_theme(self, builder):
        prompt = builder.build_enrichment_prompt(
            seed_prompt="Group by department",
            role="data",
            level="mid",
            theme_guidance="GROUP BY usage",
        )
        assert "GROUP BY usage" in prompt


class TestSQLPromptBuilderSchemaPropagation:
    def test_schema_change_propagates_to_generation_prompt(self):
        """Schema changes in SQLDatabase automatically appear in prompt output."""
        import sqlite3
        from services.sql_engine.schema_summary_generator import SchemaSummaryGenerator

        conn = sqlite3.connect(":memory:")
        conn.execute("CREATE TABLE custom_table (col_x INTEGER, col_y TEXT)")
        conn.commit()

        custom_builder = SQLPromptBuilder(conn)
        prompt = custom_builder.build_generation_prompt(
            role="backend", level="mid", n=1
        )

        assert "custom_table" in custom_builder._schema_summary
        assert "col_x" in custom_builder._schema_summary
        assert "custom_table" in prompt
