# services/question_intelligence/mappers/runtime_question_mapper.py

import uuid

from domain.contracts.question.question import (
    Question,
    QuestionDifficulty,
    QuestionType,
)
from domain.contracts.question.generated_question import GeneratedQuestion
from domain.contracts.question.question_origin_type import QuestionOriginType
from domain.contracts.question.question_provenance import QuestionProvenance
from domain.contracts.question.question_runtime_lineage import QuestionRuntimeLineage
from domain.contracts.question.question_bank_item import QuestionBankItem
from domain.contracts.question.question_runtime_telemetry import QuestionRuntimeTelemetry

from services.question_intelligence.mappers.difficulty_mapper import map_corpus_difficulty

from services.interview_selection.assembled_question import AssembledQuestion


class RuntimeQuestionMapper:

    # =====================================================
    # RETRIEVED QUESTIONS
    # =====================================================

    def map_assembled_question(
        self,
        assembled: AssembledQuestion,
    ) -> Question:

        item = assembled.item

        runtime_lineage = QuestionRuntimeLineage(
            selection_score=assembled.selection_score,
            selection_reason=assembled.selection_reason,
            assembly_reason=assembled.assembly_reason,
            interview_stage=assembled.stage,
            planner_rationale=(assembled.score_breakdown.rationale),
        )

        runtime_telemetry = QuestionRuntimeTelemetry(
            novelty_bonus=assembled.score_breakdown.novelty_bonus,
            rarity_bonus=assembled.score_breakdown.category_rarity_bonus,
            cluster_penalty=assembled.score_breakdown.cluster_penalty,
        )


        return Question(
            id=str(uuid.uuid4()),
            area=item.area,
            type=QuestionType.WRITTEN,
            prompt=item.text,
            difficulty=self._map_difficulty(
                item.difficulty,
            ),
            provenance=item.provenance,
            runtime_lineage=runtime_lineage,
            runtime_telemetry=runtime_telemetry,
        )

    # =====================================================
    # GENERATED QUESTIONS
    # =====================================================

    def map_generated_question(
        self,
        generated: GeneratedQuestion,
        area,
    ) -> Question:

        provenance = QuestionProvenance(
            origin_type=QuestionOriginType.LLM_GENERATED,
            source_name="question_generator",
            generated_by_model="question_generator",
        )

        return Question(
            id=str(uuid.uuid4()),
            area=area,
            type=QuestionType.WRITTEN,
            prompt=generated.text,
            difficulty=self._map_difficulty(
                generated.difficulty,
            ),
            provenance=provenance,
        )

    # =====================================================
    # LEGACY RETRIEVED QUESTIONS
    # =====================================================


    def map_retrieved_bank_item(
        self,
        item: QuestionBankItem,
    ) -> Question:

        runtime_lineage = QuestionRuntimeLineage(
            selection_score=float(item.difficulty),
            selection_reason="retrieval_match",
            assembly_reason="legacy_runtime_mapping",
        )

        runtime_telemetry = QuestionRuntimeTelemetry(
            retrieval_score=float(item.difficulty),
        )

        return Question(
            id=str(uuid.uuid4()),
            area=item.area,
            type=QuestionType.WRITTEN,
            prompt=item.text,
            difficulty=self._map_difficulty(item.difficulty),
            provenance=item.provenance,
            runtime_lineage=runtime_lineage,
            runtime_telemetry=runtime_telemetry,
        )
    
    
    # =====================================================
    # HELPERS
    # =====================================================

    def _map_difficulty(
        self,
        value: int,
    ) -> QuestionDifficulty:
        return map_corpus_difficulty(value)
