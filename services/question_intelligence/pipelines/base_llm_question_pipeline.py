# services/question_intelligence/pipelines/base_llm_question_pipeline.py

from abc import ABC, abstractmethod
from typing import List

from domain.contracts.question.question import Question
from domain.contracts.question.question_bank_item import QuestionBankItem
from domain.contracts.question.question_origin_type import QuestionOriginType
from domain.contracts.question.question_provenance import QuestionProvenance
from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.interview.interview_type import InterviewType
from domain.contracts.user.role import RoleType
from domain.contracts.user.seniority_level import SeniorityLevel

from services.question_corpus.contracts.interview_retrieval_memory import (
    InterviewRetrievalMemory,
)
from services.question_intelligence.retrieval_query_builder import RetrievalQueryBuilder
from services.question_intelligence.retrieval.retrieval_strategy_resolver import (
    RetrievalStrategyResolver,
)
from services.question_corpus.retrieval.interview_memory_updater import (
    InterviewMemoryUpdater,
)
from services.question_intelligence.interview_theme_guidance import build_theme_guidance
from services.question_intelligence.interview_theme_memory import (
    get_interview_theme_anchor,
)

from app.core.logger import get_logger

logger = get_logger(__name__)


class BaseLLMQuestionPipeline(ABC):
    """
    Shared scaffold for LLM-based question pipelines (coding, SQL).

    Concrete subclasses implement:
      - _pipeline_label: short string used in log messages
      - _candidate_scan_k: how many candidates to fetch from the corpus
      - _generate_max_attempts: retry budget for LLM generation
      - _retrieve_candidates(): perform corpus retrieval and return bank items
      - _enrich_item(): enrich a single bank item via LLM; returns Question or None
      - _generate_with_retry(): call the LLM generator with retry logic
      - _build_provenance_model_tag(): tag for QuestionProvenance.generated_by_model
    """

    def __init__(self) -> None:
        self._retrieval_query_builder = RetrievalQueryBuilder()
        self._retrieval_strategy_resolver = RetrievalStrategyResolver()
        self._memory_updater = InterviewMemoryUpdater()

    # ------------------------------------------------------------------
    # PUBLIC — preserved signature, subclasses do NOT override this
    # ------------------------------------------------------------------

    def build(
        self,
        role: RoleType,
        level: SeniorityLevel,
        interview_type: InterviewType,
        area: InterviewArea,
        questions_per_area: int,
        corpus_quota: int | None = None,
        memory: InterviewRetrievalMemory | None = None,
        job_description: str | None = None,
        company_description: str | None = None,
    ) -> tuple[List[Question], InterviewRetrievalMemory]:
        """
        Orchestrate retrieval → enrich → generate → memory update.

        corpus_quota caps how many questions are drawn from the retrieval
        corpus. Remaining slots are filled by LLM generation. When None the
        pipeline fills as many corpus questions as available (legacy behaviour).
        """

        session_memory = memory if memory is not None else InterviewRetrievalMemory()

        questions: List[Question] = []
        enriched_pairs: list[tuple[QuestionBankItem, Question]] = []

        theme_anchor = get_interview_theme_anchor(session_memory)
        theme_guidance = build_theme_guidance(theme_anchor=theme_anchor, area=area)

        retrieval_query = self._retrieval_query_builder.build(
            role=role,
            level=level,
            area=area,
            theme_anchor=theme_anchor,
            memory=session_memory,
        )

        effective_corpus_target = (
            min(corpus_quota, questions_per_area)
            if corpus_quota is not None
            else questions_per_area
        )
        candidate_scan_k = max(effective_corpus_target, self._candidate_scan_k())

        retrieval_strategy = self._retrieval_strategy_resolver.resolve(
            area=area,
            level=level,
            questions_per_area=candidate_scan_k,
        )

        retrieved = self._retrieve_candidates(
            role=role,
            level=level,
            interview_type=interview_type,
            area=area,
            memory=session_memory,
            retrieval_query=retrieval_query,
            retrieval_strategy=retrieval_strategy,
        )

        label = self._pipeline_label()

        for item in retrieved:

            if len(questions) >= questions_per_area:
                break

            if corpus_quota is not None and len(questions) >= corpus_quota:
                break

            provenance = self._build_enrichment_provenance(item)

            enriched = self._enrich_item(
                item=item,
                role=role,
                level=level,
                area=area,
                provenance=provenance,
                theme_guidance=theme_guidance,
                job_description=job_description,
                company_description=company_description,
            )

            if enriched is None:
                logger.debug("[%s] Enrichment failed for item: %s", label, item.id)
                continue

            enriched_pairs.append((item, enriched))
            questions.append(enriched)

        remaining_slots = questions_per_area - len(questions)

        if remaining_slots > 0:
            questions.extend(
                self._generate_with_retry(
                    role=role,
                    level=level,
                    n=remaining_slots,
                    theme_guidance=theme_guidance,
                    job_description=job_description,
                    company_description=company_description,
                )
            )

        if not questions:
            questions.extend(
                self._generate_with_retry(
                    role=role,
                    level=level,
                    n=max(1, questions_per_area),
                    theme_guidance=theme_guidance,
                    job_description=job_description,
                    company_description=company_description,
                )
            )

        if len(questions) < questions_per_area:
            logger.warning(
                "[%s] Area %s produced %d questions (expected %d)",
                label,
                area.value,
                len(questions),
                questions_per_area,
            )

        final_questions = questions[:questions_per_area]

        if not final_questions:
            final_questions = self._generate_with_retry(
                role=role,
                level=level,
                n=max(1, questions_per_area),
                theme_guidance=theme_guidance,
                job_description=job_description,
                company_description=company_description,
            )[:questions_per_area]

        final_prompts = {q.prompt for q in final_questions}

        for bank_item, mapped_question in enriched_pairs:
            if mapped_question.prompt not in final_prompts:
                continue
            session_memory = self._memory_updater.record_bank_item_selection(
                memory=session_memory,
                item=bank_item,
            )

        return final_questions, session_memory

    # ------------------------------------------------------------------
    # SHARED UTILITY
    # ------------------------------------------------------------------

    def _build_enrichment_provenance(
        self,
        item: QuestionBankItem,
    ) -> QuestionProvenance:
        """
        Build a QuestionProvenance from a bank item's existing provenance and
        ingestion metadata. Identical across all LLM-based pipelines.
        """

        base = item.provenance

        source_name = (
            base.source_name
            if base and base.source_name
            else item.ingestion_metadata.source_name
        )

        source_type = (
            base.source_type
            if base and base.source_type
            else item.ingestion_metadata.source_type
        )

        dataset_version = (
            base.dataset_version
            if base and base.dataset_version
            else item.ingestion_metadata.dataset_version
        )

        retrieval_score = base.retrieval_score if base else None

        return QuestionProvenance(
            origin_type=QuestionOriginType.RETRIEVAL,
            source_name=source_name,
            source_type=source_type,
            dataset_version=dataset_version,
            retrieval_score=retrieval_score,
            generated_by_model=self._build_provenance_model_tag(),
            domains=list(item.domains),
        )

    # ------------------------------------------------------------------
    # ABSTRACT — subclasses MUST implement
    # ------------------------------------------------------------------

    @abstractmethod
    def _pipeline_label(self) -> str:
        """Short uppercase label used in log messages, e.g. 'CODING' or 'SQL'."""

    @abstractmethod
    def _candidate_scan_k(self) -> int:
        """Minimum number of corpus candidates to scan."""

    @abstractmethod
    def _retrieve_candidates(
        self,
        role: RoleType,
        level: SeniorityLevel,
        interview_type: InterviewType,
        area: InterviewArea,
        memory: InterviewRetrievalMemory,
        retrieval_query: str,
        retrieval_strategy,
    ) -> list[QuestionBankItem]:
        """Fetch candidates from the retrieval corpus."""

    @abstractmethod
    def _enrich_item(
        self,
        item: QuestionBankItem,
        role: RoleType,
        level: SeniorityLevel,
        area: InterviewArea,
        provenance: QuestionProvenance,
        theme_guidance: str | None,
        job_description: str | None = None,
        company_description: str | None = None,
    ) -> Question | None:
        """Enrich a single bank item via LLM. Return None on failure."""

    @abstractmethod
    def _generate_with_retry(
        self,
        role: RoleType,
        level: SeniorityLevel,
        n: int,
        theme_guidance: str | None = None,
        job_description: str | None = None,
        company_description: str | None = None,
    ) -> List[Question]:
        """Generate questions from scratch via LLM with retry logic."""

    @abstractmethod
    def _build_provenance_model_tag(self) -> str:
        """Value for QuestionProvenance.generated_by_model."""
