# app/ui/constants/loader_steps.py

from domain.contracts.interview.loader_step import LoaderStep

SUBMIT_FLOW = [
    LoaderStep.SUBMITTING,
    LoaderStep.RUNNING_EXECUTION,
    LoaderStep.ANALYZING,
    LoaderStep.GENERATING_FEEDBACK,
]

REPORT_FLOW = [
    LoaderStep.PREPARING_REPORT,
    LoaderStep.ANALYZING_RESULTS,
    LoaderStep.GENERATING_REPORT,
    LoaderStep.FINALIZING_REPORT,
]

SETUP_FLOW = [
    LoaderStep.GENERATING_STRUCTURE,
    LoaderStep.GENERATING_QUESTIONS,
    LoaderStep.GENERATING_TESTS,
    LoaderStep.FINALIZING,
]

__all__ = ["LoaderStep", "SUBMIT_FLOW", "REPORT_FLOW", "SETUP_FLOW"]
