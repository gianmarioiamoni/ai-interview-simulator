from pathlib import Path


class PromptLoader:

    BASE_PATH = Path(__file__).parent

    @classmethod
    def load(cls, relative_path: str) -> str:
        path = cls.BASE_PATH / relative_path
        return path.read_text()
