# services/question_intelligence/coding_llm_json_repair.py

import re

_FENCED_JSON_PATTERN = re.compile(
    r"```(?:json)?\s*([\s\S]*?)\s*```",
    re.IGNORECASE,
)

_TRAILING_COMMA_PATTERN = re.compile(
    r",\s*([}\]])",
)

_TUPLE_PATTERN = re.compile(
    r"\(([^()]*)\)",
)


def repair_llm_json_text(content: str) -> str:
    """Apply conservative repairs so json.loads can parse common LLM mistakes."""

    text = content.strip()

    fenced = _FENCED_JSON_PATTERN.search(text)
    if fenced is not None:
        text = fenced.group(1).strip()

    text = _TRAILING_COMMA_PATTERN.sub(r"\1", text)
    text = _repair_python_tuples(text)

    return text


def _repair_python_tuples(text: str) -> str:
    """Replace simple Python tuples with JSON arrays (numeric/tuple literals only)."""

    previous = None

    while previous != text:
        previous = text

        def _replace(match: re.Match[str]) -> str:
            inner = match.group(1).strip()
            if not inner:
                return "[]"
            if not _is_tuple_inner_content(inner):
                return match.group(0)
            return f"[{inner}]"

        text = _TUPLE_PATTERN.sub(_replace, text)

    return text


def _is_tuple_inner_content(inner: str) -> bool:
    if not inner:
        return False

    parts = [part.strip() for part in inner.split(",")]

    if len(parts) < 2:
        return False

    for part in parts:
        if part == "":
            return False
        if not re.fullmatch(r"-?\d+(?:\.\d+)?", part):
            return False

    return True
