# services/sql_engine/sql_result_validator.py

# SQLResultValidator
#
# Responsibility:
# - Validates SQL query results against expected rows
# - Normalizes and sorts rows for deterministic comparison
# - Does not execute queries
# - Does not build ExecutionResult

from typing import Any


class SQLResultValidator:
    def validate(
        self,
        expected_rows: list[tuple[Any, ...]],
        actual_rows: list[tuple[Any, ...]],
    ) -> bool:

        normalized_expected = self._normalize(expected_rows)
        normalized_actual = self._normalize(actual_rows)

        return normalized_expected == normalized_actual

    def _normalize(
        self,
        rows: list[tuple[Any, ...]],
    ) -> list[tuple[Any, ...]]:

        # Ensure immutability + deterministic order
        normalized = [tuple(row) for row in rows]

        # Sort lexicographically
        return sorted(normalized)
