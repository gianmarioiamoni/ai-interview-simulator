# tests/services/question_intelligence/test_interview_theme_assembly.py

from unittest.mock import MagicMock, patch

from langchain_core.documents import Document

from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.interview.interview_type import InterviewType
from domain.contracts.question.question import Question, QuestionDifficulty, QuestionType
from domain.contracts.question.question_bank_item import QuestionBankItem
from domain.contracts.question.question_origin_type import QuestionOriginType
from domain.contracts.question.question_provenance import QuestionProvenance
from domain.contracts.user.role import Role, RoleType
from domain.contracts.user.seniority_level import SeniorityLevel
from services.question_ingestion.contracts.ingestion_metadata import IngestionMetadata
from services.question_corpus.contracts.adaptive_retrieval_context import (
    AdaptiveRetrievalContext,
)
from services.question_corpus.contracts.interview_retrieval_memory import (
    InterviewRetrievalMemory,
)
from services.question_corpus.contracts.retrieval_candidate import RetrievalCandidate
from services.question_corpus.retrieval.adaptive_context_builder import (
    AdaptiveContextBuilder,
)
from services.question_corpus.retrieval.weak_domain_boost_engine import (
    WeakDomainBoostEngine,
)
from services.question_intelligence.interview_coherence_metrics import (
    InterviewCoherenceMetrics,
)
from services.question_intelligence.interview_theme_memory import (
    get_interview_theme_anchor,
    with_interview_theme_anchor,
)
from services.question_intelligence.interview_theme_selector import (
    InterviewThemeSelector,
)
from services.question_intelligence.question_generator import QuestionGenerator
from services.question_intelligence.question_set_builder import QuestionSetBuilder
from services.question_intelligence.quality.question_set_quality_analyzer import (
    QuestionSetQualityAnalyzer,
)
from services.question_intelligence.semantic_deduplicator import SemanticDeduplicator
from services.question_intelligence.retrieval_query_builder import RetrievalQueryBuilder


def test_theme_anchor_stored_in_strong_domains() -> None:

    memory = InterviewRetrievalMemory()
    updated = with_interview_theme_anchor(memory, "distributed_systems")

    assert get_interview_theme_anchor(updated) == "distributed_systems"
    assert updated.theme_anchor == "distributed_systems"


def test_theme_selector_is_data_driven_from_corpus() -> None:

    selector = InterviewThemeSelector()
    anchor = selector.select_anchor(
        role=RoleType.BACKEND_ENGINEER,
        level=SeniorityLevel.MID,
        first_area=InterviewArea.TECH_BACKGROUND,
    )

    assert anchor
    assert anchor != "other"


def test_theme_selector_prefers_cluster_and_topic_signals() -> None:
    # Patch the corpus prior so it is neutral, ensuring the test validates
    # only the preview-item signal logic (topic + text + cluster votes).
    with patch(
        "services.question_intelligence.interview_theme_selector"
        ".compute_technical_thematic_domain_counts",
        return_value={"distributed_systems": 1, "data_engineering": 1},
    ):
        selector = InterviewThemeSelector()
        preview_items = [
            _build_bank_item(
                "distributed rate limiter across multiple nodes",
                "item-1",
            ),
            _build_bank_item(
                "CAP theorem trade-offs in partitioned systems",
                "item-2",
            ),
            _build_bank_item(
                "eventual consistency in notification pipeline",
                "item-3",
            ),
        ]

        anchor = selector.select_anchor(
            role=RoleType.BACKEND_ENGINEER,
            level=SeniorityLevel.MID,
            first_area=InterviewArea.TECH_BACKGROUND,
            preview_items=preview_items,
        )

    assert anchor == "distributed_systems"


def test_adaptive_context_builder_propagates_strong_domains() -> None:

    memory = with_interview_theme_anchor(
        InterviewRetrievalMemory(),
        "system_design",
    )
    context = AdaptiveContextBuilder().build(
        memory=memory,
        role="backend_engineer",
        seniority="mid",
        area="technical_background",
        question_count=1,
    )

    assert context.memory.theme_anchor == "system_design"
    assert get_interview_theme_anchor(context.memory) == "system_design"


def test_weak_domain_boost_engine_applies_theme_affinity_soft_bias() -> None:

    memory = with_interview_theme_anchor(
        InterviewRetrievalMemory(),
        "join",
    )
    context = AdaptiveRetrievalContext(
        current_role="backend_engineer",
        seniority="mid",
        target_area="technical_case_study",
        target_question_count=1,
        memory=memory,
    )

    aligned = _build_candidate(
        document_id="aligned",
        domains="join",
        text="Explain how to perform a complex join between two tables",
        adaptive_score=0.70,
    )
    neutral = _build_candidate(
        document_id="neutral",
        domains="indexing",
        text="Explain B-tree index structure",
        adaptive_score=0.72,
    )

    boosted = WeakDomainBoostEngine().apply(
        candidates=[neutral, aligned],
        context=context,
    )

    assert boosted[0].document.metadata["document_id"] == "aligned"
    assert boosted[0].adaptive_score > neutral.adaptive_score


def test_retrieval_query_builder_includes_theme_anchor() -> None:

    query = RetrievalQueryBuilder().build(
        role=RoleType.BACKEND_ENGINEER,
        level=SeniorityLevel.MID,
        area=InterviewArea.TECH_CASE_STUDY,
        theme_anchor="distributed_systems",
    )

    assert "distributed systems" in query.lower()


def test_question_generator_includes_theme_guidance() -> None:

    llm = MagicMock()
    generator = QuestionGenerator(llm)
    prompt = generator._build_prompt(
        role=RoleType.BACKEND_ENGINEER,
        level=SeniorityLevel.MID,
        interview_type=InterviewType.TECHNICAL,
        area=InterviewArea.TECH_CASE_STUDY,
        n=1,
        variation="Focus on trade-offs",
        theme_guidance="Interview theme anchor: distributed systems",
    )

    assert "distributed systems" in prompt.lower()


def test_question_set_builder_propagates_theme_through_memory() -> None:

    areas = InterviewType.TECHNICAL.get_areas()
    area_builder = MagicMock()

    area_builder.build.side_effect = lambda **kwargs: (
        [
            Question(
                id=f"id-{kwargs['area'].value}",
                area=kwargs["area"],
                type=QuestionType.WRITTEN,
                prompt=f"Prompt for {kwargs['area'].value}",
                difficulty=QuestionDifficulty.MEDIUM,
            ),
        ],
        kwargs.get("memory") or InterviewRetrievalMemory(),
    )

    deduplicator = MagicMock()
    deduplicator.deduplicate.side_effect = lambda questions: questions

    builder = QuestionSetBuilder(
        area_builder=area_builder,
        deduplicator=deduplicator,
        quality_analyzer=QuestionSetQualityAnalyzer(),
    )

    builder.build(
        role=RoleType.BACKEND_ENGINEER,
        level=SeniorityLevel.MID,
        interview_type=InterviewType.TECHNICAL,
        areas=areas,
        questions_per_area=1,
    )

    first_call_memory = area_builder.build.call_args_list[0].kwargs["memory"]
    assert get_interview_theme_anchor(first_call_memory) is not None


def test_coherence_metrics_report_theme_consistency() -> None:

    memory = with_interview_theme_anchor(
        InterviewRetrievalMemory(),
        "distributed_systems",
    )
    questions = [
        Question(
            id="1",
            area=InterviewArea.TECH_BACKGROUND,
            type=QuestionType.WRITTEN,
            prompt="Describe your experience with distributed systems architectures",
            difficulty=QuestionDifficulty.MEDIUM,
        ),
        Question(
            id="2",
            area=InterviewArea.TECH_CASE_STUDY,
            type=QuestionType.WRITTEN,
            prompt="Design a distributed notification system with eventual consistency",
            difficulty=QuestionDifficulty.MEDIUM,
        ),
    ]

    metrics = InterviewCoherenceMetrics().compute(
        questions=questions,
        memory=memory,
    )

    assert metrics["theme_anchor"] == "distributed_systems"
    assert metrics["theme_consistency"] > 0.0


def _build_bank_item(
    text: str,
    item_id: str,
) -> QuestionBankItem:

    return QuestionBankItem(
        id=item_id,
        text=text,
        interview_type=InterviewType.TECHNICAL,
        role=Role(type=RoleType.BACKEND_ENGINEER),
        area=InterviewArea.TECH_BACKGROUND,
        level=SeniorityLevel.MID,
        difficulty=3,
        ingestion_metadata=IngestionMetadata(
            source_name="test",
            source_type="question_corpus",
            dataset_version="v1",
            ingestion_timestamp="2020-01-01T00:00:00Z",
        ),
        provenance=QuestionProvenance(
            origin_type=QuestionOriginType.RETRIEVAL,
            source_name="test",
            source_type="question_corpus",
            dataset_version="v1",
        ),
    )


def _build_candidate(
    document_id: str,
    domains: str,
    text: str,
    adaptive_score: float,
) -> RetrievalCandidate:

    return RetrievalCandidate(
        document=Document(
            page_content=text,
            metadata={
                "document_id": document_id,
                "domains": domains,
            },
        ),
        semantic_score=0.8,
        quality_score=0.8,
        final_score=adaptive_score,
        adaptive_score=adaptive_score,
    )
