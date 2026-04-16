# app/ui/presenters/feedback/blocks/test_breakdown/logic_issue_analyzer.py

from domain.contracts.feedback.error_type import ErrorType


class LogicIssueAnalyzer:

    def infer(self, expected, actual, error_type):

        if error_type != ErrorType.LOGIC:
            return None

        try:
            if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
                if actual > expected:
                    return "Result is too large → possible double counting or incorrect aggregation"
                if actual < expected:
                    return "Result is too small → missing elements or incomplete logic"

            if isinstance(expected, list) and isinstance(actual, list):
                if len(actual) != len(expected):
                    return "Output length mismatch → missing or extra elements"

                if sorted(actual) == sorted(expected) and actual != expected:
                    return "Correct elements but wrong order"

        except Exception:
            return None

        return None
