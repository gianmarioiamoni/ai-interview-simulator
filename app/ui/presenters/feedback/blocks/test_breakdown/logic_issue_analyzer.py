# app/ui/presenters/feedback/blocks/test_breakdown/logic_issue_analyzer.py

from domain.contracts.feedback.error_type import ErrorType


class LogicIssueAnalyzer:

    def infer(self, expected, actual, error_type):

        if error_type != ErrorType.LOGIC:
            return None

        try:

            # =====================================================
            # SQL DETECTION (PRIORITY)
            # =====================================================

            if self._is_sql_result(expected, actual):
                return self._infer_sql_issue(expected, actual)

            # =====================================================
            # NUMERIC ANALYSIS (CODING)
            # =====================================================

            if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):

                if actual > expected:
                    return "Result is too large → possible double counting or incorrect aggregation"

                if actual < expected:
                    return "Result is too small → missing elements or incomplete logic"

            # =====================================================
            # LIST ANALYSIS (CODING)
            # =====================================================

            if isinstance(expected, list) and isinstance(actual, list):

                # Length mismatch
                if len(actual) != len(expected):

                    if len(actual) > len(expected):
                        return "Extra elements detected → possible duplication or incorrect loop logic"

                    return "Missing elements → incomplete iteration or filtering logic"

                # Same elements, wrong order
                if sorted(actual) == sorted(expected) and actual != expected:
                    return "Correct elements but wrong order"

                # Same length, different content
                if expected != actual:
                    return "Elements differ → logic error in transformation"

        except Exception:
            return None

        return None

    # =====================================================
    # SQL ANALYSIS
    # =====================================================

    def _infer_sql_issue(self, expected, actual):

        if expected is None or actual is None:
            return None

        try:
            expected_set = set(expected)
            actual_set = set(actual)

            # Completely wrong result
            if not expected_set.intersection(actual_set):
                return "Query logic is incorrect (no matching rows)"

            # Missing rows
            if len(actual_set) < len(expected_set):
                return "Some expected rows are missing (check JOINs or filters)"

            # Extra rows
            if len(actual_set) > len(expected_set):
                return "Query returns extra rows (check filtering conditions)"

            # Same size but different rows
            if expected_set != actual_set:
                return "Rows differ (possible JOIN or aggregation issue)"

            # Duplicate rows (classic SQL bug)
            if len(actual) != len(set(actual)):
                return "Duplicate rows detected (missing DISTINCT or incorrect JOIN)"

        except Exception:
            return None

        return None

    # =====================================================
    # DETECTION
    # =====================================================

    def _is_sql_result(self, expected, actual):

        if not isinstance(expected, list) or not isinstance(actual, list):
            return False

        if not expected or not actual:
            return False

        # SQL results → list of tuples
        return isinstance(expected[0], tuple)
