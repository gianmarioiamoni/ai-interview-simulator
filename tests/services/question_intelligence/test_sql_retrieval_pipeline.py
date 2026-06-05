# tests/services/question_intelligence/test_sql_retrieval_pipeline.py

import json
from unittest.mock import MagicMock, patch

RETRIEVE_SQL_CANDIDATES = (
    "services.question_intelligence.pipelines.sql_question_pipeline."
    "retrieve_sql_candidates"
)

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
from services.question_intelligence.pipelines.sql_question_pipeline import (
    SQLQuestionPipeline,
)
from services.question_intelligence.question_retrieval_service import (
    QuestionRetrievalService,
)
from services.question_intelligence.sql_question_generator import (
    GeneratedSQLQuestion,
    SQLQuestionGenerator,
)
from services.question_ingestion.contracts.ingestion_metadata import IngestionMetadata
from services.sql_engine.sql_executor import SQLExecutor


RETRIEVED_DATABASE_PROMPT = (
    "How can you write an advanced SQL query that returns the top 5 employees "
    "with the highest salary in the Engineering department?"
)

CORPUS_QUESTION_ID = "3d6331e56eb20b84"

ENRICHED_SQL_JSON = json.dumps(
    [
        {
            "prompt": (
                "Return the top 5 highest-paid employees in the Engineering "
                "department, ordered by salary descending."
            ),
            "reference_query": (
                "SELECT e.name, e.salary FROM employees e "
                "JOIN departments d ON e.department_id = d.id "
                "WHERE d.name = 'Engineering' "
                "ORDER BY e.salary DESC LIMIT 5"
            ),
            "test_cases": [
                {
                    "expected_query": (
                        "SELECT name, salary FROM employees "
                        "WHERE department_id = 1 "
                        "ORDER BY salary DESC LIMIT 5"
                    ),
                    "ordered": True,
                },
                {
                    "expected_query": (
                        "SELECT e.name, e.salary FROM employees e "
                        "INNER JOIN departments d ON d.id = e.department_id "
                        "WHERE d.name = 'Engineering' "
                        "ORDER BY e.salary DESC LIMIT 5"
                    ),
                    "ordered": True,
                },
            ],
        },
    ],
)

GENERATED_FALLBACK_JSON = json.dumps(
    [
        {
            "prompt": "List all department names.",
            "reference_query": "SELECT name FROM departments",
            "test_cases": [
                {
                    "expected_query": "SELECT name FROM departments ORDER BY name",
                    "ordered": False,
                },
                {
                    "expected_query": "SELECT d.name FROM departments d",
                    "ordered": False,
                },
            ],
        },
    ],
)


def _build_database_bank_item(
    text: str = RETRIEVED_DATABASE_PROMPT,
    question_id: str = CORPUS_QUESTION_ID,
) -> QuestionBankItem:

    return QuestionBankItem(
        id=question_id,
        text=text,
        interview_type=InterviewType.TECHNICAL,
        role=Role(type=RoleType.BACKEND_ENGINEER),
        area=InterviewArea.TECH_DATABASE,
        level=SeniorityLevel.MID,
        difficulty=2,
        ingestion_metadata=IngestionMetadata(
            source_name="bernabepuente/database-sql-instruction-dataset",
            source_type="question_corpus",
            dataset_version="v1",
            ingestion_timestamp="2020-01-01T00:00:00Z",
        ),
        provenance=QuestionProvenance(
            origin_type=QuestionOriginType.RETRIEVAL,
            source_name="bernabepuente/database-sql-instruction-dataset",
            source_type="question_corpus",
            dataset_version="v1",
            retrieval_score=0.82,
        ),
    )


def _mock_llm_with_responses(responses: list[str]) -> MagicMock:

    llm = MagicMock()
    llm.invoke.side_effect = [
        MagicMock(content=content) for content in responses
    ]
    return llm


def _assert_database_contract(question) -> None:

    assert question.type == QuestionType.DATABASE
    assert question.area == InterviewArea.TECH_DATABASE
    assert question.db_schema
    assert question.db_seed_data
    assert question.reference_solution
    assert len(question.sql_test_cases) >= 1

    for test_case in question.sql_test_cases:
        assert test_case.expected_query
        assert test_case.id

    execution = SQLExecutor().execute(
        question=question,
        query=question.reference_solution,
    )

    assert execution.total_tests == len(question.sql_test_cases)
    assert execution.success is True
    assert execution.passed_tests == execution.total_tests


def test_enrich_from_prompt_success() -> None:

    llm = _mock_llm_with_responses([ENRICHED_SQL_JSON])
    generator = SQLQuestionGenerator(llm)

    item = _build_database_bank_item()
    provenance = QuestionProvenance(
        origin_type=QuestionOriginType.RETRIEVAL,
        source_name=item.ingestion_metadata.source_name,
        source_type=item.ingestion_metadata.source_type,
        dataset_version=item.ingestion_metadata.dataset_version,
        retrieval_score=0.82,
        generated_by_model="sql_question_enrichment",
    )

    question = generator.enrich_from_prompt(
        seed_prompt=RETRIEVED_DATABASE_PROMPT,
        role=RoleType.BACKEND_ENGINEER,
        level=SeniorityLevel.MID,
        provenance=provenance,
    )

    assert question is not None
    assert question.provenance is not None
    assert question.provenance.origin_type == QuestionOriginType.RETRIEVAL
    assert question.provenance.generated_by_model == "sql_question_enrichment"
    assert RETRIEVED_DATABASE_PROMPT not in question.prompt
    _assert_database_contract(question)

    llm.invoke.assert_called_once()
    call_prompt = llm.invoke.call_args[0][0]
    assert RETRIEVED_DATABASE_PROMPT in call_prompt


def test_enrich_from_prompt_failure_returns_none() -> None:

    llm = _mock_llm_with_responses(["not-json"])
    generator = SQLQuestionGenerator(llm)

    question = generator.enrich_from_prompt(
        seed_prompt=RETRIEVED_DATABASE_PROMPT,
        role=RoleType.BACKEND_ENGINEER,
        level=SeniorityLevel.MID,
    )

    assert question is None


def test_sql_pipeline_retrieval_and_enrichment_success() -> None:

    retrieval_service = MagicMock(spec=QuestionRetrievalService)
    llm = _mock_llm_with_responses([ENRICHED_SQL_JSON])
    pipeline = SQLQuestionPipeline(
        retrieval_service=retrieval_service,
        sql_generator=SQLQuestionGenerator(llm),
    )

    with patch(
        RETRIEVE_SQL_CANDIDATES,
        return_value=[_build_database_bank_item()],
    ) as mock_retrieve:
        questions, memory = pipeline.build(
            role=RoleType.BACKEND_ENGINEER,
            level=SeniorityLevel.MID,
            interview_type=InterviewType.TECHNICAL,
            area=InterviewArea.TECH_DATABASE,
            questions_per_area=1,
        )

    assert len(questions) == 1
    assert questions[0].provenance is not None
    assert questions[0].provenance.origin_type == QuestionOriginType.RETRIEVAL
    _assert_database_contract(questions[0])

    mock_retrieve.assert_called_once()
    assert CORPUS_QUESTION_ID in memory.asked_question_ids
    llm.invoke.assert_called_once()


def test_sql_pipeline_enrichment_failure_falls_back_to_generate() -> None:

    retrieval_service = MagicMock(spec=QuestionRetrievalService)
    llm = _mock_llm_with_responses(
        [
            "invalid-json",
            GENERATED_FALLBACK_JSON,
        ],
    )

    pipeline = SQLQuestionPipeline(
        retrieval_service=retrieval_service,
        sql_generator=SQLQuestionGenerator(llm),
    )

    with patch(
        RETRIEVE_SQL_CANDIDATES,
        return_value=[_build_database_bank_item()],
    ):
        questions, memory = pipeline.build(
            role=RoleType.BACKEND_ENGINEER,
            level=SeniorityLevel.MID,
            interview_type=InterviewType.TECHNICAL,
            area=InterviewArea.TECH_DATABASE,
            questions_per_area=1,
        )

    assert len(questions) == 1
    assert questions[0].prompt == "List all department names."
    assert questions[0].provenance is None
    _assert_database_contract(questions[0])

    assert llm.invoke.call_count == 2
    assert CORPUS_QUESTION_ID not in memory.asked_question_ids


def test_sql_pipeline_selects_first_actionable_candidate() -> None:

    retrieval_service = MagicMock(spec=QuestionRetrievalService)
    llm = _mock_llm_with_responses([ENRICHED_SQL_JSON])
    pipeline = SQLQuestionPipeline(
        retrieval_service=retrieval_service,
        sql_generator=SQLQuestionGenerator(llm),
    )

    with patch(
        RETRIEVE_SQL_CANDIDATES,
        return_value=[_build_database_bank_item()],
    ):
        questions, memory = pipeline.build(
        role=RoleType.BACKEND_ENGINEER,
        level=SeniorityLevel.MID,
        interview_type=InterviewType.TECHNICAL,
        area=InterviewArea.TECH_DATABASE,
        questions_per_area=1,
    )

    assert len(questions) == 1
    assert questions[0].provenance is not None
    assert CORPUS_QUESTION_ID in memory.asked_question_ids
    llm.invoke.assert_called_once()


def test_sql_pipeline_selects_second_when_first_non_actionable() -> None:

    retrieval_service = MagicMock(spec=QuestionRetrievalService)
    llm = _mock_llm_with_responses([ENRICHED_SQL_JSON])
    pipeline = SQLQuestionPipeline(
        retrieval_service=retrieval_service,
        sql_generator=SQLQuestionGenerator(llm),
    )

    with patch(
        RETRIEVE_SQL_CANDIDATES,
        return_value=[
            _build_database_bank_item(
                text="What is a view in SQL?",
                question_id="theory-only-id",
            ),
            _build_database_bank_item(
                text=RETRIEVED_DATABASE_PROMPT,
                question_id="actionable-second-id",
            ),
        ],
    ):
        questions, memory = pipeline.build(
        role=RoleType.BACKEND_ENGINEER,
        level=SeniorityLevel.MID,
        interview_type=InterviewType.TECHNICAL,
        area=InterviewArea.TECH_DATABASE,
        questions_per_area=1,
    )

    assert len(questions) == 1
    assert questions[0].provenance is not None
    assert "actionable-second-id" in memory.asked_question_ids
    assert "theory-only-id" not in memory.asked_question_ids
    llm.invoke.assert_called_once()


def test_sql_pipeline_selects_second_when_first_enrichment_fails() -> None:

    second_prompt = (
        "Write a SQL query to list employees who are assigned to "
        "more than one project using a join."
    )

    retrieval_service = MagicMock(spec=QuestionRetrievalService)
    llm = _mock_llm_with_responses(
        [
            "invalid-json",
            ENRICHED_SQL_JSON,
        ],
    )
    pipeline = SQLQuestionPipeline(
        retrieval_service=retrieval_service,
        sql_generator=SQLQuestionGenerator(llm),
    )

    with patch(
        RETRIEVE_SQL_CANDIDATES,
        return_value=[
            _build_database_bank_item(question_id="first-actionable-id"),
            _build_database_bank_item(
                text=second_prompt,
                question_id="second-actionable-id",
            ),
        ],
    ):
        questions, memory = pipeline.build(
        role=RoleType.BACKEND_ENGINEER,
        level=SeniorityLevel.MID,
        interview_type=InterviewType.TECHNICAL,
        area=InterviewArea.TECH_DATABASE,
        questions_per_area=1,
    )

    assert len(questions) == 1
    assert questions[0].provenance is not None
    assert "second-actionable-id" in memory.asked_question_ids
    assert "first-actionable-id" not in memory.asked_question_ids
    assert llm.invoke.call_count == 2


def test_sql_pipeline_skips_non_actionable_retrieved_prompt() -> None:

    retrieval_service = MagicMock(spec=QuestionRetrievalService)
    llm = _mock_llm_with_responses([GENERATED_FALLBACK_JSON])
    pipeline = SQLQuestionPipeline(
        retrieval_service=retrieval_service,
        sql_generator=SQLQuestionGenerator(llm),
    )

    with patch(
        RETRIEVE_SQL_CANDIDATES,
        return_value=[
            _build_database_bank_item(
                text="What is database replication?",
                question_id="theory-only-id",
            ),
        ],
    ):
        questions, _memory = pipeline.build(
        role=RoleType.BACKEND_ENGINEER,
        level=SeniorityLevel.MID,
        interview_type=InterviewType.TECHNICAL,
        area=InterviewArea.TECH_DATABASE,
        questions_per_area=1,
    )

    assert len(questions) == 1
    assert questions[0].prompt == "List all department names."
    llm.invoke.assert_called_once()


def test_sql_pipeline_memory_update_only_for_enriched_selection() -> None:

    retrieval_service = MagicMock(spec=QuestionRetrievalService)
    llm = _mock_llm_with_responses([ENRICHED_SQL_JSON])
    pipeline = SQLQuestionPipeline(
        retrieval_service=retrieval_service,
        sql_generator=SQLQuestionGenerator(llm),
    )

    with patch(
        RETRIEVE_SQL_CANDIDATES,
        return_value=[
            _build_database_bank_item(
                text="What is a view in SQL?",
                question_id="skipped-id",
            ),
            _build_database_bank_item(question_id="enriched-id"),
            _build_database_bank_item(
                text=(
                    "Write a SQL query to list employees who are assigned to "
                    "more than one project using a join."
                ),
                question_id="overflow-id",
            ),
        ],
    ):
        questions, memory = pipeline.build(
        role=RoleType.BACKEND_ENGINEER,
        level=SeniorityLevel.MID,
        interview_type=InterviewType.TECHNICAL,
        area=InterviewArea.TECH_DATABASE,
        questions_per_area=1,
    )

    assert len(questions) == 1
    assert "enriched-id" in memory.asked_question_ids
    assert "skipped-id" not in memory.asked_question_ids
    assert "overflow-id" not in memory.asked_question_ids


def test_sql_pipeline_generate_retry_after_first_failure() -> None:

    retrieval_service = MagicMock(spec=QuestionRetrievalService)
    llm = _mock_llm_with_responses(
        [
            "invalid-json",
            GENERATED_FALLBACK_JSON,
        ],
    )
    pipeline = SQLQuestionPipeline(
        retrieval_service=retrieval_service,
        sql_generator=SQLQuestionGenerator(llm),
    )

    with patch(RETRIEVE_SQL_CANDIDATES, return_value=[]):
        questions, _memory = pipeline.build(
            role=RoleType.BACKEND_ENGINEER,
            level=SeniorityLevel.MID,
            interview_type=InterviewType.TECHNICAL,
            area=InterviewArea.TECH_DATABASE,
            questions_per_area=1,
        )

    assert len(questions) == 1
    assert questions[0].prompt == "List all department names."
    assert llm.invoke.call_count == 2


def test_sql_pipeline_never_returns_empty_list() -> None:

    retrieval_service = MagicMock(spec=QuestionRetrievalService)
    llm = _mock_llm_with_responses([GENERATED_FALLBACK_JSON])
    pipeline = SQLQuestionPipeline(
        retrieval_service=retrieval_service,
        sql_generator=SQLQuestionGenerator(llm),
    )

    with patch(
        RETRIEVE_SQL_CANDIDATES,
        return_value=[
            _build_database_bank_item(
                text="What is database replication?",
                question_id="theory-only-id",
            ),
        ],
    ):
        questions, _memory = pipeline.build(
            role=RoleType.FULLSTACK_ENGINEER,
            level=SeniorityLevel.MID,
            interview_type=InterviewType.TECHNICAL,
            area=InterviewArea.TECH_DATABASE,
            questions_per_area=1,
        )

    assert len(questions) >= 1
    _assert_database_contract(questions[0])


def test_example_enriched_generated_sql_question_model() -> None:

    parsed = GeneratedSQLQuestion.model_validate(
        json.loads(ENRICHED_SQL_JSON)[0],
    )

    assert parsed.reference_query.startswith("SELECT")
    assert len(parsed.test_cases) == 2
    assert "Engineering" in parsed.prompt
