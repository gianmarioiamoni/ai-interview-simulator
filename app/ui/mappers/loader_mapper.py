from app.ui.constants.loader_steps import LoaderStep


LOADER_TEXT = {
    LoaderStep.GENERATING_STRUCTURE: "🧠 Generating interview structure...",
    LoaderStep.GENERATING_QUESTIONS: "📚 Creating questions...",
    LoaderStep.GENERATING_TESTS: "🧪 Preparing test cases...",
    LoaderStep.FINALIZING: "⚙️ Finalizing interview...",
}


def map_loader_text(step: str | None) -> str:
    if not step:
        return ""
    try:
        return LOADER_TEXT[LoaderStep(step)]
    except Exception:
        return "Processing..."
