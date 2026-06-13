# app/ui/presenters/feedback/blocks/failure/edge_case_detector.py

from typing import Any


class EdgeCaseDetector:
    """
    Scans test results for boundary-value patterns that indicate edge-case
    failures (empty lists, 0/1 numeric boundaries).

    Stateless — safe to share across requests.
    """

    def detect(self, test_results: list[Any] | None) -> bool:
        if not test_results:
            return False

        for t in test_results:
            if t.status == "passed":
                continue
            if t.expected is None or t.actual is None:
                continue

            if t.expected == [] or t.actual == []:
                return True

            if isinstance(t.expected, (int, float)) and t.expected in (0, 1):
                return True

        return False
