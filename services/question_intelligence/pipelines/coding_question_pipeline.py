# services/question_intelligence/pipelines/coding_question_pipeline.py

import re
import uuid

from typing import List

from domain.contracts.question.question import (
    Question,
    QuestionType,
)

from domain.contracts.execution.coding_test_case import (
    CodingTestCase,
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

from services.question_intelligence.coding_question_generator import (
    CodingQuestionGenerator,
    GeneratedCodingQuestion,
)

from services.question_intelligence.pipelines.coding_pipeline_retrieval import (
    CodingPipelineRetrievalHelper,
    retrieve_coding_candidates,
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

from services.question_intelligence.mappers.difficulty_mapper import map_corpus_difficulty

from infrastructure.config.settings import settings
from app.core.logger import get_logger

logger = get_logger(__name__)

_ACTIONABLE_CODING_PATTERN = re.compile(
    r"\b(solve|implement|write\s+(a\s+)?function|algorithm|leetcode)\b",
    re.IGNORECASE,
)

_CODING_CANDIDATE_SCAN_K = 10
_CODING_GENERATE_MAX_ATTEMPTS = settings.coding_pipeline_retry_attempts


class CodingQuestionPipeline(BaseLLMQuestionPipeline):

    def __init__(
        self,
        retrieval_service: QuestionRetrievalService,
        coding_generator: CodingQuestionGenerator,
        coding_retrieval_helper: CodingPipelineRetrievalHelper | None = None,
    ) -> None:

        super().__init__()
        self._retrieval_service = retrieval_service
        self._coding_generator = coding_generator
        self._coding_retrieval_helper = coding_retrieval_helper

    # ------------------------------------------------------------------
    # BaseLLMQuestionPipeline implementation
    # ------------------------------------------------------------------

    def _pipeline_label(self) -> str:
        return "CODING"

    def _candidate_scan_k(self) -> int:
        return _CODING_CANDIDATE_SCAN_K

    def _build_provenance_model_tag(self) -> str:
        return "coding_question_enrichment"

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

        return retrieve_coding_candidates(
            retrieval_service=self._retrieval_service,
            query=retrieval_query,
            retrieval_strategy=retrieval_strategy,
            role=role.value,
            level=level.value,
            interview_type=interview_type.value,
            area=area.value,
            memory=memory,
            coding_retrieval_helper=self._coding_retrieval_helper,
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
    ) -> Question | None:

        if not self._is_actionable_coding_prompt(item.text):
            logger.debug("[CODING] Skipping non-actionable retrieved prompt: %s", item.id)
            return None

        theme_guidance_text = theme_guidance

        enriched = self._coding_generator.enrich_from_prompt(
            seed_prompt=item.text,
            role=role,
            level=level,
            provenance=provenance,
            theme_guidance=theme_guidance_text,
            job_description=job_description,
            company_description=company_description,
        )

        if enriched is None:
            logger.debug("[CODING] Enrichment failed for actionable prompt: %s", item.id)
            return None

        try:
            return self._map_item(
                item=enriched,
                area=area,
                provenance=provenance,
                source_difficulty=item.difficulty,
            )
        except ValueError as exc:
            logger.warning("[CODING enrich] Alignment failed: %s", exc)
            return None

    def _generate_with_retry(
        self,
        role: RoleType,
        level: SeniorityLevel,
        n: int,
        theme_guidance: str | None = None,
        job_description: str | None = None,
        company_description: str | None = None,
    ) -> List[Question]:

        area = InterviewArea.TECH_CODING
        last_result: List[Question] = []

        for attempt in range(1, _CODING_GENERATE_MAX_ATTEMPTS + 1):

            raw_items = self._coding_generator.generate(
                role=role,
                level=level,
                n=n,
                theme_guidance=theme_guidance,
                job_description=job_description,
                company_description=company_description,
            )

            mapped: List[Question] = []

            for raw_item in raw_items:
                try:
                    mapped.append(self._map_item(item=raw_item, area=area))
                except ValueError as exc:
                    logger.warning(
                        "[CODING generate] Alignment failed "
                        "(attempt %d/%d): %s",
                        attempt,
                        _CODING_GENERATE_MAX_ATTEMPTS,
                        exc,
                    )

            last_result = mapped

            if last_result:
                return last_result

        return last_result

    # ------------------------------------------------------------------
    # PRIVATE HELPERS
    # ------------------------------------------------------------------

    def _map_item(
        self,
        item: GeneratedCodingQuestion,
        area: InterviewArea,
        provenance: QuestionProvenance | None = None,
        source_difficulty: int | None = None,
    ) -> Question:

        coding_spec = item.coding_spec

        self._validate_alignment(item, coding_spec)

        return Question(
            id=str(uuid.uuid4()),
            area=area,
            type=QuestionType.CODING,
            prompt=item.prompt,
            function_name=coding_spec.entrypoint,
            coding_spec=coding_spec,
            difficulty=map_corpus_difficulty(source_difficulty),
            provenance=provenance,
            visible_tests=[
                CodingTestCase(**t.model_dump()) for t in item.visible_tests
            ],
        )

    def _validate_alignment(
        self,
        item: GeneratedCodingQuestion,
        spec,
    ) -> None:

        prompt = item.prompt

        if spec.entrypoint not in prompt:
            raise ValueError(f"Entrypoint '{spec.entrypoint}' not found in prompt")

        for p in spec.parameters:
            if p not in prompt:
                raise ValueError(f"Parameter '{p}' not found in prompt")

    def _is_actionable_coding_prompt(self, text: str) -> bool:

        return bool(_ACTIONABLE_CODING_PATTERN.search(text))
