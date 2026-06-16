# services/question_intelligence/sql_question_generator.py

import uuid
from typing import List

from pydantic import BaseModel, Field

from domain.contracts.question.question import (
    Question,
    QuestionType,
    QuestionDifficulty,
    SQLTestCase,
)
from domain.contracts.question.question_provenance import QuestionProvenance
from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.user.role import RoleType
from domain.contracts.user.seniority_level import SeniorityLevel

from app.ports.llm_port import LLMPort
from infrastructure.llm.metrics.llm_operation_context import LLMOperationContext
from infrastructure.llm.metrics.llm_operation_names import QUESTION_GENERATION

from services.sql_engine.sql_database import SQLDatabase
from services.question_intelligence.mappers.difficulty_mapper import map_corpus_difficulty

from app.core.logger import get_logger

logger = get_logger(__name__)


# =========================================================
# DTOs
# =========================================================


class GeneratedSQLTestCase(BaseModel):
    expected_query: str
    ordered: bool | None = None


class GeneratedSQLQuestion(BaseModel):
    prompt: str
    reference_query: str
    test_cases: List[GeneratedSQLTestCase] = Field(default_factory=list)


# =========================================================
# Generator
# =========================================================


class SQLQuestionGenerator:
    """
    Coordinates SQL question generation and enrichment.

    Delegates prompt construction to SQLPromptBuilder and
    parsing/validation to SQLResponseParser. Keeps only the
    LLM invocation and domain-mapping responsibilities.
    """

    def __init__(self, llm: LLMPort) -> None:
        self._llm = llm
        self._db = SQLDatabase()

        # Lazy import to avoid circular dependency at module level
        from services.question_intelligence.sql_prompt_builder import SQLPromptBuilder
        from services.question_intelligence.sql_response_parser import SQLResponseParser

        self._prompt_builder = SQLPromptBuilder()
        self._response_parser = SQLResponseParser(self._db)

    # -----------------------------------------------------

    def generate(
        self,
        role: RoleType,
        level: SeniorityLevel,
        n: int = 1,
        theme_guidance: str | None = None,
    ) -> List[Question]:

        prompt = self._prompt_builder.build_generation_prompt(
            role=role.value,
            level=level.value,
            n=n,
            theme_guidance=theme_guidance,
        )

        with LLMOperationContext.scope(QUESTION_GENERATION):
            response = self._llm.invoke(prompt)

        try:
            validated_items = self._response_parser.parse(response.content)
        except ValueError as e:
            raise ValueError(str(e)) from e

        executable_items = self._response_parser.filter_executable(validated_items)

        return [self._map_to_question(item) for item in executable_items]

    # -----------------------------------------------------

    def enrich_from_prompt(
        self,
        seed_prompt: str,
        role: RoleType,
        level: SeniorityLevel,
        provenance: QuestionProvenance | None = None,
        theme_guidance: str | None = None,
        source_difficulty: int | None = None,
    ) -> Question | None:

        prompt = self._prompt_builder.build_enrichment_prompt(
            seed_prompt=seed_prompt,
            role=role.value,
            level=level.value,
            theme_guidance=theme_guidance,
        )

        try:
            with LLMOperationContext.scope(QUESTION_GENERATION):
                response = self._llm.invoke(prompt)
            validated_items = self._response_parser.parse(response.content)
            executable_items = self._response_parser.filter_executable(validated_items)
        except ValueError as e:
            logger.warning("[SQL enrich] Failed enrichment: %s", e)
            return None
        except Exception as e:
            logger.warning("[SQL enrich] Unexpected error during enrichment: %s", e)
            return None

        if not executable_items:
            logger.warning("[SQL enrich] No executable SQL after enrichment validation")
            return None

        return self._map_to_question(
            executable_items[0],
            provenance=provenance,
            source_difficulty=source_difficulty,
        )

    # =========================================================
    # MAPPING
    # =========================================================

    def _map_to_question(
        self,
        item: GeneratedSQLQuestion,
        provenance: QuestionProvenance | None = None,
        source_difficulty: int | None = None,
    ) -> Question:

        return Question(
            id=str(uuid.uuid4()),
            area=InterviewArea.TECH_DATABASE,
            type=QuestionType.DATABASE,
            prompt=item.prompt,
            difficulty=map_corpus_difficulty(source_difficulty),
            reference_solution=item.reference_query,
            expected_ordered=False,
            db_schema=self._db.get_schema_sql(),
            db_seed_data=self._db.get_seed_sql(),
            provenance=provenance,
            sql_test_cases=[
                SQLTestCase(
                    id=f"tc_{i}",
                    expected_query=tc.expected_query,
                    ordered=tc.ordered,
                )
                for i, tc in enumerate(item.test_cases)
            ],
        )
