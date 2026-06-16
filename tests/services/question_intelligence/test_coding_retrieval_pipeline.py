# tests/services/question_intelligence/test_coding_retrieval_pipeline.py

import json
from unittest.mock import MagicMock, patch

from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.interview.interview_type import InterviewType
from domain.contracts.question.question import QuestionType
from domain.contracts.question.question_bank_item import QuestionBankItem
from domain.contracts.question.question_origin_type import QuestionOriginType
from domain.contracts.question.question_provenance import QuestionProvenance
from domain.contracts.user.role import Role, RoleType
from domain.contracts.user.seniority_level import SeniorityLevel
from services.question_corpus.contracts.interview_retrieval_memory import (
    InterviewRetrievalMemory,
)
from services.question_intelligence.coding_question_generator import (
    CodingQuestionGenerator,
    GeneratedCodingQuestion,
    MAX_INVALID_JSON_ATTEMPTS,
)
from services.question_intelligence.pipelines.coding_question_pipeline import (
    CodingQuestionPipeline,
)

RETRIEVE_CODING_CANDIDATES = (
    "services.question_intelligence.pipelines.coding_question_pipeline."
    "retrieve_coding_candidates"
)
from services.question_intelligence.question_retrieval_service import (
    QuestionRetrievalService,
)
from services.question_ingestion.contracts.ingestion_metadata import IngestionMetadata
from services.coding_engine.coding_executor import CodingExecutor


RETRIEVED_CODING_PROMPT = "How would you solve Two Sum?"

CORPUS_QUESTION_ID = "10c7c8350619e4f0"

ENRICHED_CODING_JSON = json.dumps(
    [
        {
            "prompt": (
                "Given an integer array nums and an integer target, return indices "
                "of the two numbers such that they add up to target. "
                "Implement two_sum(nums, target)."
            ),
            "coding_spec": {
                "type": "function",
                "entrypoint": "two_sum",
                "parameters": ["nums", "target"],
            },
            "visible_tests": [
                {
                    "args": [[2, 7, 11, 15], 9],
                    "expected": [0, 1],
                },
                {
                    "args": [[3, 3], 6],
                    "expected": [0, 1],
                },
            ],
        },
    ],
)

MISALIGNED_ENRICH_JSON = json.dumps(
    [
        {
            "prompt": "Return indices of two numbers that add to a target.",
            "coding_spec": {
                "type": "function",
                "entrypoint": "two_sum",
                "parameters": ["nums", "target"],
            },
            "visible_tests": [
                {"args": [[2, 7, 11, 15], 9], "expected": [0, 1]},
                {"args": [[3, 3], 6], "expected": [0, 1]},
            ],
        },
    ],
)

GENERATED_FALLBACK_JSON = json.dumps(
    [
        {
            "prompt": (
                "Return the larger of two integers a and b. "
                "Implement max_of_two(a, b)."
            ),
            "coding_spec": {
                "type": "function",
                "entrypoint": "max_of_two",
                "parameters": ["a", "b"],
            },
            "visible_tests": [
                {"args": [1, 2], "expected": 2},
                {"args": [5, 3], "expected": 5},
            ],
        },
    ],
)

TWO_SUM_REFERENCE_CODE = """
def two_sum(nums, target):
    seen = {}
    for i, value in enumerate(nums):
        complement = target - value
        if complement in seen:
            return [seen[complement], i]
        seen[value] = i
    return []
"""

MAX_OF_TWO_REFERENCE_CODE = """
def max_of_two(a, b):
    return a if a >= b else b
"""


def _build_coding_bank_item(
    text: str = RETRIEVED_CODING_PROMPT,
    question_id: str = CORPUS_QUESTION_ID,
) -> QuestionBankItem:

    return QuestionBankItem(
        id=question_id,
        text=text,
        interview_type=InterviewType.TECHNICAL,
        role=Role(type=RoleType.FULLSTACK_ENGINEER),
        area=InterviewArea.TECH_CODING,
        level=SeniorityLevel.JUNIOR,
        difficulty=2,
        ingestion_metadata=IngestionMetadata(
            source_name="tech-interview-handbook/question-groups",
            source_type="question_corpus",
            dataset_version="v1",
            ingestion_timestamp="2020-01-01T00:00:00Z",
        ),
        provenance=QuestionProvenance(
            origin_type=QuestionOriginType.RETRIEVAL,
            source_name="tech-interview-handbook/question-groups",
            source_type="question_corpus",
            dataset_version="v1",
            retrieval_score=0.85,
        ),
    )


def _mock_llm_with_responses(responses: list[str]) -> MagicMock:

    llm = MagicMock()
    llm.invoke.side_effect = [
        MagicMock(content=content) for content in responses
    ]
    return llm


def _assert_coding_contract(question) -> None:

    assert question.type == QuestionType.CODING
    assert question.area == InterviewArea.TECH_CODING
    assert question.coding_spec is not None
    assert question.function_name == question.coding_spec.entrypoint
    assert len(question.visible_tests) >= 1

    reference_code = (
        TWO_SUM_REFERENCE_CODE
        if question.coding_spec.entrypoint == "two_sum"
        else MAX_OF_TWO_REFERENCE_CODE
    )

    execution = CodingExecutor().execute(
        question=question,
        user_code=reference_code,
    )

    assert execution.total_tests == len(question.visible_tests)
    assert execution.success is True
    assert execution.passed_tests == execution.total_tests


def test_enrich_from_prompt_success() -> None:

    llm = _mock_llm_with_responses([ENRICHED_CODING_JSON])
    generator = CodingQuestionGenerator(llm)

    enriched = generator.enrich_from_prompt(
        seed_prompt=RETRIEVED_CODING_PROMPT,
        role=RoleType.FULLSTACK_ENGINEER,
        level=SeniorityLevel.JUNIOR,
    )

    assert enriched is not None
    assert enriched.coding_spec.entrypoint == "two_sum"
    assert "nums" in enriched.prompt
    assert "target" in enriched.prompt
    assert len(enriched.visible_tests) >= 2

    llm.invoke.assert_called_once()
    call_prompt = llm.invoke.call_args[0][0]
    assert RETRIEVED_CODING_PROMPT in call_prompt


def test_enrich_from_prompt_failure_returns_none() -> None:

    llm = _mock_llm_with_responses(["not-json"] * MAX_INVALID_JSON_ATTEMPTS)
    generator = CodingQuestionGenerator(llm)

    enriched = generator.enrich_from_prompt(
        seed_prompt=RETRIEVED_CODING_PROMPT,
        role=RoleType.FULLSTACK_ENGINEER,
        level=SeniorityLevel.JUNIOR,
    )

    assert enriched is None
    assert llm.invoke.call_count == MAX_INVALID_JSON_ATTEMPTS


def test_coding_pipeline_retrieval_and_enrichment_success() -> None:

    retrieval_service = MagicMock(spec=QuestionRetrievalService)
    llm = _mock_llm_with_responses([ENRICHED_CODING_JSON])
    pipeline = CodingQuestionPipeline(
        retrieval_service=retrieval_service,
        coding_generator=CodingQuestionGenerator(llm),
    )

    with patch(
        RETRIEVE_CODING_CANDIDATES,
        return_value=[_build_coding_bank_item()],
    ):
        questions, memory = pipeline.build(
            role=RoleType.FULLSTACK_ENGINEER,
            level=SeniorityLevel.JUNIOR,
            interview_type=InterviewType.TECHNICAL,
            area=InterviewArea.TECH_CODING,
            questions_per_area=1,
        )

    assert len(questions) == 1
    assert questions[0].provenance is not None
    assert questions[0].provenance.origin_type == QuestionOriginType.RETRIEVAL
    assert questions[0].provenance.generated_by_model == "coding_question_enrichment"
    assert questions[0].function_name == "two_sum"
    _assert_coding_contract(questions[0])

    assert CORPUS_QUESTION_ID in memory.asked_question_ids
    llm.invoke.assert_called_once()


def test_coding_pipeline_enrichment_failure_falls_back_to_generate() -> None:

    retrieval_service = MagicMock(spec=QuestionRetrievalService)
    llm = _mock_llm_with_responses(
        ["invalid-json"] * MAX_INVALID_JSON_ATTEMPTS
        + [GENERATED_FALLBACK_JSON],
    )

    pipeline = CodingQuestionPipeline(
        retrieval_service=retrieval_service,
        coding_generator=CodingQuestionGenerator(llm),
    )

    with patch(
        RETRIEVE_CODING_CANDIDATES,
        return_value=[_build_coding_bank_item()],
    ):
        questions, memory = pipeline.build(
            role=RoleType.FULLSTACK_ENGINEER,
            level=SeniorityLevel.JUNIOR,
            interview_type=InterviewType.TECHNICAL,
            area=InterviewArea.TECH_CODING,
            questions_per_area=1,
        )

    assert len(questions) == 1
    assert questions[0].coding_spec.entrypoint == "max_of_two"
    assert questions[0].provenance is None
    _assert_coding_contract(questions[0])

    assert llm.invoke.call_count == MAX_INVALID_JSON_ATTEMPTS + 1
    assert CORPUS_QUESTION_ID not in memory.asked_question_ids


def test_coding_pipeline_skips_non_actionable_retrieved_prompt() -> None:

    retrieval_service = MagicMock(spec=QuestionRetrievalService)
    llm = _mock_llm_with_responses([GENERATED_FALLBACK_JSON])
    pipeline = CodingQuestionPipeline(
        retrieval_service=retrieval_service,
        coding_generator=CodingQuestionGenerator(llm),
    )

    with patch(
        RETRIEVE_CODING_CANDIDATES,
        return_value=[
            _build_coding_bank_item(
                text="Explain binary search.",
                question_id="theory-only-id",
            ),
        ],
    ):
        questions, _memory = pipeline.build(
            role=RoleType.FULLSTACK_ENGINEER,
            level=SeniorityLevel.JUNIOR,
            interview_type=InterviewType.TECHNICAL,
            area=InterviewArea.TECH_CODING,
            questions_per_area=1,
        )

    assert len(questions) == 1
    assert questions[0].coding_spec.entrypoint == "max_of_two"
    llm.invoke.assert_called_once()


def test_coding_pipeline_memory_update_only_for_enriched_selection() -> None:

    retrieval_service = MagicMock(spec=QuestionRetrievalService)
    llm = _mock_llm_with_responses([ENRICHED_CODING_JSON])
    pipeline = CodingQuestionPipeline(
        retrieval_service=retrieval_service,
        coding_generator=CodingQuestionGenerator(llm),
    )

    with patch(
        RETRIEVE_CODING_CANDIDATES,
        return_value=[
            _build_coding_bank_item(question_id="enriched-id"),
            _build_coding_bank_item(
                text="How would you solve Valid Parentheses?",
                question_id="overflow-id",
            ),
        ],
    ):
        questions, memory = pipeline.build(
            role=RoleType.FULLSTACK_ENGINEER,
            level=SeniorityLevel.JUNIOR,
            interview_type=InterviewType.TECHNICAL,
            area=InterviewArea.TECH_CODING,
            questions_per_area=1,
        )

    assert len(questions) == 1
    assert "enriched-id" in memory.asked_question_ids
    assert "overflow-id" not in memory.asked_question_ids


def test_coding_pipeline_selects_second_when_first_alignment_fails() -> None:

    retrieval_service = MagicMock(spec=QuestionRetrievalService)
    llm = _mock_llm_with_responses(
        [MISALIGNED_ENRICH_JSON, ENRICHED_CODING_JSON],
    )
    pipeline = CodingQuestionPipeline(
        retrieval_service=retrieval_service,
        coding_generator=CodingQuestionGenerator(llm),
    )

    with patch(
        RETRIEVE_CODING_CANDIDATES,
        return_value=[
            _build_coding_bank_item(question_id="first-actionable-id"),
            _build_coding_bank_item(
                text="How would you implement merge sort?",
                question_id="second-actionable-id",
            ),
        ],
    ):
        questions, memory = pipeline.build(
            role=RoleType.FULLSTACK_ENGINEER,
            level=SeniorityLevel.JUNIOR,
            interview_type=InterviewType.TECHNICAL,
            area=InterviewArea.TECH_CODING,
            questions_per_area=1,
        )

    assert len(questions) == 1
    assert questions[0].provenance is not None
    assert "second-actionable-id" in memory.asked_question_ids
    assert "first-actionable-id" not in memory.asked_question_ids
    assert llm.invoke.call_count == 2


def test_coding_pipeline_selects_third_after_two_enrich_failures() -> None:

    retrieval_service = MagicMock(spec=QuestionRetrievalService)
    llm = _mock_llm_with_responses(
        [
            MISALIGNED_ENRICH_JSON,
            *["invalid-json"] * MAX_INVALID_JSON_ATTEMPTS,
            ENRICHED_CODING_JSON,
        ],
    )
    pipeline = CodingQuestionPipeline(
        retrieval_service=retrieval_service,
        coding_generator=CodingQuestionGenerator(llm),
    )

    with patch(
        RETRIEVE_CODING_CANDIDATES,
        return_value=[
            _build_coding_bank_item(question_id="first-id"),
            _build_coding_bank_item(
                text="How would you solve Valid Parentheses?",
                question_id="second-id",
            ),
            _build_coding_bank_item(
                text="Implement a function to reverse a linked list.",
                question_id="third-id",
            ),
        ],
    ):
        questions, memory = pipeline.build(
            role=RoleType.FULLSTACK_ENGINEER,
            level=SeniorityLevel.JUNIOR,
            interview_type=InterviewType.TECHNICAL,
            area=InterviewArea.TECH_CODING,
            questions_per_area=1,
        )

    assert len(questions) == 1
    assert questions[0].provenance is not None
    assert "third-id" in memory.asked_question_ids


def test_coding_pipeline_all_candidates_fail_then_fallback() -> None:

    retrieval_service = MagicMock(spec=QuestionRetrievalService)
    llm = _mock_llm_with_responses(
        ["invalid-json"] * MAX_INVALID_JSON_ATTEMPTS
        + [MISALIGNED_ENRICH_JSON]
        + ["invalid-json"] * MAX_INVALID_JSON_ATTEMPTS
        + [GENERATED_FALLBACK_JSON],
    )
    pipeline = CodingQuestionPipeline(
        retrieval_service=retrieval_service,
        coding_generator=CodingQuestionGenerator(llm),
    )

    with patch(
        RETRIEVE_CODING_CANDIDATES,
        return_value=[
            _build_coding_bank_item(question_id="first-id"),
            _build_coding_bank_item(
                text="How would you implement binary search?",
                question_id="second-id",
            ),
        ],
    ):
        questions, memory = pipeline.build(
            role=RoleType.FULLSTACK_ENGINEER,
            level=SeniorityLevel.JUNIOR,
            interview_type=InterviewType.TECHNICAL,
            area=InterviewArea.TECH_CODING,
            questions_per_area=1,
        )

    assert len(questions) == 1
    assert questions[0].coding_spec.entrypoint == "max_of_two"
    assert questions[0].provenance is None
    assert CORPUS_QUESTION_ID not in memory.asked_question_ids


def test_coding_pipeline_generate_retry_after_first_failure() -> None:

    retrieval_service = MagicMock(spec=QuestionRetrievalService)
    llm = _mock_llm_with_responses(
        [
            "invalid-json",
            GENERATED_FALLBACK_JSON,
        ],
    )
    pipeline = CodingQuestionPipeline(
        retrieval_service=retrieval_service,
        coding_generator=CodingQuestionGenerator(llm),
    )

    with patch(RETRIEVE_CODING_CANDIDATES, return_value=[]):
        questions, _memory = pipeline.build(
            role=RoleType.FULLSTACK_ENGINEER,
            level=SeniorityLevel.JUNIOR,
            interview_type=InterviewType.TECHNICAL,
            area=InterviewArea.TECH_CODING,
            questions_per_area=1,
        )

    assert len(questions) == 1
    assert questions[0].coding_spec.entrypoint == "max_of_two"
    assert llm.invoke.call_count == 2


def test_coding_pipeline_never_returns_empty_list() -> None:

    retrieval_service = MagicMock(spec=QuestionRetrievalService)
    llm = _mock_llm_with_responses([GENERATED_FALLBACK_JSON])
    pipeline = CodingQuestionPipeline(
        retrieval_service=retrieval_service,
        coding_generator=CodingQuestionGenerator(llm),
    )

    with patch(
        RETRIEVE_CODING_CANDIDATES,
        return_value=[
            _build_coding_bank_item(
                text="Explain binary search.",
                question_id="theory-only-id",
            ),
        ],
    ):
        questions, _memory = pipeline.build(
            role=RoleType.FULLSTACK_ENGINEER,
            level=SeniorityLevel.JUNIOR,
            interview_type=InterviewType.TECHNICAL,
            area=InterviewArea.TECH_CODING,
            questions_per_area=1,
        )

    assert len(questions) >= 1
    _assert_coding_contract(questions[0])


def test_example_enriched_generated_coding_question_model() -> None:

    parsed = GeneratedCodingQuestion.model_validate(
        json.loads(ENRICHED_CODING_JSON)[0],
    )

    assert parsed.coding_spec.entrypoint == "two_sum"
    assert len(parsed.visible_tests) == 2
    assert "two_sum" in parsed.prompt


# ---------------------------------------------------------
# DIFFICULTY PROPAGATION REGRESSION
# ---------------------------------------------------------


def test_coding_corpus_difficulty_2_maps_to_easy() -> None:

    retrieval_service = MagicMock(spec=QuestionRetrievalService)
    llm = _mock_llm_with_responses([ENRICHED_CODING_JSON])
    pipeline = CodingQuestionPipeline(
        retrieval_service=retrieval_service,
        coding_generator=CodingQuestionGenerator(llm),
    )

    item = _build_coding_bank_item()
    item = item.model_copy(update={"difficulty": 2})

    with patch(RETRIEVE_CODING_CANDIDATES, return_value=[item]):
        questions, _ = pipeline.build(
            role=RoleType.FULLSTACK_ENGINEER,
            level=SeniorityLevel.JUNIOR,
            interview_type=InterviewType.TECHNICAL,
            area=InterviewArea.TECH_CODING,
            questions_per_area=1,
        )

    from domain.contracts.question.question import QuestionDifficulty
    assert questions[0].difficulty == QuestionDifficulty.EASY


def test_coding_corpus_difficulty_5_maps_to_hard() -> None:

    retrieval_service = MagicMock(spec=QuestionRetrievalService)
    llm = _mock_llm_with_responses([ENRICHED_CODING_JSON])
    pipeline = CodingQuestionPipeline(
        retrieval_service=retrieval_service,
        coding_generator=CodingQuestionGenerator(llm),
    )

    item = _build_coding_bank_item()
    item = item.model_copy(update={"difficulty": 5})

    with patch(RETRIEVE_CODING_CANDIDATES, return_value=[item]):
        questions, _ = pipeline.build(
            role=RoleType.FULLSTACK_ENGINEER,
            level=SeniorityLevel.JUNIOR,
            interview_type=InterviewType.TECHNICAL,
            area=InterviewArea.TECH_CODING,
            questions_per_area=1,
        )

    from domain.contracts.question.question import QuestionDifficulty
    assert questions[0].difficulty == QuestionDifficulty.HARD
