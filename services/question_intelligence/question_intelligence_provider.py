# services/question_intelligence/question_intelligence_provider.py

from typing import List

from domain.contracts.interview.interview_type import InterviewType
from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.question.question import Question

from services.question_intelligence.question_intelligence_service import (
    QuestionIntelligenceService,
)
from services.question_intelligence.question_set_builder import QuestionSetBuilder
from services.question_intelligence.question_selection_service import (
    QuestionSelectionService,
)
from services.question_intelligence.question_retrieval_service import (
    QuestionRetrievalService,
)
from services.question_intelligence.question_generator import QuestionGenerator
from services.question_intelligence.coding_question_generator import (
    CodingQuestionGenerator,
)
from services.question_intelligence.sql_question_generator import (
    SQLQuestionGenerator,
)
from services.question_intelligence.question_vector_store import (
    QuestionVectorStore,
)

from services.question_intelligence.area_question_builder import (
    AreaQuestionBuilder,
)

from infrastructure.vector_store.chroma_question_store import (
    ChromaQuestionStore,
)

from services.question_intelligence.semantic_deduplicator import SemanticDeduplicator

from app.settings.constants import QUESTIONS_PER_AREA, DEDUPLICATION_THRESHOLD
from app.ports.llm_port import LLMPort


class QuestionIntelligenceProvider:

    def __init__(self, llm: LLMPort) -> None:

        # -----------------------------------------------------
        # Infrastructure
        # -----------------------------------------------------

        chroma_store = ChromaQuestionStore()
        vector_store = QuestionVectorStore(chroma_store)

        retrieval_service = QuestionRetrievalService(vector_store)

        # -----------------------------------------------------
        # Services (NO global LLM usage)
        # -----------------------------------------------------

        # LLM injected everywhere needed
        generator = QuestionGenerator(llm)
        coding_generator = CodingQuestionGenerator(llm)
        sql_generator = SQLQuestionGenerator(llm)

        area_builder = AreaQuestionBuilder(
            retrieval_service=retrieval_service,
            generator=generator,
            coding_generator=coding_generator,
            sql_generator=sql_generator,
        )

        deduplicator = SemanticDeduplicator(threshold=DEDUPLICATION_THRESHOLD)


        question_set_builder = QuestionSetBuilder(
            area_builder=area_builder,
            deduplicator=deduplicator,
        )

        self._service = QuestionIntelligenceService(question_set_builder=question_set_builder)

    # =========================================================
    # PUBLIC API
    # =========================================================

    def generate(
        self,
        role: str,
        level: str,
        interview_type: InterviewType,
        areas: List[InterviewArea],
        questions_per_area: int = QUESTIONS_PER_AREA,
    ) -> List[Question]:

        return self._service.generate_interview_questions(
            role=role,
            level=level,
            interview_type=interview_type,
            areas=areas,
            questions_per_area=questions_per_area,
        )
