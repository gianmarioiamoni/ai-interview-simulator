# services/question_intelligence/pipelines/sql_question_pipeline.py

import re
import random
from typing import Callable, List

from domain.contracts.question.question import (
    Question,
)
from domain.contracts.question.question_bank_item import (
    QuestionBankItem,
)
from domain.contracts.question.question_provenance import (
    QuestionProvenance,
)
from domain.contracts.question.scenario_anchor import ScenarioAnchor

from domain.contracts.interview.interview_area import (
    InterviewArea,
)
from domain.contracts.interview.interview_type import (
    InterviewType,
)
from domain.contracts.interview.business_context import BusinessContext

from domain.contracts.user.role import RoleType

from domain.contracts.user.seniority_level import (
    SeniorityLevel,
)

from services.question_intelligence.mappers.difficulty_mapper import map_corpus_difficulty
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

from services.question_corpus.contracts.interview_retrieval_memory import (
    InterviewRetrievalMemory,
)

from services.question_intelligence.pipelines.base_llm_question_pipeline import (
    BaseLLMQuestionPipeline,
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

_BUSINESS_CONTEXT_METADATA_ONLY = frozenset({
    BusinessContext.FINTECH,
    BusinessContext.ECOMMERCE,
    BusinessContext.SAAS,
    BusinessContext.HEALTHCARE,
})

_SCENARIO_ANCHOR_POOL: list[ScenarioAnchor] = list(ScenarioAnchor)

SQLGeneratorFactory = Callable[[BusinessContext], SQLQuestionGenerator]


def _pick_scenario_anchor() -> ScenarioAnchor:
    return random.choice(_SCENARIO_ANCHOR_POOL)


class SQLQuestionPipeline(BaseLLMQuestionPipeline):

    def __init__(
        self,
        retrieval_service: QuestionRetrievalService,
        sql_generator: SQLQuestionGenerator,
        sql_retrieval_helper: SqlPipelineRetrievalHelper | None = None,
        generator_factory: SQLGeneratorFactory | None = None,
    ) -> None:

        super().__init__()
        self._retrieval_service = retrieval_service
        self._sql_generator = sql_generator
        self._sql_retrieval_helper = sql_retrieval_helper
        # Factory resolves the correct schema-scoped generator per BusinessContext.
        # When None, falls back to the default sql_generator for all contexts.
        self._generator_factory = generator_factory

    # ------------------------------------------------------------------
    # BaseLLMQuestionPipeline implementation
    # ------------------------------------------------------------------

    def _pipeline_label(self) -> str:
        return "SQL"

    def _candidate_scan_k(self) -> int:
        return _SQL_CANDIDATE_SCAN_K

    def _build_provenance_model_tag(self) -> str:
        return "sql_question_enrichment"

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

        return retrieve_sql_candidates(
            retrieval_service=self._retrieval_service,
            query=retrieval_query,
            retrieval_strategy=retrieval_strategy,
            role=role.value,
            level=level.value,
            interview_type=interview_type.value,
            area=area.value,
            memory=memory,
            sql_retrieval_helper=self._sql_retrieval_helper,
        )

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
        business_context: BusinessContext | None = None,
    ) -> Question | None:

        if business_context in _BUSINESS_CONTEXT_METADATA_ONLY:
            return self._generate_from_item_metadata(
                item=item,
                role=role,
                level=level,
                theme_guidance=theme_guidance,
                job_description=job_description,
                company_description=company_description,
                business_context=business_context,
            )

        if not self._is_actionable_sql_prompt(item.text):
            logger.debug("[SQL] Skipping non-actionable retrieved prompt: %s", item.id)
            return None

        difficulty_label = map_corpus_difficulty(item.difficulty).value

        enriched = self._sql_generator.enrich_from_prompt(
            seed_prompt=item.text,
            role=role,
            level=level,
            provenance=provenance,
            theme_guidance=theme_guidance,
            source_difficulty=item.difficulty,
            domains=[d.value for d in item.domains],
            expected_topics=list(item.expected_topics),
            difficulty_label=difficulty_label,
            job_description=job_description,
            company_description=company_description,
        )

        if enriched is None:
            logger.debug("[SQL] Enrichment failed for actionable prompt: %s", item.id)
            return None

        return enriched

    def _generate_with_retry(
        self,
        role: RoleType,
        level: SeniorityLevel,
        n: int,
        theme_guidance: str | None = None,
        job_description: str | None = None,
        company_description: str | None = None,
        business_context: BusinessContext | None = None,
    ) -> List[Question]:

        generator = self._resolve_generator(business_context)
        last_result: List[Question] = []

        for attempt in range(1, _SQL_GENERATE_MAX_ATTEMPTS + 1):

            try:
                last_result = generator.generate(
                    role=role,
                    level=level,
                    n=n,
                    theme_guidance=theme_guidance,
                    job_description=job_description,
                    company_description=company_description,
                )
            except ValueError as exc:
                logger.warning(
                    "[SQL generate] Attempt %d/%d failed: %s",
                    attempt,
                    _SQL_GENERATE_MAX_ATTEMPTS,
                    exc,
                )
                last_result = []

            if last_result:
                return last_result

        return last_result

    # ------------------------------------------------------------------
    # PRIVATE HELPERS
    # ------------------------------------------------------------------

    def _resolve_generator(self, business_context: BusinessContext | None) -> SQLQuestionGenerator:
        if self._generator_factory is not None and business_context is not None:
            return self._generator_factory(business_context)
        return self._sql_generator

    def _is_actionable_sql_prompt(self, text: str) -> bool:
        return bool(_ACTIONABLE_SQL_PATTERN.search(text))

    def _generate_from_item_metadata(
        self,
        item: QuestionBankItem,
        role: RoleType,
        level: SeniorityLevel,
        theme_guidance: str | None,
        job_description: str | None,
        company_description: str | None,
        business_context: BusinessContext | None = None,
    ) -> Question | None:
        difficulty_label = map_corpus_difficulty(item.difficulty).value
        domains = [d.value for d in item.domains] if item.domains else None
        scenario_anchor = _pick_scenario_anchor()
        generator = self._resolve_generator(business_context)

        try:
            results = generator.generate(
                role=role,
                level=level,
                n=1,
                theme_guidance=theme_guidance,
                domains=domains,
                difficulty_label=difficulty_label,
                scenario_anchor=scenario_anchor,
                job_description=job_description,
                company_description=company_description,
            )
        except ValueError as exc:
            logger.warning("[SQL metadata-gen] Generation failed: %s", exc)
            return None

        return results[0] if results else None
