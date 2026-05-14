# services/question_intelligence/pipelines/coding_question_pipeline.py

import uuid

from typing import List

from domain.contracts.question.question import (
    Question,
    QuestionType,
)

from domain.contracts.execution.coding_test_case import (
    CodingTestCase,
)

from domain.contracts.execution.coding_spec import (
    CodingSpec,
)

from domain.contracts.interview.interview_area import (
    InterviewArea,
)

from domain.contracts.user.role import RoleType

from domain.contracts.user.seniority_level import (
    SeniorityLevel,
)

from services.question_intelligence.coding_question_generator import (
    CodingQuestionGenerator,
    GeneratedCodingQuestion,
)

from app.core.logger import get_logger

logger = get_logger(__name__)


class CodingQuestionPipeline:

    def __init__(
        self,
        coding_generator: CodingQuestionGenerator,
    ) -> None:

        self._coding_generator = coding_generator

    # =====================================================
    # PUBLIC
    # =====================================================

    def build(
        self,
        role: RoleType,
        level: SeniorityLevel,
        area: InterviewArea,
        questions_per_area: int,
    ) -> List[Question]:

        raw_items = self._coding_generator.generate(
            role=role,
            level=level,
            n=questions_per_area,
        )

        questions: List[Question] = []

        for item in raw_items:

            coding_spec = item.coding_spec

            self._validate_alignment(
                item,
                coding_spec,
            )

            question = Question(
                id=str(uuid.uuid4()),
                area=area,
                type=QuestionType.CODING,
                prompt=item.prompt,
                coding_spec=coding_spec,
                visible_tests=[
                    CodingTestCase(**t.model_dump()) for t in item.visible_tests
                ],
            )

            questions.append(question)

        if len(questions) < questions_per_area:

            logger.warning(
                f"[CODING] Area {area.value} produced "
                f"{len(questions)} questions "
                f"(expected {questions_per_area})"
            )

        return questions

    # =====================================================
    # VALIDATION
    # =====================================================

    def _validate_alignment(
        self,
        item: GeneratedCodingQuestion,
        spec: CodingSpec,
    ) -> None:

        prompt = item.prompt

        if spec.entrypoint not in prompt:
            raise ValueError(f"Entrypoint '{spec.entrypoint}' not found in prompt")

        for p in spec.parameters:

            if p not in prompt:
                raise ValueError(f"Parameter '{p}' not found in prompt")
