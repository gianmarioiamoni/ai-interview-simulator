# tests/services/sql_engine/test_schema_registry.py

import pytest

from domain.contracts.interview.business_context import BusinessContext
from domain.contracts.question.sql_domain import SqlDomain
from services.sql_engine.schema_definition import SchemaDefinition
from services.sql_engine.schema_registry import SchemaRegistry


class TestSchemaRegistryLookup:
    def test_generic_returns_generic_definition(self):
        defn = SchemaRegistry.get(BusinessContext.GENERIC)
        assert defn.context_key == BusinessContext.GENERIC

    def test_fintech_returns_fintech_definition(self):
        defn = SchemaRegistry.get(BusinessContext.FINTECH)
        assert defn.context_key == BusinessContext.FINTECH

    def test_ecommerce_falls_back_to_generic(self):
        defn = SchemaRegistry.get(BusinessContext.ECOMMERCE)
        assert defn.context_key == BusinessContext.GENERIC

    def test_saas_falls_back_to_generic(self):
        defn = SchemaRegistry.get(BusinessContext.SAAS)
        assert defn.context_key == BusinessContext.GENERIC

    def test_generic_schema_contains_hr_tables(self):
        defn = SchemaRegistry.get(BusinessContext.GENERIC)
        assert "employees" in defn.schema_sql
        assert "departments" in defn.schema_sql
        assert "projects" in defn.schema_sql

    def test_fintech_schema_contains_fintech_tables(self):
        defn = SchemaRegistry.get(BusinessContext.FINTECH)
        assert "accounts" in defn.schema_sql
        assert "transactions" in defn.schema_sql
        assert "customers" in defn.schema_sql
        assert "portfolios" in defn.schema_sql

    def test_fintech_schema_not_contain_hr_tables(self):
        defn = SchemaRegistry.get(BusinessContext.FINTECH)
        assert "employees" not in defn.schema_sql
        assert "departments" not in defn.schema_sql

    def test_generic_seed_data_present(self):
        defn = SchemaRegistry.get(BusinessContext.GENERIC)
        assert "INSERT INTO employees" in defn.seed_sql
        assert "INSERT INTO departments" in defn.seed_sql

    def test_fintech_seed_data_present(self):
        defn = SchemaRegistry.get(BusinessContext.FINTECH)
        assert "INSERT INTO accounts" in defn.seed_sql
        assert "INSERT INTO transactions" in defn.seed_sql

    def test_fintech_has_domain_tags(self):
        defn = SchemaRegistry.get(BusinessContext.FINTECH)
        assert SqlDomain.JOIN in defn.domain_tags
        assert SqlDomain.TRANSACTION in defn.domain_tags

    def test_fintech_has_summary_hint(self):
        defn = SchemaRegistry.get(BusinessContext.FINTECH)
        assert defn.summary_hint is not None
        assert len(defn.summary_hint) > 0

    def test_generic_summary_hint_is_none(self):
        defn = SchemaRegistry.get(BusinessContext.GENERIC)
        assert defn.summary_hint is None

    def test_returns_schema_definition_instance(self):
        defn = SchemaRegistry.get(BusinessContext.FINTECH)
        assert isinstance(defn, SchemaDefinition)


class TestSchemaDefinitionContract:
    def test_schema_definition_is_frozen(self):
        defn = SchemaRegistry.get(BusinessContext.GENERIC)
        with pytest.raises((AttributeError, TypeError)):
            defn.schema_sql = "mutated"  # type: ignore[misc]

    def test_schema_definition_fields_present(self):
        defn = SchemaRegistry.get(BusinessContext.FINTECH)
        assert defn.context_key is not None
        assert defn.schema_sql
        assert defn.seed_sql
        assert isinstance(defn.domain_tags, tuple)
