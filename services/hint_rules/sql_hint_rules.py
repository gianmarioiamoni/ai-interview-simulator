# services/hint_rules/sql_hint_rules.py

from typing import List


class SQLHintRules:

    @staticmethod
    def generate(query: str) -> List[str]:

        if not query:
            return []

        q = query.lower()

        hints: List[str] = []

        # -----------------------------------------------------
        # LIMIT missing
        # -----------------------------------------------------

        if "limit" not in q:
            hints.append(
                "Your query may return too many rows. Consider adding a LIMIT clause."
            )

        # -----------------------------------------------------
        # ORDER BY missing
        # -----------------------------------------------------

        if "order by" not in q:
            hints.append("Results may not be deterministic. Consider adding ORDER BY.")

        # -----------------------------------------------------
        # SELECT *
        # -----------------------------------------------------

        if "select *" in q:
            hints.append(
                "Avoid SELECT *. Specify only required columns for better performance."
            )

        return hints
