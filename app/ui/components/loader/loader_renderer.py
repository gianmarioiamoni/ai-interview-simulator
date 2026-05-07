# app/ui/components/loader/loader_renderer.py

from app.ui.components.loader.loader_template import LOADER_HTML


def render_loader(message: str, progress: int) -> str:

    return LOADER_HTML.format(
        message=message,
        progress=progress,
    )
