# app/execution/sql_executor.py

import sqlite3


class SQLExecutor:
    # Executes SQL queries against a temporary SQLite database.

    def __init__(self):

        self.conn = sqlite3.connect(":memory:")

    def execute(self, query: str):

        try:

            cursor = self.conn.cursor()

            cursor.execute(query)

            rows = cursor.fetchall()

            return {
                "success": True,
                "rows": rows,
            }

        except Exception as e:

            return {
                "success": False,
                "error": str(e),
            }
