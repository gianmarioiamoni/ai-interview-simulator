# app/prompts/prompt_loader.py

from pathlib import Path


class PromptLoader:

    BASE_PATH = Path(__file__).parent

    @classmethod
    def load(cls, relative_path: str) -> str:
        path = cls.BASE_PATH / relative_path

        if not path.exists():
            raise FileNotFoundError(f"Prompt not found: {path}")

        return path.read_text()
