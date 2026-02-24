# services/sql_engine/sql_executor.py

# SQLExecutor
#
# Responsibility:
# Executes SQL queries against a provided SQLite connection.
# Handles SQL syntax/runtime errors.
# Does not perform result validation.

import sqlite3
from typing import Any


class SQLExecutionOutput:
    def __init__(
        self,
        success: bool,
        rows: list[tuple[Any, ...]] | None = None,
        columns: list[str] | None = None,
        error: str | None = None,
    ) -> None:
        self.success = success
        self.rows = rows or []
        self.columns = columns or []
        self.error = error


class SQLExecutor:

    def _get_cursor(self, connection: sqlite3.Connection):
        return connection.cursor()

    def execute(
        self,
        connection: sqlite3.Connection,
        query: str,
    ) -> SQLExecutionOutput:

        cursor = self._get_cursor(connection)

        try:
            cursor.execute(query)

            # Fetch only if SELECT-like
            if query.strip().lower().startswith("select"):
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
            else:
                connection.commit()
                rows = []
                columns = []

            return SQLExecutionOutput(
                success=True,
                rows=rows,
                columns=columns,
            )

        except sqlite3.OperationalError as e:
            return SQLExecutionOutput(
                success=False,
                error=str(e),
            )

        except Exception as e:
            return SQLExecutionOutput(
                success=False,
                error=str(e),
            )
