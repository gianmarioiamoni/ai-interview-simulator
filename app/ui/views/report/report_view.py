# app/ui/views/report/report_view.py

from .report_view_model_builder import ReportViewModelBuilder
from .report_renderer import ReportRenderer


class ReportViewFacade:

    def __init__(self):
        self.vm_builder = ReportViewModelBuilder()
        self.renderer = ReportRenderer()

    def build(self, report):
        vm = self.vm_builder.build(report)
        return self.renderer.render(vm)


def build_report_markdown(report):
    return ReportViewFacade().build(report)
