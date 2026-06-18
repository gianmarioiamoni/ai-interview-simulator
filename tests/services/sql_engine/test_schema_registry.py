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

    def test_ecommerce_returns_ecommerce_definition(self):
        defn = SchemaRegistry.get(BusinessContext.ECOMMERCE)
        assert defn.context_key == BusinessContext.ECOMMERCE

    def test_saas_returns_saas_definition(self):
        defn = SchemaRegistry.get(BusinessContext.SAAS)
        assert defn.context_key == BusinessContext.SAAS

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


class TestEcommerceSchema:
    def test_ecommerce_schema_contains_expected_tables(self):
        defn = SchemaRegistry.get(BusinessContext.ECOMMERCE)
        for table in ("customers", "products", "categories", "orders", "order_items"):
            assert table in defn.schema_sql

    def test_ecommerce_schema_not_contain_hr_tables(self):
        defn = SchemaRegistry.get(BusinessContext.ECOMMERCE)
        assert "employees" not in defn.schema_sql
        assert "departments" not in defn.schema_sql

    def test_ecommerce_schema_not_contain_fintech_tables(self):
        defn = SchemaRegistry.get(BusinessContext.ECOMMERCE)
        assert "accounts" not in defn.schema_sql
        assert "transactions" not in defn.schema_sql

    def test_ecommerce_seed_data_present(self):
        defn = SchemaRegistry.get(BusinessContext.ECOMMERCE)
        for table in ("customers", "products", "categories", "orders", "order_items"):
            assert f"INSERT INTO {table}" in defn.seed_sql

    def test_ecommerce_referential_integrity(self):
        """SQLite must accept DDL + seed without FK violations."""
        from services.sql_engine.sql_database import SQLDatabase
        defn = SchemaRegistry.get(BusinessContext.ECOMMERCE)
        db = SQLDatabase(schema_definition=defn)
        result = db.connection.execute("SELECT COUNT(*) FROM order_items").fetchall()
        assert result[0][0] == 7

    def test_ecommerce_has_domain_tags(self):
        defn = SchemaRegistry.get(BusinessContext.ECOMMERCE)
        assert SqlDomain.JOIN in defn.domain_tags
        assert SqlDomain.GROUP_BY in defn.domain_tags

    def test_ecommerce_has_summary_hint(self):
        defn = SchemaRegistry.get(BusinessContext.ECOMMERCE)
        assert defn.summary_hint is not None
        assert "order" in defn.summary_hint.lower()

    def test_ecommerce_join_query_executes(self):
        from services.sql_engine.sql_database import SQLDatabase
        defn = SchemaRegistry.get(BusinessContext.ECOMMERCE)
        db = SQLDatabase(schema_definition=defn)
        result = db.connection.execute(
            "SELECT c.name, COUNT(o.id) FROM customers c "
            "JOIN orders o ON o.customer_id = c.id GROUP BY c.id"
        ).fetchall()
        assert len(result) > 0

    def test_ecommerce_aggregation_query_executes(self):
        from services.sql_engine.sql_database import SQLDatabase
        defn = SchemaRegistry.get(BusinessContext.ECOMMERCE)
        db = SQLDatabase(schema_definition=defn)
        result = db.connection.execute(
            "SELECT p.name, SUM(oi.quantity) as total_sold "
            "FROM products p JOIN order_items oi ON oi.product_id = p.id "
            "GROUP BY p.id HAVING total_sold > 0"
        ).fetchall()
        assert len(result) > 0


class TestSaasSchema:
    def test_saas_schema_contains_expected_tables(self):
        defn = SchemaRegistry.get(BusinessContext.SAAS)
        for table in ("tenants", "users", "plans", "subscriptions", "usage_events"):
            assert table in defn.schema_sql

    def test_saas_schema_not_contain_hr_tables(self):
        defn = SchemaRegistry.get(BusinessContext.SAAS)
        assert "employees" not in defn.schema_sql
        assert "departments" not in defn.schema_sql

    def test_saas_schema_not_contain_fintech_tables(self):
        defn = SchemaRegistry.get(BusinessContext.SAAS)
        assert "accounts" not in defn.schema_sql
        assert "transactions" not in defn.schema_sql

    def test_saas_seed_data_present(self):
        defn = SchemaRegistry.get(BusinessContext.SAAS)
        for table in ("tenants", "users", "plans", "subscriptions", "usage_events"):
            assert f"INSERT INTO {table}" in defn.seed_sql

    def test_saas_referential_integrity(self):
        from services.sql_engine.sql_database import SQLDatabase
        defn = SchemaRegistry.get(BusinessContext.SAAS)
        db = SQLDatabase(schema_definition=defn)
        result = db.connection.execute("SELECT COUNT(*) FROM usage_events").fetchall()
        assert result[0][0] == 10

    def test_saas_has_domain_tags(self):
        defn = SchemaRegistry.get(BusinessContext.SAAS)
        assert SqlDomain.JOIN in defn.domain_tags
        assert SqlDomain.GROUP_BY in defn.domain_tags

    def test_saas_has_summary_hint(self):
        defn = SchemaRegistry.get(BusinessContext.SAAS)
        assert defn.summary_hint is not None
        assert "saas" in defn.summary_hint.lower()

    def test_saas_join_query_executes(self):
        from services.sql_engine.sql_database import SQLDatabase
        defn = SchemaRegistry.get(BusinessContext.SAAS)
        db = SQLDatabase(schema_definition=defn)
        result = db.connection.execute(
            "SELECT t.name, p.name FROM tenants t "
            "JOIN subscriptions s ON s.tenant_id = t.id "
            "JOIN plans p ON p.id = s.plan_id"
        ).fetchall()
        assert len(result) > 0

    def test_saas_aggregation_query_executes(self):
        from services.sql_engine.sql_database import SQLDatabase
        defn = SchemaRegistry.get(BusinessContext.SAAS)
        db = SQLDatabase(schema_definition=defn)
        result = db.connection.execute(
            "SELECT t.name, SUM(ue.units) as total_units "
            "FROM tenants t JOIN usage_events ue ON ue.tenant_id = t.id "
            "GROUP BY t.id HAVING total_units > 100"
        ).fetchall()
        assert len(result) > 0


class TestHealthcareSchema:
    def test_healthcare_returns_healthcare_definition(self):
        defn = SchemaRegistry.get(BusinessContext.HEALTHCARE)
        assert defn.context_key == BusinessContext.HEALTHCARE

    def test_healthcare_schema_contains_expected_tables(self):
        defn = SchemaRegistry.get(BusinessContext.HEALTHCARE)
        for table in ("patients", "appointments", "diagnoses", "prescriptions", "providers"):
            assert table in defn.schema_sql

    def test_healthcare_schema_not_contain_hr_tables(self):
        defn = SchemaRegistry.get(BusinessContext.HEALTHCARE)
        assert "employees" not in defn.schema_sql
        assert "departments" not in defn.schema_sql

    def test_healthcare_schema_not_contain_fintech_tables(self):
        defn = SchemaRegistry.get(BusinessContext.HEALTHCARE)
        assert "accounts" not in defn.schema_sql
        assert "transactions" not in defn.schema_sql

    def test_healthcare_seed_data_present(self):
        defn = SchemaRegistry.get(BusinessContext.HEALTHCARE)
        for table in ("patients", "appointments", "diagnoses", "prescriptions", "providers"):
            assert f"INSERT INTO {table}" in defn.seed_sql

    def test_healthcare_referential_integrity(self):
        from services.sql_engine.sql_database import SQLDatabase
        defn = SchemaRegistry.get(BusinessContext.HEALTHCARE)
        db = SQLDatabase(schema_definition=defn)
        result = db.connection.execute("SELECT COUNT(*) FROM diagnoses").fetchall()
        assert result[0][0] == 8

    def test_healthcare_has_domain_tags(self):
        defn = SchemaRegistry.get(BusinessContext.HEALTHCARE)
        assert SqlDomain.JOIN in defn.domain_tags
        assert SqlDomain.GROUP_BY in defn.domain_tags

    def test_healthcare_has_summary_hint(self):
        defn = SchemaRegistry.get(BusinessContext.HEALTHCARE)
        assert defn.summary_hint is not None
        assert "patient" in defn.summary_hint.lower()

    def test_healthcare_has_vocabulary_hint(self):
        defn = SchemaRegistry.get(BusinessContext.HEALTHCARE)
        assert len(defn.vocabulary_hint) > 0
        assert "patient" in defn.vocabulary_hint

    def test_healthcare_join_query_executes(self):
        from services.sql_engine.sql_database import SQLDatabase
        defn = SchemaRegistry.get(BusinessContext.HEALTHCARE)
        db = SQLDatabase(schema_definition=defn)
        result = db.connection.execute(
            "SELECT p.name, COUNT(a.id) FROM patients p "
            "JOIN appointments a ON a.patient_id = p.id GROUP BY p.id"
        ).fetchall()
        assert len(result) > 0

    def test_healthcare_aggregation_query_executes(self):
        from services.sql_engine.sql_database import SQLDatabase
        defn = SchemaRegistry.get(BusinessContext.HEALTHCARE)
        db = SQLDatabase(schema_definition=defn)
        result = db.connection.execute(
            "SELECT pr.specialty, COUNT(DISTINCT d.patient_id) as patient_count "
            "FROM providers pr JOIN appointments a ON a.provider_id = pr.id "
            "JOIN diagnoses d ON d.appointment_id = a.id GROUP BY pr.specialty"
        ).fetchall()
        assert len(result) > 0
