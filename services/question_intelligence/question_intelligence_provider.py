# services/question_intelligence/question_intelligence_provider.py

# QuestionIntelligenceProvider
#
# Responsibility:
# Provides a fully wired QuestionIntelligenceService.
# Encapsulates dependency construction.
#
# This avoids leaking infrastructure wiring into UI/application layer.

from typing import List

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
from services.question_intelligence.question_vector_store import (
    QuestionVectorStore,
)


class QuestionIntelligenceProvider:
    def __init__(self) -> None:

        # -----------------------------------------------------
        # Infrastructure
        # -----------------------------------------------------

        vector_store = QuestionVectorStore()

        # -----------------------------------------------------
        # Services
        # -----------------------------------------------------

        retrieval_service = QuestionRetrievalService(vector_store)
        generator = QuestionGenerator()
        coding_generator = CodingQuestionGenerator()

        selection_service = QuestionSelectionService(
            retrieval_service=retrieval_service,
            generator=generator,
            coding_generator=coding_generator,
        )

        set_builder = QuestionSetBuilder(selection_service)

        self._service = QuestionIntelligenceService(set_builder)

    # =========================================================
    # PUBLIC API
    # =========================================================

    def generate(
        self,
        role: str,
        level: str,
        interview_type: str,
        areas: List[str],
    ) -> List[Question]:

        return self._service.generate_interview_questions(
            role=role,
            level=level,
            interview_type=interview_type,
            areas=areas,
        )
