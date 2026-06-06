# tests/services/question_intelligence/test_session_variety_selection.py

from unittest.mock import MagicMock

from langchain_core.documents import Document

from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.interview.interview_type import InterviewType
from domain.contracts.question.question import Question, QuestionDifficulty, QuestionType
from domain.contracts.question.question_bank_item import QuestionBankItem
from domain.contracts.question.question_origin_type import QuestionOriginType
from domain.contracts.question.question_provenance import QuestionProvenance
from domain.contracts.user.role import Role, RoleType
from domain.contracts.user.seniority_level import SeniorityLevel
from services.question_corpus.contracts.adaptive_retrieval_context import (
    AdaptiveRetrievalContext,
)
from services.question_corpus.contracts.interview_retrieval_memory import (
    InterviewRetrievalMemory,
)
from services.question_corpus.contracts.retrieval_candidate import RetrievalCandidate
from services.question_corpus.retrieval.interview_memory_updater import (
    InterviewMemoryUpdater,
)
from services.question_intelligence.performance_responsive_candidate_selector import (
    PerformanceResponsiveCandidateSelector,
)
from services.question_intelligence.session_variety_memory import (
    SessionVarietyMemoryHelper,
)
from services.question_intelligence.session_variety_scorer import SessionVarietyScorer
from services.question_ingestion.contracts.ingestion_metadata import IngestionMetadata


def _context(
    target_difficulty: int = 4,
    memory: InterviewRetrievalMemory | None = None,
) -> AdaptiveRetrievalContext:

    return AdaptiveRetrievalContext(
        current_role="backend_engineer",
        seniority="mid",
        target_area="technical_technical_knowledge",
        target_question_count=1,
        target_difficulty=target_difficulty,
        memory=memory or InterviewRetrievalMemory(),
    )


def _candidate(
    doc_id: str,
    prompt: str,
    difficulty: int,
    score: float = 0.8,
) -> RetrievalCandidate:

    return RetrievalCandidate(
        document=Document(
            page_content=prompt,
            metadata={
                "document_id": doc_id,
                "difficulty": difficulty,
                "area": "technical_technical_knowledge",
            },
        ),
        semantic_score=score,
        quality_score=score,
        final_score=score,
        adaptive_score=score,
    )


def _bank_item(text: str, item_id: str = "prior") -> QuestionBankItem:

    return QuestionBankItem(
        id=item_id,
        text=text,
        interview_type=InterviewType.TECHNICAL,
        role=Role(type=RoleType.BACKEND_ENGINEER),
        area=InterviewArea.TECH_TECHNICAL_KNOWLEDGE,
        level=SeniorityLevel.MID,
        difficulty=4,
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


def test_session_memory_records_prompts_and_topics() -> None:

    helper = SessionVarietyMemoryHelper(
        topic_extractor=MagicMock(extract=MagicMock(side_effect=["apis", "databases"])),
    )

    memory = helper.record_prompt(
        memory=InterviewRetrievalMemory(),
        prompt="Explain REST API versioning strategies.",
    )
    memory = helper.record_prompt(
        memory=memory,
        prompt="How would you optimize SQL indexes?",
    )

    assert len(memory.session_selected_prompts) == 2
    assert memory.session_used_topics == ["apis", "databases"]


def test_memory_updater_records_session_variety_on_bank_item_selection() -> None:

    topic_extractor = MagicMock()
    topic_extractor.extract.return_value = "distributed_systems"

    updater = InterviewMemoryUpdater(
        variety_memory_helper=SessionVarietyMemoryHelper(
            topic_extractor=topic_extractor,
        ),
    )

    updated = updater.record_bank_item_selection(
        memory=InterviewRetrievalMemory(),
        item=_bank_item("Describe CAP theorem trade-offs in distributed systems."),
    )

    assert len(updated.session_selected_prompts) == 1
    assert "distributed_systems" in updated.session_used_topics


def test_session_dedup_filters_near_duplicate_candidates() -> None:

    scorer = SessionVarietyScorer(
        semantic_deduplicator=MagicMock(),
        cluster_suppressor=MagicMock(),
        planner_scoring_engine=MagicMock(),
    )

    memory = InterviewRetrievalMemory(
        session_selected_prompts=[
            "Explain REST API versioning strategies for microservices.",
        ],
    )
    pool = [
        _candidate(
            "dup",
            "Explain REST API versioning strategies for microservices.",
            difficulty=4,
            score=0.95,
        ),
        _candidate(
            "novel",
            "How do you design idempotent payment processing?",
            difficulty=4,
            score=0.70,
        ),
    ]

    filtered = scorer.filter_session_duplicates(pool=pool, memory=memory)

    assert filtered[0].document.metadata["document_id"] == "novel"


def test_topic_variety_prefers_unused_topic_at_equal_difficulty() -> None:

    topic_extractor = MagicMock()
    topic_extractor.extract.side_effect = lambda text: (
        "apis" if "API" in text else "databases"
    )

    variety_scorer = SessionVarietyScorer(
        topic_extractor=topic_extractor,
        semantic_deduplicator=MagicMock(),
        cluster_suppressor=MagicMock(
            apply_penalty=MagicMock(side_effect=lambda candidate, selected_questions, current_score: current_score),
        ),
        planner_scoring_engine=MagicMock(
            score=MagicMock(
                return_value=MagicMock(novelty_bonus=0.0, final_score=4.0),
            ),
        ),
    )

    selector = PerformanceResponsiveCandidateSelector(variety_scorer=variety_scorer)
    memory = InterviewRetrievalMemory(session_used_topics=["apis"])
    pool = [
        _candidate("api-q", "Describe API gateway rate limiting.", difficulty=4, score=0.95),
        _candidate("db-q", "Explain database transaction isolation levels.", difficulty=4, score=0.70),
    ]

    selected = selector.select(pool=pool, context=_context(memory=memory))

    assert selected[0].document.metadata["document_id"] == "db-q"


def test_adaptive_difficulty_still_beats_variety() -> None:

    variety_scorer = SessionVarietyScorer(
        topic_extractor=MagicMock(extract=MagicMock(return_value="other")),
        semantic_deduplicator=MagicMock(),
        cluster_suppressor=MagicMock(
            apply_penalty=MagicMock(side_effect=lambda candidate, selected_questions, current_score: current_score),
        ),
        planner_scoring_engine=MagicMock(
            score=MagicMock(
                return_value=MagicMock(novelty_bonus=0.0, final_score=4.0),
            ),
        ),
    )

    selector = PerformanceResponsiveCandidateSelector(variety_scorer=variety_scorer)
    pool = [
        _candidate("novel-hard", "Unique blockchain consensus design question.", difficulty=5, score=0.95),
        _candidate("aligned", "Standard caching strategy question.", difficulty=4, score=0.70),
    ]

    selected = selector.select(pool=pool, context=_context(target_difficulty=4))

    assert selected[0].document.metadata["document_id"] == "aligned"


def test_memory_updater_records_variety_from_question_evaluation() -> None:

    topic_extractor = MagicMock()
    topic_extractor.extract.return_value = "career"

    updater = InterviewMemoryUpdater(
        variety_memory_helper=SessionVarietyMemoryHelper(
            topic_extractor=topic_extractor,
        ),
    )

    question = Question(
        id="q-1",
        area=InterviewArea.TECH_BACKGROUND,
        type=QuestionType.WRITTEN,
        prompt="Tell me about your backend engineering experience.",
        difficulty=QuestionDifficulty.MEDIUM,
    )

    updated = updater.update_from_question_evaluation(
        memory=InterviewRetrievalMemory(),
        question=question,
        evaluation_score=0.8,
    )

    assert updated.session_selected_prompts == [question.prompt]
    assert updated.session_used_topics == ["career"]
