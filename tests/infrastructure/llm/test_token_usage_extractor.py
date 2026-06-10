# tests/infrastructure/llm/test_token_usage_extractor.py

from langchain_core.messages import AIMessage

from infrastructure.llm.observability.token_usage_extractor import TokenUsageExtractor


def test_extract_usage_metadata_path() -> None:
    message = AIMessage(
        content="ok",
        usage_metadata={
            "input_tokens": 100,
            "output_tokens": 25,
            "total_tokens": 125,
            "input_token_details": {"cache_read": 10},
            "output_token_details": {"reasoning": 5},
        },
        response_metadata={
            "model_name": "gpt-4o-mini",
            "finish_reason": "stop",
            "id": "req-1",
        },
    )

    snapshot = TokenUsageExtractor.extract(message, model_fallback="fallback")

    assert snapshot.input_tokens == 100
    assert snapshot.output_tokens == 25
    assert snapshot.total_tokens == 125
    assert snapshot.cache_read_tokens == 10
    assert snapshot.reasoning_tokens == 5
    assert snapshot.model_name == "gpt-4o-mini"
    assert snapshot.finish_reason == "stop"
    assert snapshot.request_id == "req-1"
    assert snapshot.source == "usage_metadata"


def test_extract_token_usage_fallback_path() -> None:
    message = AIMessage(
        content="ok",
        response_metadata={
            "token_usage": {
                "prompt_tokens": 40,
                "completion_tokens": 12,
                "total_tokens": 52,
                "prompt_tokens_details": {"cached_tokens": 8},
                "completion_tokens_details": {"reasoning_tokens": 3},
            },
            "model_name": "gpt-4o-mini-2024-07-18",
            "finish_reason": "stop",
            "id": "req-2",
        },
    )

    snapshot = TokenUsageExtractor.extract(message, model_fallback="fallback")

    assert snapshot.input_tokens == 40
    assert snapshot.output_tokens == 12
    assert snapshot.total_tokens == 52
    assert snapshot.cache_read_tokens == 8
    assert snapshot.reasoning_tokens == 3
    assert snapshot.model_name == "gpt-4o-mini-2024-07-18"
    assert snapshot.source == "token_usage"


def test_extract_missing_metadata_path() -> None:
    message = AIMessage(content="ok")

    snapshot = TokenUsageExtractor.extract(message, model_fallback="gpt-4o-mini")

    assert snapshot.input_tokens is None
    assert snapshot.output_tokens is None
    assert snapshot.total_tokens is None
    assert snapshot.cache_read_tokens is None
    assert snapshot.reasoning_tokens is None
    assert snapshot.model_name == "gpt-4o-mini"
    assert snapshot.finish_reason is None
    assert snapshot.request_id is None
    assert snapshot.source == "none"


def test_extract_cached_token_path() -> None:
    message = AIMessage(
        content="ok",
        usage_metadata={
            "input_tokens": 500,
            "output_tokens": 50,
            "total_tokens": 550,
            "input_token_details": {"cache_read": 400},
            "output_token_details": {"reasoning": 0},
        },
        response_metadata={"model_name": "gpt-4o-mini", "finish_reason": "stop"},
    )

    snapshot = TokenUsageExtractor.extract(message, model_fallback="fallback")

    assert snapshot.input_tokens == 500
    assert snapshot.cache_read_tokens == 400
    assert snapshot.total_tokens == 550
