# services/evaluation_engine.py

from domain.contracts.question import Question
from domain.contracts.question_evaluation import QuestionEvaluation

from services.question_evaluation_service import QuestionEvaluationService


class EvaluationEngine:
    # Application-level engine responsible for evaluating answers.
    # Wraps QuestionEvaluationService so the evaluation logic
    # can later be reused inside LangGraph nodes.

    def __init__(self, service: QuestionEvaluationService | None = None):

        self._service = service or QuestionEvaluationService()

    def evaluate(
        self,
        question: Question,
        answer_text: str,
    ) -> QuestionEvaluation:

        return self._service.evaluate(
            question=question,
            answer_text=answer_text,
        )
