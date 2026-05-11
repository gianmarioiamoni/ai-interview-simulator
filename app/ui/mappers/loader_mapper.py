# app/ui/mappers/loader_mapper.py

from app.ui.constants.loader_steps import LoaderStep


def map_loader_text(step: LoaderStep | None) -> str:

    if step is None:
        return ""

    mapping = {
        LoaderStep.GENERATING_STRUCTURE: "🧠 Designing interview structure...",
        LoaderStep.GENERATING_QUESTIONS: "📚 Generating questions. This may take a while. Please wait...",
        LoaderStep.GENERATING_TESTS: "🧪 Preparing test cases. This may take few seconds...",
        LoaderStep.FINALIZING: "⚙️ Finalizing interview...",
    }

    return mapping.get(step, "Processing...")


def map_loader_progress(step: LoaderStep | None) -> int:

    if step is None:
        return 0

    mapping = {
        LoaderStep.GENERATING_STRUCTURE: 10,
        LoaderStep.GENERATING_QUESTIONS: 40,
        LoaderStep.GENERATING_TESTS: 70,
        LoaderStep.FINALIZING: 90,
    }

    return mapping.get(step, 0)
