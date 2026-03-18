# domain/contracts/interview_state/results.py

from typing import Optional

from domain.contracts.question import Question, QuestionType
from domain.contracts.question_evaluation import QuestionEvaluation
from domain.contracts.execution_result import ExecutionResult
from domain.contracts.question_result import QuestionResult


class InterviewStateResultsMixin:
    # =========================================================
    # RESULT MANAGEMENT
    # =========================================================

    def register_evaluation(self, evaluation: QuestionEvaluation):

        qid = evaluation.question_id

        result = self.results_by_question.get(qid)

        if result is None:
            result = QuestionResult(question_id=qid)

        result = result.model_copy(update={"evaluation": evaluation})

        new_map = dict(self.results_by_question)
        new_map[qid] = result

        self.results_by_question = new_map

    # ---------------------------------------------------------

    def register_execution(self, execution: ExecutionResult):

        qid = execution.question_id

        result = self.results_by_question.get(qid)

        if result is None:
            result = QuestionResult(question_id=qid)

        result = result.model_copy(update={"execution": execution})

        new_map = dict(self.results_by_question)
        new_map[qid] = result

        self.results_by_question = new_map

    # ---------------------------------------------------------

    def get_result_for_question(self, question_id: str) -> Optional[QuestionResult]:

        return self.results_by_question.get(question_id)

    # ---------------------------------------------------------

    def get_last_result(self):

        if self.last_answer is None:
            return None

        return self.results_by_question.get(self.last_answer.question_id)

    # ---------------------------------------------------------

    def is_question_processed(self, question: Question) -> bool:

        result = self.results_by_question.get(question.id)

        if result is None:
            return False

        if question.type == QuestionType.WRITTEN:
            return result.evaluation is not None

        if question.type in (QuestionType.CODING, QuestionType.DATABASE):
            return result.execution is not None

        return False
