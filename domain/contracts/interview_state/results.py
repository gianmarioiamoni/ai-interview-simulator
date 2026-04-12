# domain/contracts/interview_state/results.py

from typing import Optional

from domain.contracts.question.question import Question, QuestionType
from domain.contracts.question.question_evaluation import QuestionEvaluation
from domain.contracts.execution.execution_result import ExecutionResult
from domain.contracts.question.question_result import QuestionResult


class InterviewStateResultsMixin:
    # =========================================================
    # RESULT MANAGEMENT
    # =========================================================

    def register_evaluation(self, evaluation: QuestionEvaluation):

        qid = evaluation.question_id

        result = self.results_by_question.get(qid)

        question = next((q for q in self.questions if q.id == qid), None)

        if result is None:
            result = QuestionResult(
                question_id=qid,
                question=question,
            )

        else:
            if result.question is None:
                result = result.model_copy(update={"question": question})

        result = result.model_copy(update={"evaluation": evaluation})

        new_map = dict(self.results_by_question)
        new_map[qid] = result

        self.results_by_question = new_map

    # ---------------------------------------------------------

    def register_execution(self, execution: ExecutionResult):

        qid = execution.question_id

        result = self.results_by_question.get(qid)

        question = next((q for q in self.questions if q.id == qid), None)

        if result is None:
            result = QuestionResult(
                question_id=qid,
                question=question,
            )

        else:
            if result.question is None:
                result = result.model_copy(update={"question": question})

        result = result.model_copy(update={"execution": execution})

        new_map = dict(self.results_by_question)
        new_map[qid] = result

        self.results_by_question = new_map

    # ---------------------------------------------------------

    def get_result_for_question(self, question_id: str) -> Optional[QuestionResult]:

        return self.results_by_question.get(question_id)

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
