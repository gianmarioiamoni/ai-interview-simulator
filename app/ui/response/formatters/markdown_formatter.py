# app/ui/response/formatters/markdown_formatter.py


class MarkdownFormatter:

    @staticmethod
    def section(title: str, content: str) -> str:
        return f"### {title}\n\n{content}"

    @staticmethod
    def error_block(message: str) -> str:
        return f"⚠️ Fix this first:\n```\n{message}\n```\n\n"
