# services/sql_engine/schema_summary_generator.py

# SchemaSummaryGenerator
#
# Responsibility:
# Generates a textual summary of the SQLite schema.
# Used for LLM prompting and debugging.

import sqlite3


class SchemaSummaryGenerator:
    def generate(self, connection: sqlite3.Connection) -> str:
        cursor = connection.cursor()

        # Get all user-defined tables
        cursor.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type='table'
            AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """
        )

        tables = [row[0] for row in cursor.fetchall()]

        summary_lines = []

        for table in tables:
            summary_lines.append(f"Table {table}:")
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()

            for column in columns:
                # column structure: (cid, name, type, notnull, default_value, pk)
                col_name = column[1]
                col_type = column[2]
                summary_lines.append(f"  - {col_name} ({col_type})")

            summary_lines.append("")

        fk_lines = self._collect_foreign_keys(cursor, tables)
        if fk_lines:
            summary_lines.append("Foreign keys:")
            summary_lines.extend(fk_lines)

        return "\n".join(summary_lines).strip()

    def _collect_foreign_keys(
        self, cursor: "sqlite3.Cursor", tables: list[str]
    ) -> list[str]:
        lines = []
        for table in tables:
            cursor.execute(f"PRAGMA foreign_key_list({table})")
            for fk in cursor.fetchall():
                # fk structure: (id, seq, table, from, to, on_update, on_delete, match)
                from_col = fk[3]
                ref_table = fk[2]
                ref_col = fk[4]
                lines.append(f"  - {table}.{from_col} → {ref_table}.{ref_col}")
        return lines
