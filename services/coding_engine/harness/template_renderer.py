# services/coding_engine/harness/template_renderer.py

from jinja2 import Environment, FileSystemLoader


class TemplateRenderer:

    def __init__(self, template_dir: str):
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=False,  # CRITICO: stiamo generando codice Python
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def render(self, template_name: str, context: dict) -> str:
        template = self.env.get_template(template_name)
        return template.render(**context)
