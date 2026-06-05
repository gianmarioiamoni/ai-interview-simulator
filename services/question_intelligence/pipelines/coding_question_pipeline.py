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

from services.question_intelligence.retrieval_query_builder import (
    RetrievalQueryBuilder,
)

from services.question_intelligence.retrieval.retrieval_strategy_resolver import (
    RetrievalStrategyResolver,
)

from services.question_corpus.contracts.interview_retrieval_memory import (
    InterviewRetrievalMemory,
)
from services.question_corpus.retrieval.interview_memory_updater import (
    InterviewMemoryUpdater,
)

from app.core.logger import get_logger

logger = get_logger(__name__)

_ACTIONABLE_CODING_PATTERN = re.compile(
    r"\b(solve|implement|write\s+(a\s+)?function|algorithm|leetcode)\b",
    re.IGNORECASE,
)

_CODING_CANDIDATE_SCAN_K = 10
_CODING_GENERATE_MAX_ATTEMPTS = 2


class CodingQuestionPipeline:

    def __init__(
        self,
        retrieval_service: QuestionRetrievalService,
        coding_generator: CodingQuestionGenerator,
        coding_retrieval_helper: CodingPipelineRetrievalHelper | None = None,
    ) -> None:

        self._retrieval_service = retrieval_service
        self._coding_generator = coding_generator
        self._coding_retrieval_helper = coding_retrieval_helper
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
        memory: InterviewRetrievalMemory | None = None,
    ) -> tuple[List[Question], InterviewRetrievalMemory]:

        session_memory = (
            memory if memory is not None else InterviewRetrievalMemory()
        )

        questions: List[Question] = []
        enriched_pairs: list[tuple[QuestionBankItem, Question]] = []

        retrieval_query = self._retrieval_query_builder.build(
            role=role,
            level=level,
            area=area,
        )

        candidate_scan_k = max(
            questions_per_area,
            _CODING_CANDIDATE_SCAN_K,
        )

        retrieval_strategy = self._retrieval_strategy_resolver.resolve(
            area=area,
            level=level,
            questions_per_area=candidate_scan_k,
        )

        retrieved = retrieve_coding_candidates(
            retrieval_service=self._retrieval_service,
            query=retrieval_query,
            retrieval_strategy=retrieval_strategy,
            role=role.value,
            level=level.value,
            interview_type=interview_type.value,
            area=area.value,
            memory=session_memory,
            coding_retrieval_helper=self._coding_retrieval_helper,
        )

        for item in retrieved:

            if len(questions) >= questions_per_area:
                break

            if not self._is_actionable_coding_prompt(item.text):
                logger.debug(
                    f"[CODING] Skipping non-actionable retrieved prompt: {item.id}",
                )
                continue

            provenance = self._build_enrichment_provenance(item)

            enriched = self._coding_generator.enrich_from_prompt(
                seed_prompt=item.text,
                role=role,
                level=level,
                provenance=provenance,
            )

            if enriched is None:
                logger.debug(
                    f"[CODING] Enrichment failed for actionable prompt: {item.id}",
                )
                continue

            try:
                mapped = self._map_item(
                    item=enriched,
                    area=area,
                    provenance=provenance,
                )
            except ValueError as exc:
                logger.warning(f"[CODING enrich] Alignment failed: {exc}")
                continue

            enriched_pairs.append((item, mapped))
            questions.append(mapped)

        remaining_slots = questions_per_area - len(questions)

        if remaining_slots > 0:
            questions.extend(
                self._generate_with_retry(
                    role=role,
                    level=level,
                    n=remaining_slots,
                ),
            )

        if not questions:
            questions.extend(
                self._generate_with_retry(
                    role=role,
                    level=level,
                    n=max(1, questions_per_area),
                ),
            )

        if len(questions) < questions_per_area:
            logger.warning(
                f"[CODING] Area {area.value} produced "
                f"{len(questions)} questions "
                f"(expected {questions_per_area})",
            )

        final_questions = questions[:questions_per_area]

        if not final_questions:
            final_questions = self._generate_with_retry(
                role=role,
                level=level,
                n=max(1, questions_per_area),
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
    # MAPPING
    # =====================================================

    def _generate_with_retry(
        self,
        role: RoleType,
        level: SeniorityLevel,
        n: int,
    ) -> List[Question]:

        area = InterviewArea.TECH_CODING
        last_result: List[Question] = []

        for attempt in range(1, _CODING_GENERATE_MAX_ATTEMPTS + 1):

            raw_items = self._coding_generator.generate(
                role=role,
                level=level,
                n=n,
            )

            mapped: List[Question] = []

            for raw_item in raw_items:
                try:
                    mapped.append(
                        self._map_item(
                            item=raw_item,
                            area=area,
                        ),
                    )
                except ValueError as exc:
                    logger.warning(
                        f"[CODING generate] Alignment failed "
                        f"(attempt {attempt}/{_CODING_GENERATE_MAX_ATTEMPTS}): {exc}",
                    )

            last_result = mapped

            if last_result:
                return last_result

        return last_result

    def _map_item(
        self,
        item: GeneratedCodingQuestion,
        area: InterviewArea,
        provenance: QuestionProvenance | None = None,
    ) -> Question:

        coding_spec = item.coding_spec

        self._validate_alignment(
            item,
            coding_spec,
        )

        return Question(
            id=str(uuid.uuid4()),
            area=area,
            type=QuestionType.CODING,
            prompt=item.prompt,
            function_name=coding_spec.entrypoint,
            coding_spec=coding_spec,
            provenance=provenance,
            visible_tests=[
                CodingTestCase(**t.model_dump()) for t in item.visible_tests
            ],
        )

    # =====================================================
    # VALIDATION
    # =====================================================

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

    # =====================================================
    # INTERNALS
    # =====================================================

    def _is_actionable_coding_prompt(self, text: str) -> bool:

        return bool(_ACTIONABLE_CODING_PATTERN.search(text))

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
            generated_by_model="coding_question_enrichment",
        )
