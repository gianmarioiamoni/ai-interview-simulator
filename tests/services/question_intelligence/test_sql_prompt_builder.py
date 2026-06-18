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

    def test_generation_prompt_with_domain_focus(self, builder):
        prompt = builder.build_generation_prompt(
            role="backend", level="mid", n=1, domains=["window_function", "cte"]
        )
        assert "DOMAIN FOCUS" in prompt
        assert "window_function" in prompt
        assert "cte" in prompt

    def test_generation_prompt_no_domain_focus_when_empty(self, builder):
        prompt = builder.build_generation_prompt(role="backend", level="mid", n=1)
        assert "DOMAIN FOCUS" not in prompt

    def test_generation_prompt_with_difficulty_label(self, builder):
        prompt = builder.build_generation_prompt(
            role="backend", level="senior", n=1, difficulty_label="hard"
        )
        assert "DIFFICULTY TARGET" in prompt
        assert "HARD" in prompt

    def test_generation_prompt_no_difficulty_block_when_absent(self, builder):
        prompt = builder.build_generation_prompt(role="backend", level="mid", n=1)
        assert "DIFFICULTY TARGET" not in prompt

    def test_generation_prompt_with_scenario_anchor(self, builder):
        prompt = builder.build_generation_prompt(
            role="backend", level="mid", n=1, scenario_anchor="reporting"
        )
        assert "SCENARIO FOCUS" in prompt
        assert "reporting" in prompt

    def test_generation_prompt_no_scenario_block_when_absent(self, builder):
        prompt = builder.build_generation_prompt(role="backend", level="mid", n=1)
        assert "SCENARIO FOCUS" not in prompt

    def test_generation_prompt_all_metadata_combined(self, builder):
        prompt = builder.build_generation_prompt(
            role="backend",
            level="senior",
            n=2,
            domains=["joins", "aggregation"],
            difficulty_label="intermediate",
            scenario_anchor="anti_pattern",
        )
        assert "DOMAIN FOCUS" in prompt
        assert "joins" in prompt
        assert "DIFFICULTY TARGET" in prompt
        assert "INTERMEDIATE" in prompt
        assert "SCENARIO FOCUS" in prompt
        assert "anti_pattern" in prompt


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

    def test_enrichment_prompt_has_grounding_reference_label(self, builder):
        prompt = builder.build_enrichment_prompt(
            seed_prompt="Explain window functions", role="backend", level="senior"
        )
        assert "grounding reference" in prompt
        assert "conceptual" not in prompt

    def test_enrichment_prompt_with_domain_constraint(self, builder):
        prompt = builder.build_enrichment_prompt(
            seed_prompt="Write a query",
            role="backend",
            level="mid",
            domains=["window_function"],
        )
        assert "DOMAIN CONSTRAINT" in prompt
        assert "window_function" in prompt
        assert "mandatory" in prompt

    def test_enrichment_prompt_with_expected_topics(self, builder):
        prompt = builder.build_enrichment_prompt(
            seed_prompt="Write a query",
            role="backend",
            level="mid",
            expected_topics=["ROW_NUMBER", "PARTITION BY"],
        )
        assert "REQUIRED KEYWORDS" in prompt
        assert "ROW_NUMBER" in prompt
        assert "PARTITION BY" in prompt

    def test_enrichment_prompt_with_difficulty_label(self, builder):
        prompt = builder.build_enrichment_prompt(
            seed_prompt="Write a query",
            role="backend",
            level="senior",
            difficulty_label="hard",
        )
        assert "DIFFICULTY" in prompt
        assert "HARD" in prompt

    def test_enrichment_prompt_no_constraint_blocks_when_empty(self, builder):
        prompt = builder.build_enrichment_prompt(
            seed_prompt="Write a query", role="backend", level="mid"
        )
        assert "DOMAIN CONSTRAINT" not in prompt
        assert "REQUIRED KEYWORDS" not in prompt
        assert "DIFFICULTY" not in prompt

    def test_enrichment_prompt_preserves_domain_intent_instruction(self, builder):
        prompt = builder.build_enrichment_prompt(
            seed_prompt="Write a query using CTE",
            role="backend",
            level="mid",
            domains=["cte"],
        )
        assert "preserving the SQL domain" in prompt


class TestSQLPromptBuilderVocabularyBlock:
    def test_no_vocabulary_block_when_no_hint(self, builder):
        prompt = builder.build_generation_prompt(role="backend", level="mid", n=1)
        assert "BUSINESS VOCABULARY" not in prompt

    def test_vocabulary_block_present_when_hint_set(self):
        from services.sql_engine.sql_database import SQLDatabase
        from services.sql_engine.schema_registry import SchemaRegistry
        from domain.contracts.interview.business_context import BusinessContext

        defn = SchemaRegistry.get(BusinessContext.FINTECH)
        db = SQLDatabase(schema_definition=defn)
        b = SQLPromptBuilder(db.connection, vocabulary_hint=defn.vocabulary_hint)

        prompt = b.build_generation_prompt(role="backend", level="mid", n=1)
        assert "BUSINESS VOCABULARY" in prompt

    def test_vocabulary_block_contains_fintech_terms(self):
        from services.sql_engine.sql_database import SQLDatabase
        from services.sql_engine.schema_registry import SchemaRegistry
        from domain.contracts.interview.business_context import BusinessContext

        defn = SchemaRegistry.get(BusinessContext.FINTECH)
        db = SQLDatabase(schema_definition=defn)
        b = SQLPromptBuilder(db.connection, vocabulary_hint=defn.vocabulary_hint)

        prompt = b.build_generation_prompt(role="backend", level="mid", n=1)
        for term in ("fraud", "settlement", "ledger", "chargeback"):
            assert term in prompt

    def test_vocabulary_block_contains_ecommerce_terms(self):
        from services.sql_engine.sql_database import SQLDatabase
        from services.sql_engine.schema_registry import SchemaRegistry
        from domain.contracts.interview.business_context import BusinessContext

        defn = SchemaRegistry.get(BusinessContext.ECOMMERCE)
        db = SQLDatabase(schema_definition=defn)
        b = SQLPromptBuilder(db.connection, vocabulary_hint=defn.vocabulary_hint)

        prompt = b.build_generation_prompt(role="backend", level="mid", n=1)
        for term in ("inventory", "fulfillment", "returns", "sku"):
            assert term in prompt

    def test_vocabulary_block_contains_saas_terms(self):
        from services.sql_engine.sql_database import SQLDatabase
        from services.sql_engine.schema_registry import SchemaRegistry
        from domain.contracts.interview.business_context import BusinessContext

        defn = SchemaRegistry.get(BusinessContext.SAAS)
        db = SQLDatabase(schema_definition=defn)
        b = SQLPromptBuilder(db.connection, vocabulary_hint=defn.vocabulary_hint)

        prompt = b.build_generation_prompt(role="backend", level="mid", n=1)
        for term in ("churn", "retention", "MRR", "ARR"):
            assert term in prompt

    def test_vocabulary_block_in_enrichment_prompt(self):
        from services.sql_engine.sql_database import SQLDatabase
        from services.sql_engine.schema_registry import SchemaRegistry
        from domain.contracts.interview.business_context import BusinessContext

        defn = SchemaRegistry.get(BusinessContext.FINTECH)
        db = SQLDatabase(schema_definition=defn)
        b = SQLPromptBuilder(db.connection, vocabulary_hint=defn.vocabulary_hint)

        prompt = b.build_enrichment_prompt(
            seed_prompt="Find top accounts", role="backend", level="mid"
        )
        assert "BUSINESS VOCABULARY" in prompt
        assert "fraud" in prompt

    def test_no_vocabulary_block_in_enrichment_when_no_hint(self, builder):
        prompt = builder.build_enrichment_prompt(
            seed_prompt="Find top earners", role="backend", level="senior"
        )
        assert "BUSINESS VOCABULARY" not in prompt


class TestSQLPromptBuilderSchemaCoverageBlock:
    def test_schema_coverage_block_present_in_generation(self, builder):
        prompt = builder.build_generation_prompt(role="backend", level="mid", n=1)
        assert "SCHEMA COVERAGE GUIDANCE" in prompt

    def test_schema_coverage_block_lists_tables(self, builder):
        prompt = builder.build_generation_prompt(role="backend", level="mid", n=1)
        assert "employees" in prompt
        assert "departments" in prompt

    def test_schema_coverage_block_contains_diversity_instruction(self, builder):
        prompt = builder.build_generation_prompt(role="backend", level="mid", n=1)
        assert "Avoid repeatedly" in prompt
        assert "less-used tables" in prompt

    def test_schema_coverage_block_present_in_enrichment(self, builder):
        prompt = builder.build_enrichment_prompt(
            seed_prompt="List employees", role="backend", level="mid"
        )
        assert "SCHEMA COVERAGE GUIDANCE" in prompt

    def test_schema_coverage_lists_fintech_tables(self):
        from services.sql_engine.sql_database import SQLDatabase
        from services.sql_engine.schema_registry import SchemaRegistry
        from domain.contracts.interview.business_context import BusinessContext

        defn = SchemaRegistry.get(BusinessContext.FINTECH)
        db = SQLDatabase(schema_definition=defn)
        b = SQLPromptBuilder(db.connection, vocabulary_hint=defn.vocabulary_hint)

        prompt = b.build_generation_prompt(role="backend", level="mid", n=1)
        assert "SCHEMA COVERAGE GUIDANCE" in prompt
        for table in ("accounts", "transactions", "portfolios"):
            assert table in prompt

    def test_schema_coverage_lists_ecommerce_tables(self):
        from services.sql_engine.sql_database import SQLDatabase
        from services.sql_engine.schema_registry import SchemaRegistry
        from domain.contracts.interview.business_context import BusinessContext

        defn = SchemaRegistry.get(BusinessContext.ECOMMERCE)
        db = SQLDatabase(schema_definition=defn)
        b = SQLPromptBuilder(db.connection, vocabulary_hint=defn.vocabulary_hint)

        prompt = b.build_generation_prompt(role="backend", level="mid", n=1)
        assert "SCHEMA COVERAGE GUIDANCE" in prompt
        for table in ("orders", "order_items", "products", "categories"):
            assert table in prompt

    def test_schema_coverage_lists_saas_tables(self):
        from services.sql_engine.sql_database import SQLDatabase
        from services.sql_engine.schema_registry import SchemaRegistry
        from domain.contracts.interview.business_context import BusinessContext

        defn = SchemaRegistry.get(BusinessContext.SAAS)
        db = SQLDatabase(schema_definition=defn)
        b = SQLPromptBuilder(db.connection, vocabulary_hint=defn.vocabulary_hint)

        prompt = b.build_generation_prompt(role="backend", level="mid", n=1)
        assert "SCHEMA COVERAGE GUIDANCE" in prompt
        for table in ("tenants", "subscriptions", "usage_events"):
            assert table in prompt


class TestSQLPromptBuilderBackwardCompatibility:
    def test_default_builder_no_vocabulary_block(self, builder):
        """Builder constructed without vocabulary_hint emits no vocabulary block."""
        prompt = builder.build_generation_prompt(role="backend", level="mid", n=1)
        assert "BUSINESS VOCABULARY" not in prompt

    def test_default_builder_still_has_schema_coverage(self, builder):
        """Schema coverage block is always present regardless of vocabulary_hint."""
        prompt = builder.build_generation_prompt(role="backend", level="mid", n=1)
        assert "SCHEMA COVERAGE GUIDANCE" in prompt

    def test_existing_blocks_unaffected(self, builder):
        prompt = builder.build_generation_prompt(
            role="backend",
            level="senior",
            n=2,
            domains=["joins"],
            difficulty_label="hard",
            scenario_anchor="reporting",
        )
        assert "DOMAIN FOCUS" in prompt
        assert "DIFFICULTY TARGET" in prompt
        assert "SCENARIO FOCUS" in prompt
        assert "EXECUTION CONSTRAINTS" in prompt


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
