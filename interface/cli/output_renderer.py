# interface/cli/output_renderer.py

# CLIOutputRenderer
#
# Responsibility:
# - rendering leggibile
# - No direct state modifications
# - Return raw data

from domain.contracts.question import Question
from domain.contracts.question_evaluation import QuestionEvaluation
from domain.contracts.execution_result import ExecutionResult


class CLIOutputRenderer:
    # Responsible only for formatting and printing output

    def render_question(self, question: Question) -> None:
        print("\n----------------------------------------")
        print(f"Question ({question.type.upper()}):")
        print(question.prompt)
        print("----------------------------------------")

    def render_execution_result(self, result: ExecutionResult) -> None:
        print("\nExecution Result:")
        print(f"Status: {result.status}")
        print(f"Details: {result.details}")

    def render_evaluation(self, evaluation: QuestionEvaluation) -> None:
        print("\nEvaluation:")
        print(f"Score: {evaluation.score}")
        print(f"Feedback: {evaluation.feedback}")

    def render_completion(self, total_score: float) -> None:
        print("\n========================================")
        print("Interview Completed")
        print(f"Final Score: {total_score}")
        print("========================================")
