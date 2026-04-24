from domain.contracts.feedback.error_type import ErrorType
from app.contracts.feedback_bundle import LearningSuggestion


class LearningBuilder:

    def build(self, error_type, question=None):

        is_sql = False

        if question and hasattr(question, "is_database"):
            is_sql = question.is_database()

        # -----------------------------------------------------
        # SQL BRANCH
        # -----------------------------------------------------

        if is_sql:

            if error_type == ErrorType.LOGIC:
                return [
                    LearningSuggestion(
                        topic="SQL query logic",
                        action="Verify JOIN conditions, filters, and aggregation logic",
                    )
                ]

            if error_type == ErrorType.RUNTIME:
                return [
                    LearningSuggestion(
                        topic="SQL execution",
                        action="Check syntax, table names, and column references",
                    )
                ]

            return [
                LearningSuggestion(
                    topic="SQL debugging",
                    action="Compare expected vs actual result sets to identify logic errors",
                )
            ]

        # -----------------------------------------------------
        # CODING (DEFAULT)
        # -----------------------------------------------------

        if error_type == ErrorType.LOGIC:
            return [
                LearningSuggestion(
                    topic="Algorithm correctness",
                    action="Focus on edge cases and verify output logic step-by-step",
                )
            ]

        if error_type == ErrorType.RUNTIME:
            return [
                LearningSuggestion(
                    topic="Runtime debugging",
                    action="Handle edge inputs and check for None / invalid values",
                )
            ]

        return [
            LearningSuggestion(
                topic="Debugging",
                action="Analyze failing test cases to identify incorrect logic paths",
            )
        ]
