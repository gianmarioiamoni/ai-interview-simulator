import sqlite3
import logging
from typing import List, Tuple

logger = logging.getLogger(__name__)


class SQLEvaluator:

    def evaluate(
        self,
        cursor: sqlite3.Cursor,
        candidate_query: str,
        reference_query: str,
        ordered: bool = True,
    ) -> tuple[bool, List[Tuple], List[Tuple]]:

        # ---------------------------------------------------------
        # Execute candidate query
        # ---------------------------------------------------------

        cursor.execute(candidate_query)
        candidate_rows = cursor.fetchall()

        # ---------------------------------------------------------
        # Execute reference solution
        # ---------------------------------------------------------

        cursor.execute(reference_query)
        reference_rows = cursor.fetchall()

        # ---------------------------------------------------------
        # Normalize
        # ---------------------------------------------------------

        candidate_rows = self._normalize(candidate_rows)
        reference_rows = self._normalize(reference_rows)

        # ---------------------------------------------------------
        # Compare
        # ---------------------------------------------------------

        if ordered:

            success = candidate_rows == reference_rows

        else:

            success = sorted(candidate_rows) == sorted(reference_rows)

        return success, candidate_rows, reference_rows

    # ---------------------------------------------------------

    def _normalize(self, rows):

        normalized = []

        for row in rows:

            normalized.append(
                tuple(
                    str(value).strip() if value is not None else None for value in row
                )
            )

        return normalized
