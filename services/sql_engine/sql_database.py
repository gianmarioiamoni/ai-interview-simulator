# services/sql_engine/sql_database.py

import sqlite3

from services.sql_engine.schema_definition import SchemaDefinition


class SQLDatabase:
    def __init__(self, schema_definition: SchemaDefinition | None = None) -> None:
        if schema_definition is None:
            from services.sql_engine.schema_registry import SchemaRegistry
            from domain.contracts.interview.business_context import BusinessContext
            schema_definition = SchemaRegistry.get(BusinessContext.GENERIC)

        self._schema_sql = schema_definition.schema_sql
        self._seed_sql = schema_definition.seed_sql

        self._connection = sqlite3.connect(":memory:")
        self._initialize()

    # =====================================================
    # PUBLIC API
    # =====================================================

    @property
    def connection(self) -> sqlite3.Connection:
        return self._connection

    def get_schema_sql(self) -> str:
        return self._schema_sql

    def get_seed_sql(self) -> str:
        return self._seed_sql

    def get_fresh_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(":memory:")
        cursor = conn.cursor()

        cursor.executescript(self._schema_sql)
        cursor.executescript(self._seed_sql)

        return conn

    # =====================================================
    # INTERNAL
    # =====================================================

    def _initialize(self) -> None:
        cursor = self._connection.cursor()
        cursor.executescript(self._schema_sql)
        cursor.executescript(self._seed_sql)
        self._connection.commit()
