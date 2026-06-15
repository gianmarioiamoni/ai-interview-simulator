# services/hint_rules/sql_hint_rules.py

from typing import List


class SQLHintRules:

    @staticmethod
    def generate(query: str, *, has_failures: bool = False) -> List[str]:
        """
        Generate style hints for a SQL query.

        When has_failures is True (test cases are failing), style hints are
        suppressed because the primary issue is correctness, not style.
        """

        if not query:
            return []

        if has_failures:
            return []

        q = query.lower()

        hints: List[str] = []

        if "limit" not in q:
            hints.append(
                "Your query may return too many rows. Consider adding a LIMIT clause."
            )

        if "order by" not in q:
            hints.append("Results may not be deterministic. Consider adding ORDER BY.")

        if "select *" in q:
            hints.append(
                "Avoid SELECT *. Specify only required columns for better performance."
            )

        return hints
