# services/question_intelligence/coding_llm_json_repair.py

import json
import re
from typing import Any

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

# Fields that contain Python source code or free-form text.
# Tuple repair must never be applied to their values.
_CODE_FIELDS: frozenset[str] = frozenset(
    {
        "reference_solution",
        "prompt",
        "explanation",
        "feedback",
        "hint",
    }
)

# Fields whose values are JSON data structures and may legitimately contain
# Python-style numeric tuple literals emitted by LLM responses.
# Order matters: leaf fields (args, expected) must be processed before their
# container fields (visible_tests, hidden_tests) so the targeted span repair
# operates on the innermost values first.
_DATA_FIELDS: tuple[str, ...] = (
    "args",
    "expected",
    "visible_tests",
    "hidden_tests",
)


def repair_llm_json_text(content: str) -> str:
    """
    Apply conservative repairs so json.loads can parse common LLM mistakes.

    Repair steps applied in order:

    1. Strip markdown fences (``` / ```json).
    2. Remove trailing commas before } or ].
    3. Apply Python-tuple → JSON-array normalisation **only** inside
       data-field value regions (args, expected, visible_tests, hidden_tests)
       using a targeted raw-string pass that never touches code fields.
    4. Parse to a Python object and walk the tree for a second field-aware
       repair pass on any residual string values in data fields.

    The raw-string pass (step 3) is needed because LLMs sometimes embed Python
    tuple literals directly in the JSON text, making it unparseable before we
    can do a structural walk.
    """

    text = content.strip()

    # ── Step 1: fence stripping ──────────────────────────────────────────────
    fenced = _FENCED_JSON_PATTERN.search(text)
    if fenced is not None:
        text = fenced.group(1).strip()

    # ── Step 2: trailing comma removal ───────────────────────────────────────
    text = _TRAILING_COMMA_PATTERN.sub(r"\1", text)

    # ── Step 3: targeted raw-text tuple repair ───────────────────────────────
    # Only repair content that belongs to known data fields.
    text = _repair_data_field_regions(text)

    # ── Step 4: structural walk for residual string values ───────────────────
    try:
        parsed = json.loads(text)
        repaired = _repair_data_fields(parsed)
        return json.dumps(repaired)
    except (json.JSONDecodeError, ValueError):
        return text


# ---------------------------------------------------------------------------
# Step 3 — targeted raw-text pass
# ---------------------------------------------------------------------------


def _repair_data_field_regions(text: str) -> str:
    """
    For every data field key found in the raw JSON text, apply numeric-tuple
    repair to its value region.  Code fields and all other fields are left
    untouched.
    """
    for field in _DATA_FIELDS:
        text = _repair_field_value_in_text(text, field)
    return text


def _repair_field_value_in_text(text: str, field: str) -> str:
    """
    Find every occurrence of `"<field>": <value>` in *text* and apply tuple
    repair to the value span.  Returns the modified text.
    """
    # The lookbehind ensures we match the field key as a JSON object key
    # (preceded by whitespace, comma, or opening brace/bracket) rather than
    # as part of a longer string value.
    key_pat = re.compile(
        r'(?<=[,\{\[\s\n])' + re.escape(f'"{field}"') + r'\s*:\s*',
    )

    result_parts: list[str] = []
    last_end = 0

    for m in key_pat.finditer(text):
        value_start = m.end()
        value_span, value_end = _extract_json_value_span(text, value_start)
        if value_span is None:
            continue

        repaired_span = _repair_value_span(value_span)

        result_parts.append(text[last_end : m.start()])
        result_parts.append(m.group(0))
        result_parts.append(repaired_span)
        last_end = value_end

    result_parts.append(text[last_end:])
    return "".join(result_parts)


def _repair_value_span(span: str) -> str:
    """
    Repair a raw JSON value span that may contain Python tuple literals.

    - Arrays / objects: apply tuple repair directly (tuples appear unquoted).
    - JSON strings: decode, repair content, re-encode (so "(1,2)" → [1,2]).
    - Primitives: return unchanged.
    """
    stripped = span.strip()

    # JSON string value: repair the *content* then re-evaluate
    if stripped.startswith('"'):
        try:
            inner = json.loads(stripped)  # decode the JSON string
        except json.JSONDecodeError:
            return span
        repaired = _repair_tuple_in_span(inner)
        if repaired != inner:
            # Try to parse the repaired content as JSON (e.g. "[1, 5]" → array)
            try:
                parsed = json.loads(repaired)
                return json.dumps(parsed)
            except json.JSONDecodeError:
                return json.dumps(repaired)
        return span

    # Array or object or tuple literal: repair in-place
    return _repair_tuple_in_span(span)


def _extract_json_value_span(text: str, start: int) -> tuple[str | None, int]:
    """
    Extract the JSON value starting at *start* in *text*.
    Returns (span_str, end_index) or (None, start) on failure.
    """
    if start >= len(text):
        return None, start

    ch = text[start]

    # String value
    if ch == '"':
        end = start + 1
        while end < len(text):
            c = text[end]
            if c == '\\':
                end += 2
                continue
            if c == '"':
                end += 1
                return text[start:end], end
            end += 1
        return None, start

    # Array or object — count brackets
    if ch in ('[', '{'):
        depth = 0
        in_str = False
        end = start
        while end < len(text):
            c = text[end]
            if in_str:
                if c == '\\':
                    end += 2
                    continue
                if c == '"':
                    in_str = False
            else:
                if c == '"':
                    in_str = True
                elif c in ('[', '{'):
                    depth += 1
                elif c in (']', '}'):
                    depth -= 1
                    if depth == 0:
                        end += 1
                        return text[start:end], end
            end += 1
        return None, start

    # Primitive (number, bool, null) or Python tuple literal starting with (
    end = start
    if ch == '(':
        # Scan to the matching closing paren
        depth = 0
        while end < len(text):
            c = text[end]
            if c == '(':
                depth += 1
            elif c == ')':
                depth -= 1
                if depth == 0:
                    end += 1
                    return text[start:end], end
            end += 1
        return None, start

    while end < len(text) and text[end] not in (',', '}', ']', '\n', ' ', '\t'):
        end += 1
    return text[start:end], end


def _repair_tuple_in_span(span: str) -> str:
    """
    Apply numeric tuple → JSON array repair to a raw value span.

    Only replaces tuples that appear as bare JSON values, not inside
    JSON string literals.  This avoids converting `"(1, 5)"` (a JSON string
    whose content happens to be a tuple) into `"[1, 5]"` (still a string).
    """
    previous = None
    text = span
    in_str = False
    # Use a char-level pass to skip string contents
    # Simpler: use a regex that excludes matches preceded by an un-escaped quote
    # that would indicate we're inside a string value.
    # Since _repair_value_span already handles the string-decode case,
    # here we only need to handle bare tuple literals (not inside "…").
    while previous != text:
        previous = text

        def _replace(match: re.Match) -> str:
            pos = match.start()
            # Check if this match is inside a JSON string by counting
            # unescaped quotes before it.
            prefix = text[:pos]
            # Count unescaped quotes: if odd → inside string
            quote_count = len(re.findall(r'(?<!\\)"', prefix))
            if quote_count % 2 == 1:
                return match.group(0)  # inside a string — leave unchanged
            inner = match.group(1).strip()
            if not inner:
                return match.group(0)
            if not _is_tuple_inner_content(inner):
                return match.group(0)
            return f"[{inner}]"

        text = _TUPLE_PATTERN.sub(_replace, text)

    return text


# ---------------------------------------------------------------------------
# Step 4 — structural walk for residual string values
# ---------------------------------------------------------------------------


def _repair_data_fields(value: Any) -> Any:
    """
    Recursively walk the parsed JSON object.  Apply tuple-literal repair only
    to data-field values — never to code fields.
    """
    if isinstance(value, list):
        return [_repair_data_fields(item) for item in value]

    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, val in value.items():
            if key in _CODE_FIELDS:
                result[key] = val
            elif key in _DATA_FIELDS:
                result[key] = _repair_value(val)
            else:
                result[key] = _repair_data_fields(val)
        return result

    return value


def _repair_value(value: Any) -> Any:
    if isinstance(value, list):
        return [_repair_value(item) for item in value]
    if isinstance(value, dict):
        return _repair_data_fields(value)
    if isinstance(value, str):
        return _repair_tuple_string(value)
    return value


def _repair_tuple_string(text: str) -> Any:
    stripped = text.strip()
    previous = None
    while previous != stripped:
        previous = stripped

        def _replace(match: re.Match) -> str:
            inner = match.group(1).strip()
            if not inner:
                return match.group(0)
            if not _is_tuple_inner_content(inner):
                return match.group(0)
            return f"[{inner}]"

        stripped = _TUPLE_PATTERN.sub(_replace, stripped)

    if stripped == text.strip():
        return text
    try:
        return json.loads(stripped)
    except (json.JSONDecodeError, ValueError):
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
