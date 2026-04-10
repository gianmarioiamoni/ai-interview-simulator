# app/ui/presenters/feedback/renderers/feedback_markdown_renderer.py

from typing import List


class FeedbackMarkdownRenderer:

    def render(self, blocks) -> str:
        lines: List[str] = []

        for b in blocks:
            lines.append(f"## {b.title}")
            lines.append(b.content)
            lines.append("")

        return "\n".join(lines)
