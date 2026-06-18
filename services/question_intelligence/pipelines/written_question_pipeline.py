# services/question_intelligence/pipelines/written_question_pipeline.py

from typing import List

from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.interview.interview_type import InterviewType
from domain.contracts.user.role import RoleType
from domain.contracts.user.seniority_level import SeniorityLevel
from domain.contracts.question.question import Question

from services.question_corpus.contracts.interview_retrieval_memory import (
    InterviewRetrievalMemory,
)
from services.question_intelligence.question_retrieval_service import (
    QuestionRetrievalService,
)
from services.question_intelligence.question_generator import QuestionGenerator
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
from services.question_intelligence.pipelines.written_difficulty_balancer import (
    WrittenDifficultyBalancer,
)
from services.question_intelligence.pipelines.written_question_mapper import (
    WrittenQuestionMapper,
)

from app.core.logger import get_logger
from app.settings.constants import QUESTIONS_PER_AREA

logger = get_logger(__name__)


class WrittenQuestionPipeline:

    def __init__(
        self,
        retrieval_service: QuestionRetrievalService,
        generator: QuestionGenerator,
    ) -> None:
        self._retrieval_service = retrieval_service
        self._generator = generator
        self._retrieval_query_builder = RetrievalQueryBuilder()
        self._retrieval_strategy_resolver = RetrievalStrategyResolver()
        self._memory_updater = InterviewMemoryUpdater()
        self._mapper = WrittenQuestionMapper()
        self._balancer = WrittenDifficultyBalancer()

    # =====================================================
    # PUBLIC
    # =====================================================

    def build(
        self,
        role: RoleType,
        level: SeniorityLevel,
        interview_type: InterviewType,
        area: InterviewArea,
        questions_per_area: int = QUESTIONS_PER_AREA,
        corpus_quota: int | None = None,
        memory: InterviewRetrievalMemory | None = None,
        job_description: str | None = None,
        company_description: str | None = None,
    ) -> tuple[List[Question], InterviewRetrievalMemory]:
        """
        Build questions for a single area.

        corpus_quota caps how many questions are drawn from the retrieval corpus.
        Remaining slots (questions_per_area - corpus_quota) are always filled by
        LLM generation. When None the pipeline fills as many corpus questions as
        available before falling back to generation (legacy behaviour).
        """

        session_memory = (
            memory if memory is not None else InterviewRetrievalMemory()
        )

        questions: List[Question] = []
        retrieved_pairs = []

        # -------------------------------------------------
        # QUERY
        # -------------------------------------------------

        theme_anchor = get_interview_theme_anchor(session_memory)

        retrieval_query = self._retrieval_query_builder.build(
            role=role,
            level=level,
            area=area,
            theme_anchor=theme_anchor,
        )

        # -------------------------------------------------
        # STRATEGY
        # -------------------------------------------------

        effective_corpus_target = (
            min(corpus_quota, questions_per_area)
            if corpus_quota is not None
            else questions_per_area
        )

        retrieval_strategy = self._retrieval_strategy_resolver.resolve(
            area=area,
            level=level,
            questions_per_area=effective_corpus_target,
        )

        # -------------------------------------------------
        # RETRIEVAL
        # -------------------------------------------------

        retrieved = self._retrieval_service.retrieve(
            query=retrieval_query,
            retrieval_strategy=retrieval_strategy,
            role=role.value,
            level=level.value,
            interview_type=interview_type.value,
            area=area.value,
            memory=session_memory,
        )

        for item in retrieved:
            if corpus_quota is not None and len(questions) >= corpus_quota:
                break

            mapped = self._mapper.from_bank_item(item)
            retrieved_pairs.append((item, mapped))
            questions.append(mapped)

        # -------------------------------------------------
        # GENERATION
        # -------------------------------------------------

        remaining_slots = questions_per_area - len(questions)

        if remaining_slots > 0:
            generated = self._generator.generate(
                role=role,
                level=level,
                interview_type=interview_type,
                area=area,
                n=remaining_slots,
                theme_guidance=build_theme_guidance(
                    theme_anchor=theme_anchor,
                    area=area,
                ),
                job_description=job_description,
                company_description=company_description,
            )

            for gen in generated:
                questions.append(self._mapper.from_generated(gen, area))

        # -------------------------------------------------
        # BALANCING
        # -------------------------------------------------

        selected = self._balancer.select(
            questions=questions,
            total=questions_per_area,
        )

        selected_prompts = {q.prompt for q in selected}

        for bank_item, mapped_question in retrieved_pairs:
            if mapped_question.prompt not in selected_prompts:
                continue
            session_memory = self._memory_updater.record_bank_item_selection(
                memory=session_memory,
                item=bank_item,
            )

        return selected, session_memory
