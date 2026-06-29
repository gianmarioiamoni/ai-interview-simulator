# services/humanizer/guards/follow_up_guard.py

import re
import unicodedata
from infrastructure.config.settings import Settings
from services.humanizer.guards.follow_up_guard_result import FollowUpGuardResult


# ---------------------------------------------------------------------------
# Constants — stable rule codes (FG-prefixed, referenced in failed_rules)
# ---------------------------------------------------------------------------

_R_MIN_LENGTH       = "FG001:min_length"
_R_MAX_LENGTH       = "FG002:max_length"
_R_KEYWORD_OVERLAP  = "FG003:keyword_overlap"
_R_AREA_ANCHOR      = "FG004:area_anchor"
_R_NOT_DUPLICATE    = "FG005:not_duplicate"
_R_NOT_JSON         = "FG006:not_json"
_R_NOT_MARKDOWN     = "FG007:not_markdown"
_R_NO_PLACEHOLDER   = "FG008:no_placeholder"
_R_HAS_QUESTION     = "FG009:has_question_mark"
_R_NO_CODE_BLOCK    = "FG010:no_code_block"
_R_NO_HTML_XML      = "FG011:no_html_xml"
_R_NO_INJECTION     = "FG012:no_prompt_injection"
_R_NO_ROLE_OVERRIDE = "FG013:no_role_override"
_R_NO_SYS_LEAKAGE   = "FG014:no_system_leakage"
_R_NO_SQL           = "FG015:no_sql_payload"
_R_NO_PYTHON        = "FG016:no_python_payload"
_R_NO_TEMPLATE      = "FG017:no_template_text"

_ALL_RULES: tuple[str, ...] = (
    _R_MIN_LENGTH, _R_MAX_LENGTH, _R_KEYWORD_OVERLAP, _R_AREA_ANCHOR,
    _R_NOT_DUPLICATE, _R_NOT_JSON, _R_NOT_MARKDOWN, _R_NO_PLACEHOLDER,
    _R_HAS_QUESTION, _R_NO_CODE_BLOCK, _R_NO_HTML_XML, _R_NO_INJECTION,
    _R_NO_ROLE_OVERRIDE, _R_NO_SYS_LEAKAGE, _R_NO_SQL, _R_NO_PYTHON,
    _R_NO_TEMPLATE,
)

# ---------------------------------------------------------------------------
# Injection / forbidden patterns
# ---------------------------------------------------------------------------

_INJECTION_PATTERNS: tuple[str, ...] = (
    "ignore previous instructions",
    "forget previous instructions",
    "ignore all previous",
    "forget all previous",
    "disregard previous",
    "override previous",
    "system prompt",
    "developer prompt",
    "assistant prompt",
    "[system]",
    "[assistant]",
    "[developer]",
    "<system>",
    "<assistant>",
    "<developer>",
    "###system",
    "###assistant",
    "|system|",
    "|assistant|",
    "-----\nsystem",
    "----\nsystem",
    "--- system",
)

_ROLE_OVERRIDE_PATTERNS: tuple[str, ...] = (
    "you are chatgpt",
    "you are gpt",
    "you are an ai",
    "you are now",
    "act as ",
    "pretend you are",
    "pretend to be",
    "roleplay as",
    "role: ",
    "role:",
)

_SYSTEM_LEAKAGE_PATTERNS: tuple[str, ...] = (
    "reveal your system",
    "show your prompt",
    "print your instructions",
    "output your system",
    "what are your instructions",
    "tell me your prompt",
)

_SQL_PATTERNS: tuple[str, ...] = (
    "select * from",
    "drop table",
    "insert into",
    "delete from",
    "'; --",
    "1=1",
    "union select",
)

_PYTHON_PATTERNS: tuple[str, ...] = (
    "import os",
    "import sys",
    "os.system(",
    "subprocess.",
    "__import__(",
    "exec(",
    "eval(",
    "open(",
)

_TEMPLATE_TEXT_PATTERNS: tuple[str, ...] = (
    "your question here",
    "insert question here",
    "[question]",
    "[follow-up]",
    "[placeholder]",
    "todo:",
    "fixme:",
    "tbd:",
)

# ---------------------------------------------------------------------------
# Stopwords for keyword overlap (common English words to exclude)
# ---------------------------------------------------------------------------

_STOPWORDS: frozenset[str] = frozenset({
    "the", "and", "for", "are", "but", "not", "you", "all", "can", "her",
    "was", "one", "our", "out", "day", "get", "has", "him", "his", "how",
    "its", "may", "new", "now", "old", "see", "two", "way", "who", "did",
    "also", "back", "come", "from", "give", "good", "have", "here", "into",
    "just", "know", "like", "long", "make", "many", "more", "most", "move",
    "much", "must", "name", "need", "over", "same", "say", "she", "some",
    "such", "take", "than", "that", "them", "then", "there", "they",
    "think", "this", "time", "very", "well", "were", "what", "when",
    "where", "which", "while", "will", "with", "would", "your",
})

# Minimum word length for keyword overlap check
_MIN_WORD_LEN: int = 4

# Max normalised edit distance ratio to consider a duplicate (Levenshtein)
_DUPLICATE_SIMILARITY_THRESHOLD: float = 0.70


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

class FollowUpGuard:
    """Deterministic, embedding-free validator for generated follow-up text.

    All rules operate on string properties only. No LLM calls, no I/O,
    no external dependencies. See M1-3 §E for rule definitions.
    """

    def validate(
        self,
        *,
        follow_up_text: str,
        previous_answer: str,
        question_prompt: str,
        question_area: str,
        settings: Settings,
    ) -> FollowUpGuardResult:
        """Validate a generated follow-up text against all guard rules.

        Args:
            follow_up_text: The generated follow-up question text.
            previous_answer: The candidate's previous answer (raw).
            question_prompt: The base question prompt (for duplicate check).
            question_area: The area label of the current question.
            settings: Application settings (single source of truth).

        Returns:
            FollowUpGuardResult with accepted=True iff all rules pass.
        """
        sanitized_output = _sanitize(follow_up_text)
        sanitized_input = (
            _sanitize(previous_answer[:settings.follow_up_max_input_chars])
            if settings.follow_up_sanitize_input
            else previous_answer
        )

        failed: list[str] = []
        warnings: list[str] = []

        # --- Structural rules ---
        _check_min_length(sanitized_output, settings.follow_up_min_length, failed)
        _check_max_length(sanitized_output, failed)
        _check_has_question_mark(sanitized_output, failed)
        _check_not_json(sanitized_output, failed)
        _check_not_markdown(sanitized_output, failed)
        _check_no_code_block(sanitized_output, failed)
        _check_no_html_xml(sanitized_output, failed)
        _check_no_placeholder(sanitized_output, failed)
        _check_no_template_text(sanitized_output, failed)

        # --- Content rules ---
        _check_keyword_overlap(
            sanitized_output,
            sanitized_input,
            settings.follow_up_min_keyword_overlap,
            failed,
            warnings,
        )
        _check_area_anchor(sanitized_output, question_area, failed, warnings)
        _check_not_duplicate(sanitized_output, question_prompt, failed)

        # --- Security rules ---
        _check_no_injection(sanitized_output, failed)
        _check_no_role_override(sanitized_output, failed)
        _check_no_system_leakage(sanitized_output, failed)
        _check_no_sql(sanitized_output, failed)
        _check_no_python(sanitized_output, failed)

        return FollowUpGuardResult.build(
            failed=failed,
            warnings=warnings,
            total_rules=len(_ALL_RULES),
        )


# ---------------------------------------------------------------------------
# Sanitization
# ---------------------------------------------------------------------------

def _sanitize(text: str) -> str:
    """Strip control characters and normalise whitespace."""
    cleaned = "".join(
        ch for ch in text
        if unicodedata.category(ch) not in ("Cc", "Cf") or ch in ("\n", "\t")
    )
    return cleaned.strip()


# ---------------------------------------------------------------------------
# Structural rule implementations
# ---------------------------------------------------------------------------

def _check_min_length(text: str, min_length: int, failed: list[str]) -> None:
    if len(text) < min_length:
        failed.append(f"{_R_MIN_LENGTH}:len={len(text)}<{min_length}")


def _check_max_length(text: str, failed: list[str]) -> None:
    # Soft upper bound: > 2000 chars is likely a hallucination or injected block
    if len(text) > 2000:
        failed.append(f"{_R_MAX_LENGTH}:len={len(text)}>2000")


def _check_has_question_mark(text: str, failed: list[str]) -> None:
    if "?" not in text:
        failed.append(_R_HAS_QUESTION)


def _check_not_json(text: str, failed: list[str]) -> None:
    stripped = text.lstrip()
    if stripped.startswith("{") or '"decision":' in text or '"message":' in text:
        failed.append(_R_NOT_JSON)


def _check_not_markdown(text: str, failed: list[str]) -> None:
    if re.search(r"^#{1,6}\s", text, re.MULTILINE):
        failed.append(f"{_R_NOT_MARKDOWN}:header")
        return
    if "**" in text or "__" in text:
        failed.append(f"{_R_NOT_MARKDOWN}:bold")


def _check_no_code_block(text: str, failed: list[str]) -> None:
    if "```" in text or "~~~" in text:
        failed.append(_R_NO_CODE_BLOCK)


def _check_no_html_xml(text: str, failed: list[str]) -> None:
    if re.search(r"<[a-zA-Z][^>]*>", text):
        failed.append(_R_NO_HTML_XML)


def _check_no_placeholder(text: str, failed: list[str]) -> None:
    if re.search(r"\{\{[^}]+\}\}", text):
        failed.append(_R_NO_PLACEHOLDER)


def _check_no_template_text(text: str, failed: list[str]) -> None:
    lower = text.lower()
    for pattern in _TEMPLATE_TEXT_PATTERNS:
        if pattern in lower:
            failed.append(f"{_R_NO_TEMPLATE}:{pattern!r}")
            return


# ---------------------------------------------------------------------------
# Content rule implementations
# ---------------------------------------------------------------------------

def _extract_keywords(text: str) -> frozenset[str]:
    """Extract qualifying words: ≥ MIN_WORD_LEN chars, not a stopword."""
    words = re.findall(r"[a-zA-Z]+", text.lower())
    return frozenset(
        w for w in words
        if len(w) >= _MIN_WORD_LEN and w not in _STOPWORDS
    )


def _check_keyword_overlap(
    follow_up: str,
    answer: str,
    min_overlap: int,
    failed: list[str],
    warnings: list[str],
) -> None:
    answer_kw = _extract_keywords(answer)
    if not answer_kw:
        warnings.append("FG003:no_qualifying_keywords_in_answer")
        return
    follow_up_kw = _extract_keywords(follow_up)
    overlap = len(answer_kw & follow_up_kw)
    if overlap < min_overlap:
        failed.append(f"{_R_KEYWORD_OVERLAP}:overlap={overlap}<{min_overlap}")


def _check_area_anchor(
    follow_up: str,
    question_area: str,
    failed: list[str],
    warnings: list[str],
) -> None:
    """Check that at least one token from the area label appears in follow-up."""
    area_tokens = {
        t.lower() for t in re.split(r"[_\s]+", question_area)
        if len(t) >= _MIN_WORD_LEN
    }
    if not area_tokens:
        warnings.append("FG004:no_qualifying_area_tokens")
        return
    lower_follow_up = follow_up.lower()
    if not any(token in lower_follow_up for token in area_tokens):
        failed.append(f"{_R_AREA_ANCHOR}:area={question_area!r}")


def _normalise_for_dup(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().strip())


def _levenshtein_ratio(a: str, b: str) -> float:
    """Normalised Levenshtein similarity ∈ [0, 1]."""
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    la, lb = len(a), len(b)
    # Use the shorter string as a cap for memory efficiency
    if la > 500 or lb > 500:
        # Truncate for performance; still catches near-verbatim copies
        a, b = a[:500], b[:500]
        la, lb = len(a), len(b)
    prev = list(range(lb + 1))
    for i, ca in enumerate(a):
        curr = [i + 1] + [0] * lb
        for j, cb in enumerate(b):
            cost = 0 if ca == cb else 1
            curr[j + 1] = min(curr[j] + 1, prev[j + 1] + 1, prev[j] + cost)
        prev = curr
    dist = prev[lb]
    return 1.0 - dist / max(la, lb)


def _check_not_duplicate(follow_up: str, question_prompt: str, failed: list[str]) -> None:
    ratio = _levenshtein_ratio(
        _normalise_for_dup(follow_up),
        _normalise_for_dup(question_prompt),
    )
    if ratio >= _DUPLICATE_SIMILARITY_THRESHOLD:
        failed.append(f"{_R_NOT_DUPLICATE}:similarity={ratio:.2f}")


# ---------------------------------------------------------------------------
# Security rule implementations
# ---------------------------------------------------------------------------

def _lower_stripped(text: str) -> str:
    return text.lower().replace("\n", " ").replace("\r", " ")


def _check_no_injection(text: str, failed: list[str]) -> None:
    lower = _lower_stripped(text)
    for pattern in _INJECTION_PATTERNS:
        if pattern in lower:
            failed.append(f"{_R_NO_INJECTION}:pattern={pattern!r}")
            return


def _check_no_role_override(text: str, failed: list[str]) -> None:
    lower = _lower_stripped(text)
    for pattern in _ROLE_OVERRIDE_PATTERNS:
        if pattern in lower:
            failed.append(f"{_R_NO_ROLE_OVERRIDE}:pattern={pattern!r}")
            return


def _check_no_system_leakage(text: str, failed: list[str]) -> None:
    lower = _lower_stripped(text)
    for pattern in _SYSTEM_LEAKAGE_PATTERNS:
        if pattern in lower:
            failed.append(f"{_R_NO_SYS_LEAKAGE}:pattern={pattern!r}")
            return


def _check_no_sql(text: str, failed: list[str]) -> None:
    lower = _lower_stripped(text)
    for pattern in _SQL_PATTERNS:
        if pattern in lower:
            failed.append(f"{_R_NO_SQL}:pattern={pattern!r}")
            return


def _check_no_python(text: str, failed: list[str]) -> None:
    lower = _lower_stripped(text)
    for pattern in _PYTHON_PATTERNS:
        if pattern in lower:
            failed.append(f"{_R_NO_PYTHON}:pattern={pattern!r}")
            return
