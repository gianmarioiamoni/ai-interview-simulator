# services/question_intelligence/pipelines/sql_question_pipeline.py

import re
from typing import List

from domain.contracts.question.question import (
    Question,
)
from domain.contracts.question.question_bank_item import (
    QuestionBankItem,
)
from domain.contracts.question.question_origin_type import (
    QuestionOriginType,
)
from domain.contracts.question.question_provenance import (
    QuestionProvenance,
)

from domain.contracts.interview.interview_area import (
    InterviewArea,
)
from domain.contracts.interview.interview_type import (
    InterviewType,
)

from domain.contracts.user.role import RoleType

from domain.contracts.user.seniority_level import (
    SeniorityLevel,
)

from services.question_intelligence.sql_question_generator import (
    SQLQuestionGenerator,
)

from services.question_intelligence.pipelines.sql_pipeline_retrieval import (
    SqlPipelineRetrievalHelper,
    retrieve_sql_candidates,
)
from services.question_intelligence.question_retrieval_service import (
    QuestionRetrievalService,
)

from services.question_intelligence.retrieval_query_builder import (
    RetrievalQueryBuilder,
)

from services.question_intelligence.retrieval.retrieval_strategy_resolver import (
    RetrievalStrategyResolver,
)

from services.question_corpus.contracts.interview_retrieval_memory import (
    InterviewRetrievalMemory,
)
from services.question_intelligence.interview_theme_guidance import (
    build_theme_guidance,
)
from services.question_intelligence.interview_theme_memory import (
    get_interview_theme_anchor,
)
from services.question_corpus.retrieval.interview_memory_updater import (
    InterviewMemoryUpdater,
)

from infrastructure.config.settings import settings
from app.core.logger import get_logger

logger = get_logger(__name__)

_ACTIONABLE_SQL_PATTERN = re.compile(
    r"\b(write|query|select|join|aggregate|count|group\s+by|where|"
    r"retrieve|fetch|find|list|filter|having|sum|avg|min|max|"
    r"index|indexing|optimiz|optimization|normaliz|normalization|"
    r"transaction|commit|rollback|isolation)\b",
    re.IGNORECASE,
)

_SQL_CANDIDATE_SCAN_K = 10
_SQL_GENERATE_MAX_ATTEMPTS = settings.sql_pipeline_retry_attempts


class SQLQuestionPipeline:

    def __init__(
        self,
        retrieval_service: QuestionRetrievalService,
        sql_generator: SQLQuestionGenerator,
        sql_retrieval_helper: SqlPipelineRetrievalHelper | None = None,
    ) -> None:

        self._retrieval_service = retrieval_service
        self._sql_generator = sql_generator
        self._sql_retrieval_helper = sql_retrieval_helper
        self._retrieval_query_builder = RetrievalQueryBuilder()
        self._retrieval_strategy_resolver = RetrievalStrategyResolver()
        self._memory_updater = InterviewMemoryUpdater()

    # =====================================================
    # PUBLIC
    # =====================================================

    def build(
        self,
        role: RoleType,
        level: SeniorityLevel,
        interview_type: InterviewType,
        area: InterviewArea,
        questions_per_area: int,
        corpus_quota: int | None = None,
        memory: InterviewRetrievalMemory | None = None,
    ) -> tuple[List[Question], InterviewRetrievalMemory]:
        """
        corpus_quota caps how many questions are drawn from the retrieval corpus.
        Remaining slots are filled by LLM generation. When None the pipeline
        fills as many corpus questions as available (legacy behaviour).
        """

        session_memory = (
            memory if memory is not None else InterviewRetrievalMemory()
        )

        questions: List[Question] = []
        enriched_pairs: list[tuple[QuestionBankItem, Question]] = []

        theme_anchor = get_interview_theme_anchor(session_memory)
        theme_guidance = build_theme_guidance(
            theme_anchor=theme_anchor,
            area=area,
        )

        retrieval_query = self._retrieval_query_builder.build(
            role=role,
            level=level,
            area=area,
            theme_anchor=theme_anchor,
            memory=session_memory,
        )

        # When corpus_quota is set, limit how many corpus candidates we scan.
        # We still scan at least _SQL_CANDIDATE_SCAN_K so non-actionable
        # prompts can be filtered without exhausting the quota prematurely.
        effective_corpus_target = (
            min(corpus_quota, questions_per_area)
            if corpus_quota is not None
            else questions_per_area
        )
        candidate_scan_k = max(
            effective_corpus_target,
            _SQL_CANDIDATE_SCAN_K,
        )

        retrieval_strategy = self._retrieval_strategy_resolver.resolve(
            area=area,
            level=level,
            questions_per_area=candidate_scan_k,
        )

        retrieved = retrieve_sql_candidates(
            retrieval_service=self._retrieval_service,
            query=retrieval_query,
            retrieval_strategy=retrieval_strategy,
            role=role.value,
            level=level.value,
            interview_type=interview_type.value,
            area=area.value,
            memory=session_memory,
            sql_retrieval_helper=self._sql_retrieval_helper,
        )

        for item in retrieved:

            if len(questions) >= questions_per_area:
                break

            if corpus_quota is not None and len(questions) >= corpus_quota:
                break

            if not self._is_actionable_sql_prompt(item.text):
                logger.debug(
                    f"[SQL] Skipping non-actionable retrieved prompt: {item.id}",
                )
                continue

            provenance = self._build_enrichment_provenance(item)

            enriched = self._sql_generator.enrich_from_prompt(
                seed_prompt=item.text,
                role=role,
                level=level,
                provenance=provenance,
                theme_guidance=theme_guidance,
            )

            if enriched is None:
                logger.debug(
                    f"[SQL] Enrichment failed for actionable prompt: {item.id}",
                )
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
                ),
            )

        if not questions:
            questions.extend(
                self._generate_with_retry(
                    role=role,
                    level=level,
                    n=max(1, questions_per_area),
                    theme_guidance=theme_guidance,
                ),
            )

        if len(questions) < questions_per_area:
            logger.warning(
                f"[SQL] Area {area.value} produced "
                f"{len(questions)} questions "
                f"(expected {questions_per_area})"
            )

        final_questions = questions[:questions_per_area]

        if not final_questions:
            final_questions = self._generate_with_retry(
                role=role,
                level=level,
                n=max(1, questions_per_area),
                theme_guidance=theme_guidance,
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

    # =====================================================
    # INTERNALS
    # =====================================================

    def _generate_with_retry(
        self,
        role: RoleType,
        level: SeniorityLevel,
        n: int,
        theme_guidance: str | None = None,
    ) -> List[Question]:

        last_result: List[Question] = []

        for attempt in range(1, _SQL_GENERATE_MAX_ATTEMPTS + 1):

            try:
                last_result = self._sql_generator.generate(
                    role=role,
                    level=level,
                    n=n,
                    theme_guidance=theme_guidance,
                )
            except ValueError as exc:
                logger.warning(
                    f"[SQL generate] Attempt {attempt}/{_SQL_GENERATE_MAX_ATTEMPTS} "
                    f"failed: {exc}",
                )
                last_result = []

            if last_result:
                return last_result

        return last_result

    def _is_actionable_sql_prompt(self, text: str) -> bool:

        return bool(_ACTIONABLE_SQL_PATTERN.search(text))

    def _build_enrichment_provenance(
        self,
        item: QuestionBankItem,
    ) -> QuestionProvenance:

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
            generated_by_model="sql_question_enrichment",
        )
