# tests/services/humanizer/follow_up/test_follow_up_parser.py
#
# Covers M1-4: STRICT parser, Guard integration, retry/fallback path,
# contract tests, regression, property tests.

import json
import pytest
from unittest.mock import MagicMock

from services.humanizer.follow_up.follow_up_parser import FollowUpParser
from services.humanizer.follow_up.follow_up_parse_error import FollowUpParseError
from services.humanizer.follow_up.follow_up_output import FollowUpOutput
from services.humanizer.guards.follow_up_guard_result import FollowUpGuardResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _settings(
    *,
    min_length: int = 20,
    max_input_chars: int = 800,
    min_keyword_overlap: int = 1,
    sanitize_input: bool = True,
) -> MagicMock:
    s = MagicMock()
    s.follow_up_min_length = min_length
    s.follow_up_max_input_chars = max_input_chars
    s.follow_up_min_keyword_overlap = min_keyword_overlap
    s.follow_up_sanitize_input = sanitize_input
    s.follow_up_allowed_areas = ""
    s.follow_up_allowed_types = "written"
    s.follow_up_logging_enabled = False
    return s


_DEFAULT_SETTINGS = _settings()

_AREA = "technical_knowledge"
_ANSWER = "Redis caching eviction LRU algorithm technical knowledge"
_PROMPT = "Explain caching strategies in distributed systems."

_VALID_RESPONSE = json.dumps({
    "follow_up_question": (
        "How does LRU eviction affect technical knowledge performance "
        "under high memory pressure?"
    ),
    "reasoning": "Candidate mentioned LRU but did not address memory limits.",
    "topic_anchor": "LRU eviction",
    "confidence": 0.85,
})


def _parse(
    raw: str = _VALID_RESPONSE,
    answer: str = _ANSWER,
    prompt: str = _PROMPT,
    area: str = _AREA,
    settings=None,
) -> tuple[FollowUpOutput, FollowUpGuardResult]:
    if settings is None:
        settings = _DEFAULT_SETTINGS
    return FollowUpParser().parse(
        raw,
        previous_answer=answer,
        question_prompt=prompt,
        question_area=area,
        settings=settings,
    )


# ---------------------------------------------------------------------------
# PAR-001..004: Happy path
# ---------------------------------------------------------------------------

def test_par_001_valid_response_returns_output_and_guard() -> None:
    output, guard = _parse()
    assert isinstance(output, FollowUpOutput)
    assert isinstance(guard, FollowUpGuardResult)


def test_par_002_guard_accepted_on_clean_input() -> None:
    _, guard = _parse()
    assert guard.accepted is True


def test_par_003_output_fields_correct() -> None:
    output, _ = _parse()
    assert "LRU" in output.follow_up_question
    assert output.confidence == 0.85
    assert output.topic_anchor == "LRU eviction"


def test_par_004_score_is_one_on_valid() -> None:
    _, guard = _parse()
    assert guard.score == 1.0


# ---------------------------------------------------------------------------
# PAR-005..009: Invalid JSON
# ---------------------------------------------------------------------------

def test_par_005_invalid_json_raises() -> None:
    with pytest.raises(FollowUpParseError) as exc:
        _parse("{not valid json}")
    assert "invalid_json" in str(exc.value)


def test_par_006_empty_string_raises() -> None:
    with pytest.raises(FollowUpParseError):
        _parse("")


def test_par_007_json_array_raises() -> None:
    with pytest.raises(FollowUpParseError):
        _parse('["a", "b"]')


def test_par_008_json_number_raises() -> None:
    with pytest.raises(FollowUpParseError):
        _parse("42")


def test_par_009_json_null_raises() -> None:
    with pytest.raises(FollowUpParseError):
        _parse("null")


# ---------------------------------------------------------------------------
# PAR-010..013: Missing fields
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("missing_field", [
    "follow_up_question",
    "reasoning",
    "topic_anchor",
    "confidence",
])
def test_par_010_013_missing_field_raises(missing_field: str) -> None:
    payload = json.loads(_VALID_RESPONSE)
    del payload[missing_field]
    with pytest.raises(FollowUpParseError) as exc:
        _parse(json.dumps(payload))
    assert "missing_fields" in str(exc.value)


# ---------------------------------------------------------------------------
# PAR-014..016: Unknown fields (contract violation)
# ---------------------------------------------------------------------------

def test_par_014_unknown_field_raises() -> None:
    payload = json.loads(_VALID_RESPONSE)
    payload["unexpected"] = "extra"
    with pytest.raises(FollowUpParseError) as exc:
        _parse(json.dumps(payload))
    assert "unknown_fields" in str(exc.value)


def test_par_015_multiple_unknown_fields_raises() -> None:
    payload = json.loads(_VALID_RESPONSE)
    payload["foo"] = 1
    payload["bar"] = 2
    with pytest.raises(FollowUpParseError) as exc:
        _parse(json.dumps(payload))
    assert "unknown_fields" in str(exc.value)


def test_par_016_empty_json_object_raises() -> None:
    with pytest.raises(FollowUpParseError) as exc:
        _parse("{}")
    assert "missing_fields" in str(exc.value)


# ---------------------------------------------------------------------------
# PAR-017..019: Wrong types
# ---------------------------------------------------------------------------

def test_par_017_confidence_string_raises() -> None:
    payload = json.loads(_VALID_RESPONSE)
    payload["confidence"] = "high"
    with pytest.raises(FollowUpParseError) as exc:
        _parse(json.dumps(payload))
    assert "schema_violation" in str(exc.value)


def test_par_018_confidence_out_of_range_raises() -> None:
    payload = json.loads(_VALID_RESPONSE)
    payload["confidence"] = 1.5
    with pytest.raises(FollowUpParseError) as exc:
        _parse(json.dumps(payload))
    assert "schema_violation" in str(exc.value)


def test_par_019_question_without_question_mark_raises() -> None:
    payload = json.loads(_VALID_RESPONSE)
    payload["follow_up_question"] = "No question mark here"
    with pytest.raises(FollowUpParseError) as exc:
        _parse(json.dumps(payload))
    assert "schema_violation" in str(exc.value)


# ---------------------------------------------------------------------------
# PAR-020..023: Markdown fences → STRICT rejection
# ---------------------------------------------------------------------------

def test_par_020_json_in_markdown_fence_raises() -> None:
    fenced = "```json\n" + _VALID_RESPONSE + "\n```"
    with pytest.raises(FollowUpParseError) as exc:
        _parse(fenced)
    assert "markdown_fence" in str(exc.value)


def test_par_021_bare_fence_raises() -> None:
    fenced = "```\n" + _VALID_RESPONSE + "\n```"
    with pytest.raises(FollowUpParseError) as exc:
        _parse(fenced)
    assert "markdown_fence" in str(exc.value)


def test_par_022_extra_text_before_json_raises() -> None:
    extra = "Here is my answer:\n" + _VALID_RESPONSE
    with pytest.raises(FollowUpParseError) as exc:
        _parse(extra)
    assert "extra_text" in str(exc.value)


def test_par_023_extra_text_after_json_raises() -> None:
    extra = _VALID_RESPONSE + "\nHope this helps."
    with pytest.raises(FollowUpParseError) as exc:
        _parse(extra)
    assert "extra_text" in str(exc.value)


# ---------------------------------------------------------------------------
# PAR-024: Guard result is always returned with output
# ---------------------------------------------------------------------------

def test_par_024_guard_always_called() -> None:
    from unittest.mock import patch, MagicMock
    mock_guard_result = FollowUpGuardResult(
        accepted=True, score=1.0, reasons=(), warnings=(), failed_rules=()
    )
    mock_guard = MagicMock()
    mock_guard.validate.return_value = mock_guard_result

    parser = FollowUpParser(guard=mock_guard)
    output, guard = parser.parse(
        _VALID_RESPONSE,
        previous_answer=_ANSWER,
        question_prompt=_PROMPT,
        question_area=_AREA,
        settings=_DEFAULT_SETTINGS,
    )
    mock_guard.validate.assert_called_once()
    assert guard is mock_guard_result


# ---------------------------------------------------------------------------
# PAR-025..027: Retry / fallback path (caller responsibility)
# ---------------------------------------------------------------------------

def test_par_025_parse_error_is_exception_not_fallback() -> None:
    """STRICT: parser raises, never returns a fallback result."""
    with pytest.raises(FollowUpParseError):
        _parse("not json at all")


def test_par_026_caller_can_retry_on_parse_error() -> None:
    """Caller pattern: retry once on FollowUpParseError."""
    call_count = 0
    responses = ["{bad}", _VALID_RESPONSE]

    def fake_llm() -> str:
        nonlocal call_count
        response = responses[call_count]
        call_count += 1
        return response

    parser = FollowUpParser()
    result = None
    for _ in range(2):
        try:
            result = parser.parse(
                fake_llm(),
                previous_answer=_ANSWER,
                question_prompt=_PROMPT,
                question_area=_AREA,
                settings=_DEFAULT_SETTINGS,
            )
            break
        except FollowUpParseError:
            continue

    assert result is not None
    output, _ = result
    assert isinstance(output, FollowUpOutput)
    assert call_count == 2


def test_par_027_parse_error_carries_raw_response() -> None:
    bad_raw = "{invalid: json}"
    try:
        _parse(bad_raw)
    except FollowUpParseError as exc:
        assert exc.raw == bad_raw
    else:
        pytest.fail("Expected FollowUpParseError")


def test_par_027b_missing_fields_carries_raw() -> None:
    payload = json.loads(_VALID_RESPONSE)
    del payload["reasoning"]
    raw = json.dumps(payload)
    try:
        _parse(raw)
    except FollowUpParseError as exc:
        assert exc.raw == raw
    else:
        pytest.fail("Expected FollowUpParseError")


def test_par_027c_unknown_fields_carries_raw() -> None:
    payload = json.loads(_VALID_RESPONSE)
    payload["extra"] = "bad"
    raw = json.dumps(payload)
    try:
        _parse(raw)
    except FollowUpParseError as exc:
        assert exc.raw == raw
    else:
        pytest.fail("Expected FollowUpParseError")


# ---------------------------------------------------------------------------
# PAR-028: Guard rejected → output still returned (guard decides)
# ---------------------------------------------------------------------------

def test_par_028_guard_rejected_output_still_returned() -> None:
    """Parser returns both output and guard result even when guard rejects."""
    short_payload = {
        "follow_up_question": "Redis?",
        "reasoning": "short",
        "topic_anchor": "Redis",
        "confidence": 0.5,
    }
    try:
        output, guard = _parse(json.dumps(short_payload))
        # If no parse error (schema passes), guard may reject
        assert isinstance(output, FollowUpOutput)
        assert isinstance(guard, FollowUpGuardResult)
    except FollowUpParseError:
        # schema_violation is also acceptable (question mark validator)
        pass


# ---------------------------------------------------------------------------
# Regression: guard FG-code stability
# ---------------------------------------------------------------------------

def test_reg_001_guard_failed_rules_use_fg_codes() -> None:
    """failed_rules must contain FG-prefixed codes only."""
    _, guard = _parse(
        answer="Redis caching eviction algorithm",
        area="technical_knowledge",
    )
    for rule in guard.failed_rules:
        assert rule.startswith("FG"), f"Expected FG-prefixed code, got: {rule!r}"


# ---------------------------------------------------------------------------
# PROP: Property tests
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("run", range(10))
def test_prop_parse_idempotent(run) -> None:
    output1, guard1 = _parse()
    output2, guard2 = _parse()
    assert output1 == output2
    assert guard1.accepted == guard2.accepted
    assert guard1.failed_rules == guard2.failed_rules


def test_prop_parse_error_always_raises_for_empty() -> None:
    with pytest.raises(FollowUpParseError):
        _parse("")


def test_prop_extra_fields_always_rejected() -> None:
    for extra in ["decision", "message", "score", "follow_up_used", "anything"]:
        payload = json.loads(_VALID_RESPONSE)
        payload[extra] = "injected"
        with pytest.raises(FollowUpParseError):
            _parse(json.dumps(payload))
