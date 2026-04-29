# app/prompts/prompt_renderer.py

from typing import Any, Dict

from jinja2 import Environment, StrictUndefined, TemplateError


class PromptRenderingError(Exception):
    pass


class PromptRenderer:
    # Centralized Jinja2 renderer for prompt templates.
    #
    # StrictUndefined: fail fast on missing variables
    # No logic: templates are presentation-only

    _env = Environment(
        undefined=StrictUndefined,
        autoescape=False,  # prompts are not HTML
        trim_blocks=True,
        lstrip_blocks=True,
    )

    @classmethod
    def render(
        cls,
        template_str: str,
        context: Dict[str, Any],
    ) -> str:

        try:
            template = cls._env.from_string(template_str)
            return template.render(**context)

        except TemplateError as e:
            raise PromptRenderingError(f"Prompt rendering failed: {str(e)}") from e
