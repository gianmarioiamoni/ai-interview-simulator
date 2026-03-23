# app/ui/presenters/result_presenter.py

from app.ui.presenters.mappers.execution_mapper import ExecutionMapper
from app.ui.presenters.feedback.feedback_builder import FeedbackBuilder
from app.ui.view_models.result_view_model import ResultViewModel


class ResultPresenter:

    def __init__(self):
        self._feedback_builder = FeedbackBuilder()

    def present(self, state, result, _question_text):

        evaluation = result.evaluation
        execution = result.execution

        execution_vm = ExecutionMapper.map([execution] if execution else [])
        errors = [r.error for r in execution_vm if r.error]

        feedback_md = self._feedback_builder.build(
            state,
            result,
            evaluation,
            execution,
        )

        score = evaluation.score if evaluation else 0
        passed = evaluation.passed if evaluation else False

        return ResultViewModel(
            score=score,
            feedback_markdown=feedback_md,
            execution_results=execution_vm,
            errors=errors,
            passed=passed,
        )
