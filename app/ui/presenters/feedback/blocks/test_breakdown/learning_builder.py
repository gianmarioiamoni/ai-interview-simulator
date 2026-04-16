# app/ui/presenters/feedback/blocks/test_breakdown/learning_builder.py

from domain.contracts.feedback.error_type import ErrorType
from app.contracts.feedback_bundle import LearningSuggestion


class LearningBuilder:

    def build(self, error_type):

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
