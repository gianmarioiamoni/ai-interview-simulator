# services/question_intelligence/session_variety_scorer.py

from domain.contracts.interview.interview_area import InterviewArea
from domain.contracts.interview.interview_type import InterviewType
from domain.contracts.question.question import Question, QuestionType
from domain.contracts.question.question_bank_item import QuestionBankItem
from domain.contracts.question.question_origin_type import QuestionOriginType
from domain.contracts.question.question_provenance import QuestionProvenance
from domain.contracts.user.role import Role, RoleType
from domain.contracts.user.seniority_level import SeniorityLevel
from services.question_corpus.contracts.adaptive_retrieval_context import (
    AdaptiveRetrievalContext,
)
from services.question_corpus.contracts.interview_retrieval_memory import (
    InterviewRetrievalMemory,
)
from services.question_corpus.contracts.retrieval_candidate import RetrievalCandidate
from services.question_intelligence.coverage.topic_extractor import TopicExtractor
from services.question_intelligence.semantic_deduplicator import SemanticDeduplicator
from services.planning.planner_selection_scoring_engine import (
    PlannerSelectionScoringEngine,
)
from services.planning.semantic_cluster_suppressor import SemanticClusterSuppressor
from services.question_ingestion.contracts.ingestion_metadata import IngestionMetadata


class SessionVarietyScorer:

    _SESSION_MAX_PER_TOPIC = 1
    _PROMPT_JACCARD_DUP_THRESHOLD = 0.82

    def __init__(
        self,
        topic_extractor: TopicExtractor | None = None,
        cluster_suppressor: SemanticClusterSuppressor | None = None,
        planner_scoring_engine: PlannerSelectionScoringEngine | None = None,
        semantic_deduplicator: SemanticDeduplicator | None = None,
    ) -> None:

        self._topic_extractor = (
            topic_extractor
            if topic_extractor is not None
            else TopicExtractor()
        )
        self._cluster_suppressor = (
            cluster_suppressor
            if cluster_suppressor is not None
            else SemanticClusterSuppressor()
        )
        self._planner_scoring_engine = (
            planner_scoring_engine
            if planner_scoring_engine is not None
            else PlannerSelectionScoringEngine()
        )
        self._semantic_deduplicator = (
            semantic_deduplicator
            if semantic_deduplicator is not None
            else SemanticDeduplicator()
        )

    def to_bank_item(
        self,
        candidate: RetrievalCandidate,
    ) -> QuestionBankItem:

        return self._to_bank_item(candidate)

    def filter_session_duplicates(
        self,
        pool: list[RetrievalCandidate],
        memory: InterviewRetrievalMemory,
    ) -> list[RetrievalCandidate]:

        if not memory.session_selected_prompts:
            return pool

        filtered = [
            candidate
            for candidate in pool
            if not self._is_prompt_duplicate(
                candidate.document.page_content.strip(),
                memory,
            )
        ]

        if not filtered and memory.session_selected_prompts:
            borderline = [
                candidate
                for candidate in pool
                if not self._is_semantic_duplicate(
                    candidate.document.page_content.strip(),
                    memory,
                )
            ]
            return borderline if borderline else pool

        return filtered if filtered else pool

    def variety_penalty_tuple(
        self,
        candidate: RetrievalCandidate,
        context: AdaptiveRetrievalContext,
        selected_bank_items: list[QuestionBankItem],
    ) -> tuple[int, int, int, int]:

        prompt = candidate.document.page_content.strip()
        memory = context.memory

        topic = self._topic_extractor.extract(prompt)
        topic_repeat = 1 if topic in memory.session_used_topics else 0

        semantic_dup = 1 if self._is_prompt_duplicate(prompt, memory) else 0
        cluster_penalty = (
            1
            if self._cluster_overlap(prompt, selected_bank_items)
            else 0
        )
        novelty_tier = topic_repeat

        return (topic_repeat, semantic_dup, cluster_penalty, novelty_tier)

    def apply_novelty_scoring(
        self,
        candidate: RetrievalCandidate,
        selected_bank_items: list[QuestionBankItem],
    ) -> float:

        bank_item = self._to_bank_item(candidate)
        suppressed = self._cluster_suppressor.apply_penalty(
            candidate=bank_item,
            selected_questions=selected_bank_items,
            current_score=float(bank_item.difficulty),
        )
        planner = self._planner_scoring_engine.score(
            candidate=bank_item,
            selected_questions=selected_bank_items,
        )

        return round(planner.final_score + suppressed, 4)

    def _is_prompt_duplicate(
        self,
        prompt: str,
        memory: InterviewRetrievalMemory,
    ) -> bool:

        if not memory.session_selected_prompts:
            return False

        for prior in memory.session_selected_prompts:
            if self._prompt_jaccard(prompt, prior) >= self._PROMPT_JACCARD_DUP_THRESHOLD:
                return True

        return False

    def _cluster_overlap(
        self,
        prompt: str,
        selected_bank_items: list[QuestionBankItem],
    ) -> bool:

        for item in selected_bank_items:
            if self._prompt_jaccard(prompt, item.text) >= 0.75:
                return True

        return False

    def _is_semantic_duplicate(
        self,
        prompt: str,
        memory: InterviewRetrievalMemory,
    ) -> bool:

        if self._is_prompt_duplicate(prompt, memory):
            return True

        probe = Question(
            id="session_variety_probe",
            area=InterviewArea.TECH_TECHNICAL_KNOWLEDGE,
            type=QuestionType.WRITTEN,
            prompt=prompt,
        )
        existing = [
            Question(
                id=f"session_{index}",
                area=InterviewArea.TECH_TECHNICAL_KNOWLEDGE,
                type=QuestionType.WRITTEN,
                prompt=selected,
            )
            for index, selected in enumerate(memory.session_selected_prompts)
        ]

        deduped = self._semantic_deduplicator.deduplicate([*existing, probe])

        return len(deduped) < len(existing) + 1

    def _prompt_jaccard(
        self,
        left: str,
        right: str,
    ) -> float:

        left_tokens = set(left.lower().split())
        right_tokens = set(right.lower().split())

        if not left_tokens or not right_tokens:
            return 0.0

        intersection = left_tokens.intersection(right_tokens)
        union = left_tokens.union(right_tokens)

        return len(intersection) / len(union)

    def _to_bank_item(
        self,
        candidate: RetrievalCandidate,
    ) -> QuestionBankItem:

        metadata = candidate.document.metadata
        difficulty_raw = metadata.get("difficulty", 3)

        try:
            difficulty = int(difficulty_raw)
        except (TypeError, ValueError):
            difficulty = 3

        area_value = metadata.get("area", InterviewArea.TECH_TECHNICAL_KNOWLEDGE.value)

        return QuestionBankItem(
            id=str(metadata.get("document_id", "candidate")),
            text=candidate.document.page_content,
            interview_type=InterviewType.TECHNICAL,
            role=Role(type=RoleType.BACKEND_ENGINEER),
            area=InterviewArea(area_value),
            level=SeniorityLevel.MID,
            difficulty=difficulty,
            ingestion_metadata=IngestionMetadata(
                source_name="session_variety",
                source_type="retrieval",
                dataset_version="v1",
                ingestion_timestamp="2020-01-01T00:00:00Z",
            ),
            provenance=QuestionProvenance(
                origin_type=QuestionOriginType.RETRIEVAL,
                source_name="session_variety",
                source_type="retrieval",
                dataset_version="v1",
            ),
        )
