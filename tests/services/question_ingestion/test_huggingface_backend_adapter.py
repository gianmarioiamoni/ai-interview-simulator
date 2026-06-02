# tests/services/question_ingestion/test_huggingface_backend_adapter.py

from services.question_ingestion.adapters.huggingface_backend_adapter import (
    BACKEND_AREA,
    BACKEND_LEVEL,
    BACKEND_ROLE,
    HuggingFaceBackendAdapter,
)


def test_adapt_maps_instruction_to_text_with_explicit_metadata() -> None:
    adapter = HuggingFaceBackendAdapter()

    record = adapter.adapt(
        payload={
            "instruction": "Explain the Circuit Breaker pattern in microservices.",
            "input": "",
            "output": "Detailed answer...",
            "thought": "Reasoning...",
        },
        source="bernabepuente/backend-api-instruction-dataset",
        source_type="huggingface",
        dataset_version="v1",
    )

    assert record.canonical_payload["text"] == (
        "Explain the Circuit Breaker pattern in microservices."
    )
    assert record.canonical_payload["area"] == BACKEND_AREA
    assert record.canonical_payload["role"] == BACKEND_ROLE
    assert record.canonical_payload["level"] == BACKEND_LEVEL
    assert record.source == "bernabepuente/backend-api-instruction-dataset"
    assert record.source_type == "huggingface"
    assert record.dataset_version == "v1"
    assert record.raw_payload["instruction"] == (
        "Explain the Circuit Breaker pattern in microservices."
    )


def test_adapt_strips_instruction_whitespace() -> None:
    adapter = HuggingFaceBackendAdapter()

    record = adapter.adapt(
        payload={
            "instruction": "  What are microservices, and why would you use them?  ",
        },
        source="bernabepuente/backend-api-instruction-dataset",
        source_type="huggingface",
        dataset_version="v1",
    )

    assert record.canonical_payload["text"] == (
        "What are microservices, and why would you use them?"
    )


def test_adapt_preserves_full_raw_payload() -> None:
    adapter = HuggingFaceBackendAdapter()

    payload = {
        "instruction": "How can you implement load balancing in microservices?",
        "input": "context snippet",
        "output": "response body",
        "thought": "chain of thought",
    }

    record = adapter.adapt(
        payload=payload,
        source="bernabepuente/backend-api-instruction-dataset",
        source_type="huggingface",
        dataset_version="v1",
    )

    assert record.raw_payload == payload
