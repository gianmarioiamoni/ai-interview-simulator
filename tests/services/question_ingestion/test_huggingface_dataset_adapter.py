# tests/services/question_ingestion/test_huggingface_dataset_adapter.py

from services.question_ingestion.adapters.huggingface_dataset_adapter import (
    HuggingFaceDatasetAdapter,
)


class _StubHuggingFaceDatasetAdapter(HuggingFaceDatasetAdapter):

    AREA = "technical_case_study"
    ROLE = "backend_engineer"
    LEVEL = "senior"


def test_base_adapt_maps_instruction_to_canonical_payload() -> None:
    adapter = _StubHuggingFaceDatasetAdapter()

    record = adapter.adapt(
        payload={
            "instruction": "  Explain load balancing in microservices.  ",
            "input": "",
            "output": "answer",
            "thought": "reasoning",
        },
        source="test-source",
        source_type="huggingface",
        dataset_version="v1",
    )

    assert record.canonical_payload["text"] == "Explain load balancing in microservices."
    assert record.canonical_payload["area"] == "technical_case_study"
    assert record.canonical_payload["role"] == "backend_engineer"
    assert record.canonical_payload["level"] == "senior"
    assert record.raw_payload["instruction"] == "  Explain load balancing in microservices.  "
