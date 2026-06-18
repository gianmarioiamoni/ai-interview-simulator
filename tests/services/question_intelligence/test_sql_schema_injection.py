# tests/services/question_intelligence/test_sql_schema_injection.py
"""
End-to-end schema propagation tests.

Verifies that:
- FINTECH BusinessContext resolves to a generator with FINTECH SQLDatabase
- GENERIC BusinessContext resolves to a generator with GENERIC SQLDatabase
- db_schema on generated Question contains fintech DDL for FINTECH context
- filter_executable validates against fintech schema (rejects HR SQL)
- GENERIC behaviour unchanged
- Factory caches generators (same instance returned on repeated calls)
"""

import json
import pytest
from unittest.mock import MagicMock

from domain.contracts.interview.business_context import BusinessContext
from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.interview.interview_type import InterviewType
from domain.contracts.user.role import RoleType
from domain.contracts.user.seniority_level import SeniorityLevel
from services.question_corpus.contracts.interview_retrieval_memory import (
    InterviewRetrievalMemory,
)
from services.question_intelligence.area_question_builder import (
    _build_sql_generator_factory,
)
from services.question_intelligence.pipelines.sql_question_pipeline import (
    SQLGeneratorFactory,
    SQLQuestionPipeline,
    _BUSINESS_CONTEXT_METADATA_ONLY,
)
from services.question_intelligence.sql_question_generator import SQLQuestionGenerator
from services.sql_engine.schema_registry import SchemaRegistry


# ── helpers ───────────────────────────────────────────────────────────────────

_FINTECH_VALID_JSON = json.dumps(
    [
        {
            "prompt": "List all accounts with balance above 5000.",
            "reference_query": "SELECT id, balance FROM accounts WHERE balance > 5000",
            "test_cases": [
                {
                    "expected_query": "SELECT id, balance FROM accounts WHERE balance > 5000",
                    "ordered": False,
                },
                {
                    "expected_query": "SELECT a.id, a.balance FROM accounts a WHERE a.balance > 5000",
                    "ordered": False,
                },
            ],
        }
    ]
)

_GENERIC_VALID_JSON = json.dumps(
    [
        {
            "prompt": "List all employees.",
            "reference_query": "SELECT name FROM employees",
            "test_cases": [
                {"expected_query": "SELECT name FROM employees", "ordered": False},
                {"expected_query": "SELECT e.name FROM employees e", "ordered": False},
            ],
        }
    ]
)


def _make_llm(json_str: str) -> MagicMock:
    llm = MagicMock()
    response = MagicMock()
    response.content = json_str
    llm.invoke.return_value = response
    return llm


# ── factory tests ─────────────────────────────────────────────────────────────


class TestSQLGeneratorFactory:
    def test_generic_returns_default_generator(self):
        llm = _make_llm(_GENERIC_VALID_JSON)
        default_gen = SQLQuestionGenerator(llm)
        factory = _build_sql_generator_factory(llm, default_gen)

        result = factory(BusinessContext.GENERIC)
        assert result is default_gen

    def test_fintech_returns_different_generator(self):
        llm = _make_llm(_FINTECH_VALID_JSON)
        default_gen = SQLQuestionGenerator(llm)
        factory = _build_sql_generator_factory(llm, default_gen)

        result = factory(BusinessContext.FINTECH)
        assert result is not default_gen

    def test_fintech_generator_has_fintech_schema(self):
        llm = _make_llm(_FINTECH_VALID_JSON)
        default_gen = SQLQuestionGenerator(llm)
        factory = _build_sql_generator_factory(llm, default_gen)

        fintech_gen = factory(BusinessContext.FINTECH)
        assert "accounts" in fintech_gen._db.get_schema_sql()
        assert "transactions" in fintech_gen._db.get_schema_sql()
        assert "employees" not in fintech_gen._db.get_schema_sql()

    def test_generic_generator_has_generic_schema(self):
        llm = _make_llm(_GENERIC_VALID_JSON)
        default_gen = SQLQuestionGenerator(llm)
        factory = _build_sql_generator_factory(llm, default_gen)

        generic_gen = factory(BusinessContext.GENERIC)
        assert "employees" in generic_gen._db.get_schema_sql()
        assert "departments" in generic_gen._db.get_schema_sql()
        assert "accounts" not in generic_gen._db.get_schema_sql()

    def test_factory_caches_fintech_generator(self):
        llm = _make_llm(_FINTECH_VALID_JSON)
        default_gen = SQLQuestionGenerator(llm)
        factory = _build_sql_generator_factory(llm, default_gen)

        gen1 = factory(BusinessContext.FINTECH)
        gen2 = factory(BusinessContext.FINTECH)
        assert gen1 is gen2

    def test_ecommerce_returns_ecommerce_scoped_generator(self):
        """ECOMMERCE is now in registry → returns ECOMMERCE SchemaDefinition."""
        llm = _make_llm(_ECOMMERCE_VALID_JSON)
        default_gen = SQLQuestionGenerator(llm)
        factory = _build_sql_generator_factory(llm, default_gen)

        ecom_gen = factory(BusinessContext.ECOMMERCE)
        assert "orders" in ecom_gen._db.get_schema_sql()
        assert "employees" not in ecom_gen._db.get_schema_sql()


# ── schema propagation to Question.db_schema ─────────────────────────────────


class TestSchemaStampedOnQuestion:
    def test_fintech_generator_stamps_fintech_db_schema(self):
        llm = _make_llm(_FINTECH_VALID_JSON)
        fintech_defn = SchemaRegistry.get(BusinessContext.FINTECH)
        gen = SQLQuestionGenerator(llm, schema_definition=fintech_defn)

        questions = gen.generate(
            role=RoleType.BACKEND_ENGINEER,
            level=SeniorityLevel.MID,
            n=1,
        )

        assert len(questions) == 1
        assert "accounts" in questions[0].db_schema
        assert "transactions" in questions[0].db_schema
        assert "employees" not in questions[0].db_schema

    def test_fintech_generator_stamps_fintech_db_seed_data(self):
        llm = _make_llm(_FINTECH_VALID_JSON)
        fintech_defn = SchemaRegistry.get(BusinessContext.FINTECH)
        gen = SQLQuestionGenerator(llm, schema_definition=fintech_defn)

        questions = gen.generate(
            role=RoleType.BACKEND_ENGINEER,
            level=SeniorityLevel.MID,
            n=1,
        )

        assert "INSERT INTO accounts" in questions[0].db_seed_data
        assert "INSERT INTO transactions" in questions[0].db_seed_data

    def test_generic_generator_stamps_generic_db_schema(self):
        llm = _make_llm(_GENERIC_VALID_JSON)
        gen = SQLQuestionGenerator(llm)

        questions = gen.generate(
            role=RoleType.BACKEND_ENGINEER,
            level=SeniorityLevel.MID,
            n=1,
        )

        assert "employees" in questions[0].db_schema
        assert "accounts" not in questions[0].db_schema


# ── filter_executable uses correct schema ─────────────────────────────────────


class TestFilterExecutableSchemaIsolation:
    def test_fintech_rejects_hr_sql(self):
        """SQL referencing `employees` must be rejected on FINTECH schema."""
        llm = MagicMock()
        hr_json = json.dumps(
            [
                {
                    "prompt": "List all employees.",
                    "reference_query": "SELECT name FROM employees",
                    "test_cases": [
                        {"expected_query": "SELECT name FROM employees", "ordered": False},
                        {"expected_query": "SELECT e.name FROM employees e", "ordered": False},
                    ],
                }
            ]
        )
        response = MagicMock()
        response.content = hr_json
        llm.invoke.return_value = response

        fintech_defn = SchemaRegistry.get(BusinessContext.FINTECH)
        gen = SQLQuestionGenerator(llm, schema_definition=fintech_defn)

        with pytest.raises(ValueError):
            gen.generate(role=RoleType.BACKEND_ENGINEER, level=SeniorityLevel.MID)

    def test_fintech_accepts_fintech_sql(self):
        """SQL referencing `accounts` must be accepted on FINTECH schema."""
        llm = _make_llm(_FINTECH_VALID_JSON)
        fintech_defn = SchemaRegistry.get(BusinessContext.FINTECH)
        gen = SQLQuestionGenerator(llm, schema_definition=fintech_defn)

        questions = gen.generate(role=RoleType.BACKEND_ENGINEER, level=SeniorityLevel.MID)
        assert len(questions) == 1

    def test_generic_rejects_fintech_sql(self):
        """SQL referencing `accounts` must be rejected on GENERIC schema."""
        llm = MagicMock()
        response = MagicMock()
        response.content = _FINTECH_VALID_JSON
        llm.invoke.return_value = response

        gen = SQLQuestionGenerator(llm)  # GENERIC schema

        with pytest.raises(ValueError):
            gen.generate(role=RoleType.BACKEND_ENGINEER, level=SeniorityLevel.MID)


# ── prompt schema summary contains correct tables ─────────────────────────────


class TestPromptSchemaSummary:
    def test_fintech_prompt_contains_accounts_not_employees(self):
        llm = _make_llm(_FINTECH_VALID_JSON)
        fintech_defn = SchemaRegistry.get(BusinessContext.FINTECH)
        gen = SQLQuestionGenerator(llm, schema_definition=fintech_defn)

        gen.generate(role=RoleType.BACKEND_ENGINEER, level=SeniorityLevel.MID)
        prompt = llm.invoke.call_args[0][0]

        assert "accounts" in prompt
        assert "transactions" in prompt
        assert "employees" not in prompt

    def test_generic_prompt_contains_employees_not_accounts(self):
        llm = _make_llm(_GENERIC_VALID_JSON)
        gen = SQLQuestionGenerator(llm)

        gen.generate(role=RoleType.BACKEND_ENGINEER, level=SeniorityLevel.MID)
        prompt = llm.invoke.call_args[0][0]

        assert "employees" in prompt
        assert "accounts" not in prompt


# ── pipeline _resolve_generator uses factory ─────────────────────────────────


class TestPipelineResolveGenerator:
    def test_no_factory_returns_default_generator(self):
        default_gen = MagicMock(spec=SQLQuestionGenerator)
        pipeline = SQLQuestionPipeline(
            retrieval_service=MagicMock(),
            sql_generator=default_gen,
            generator_factory=None,
        )
        assert pipeline._resolve_generator(BusinessContext.FINTECH) is default_gen

    def test_factory_returns_context_specific_generator(self):
        default_gen = MagicMock(spec=SQLQuestionGenerator)
        fintech_gen = MagicMock(spec=SQLQuestionGenerator)
        factory = lambda ctx: fintech_gen if ctx == BusinessContext.FINTECH else default_gen

        pipeline = SQLQuestionPipeline(
            retrieval_service=MagicMock(),
            sql_generator=default_gen,
            generator_factory=factory,
        )
        assert pipeline._resolve_generator(BusinessContext.FINTECH) is fintech_gen
        assert pipeline._resolve_generator(BusinessContext.GENERIC) is default_gen

    def test_factory_none_context_returns_default(self):
        default_gen = MagicMock(spec=SQLQuestionGenerator)
        fintech_gen = MagicMock(spec=SQLQuestionGenerator)
        factory = lambda ctx: fintech_gen

        pipeline = SQLQuestionPipeline(
            retrieval_service=MagicMock(),
            sql_generator=default_gen,
            generator_factory=factory,
        )
        assert pipeline._resolve_generator(None) is default_gen


# ── _generate_with_retry uses context-specific generator ─────────────────────


class TestGenerateWithRetrySchemaSelection:
    """Verifies that _generate_with_retry delegates to the factory-resolved
    generator, not the default sql_generator."""

    def _make_pipeline(
        self,
        default_gen: MagicMock,
        fintech_gen: MagicMock,
    ) -> SQLQuestionPipeline:
        factory = (
            lambda ctx: fintech_gen if ctx == BusinessContext.FINTECH else default_gen
        )
        return SQLQuestionPipeline(
            retrieval_service=MagicMock(),
            sql_generator=default_gen,
            generator_factory=factory,
        )

    def test_fintech_retry_calls_fintech_generator(self):
        default_gen = MagicMock(spec=SQLQuestionGenerator)
        fintech_gen = MagicMock(spec=SQLQuestionGenerator)
        fintech_gen.generate.return_value = [MagicMock()]

        pipeline = self._make_pipeline(default_gen, fintech_gen)
        result = pipeline._generate_with_retry(
            role=RoleType.BACKEND_ENGINEER,
            level=SeniorityLevel.MID,
            n=1,
            business_context=BusinessContext.FINTECH,
        )

        fintech_gen.generate.assert_called_once()
        default_gen.generate.assert_not_called()
        assert len(result) == 1

    def test_generic_retry_calls_default_generator(self):
        default_gen = MagicMock(spec=SQLQuestionGenerator)
        fintech_gen = MagicMock(spec=SQLQuestionGenerator)
        default_gen.generate.return_value = [MagicMock()]

        pipeline = self._make_pipeline(default_gen, fintech_gen)
        result = pipeline._generate_with_retry(
            role=RoleType.BACKEND_ENGINEER,
            level=SeniorityLevel.MID,
            n=1,
            business_context=BusinessContext.GENERIC,
        )

        default_gen.generate.assert_called_once()
        fintech_gen.generate.assert_not_called()
        assert len(result) == 1

    def test_no_factory_retry_always_uses_default(self):
        default_gen = MagicMock(spec=SQLQuestionGenerator)
        default_gen.generate.return_value = [MagicMock()]

        pipeline = SQLQuestionPipeline(
            retrieval_service=MagicMock(),
            sql_generator=default_gen,
            generator_factory=None,
        )
        result = pipeline._generate_with_retry(
            role=RoleType.BACKEND_ENGINEER,
            level=SeniorityLevel.MID,
            n=1,
            business_context=BusinessContext.FINTECH,
        )

        default_gen.generate.assert_called_once()
        assert len(result) == 1

    def test_fintech_retry_stamps_fintech_schema_on_question(self):
        """Integration: FINTECH retry path produces Question with fintech DDL."""
        llm = _make_llm(_FINTECH_VALID_JSON)
        default_gen = SQLQuestionGenerator(llm)
        fintech_defn = SchemaRegistry.get(BusinessContext.FINTECH)
        fintech_gen = SQLQuestionGenerator(llm, schema_definition=fintech_defn)

        factory = (
            lambda ctx: fintech_gen if ctx == BusinessContext.FINTECH else default_gen
        )
        pipeline = SQLQuestionPipeline(
            retrieval_service=MagicMock(),
            sql_generator=default_gen,
            generator_factory=factory,
        )

        results = pipeline._generate_with_retry(
            role=RoleType.BACKEND_ENGINEER,
            level=SeniorityLevel.MID,
            n=1,
            business_context=BusinessContext.FINTECH,
        )

        assert len(results) == 1
        assert "accounts" in results[0].db_schema
        assert "employees" not in results[0].db_schema

    def test_generic_retry_stamps_generic_schema_on_question(self):
        """Integration: GENERIC retry path produces Question with HR DDL."""
        llm = _make_llm(_GENERIC_VALID_JSON)
        default_gen = SQLQuestionGenerator(llm)
        fintech_gen = MagicMock(spec=SQLQuestionGenerator)

        factory = (
            lambda ctx: fintech_gen if ctx == BusinessContext.FINTECH else default_gen
        )
        pipeline = SQLQuestionPipeline(
            retrieval_service=MagicMock(),
            sql_generator=default_gen,
            generator_factory=factory,
        )

        results = pipeline._generate_with_retry(
            role=RoleType.BACKEND_ENGINEER,
            level=SeniorityLevel.MID,
            n=1,
            business_context=BusinessContext.GENERIC,
        )

        assert len(results) == 1
        assert "employees" in results[0].db_schema
        assert "accounts" not in results[0].db_schema


# ── ECOMMERCE / SAAS schema stamping ─────────────────────────────────────────

_ECOMMERCE_VALID_JSON = json.dumps(
    [
        {
            "prompt": "List all delivered orders with customer names.",
            "reference_query": "SELECT c.name, o.id FROM customers c JOIN orders o ON o.customer_id = c.id WHERE o.status = 'delivered'",
            "test_cases": [
                {
                    "expected_query": "SELECT c.name, o.id FROM customers c JOIN orders o ON o.customer_id = c.id WHERE o.status = 'delivered'",
                    "ordered": False,
                }
            ],
        }
    ]
)

_SAAS_VALID_JSON = json.dumps(
    [
        {
            "prompt": "List all active subscriptions with tenant and plan name.",
            "reference_query": "SELECT t.name, p.name FROM tenants t JOIN subscriptions s ON s.tenant_id = t.id JOIN plans p ON p.id = s.plan_id WHERE s.status = 'active'",
            "test_cases": [
                {
                    "expected_query": "SELECT t.name, p.name FROM tenants t JOIN subscriptions s ON s.tenant_id = t.id JOIN plans p ON p.id = s.plan_id WHERE s.status = 'active'",
                    "ordered": False,
                }
            ],
        }
    ]
)


class TestEcommerceSchemaStamping:
    def test_ecommerce_generator_stamps_ecommerce_db_schema(self):
        llm = _make_llm(_ECOMMERCE_VALID_JSON)
        defn = SchemaRegistry.get(BusinessContext.ECOMMERCE)
        gen = SQLQuestionGenerator(llm, schema_definition=defn)

        questions = gen.generate(role=RoleType.BACKEND_ENGINEER, level=SeniorityLevel.MID, n=1)

        assert len(questions) == 1
        assert "orders" in questions[0].db_schema
        assert "order_items" in questions[0].db_schema
        assert "employees" not in questions[0].db_schema

    def test_ecommerce_generator_stamps_ecommerce_db_seed_data(self):
        llm = _make_llm(_ECOMMERCE_VALID_JSON)
        defn = SchemaRegistry.get(BusinessContext.ECOMMERCE)
        gen = SQLQuestionGenerator(llm, schema_definition=defn)

        questions = gen.generate(role=RoleType.BACKEND_ENGINEER, level=SeniorityLevel.MID, n=1)

        assert "INSERT INTO orders" in questions[0].db_seed_data
        assert "INSERT INTO order_items" in questions[0].db_seed_data

    def test_factory_ecommerce_returns_ecommerce_scoped_generator(self):
        llm = _make_llm(_ECOMMERCE_VALID_JSON)
        default_gen = SQLQuestionGenerator(llm)
        factory = _build_sql_generator_factory(llm, default_gen)

        ecom_gen = factory(BusinessContext.ECOMMERCE)
        assert "orders" in ecom_gen._db.get_schema_sql()
        assert "employees" not in ecom_gen._db.get_schema_sql()

    def test_ecommerce_retry_stamps_ecommerce_schema(self):
        llm = _make_llm(_ECOMMERCE_VALID_JSON)
        default_gen = SQLQuestionGenerator(llm)
        factory = _build_sql_generator_factory(llm, default_gen)
        pipeline = SQLQuestionPipeline(
            retrieval_service=MagicMock(),
            sql_generator=default_gen,
            generator_factory=factory,
        )

        results = pipeline._generate_with_retry(
            role=RoleType.BACKEND_ENGINEER,
            level=SeniorityLevel.MID,
            n=1,
            business_context=BusinessContext.ECOMMERCE,
        )

        assert len(results) == 1
        assert "orders" in results[0].db_schema
        assert "employees" not in results[0].db_schema

    def test_ecommerce_in_metadata_only_set(self):
        assert BusinessContext.ECOMMERCE in _BUSINESS_CONTEXT_METADATA_ONLY


class TestSaasSchemaStamping:
    def test_saas_generator_stamps_saas_db_schema(self):
        llm = _make_llm(_SAAS_VALID_JSON)
        defn = SchemaRegistry.get(BusinessContext.SAAS)
        gen = SQLQuestionGenerator(llm, schema_definition=defn)

        questions = gen.generate(role=RoleType.BACKEND_ENGINEER, level=SeniorityLevel.MID, n=1)

        assert len(questions) == 1
        assert "tenants" in questions[0].db_schema
        assert "subscriptions" in questions[0].db_schema
        assert "employees" not in questions[0].db_schema

    def test_saas_generator_stamps_saas_db_seed_data(self):
        llm = _make_llm(_SAAS_VALID_JSON)
        defn = SchemaRegistry.get(BusinessContext.SAAS)
        gen = SQLQuestionGenerator(llm, schema_definition=defn)

        questions = gen.generate(role=RoleType.BACKEND_ENGINEER, level=SeniorityLevel.MID, n=1)

        assert "INSERT INTO tenants" in questions[0].db_seed_data
        assert "INSERT INTO usage_events" in questions[0].db_seed_data

    def test_factory_saas_returns_saas_scoped_generator(self):
        llm = _make_llm(_SAAS_VALID_JSON)
        default_gen = SQLQuestionGenerator(llm)
        factory = _build_sql_generator_factory(llm, default_gen)

        saas_gen = factory(BusinessContext.SAAS)
        assert "tenants" in saas_gen._db.get_schema_sql()
        assert "employees" not in saas_gen._db.get_schema_sql()

    def test_saas_retry_stamps_saas_schema(self):
        llm = _make_llm(_SAAS_VALID_JSON)
        default_gen = SQLQuestionGenerator(llm)
        factory = _build_sql_generator_factory(llm, default_gen)
        pipeline = SQLQuestionPipeline(
            retrieval_service=MagicMock(),
            sql_generator=default_gen,
            generator_factory=factory,
        )

        results = pipeline._generate_with_retry(
            role=RoleType.BACKEND_ENGINEER,
            level=SeniorityLevel.MID,
            n=1,
            business_context=BusinessContext.SAAS,
        )

        assert len(results) == 1
        assert "tenants" in results[0].db_schema
        assert "employees" not in results[0].db_schema

    def test_saas_in_metadata_only_set(self):
        assert BusinessContext.SAAS in _BUSINESS_CONTEXT_METADATA_ONLY
