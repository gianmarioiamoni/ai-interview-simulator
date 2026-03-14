# app/ui/handlers/report_handler.py

from domain.contracts.question_evaluation import QuestionEvaluation

from app.runtime.interview_runtime import get_runtime_evaluation_service
from app.ui.views.report_view import build_report_markdown
from app.ui.ui_router import route_ui
from app.ui.ui_state import UIState
from app.ui.state_handlers import mapper


def view_report_handler(state_value):
    """
    Generates the final interview report and switches the UI to report view.
    Implemented as a generator to allow progressive UI updates.
    """

    # ---------------------------------------------------------
    # Step 1 — Switch UI to report section with loading message
    # ---------------------------------------------------------

    yield (
        *route_ui(UIState.REPORT),
        "⏳ Generating final report...",
    )

    evaluation_service = get_runtime_evaluation_service()

    # ---------------------------------------------------------
    # Step 2 — Build evaluation list from results
    # ---------------------------------------------------------

    per_question_evaluations = []

    for q in state_value.questions:

        result = state_value.results_by_question.get(q.id)

        if result is None:
            continue

        # -----------------------------------------------------
        # Written questions already have evaluation
        # -----------------------------------------------------

        if result.evaluation is not None:
            per_question_evaluations.append(result.evaluation)
            continue

        # -----------------------------------------------------
        # Coding / Database → derive evaluation from execution
        # -----------------------------------------------------

        if result.execution is not None:

            exec_res = result.execution

            if exec_res.total_tests and exec_res.total_tests > 0:
                score = (exec_res.passed_tests / exec_res.total_tests) * 100
            else:
                score = 100 if exec_res.success else 0

            evaluation = QuestionEvaluation(
                question_id=q.id,
                score=score,
                max_score=100,
                passed=exec_res.success,
                feedback=exec_res.error or "Execution evaluated automatically.",
                strengths=[],
                weaknesses=[],
                passed_tests=exec_res.passed_tests,
                total_tests=exec_res.total_tests,
                execution_status=exec_res.status.value,
            )

            per_question_evaluations.append(evaluation)

    # ---------------------------------------------------------
    # Step 3 — Generate final evaluation only once
    # ---------------------------------------------------------

    if state_value.final_evaluation is None:

        final_eval = evaluation_service.evaluate(
            per_question_evaluations=per_question_evaluations,
            questions=state_value.questions,
            interview_type=state_value.interview_type,
            role=state_value.role.type,
        )

        state_value.final_evaluation = final_eval

    # ---------------------------------------------------------
    # Step 4 — Build report DTO
    # ---------------------------------------------------------

    report = mapper.to_final_report_dto(state_value)

    # ---------------------------------------------------------
    # Step 5 — Render report markdown
    # ---------------------------------------------------------

    report_markdown = build_report_markdown(report)

    # ---------------------------------------------------------
    # Step 6 — Return final UI state
    # ---------------------------------------------------------

    yield (
        *route_ui(UIState.REPORT),
        report_markdown,
    )
