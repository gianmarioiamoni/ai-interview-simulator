# app/ui/presenters/result_presenter.py

from app.ui.presenters.mappers.execution_mapper import ExecutionMapper
from app.ui.view_models.result_view_model import ResultViewModel


class ResultPresenter:

    def present(self, state, result, _question_text):

        execution = result.execution

        # -----------------------------------------------------
        # Execution mapping 
        # -----------------------------------------------------

        execution_vm = ExecutionMapper.map([execution] if execution else [])
        errors = [r.error for r in execution_vm if r.error]

        # -----------------------------------------------------
        # SINGLE SOURCE OF TRUTH → FEEDBACK BUNDLE
        # -----------------------------------------------------

        bundle = getattr(state, "last_feedback_bundle", None)

        feedback_md = bundle.markdown if bundle else ""

        # -----------------------------------------------------
        # REMOVE LEGACY EVALUATION DEPENDENCY
        # -----------------------------------------------------

        score = 0.0
        passed = False

        # optional: minimal derivation from bundle
        if bundle and bundle.overall_quality:
            passed = bundle.overall_quality in ["correct", "optimal"]

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
