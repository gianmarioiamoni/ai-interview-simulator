# app/ui/presenters/result_presenter.py

from app.ui.presenters.mappers.execution_mapper import ExecutionMapper
from app.ui.presenters.feedback.feedback_builder import FeedbackBuilder
from app.ui.view_models.result_view_model import ResultViewModel


class ResultPresenter:

    def __init__(self):
        self._feedback_builder = FeedbackBuilder()

    def present(self, state, result, _question_text):

        print("DEBUG AI HINT:", result.ai_hint)

        evaluation = result.evaluation
        execution = result.execution

        # -----------------------------------------------------
        # Execution mapping
        # -----------------------------------------------------

        execution_vm = ExecutionMapper.map([execution] if execution else [])
        errors = [r.error for r in execution_vm if r.error]

        # -----------------------------------------------------
        # AI-aware feedback pipeline
        # -----------------------------------------------------

        feedback_bundle = self._feedback_builder.build(
            state,
            result,
            evaluation,
            execution,
        )

        feedback_md = feedback_bundle.markdown

        # -----------------------------------------------------
        # Evaluation
        # -----------------------------------------------------

        score = evaluation.score if evaluation else 0
        passed = evaluation.passed if evaluation else False

        # -----------------------------------------------------
        # ViewModel
        # -----------------------------------------------------

        return ResultViewModel(
            score=score,
            feedback_markdown=feedback_md,
            execution_results=execution_vm,
            errors=errors,
            passed=passed,
        )
