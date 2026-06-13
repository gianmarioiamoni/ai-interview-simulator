# services/question_intelligence/pipelines/sql_question_pipeline.py

import re
from typing import List

from domain.contracts.question.question import (
    Question,
)
from domain.contracts.question.question_bank_item import (
    QuestionBankItem,
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


class SQLQuestionPipeline(BaseLLMQuestionPipeline):

    def __init__(
        self,
        retrieval_service: QuestionRetrievalService,
        sql_generator: SQLQuestionGenerator,
        sql_retrieval_helper: SqlPipelineRetrievalHelper | None = None,
    ) -> None:

        super().__init__()
        self._retrieval_service = retrieval_service
        self._sql_generator = sql_generator
        self._sql_retrieval_helper = sql_retrieval_helper

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
    ) -> Question | None:

        if not self._is_actionable_sql_prompt(item.text):
            logger.debug("[SQL] Skipping non-actionable retrieved prompt: %s", item.id)
            return None

        enriched = self._sql_generator.enrich_from_prompt(
            seed_prompt=item.text,
            role=role,
            level=level,
            provenance=provenance,
            theme_guidance=theme_guidance,
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

    def _is_actionable_sql_prompt(self, text: str) -> bool:

        return bool(_ACTIONABLE_SQL_PATTERN.search(text))
