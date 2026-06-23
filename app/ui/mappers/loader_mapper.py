# app/ui/mappers/loader_mapper.py

from app.ui.constants.loader_steps import LoaderStep


def map_loader_text(step: LoaderStep | None) -> str:

    if step is None:
        return ""

    mapping = {
        # SETUP
        LoaderStep.GENERATING_STRUCTURE: "🧠 Designing interview structure...",
        LoaderStep.GENERATING_QUESTIONS: "📚 Generating questions. This may take a while. Please wait...",
        LoaderStep.GENERATING_TESTS: "🧪 Preparing test cases. This may take few seconds...",
        LoaderStep.FINALIZING: "⚙️ Finalizing interview...",

        # SUBMIT
        LoaderStep.SUBMITTING: "👉 Submitting your answer...",
        LoaderStep.RUNNING_EXECUTION: "💻 Running execution...",
        LoaderStep.ANALYZING: "🧪 Analyzing results...",
        LoaderStep.GENERATING_FEEDBACK: "💬 Generating feedback...",

        # NAVIGATION
        LoaderStep.LOADING_NEXT_QUESTION: "⏭️ Loading next question...",

        # REPORT
        LoaderStep.PREPARING_REPORT: "📊 Preparing report data...",
        LoaderStep.ANALYZING_RESULTS: "🧪 Analyzing interview performance...",
        LoaderStep.GENERATING_REPORT: "📄 Generating final report...",
        LoaderStep.FINALIZING_REPORT: "⚙️ Finalizing report...",
    }

    return mapping.get(step, "Processing...")


def map_loader_progress(step: LoaderStep | None) -> int:

    if step is None:
        return 0

    mapping = {
        # SETUP
        LoaderStep.GENERATING_STRUCTURE: 10,
        LoaderStep.GENERATING_QUESTIONS: 40,
        LoaderStep.GENERATING_TESTS: 70,
        LoaderStep.FINALIZING: 90,

        # SUBMIT
        LoaderStep.SUBMITTING: 10,
        LoaderStep.RUNNING_EXECUTION: 40,
        LoaderStep.ANALYZING: 70,
        LoaderStep.GENERATING_FEEDBACK: 90,

        # NAVIGATION
        LoaderStep.LOADING_NEXT_QUESTION: 30,

        # REPORT
        LoaderStep.PREPARING_REPORT: 10,
        LoaderStep.ANALYZING_RESULTS: 40,
        LoaderStep.GENERATING_REPORT: 70,
        LoaderStep.FINALIZING_REPORT: 90,
    }

    return mapping.get(step, 0)
