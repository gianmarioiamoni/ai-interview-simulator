# app/ui/views/report_view.py
# EPIC-V13-05 Phase 5 — LearningProgress separately injected into report facade (Plane B).

from __future__ import annotations

from domain.contracts.progress.learning_progress import LearningProgress

from app.ui.views.report.report_view_model_builder import ReportViewModelBuilder
from app.ui.views.report.report_renderer import ReportRenderer


class ReportViewFacade:

    def __init__(self):
        self.vm_builder = ReportViewModelBuilder()
        self.renderer = ReportRenderer()

    def build(
        self,
        report,
        learning_progress: LearningProgress | None = None,
    ):
        vm = self.vm_builder.build(report, learning_progress=learning_progress)
        return self.renderer.render(vm)


def build_report_markdown(
    report,
    learning_progress: LearningProgress | None = None,
):
    return ReportViewFacade().build(report, learning_progress=learning_progress)
