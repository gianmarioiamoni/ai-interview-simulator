# tests/services/sql_engine/test_sql_database_composition.py

import sqlite3
import pytest

from domain.contracts.interview.business_context import BusinessContext
from services.sql_engine.schema_definition import SchemaDefinition
from services.sql_engine.schema_registry import SchemaRegistry
from services.sql_engine.sql_database import SQLDatabase


class TestSQLDatabaseComposition:
    def test_default_init_uses_generic_schema(self):
        db = SQLDatabase()
        cursor = db.connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM employees")
        assert cursor.fetchone()[0] == 4

    def test_explicit_generic_schema(self):
        defn = SchemaRegistry.get(BusinessContext.GENERIC)
        db = SQLDatabase(defn)
        cursor = db.connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM departments")
        assert cursor.fetchone()[0] == 3

    def test_fintech_schema_loads_accounts(self):
        defn = SchemaRegistry.get(BusinessContext.FINTECH)
        db = SQLDatabase(defn)
        cursor = db.connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM accounts")
        assert cursor.fetchone()[0] == 6

    def test_fintech_schema_loads_transactions(self):
        defn = SchemaRegistry.get(BusinessContext.FINTECH)
        db = SQLDatabase(defn)
        cursor = db.connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM transactions")
        assert cursor.fetchone()[0] == 10

    def test_fintech_schema_loads_portfolios(self):
        defn = SchemaRegistry.get(BusinessContext.FINTECH)
        db = SQLDatabase(defn)
        cursor = db.connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM portfolios")
        assert cursor.fetchone()[0] == 4

    def test_fintech_no_employees_table(self):
        defn = SchemaRegistry.get(BusinessContext.FINTECH)
        db = SQLDatabase(defn)
        cursor = db.connection.cursor()
        with pytest.raises(Exception):
            cursor.execute("SELECT * FROM employees")

    def test_get_schema_sql_returns_definition_sql(self):
        defn = SchemaRegistry.get(BusinessContext.FINTECH)
        db = SQLDatabase(defn)
        assert db.get_schema_sql() == defn.schema_sql

    def test_get_seed_sql_returns_definition_seed(self):
        defn = SchemaRegistry.get(BusinessContext.FINTECH)
        db = SQLDatabase(defn)
        assert db.get_seed_sql() == defn.seed_sql

    def test_fresh_connection_is_isolated(self):
        defn = SchemaRegistry.get(BusinessContext.FINTECH)
        db = SQLDatabase(defn)
        conn = db.get_fresh_connection()
        assert conn is not db.connection
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM accounts")
        assert cursor.fetchone()[0] == 6

    def test_custom_schema_definition(self):
        custom_defn = SchemaDefinition(
            context_key=BusinessContext.GENERIC,
            schema_sql="CREATE TABLE widgets (id INTEGER PRIMARY KEY, name TEXT);",
            seed_sql="INSERT INTO widgets VALUES (1, 'cog');",
        )
        db = SQLDatabase(custom_defn)
        cursor = db.connection.cursor()
        cursor.execute("SELECT name FROM widgets")
        assert cursor.fetchone()[0] == "cog"

    def test_no_subclassing_required(self):
        fintech_defn = SchemaRegistry.get(BusinessContext.FINTECH)
        db = SQLDatabase(fintech_defn)
        assert type(db) is SQLDatabase
