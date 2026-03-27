# app/ui/presenters/result_presenter.py

from app.ui.presenters.mappers.execution_mapper import ExecutionMapper
from app.ui.view_models.result_view_model import ResultViewModel


class ResultPresenter:

    def present(self, state, result, _question_text):

        evaluation = result.evaluation
        execution = result.execution

        # -----------------------------------------------------
        # Execution mapping
        # -----------------------------------------------------

        execution_vm = ExecutionMapper.map([execution] if execution else [])
        errors = [r.error for r in execution_vm if r.error]

        # -----------------------------------------------------
        # USE GRAPH OUTPUT
        # -----------------------------------------------------
        
        bundle = getattr(state, "last_feedback_bundle", None)

        feedback_md = bundle.markdown if bundle else ""

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
