# services/question_intelligence/constrained_equivalence_band.py

import hashlib

from domain.contracts.question.question_bank_item import QuestionBankItem
from services.question_corpus.contracts.adaptive_retrieval_context import (
    AdaptiveRetrievalContext,
)
from services.question_corpus.contracts.retrieval_candidate import RetrievalCandidate
from services.question_intelligence.coverage.topic_extractor import TopicExtractor
from services.question_intelligence.interview_theme_memory import (
    get_interview_theme_anchor,
)
from services.question_intelligence.session_variety_scorer import SessionVarietyScorer

DECONVERGENCE_AREAS: frozenset[str] = frozenset(
    {
        "technical_background",
        "technical_technical_knowledge",
        "technical_case_study",
        "technical_coding",
        "technical_database",
    }
)

EQUIVALENCE_BAND_PCT = 0.05

FRESH_START_MAX_TARGET_DISTANCE = 1

KNOWLEDGE_FRESH_START_AREA = "technical_technical_knowledge"

_CROSS_INTERVIEW_PICK_COUNTS: dict[str, int] = {}


def reset_cross_interview_pick_counts() -> None:

    _CROSS_INTERVIEW_PICK_COUNTS.clear()


class ConstrainedEquivalenceBand:

    def __init__(
        self,
        variety_scorer: SessionVarietyScorer | None = None,
        topic_extractor: TopicExtractor | None = None,
        max_allowed_jump: int = 2,
        band_pct: float = EQUIVALENCE_BAND_PCT,
    ) -> None:

        self._variety_scorer = (
            variety_scorer
            if variety_scorer is not None
            else SessionVarietyScorer()
        )
        self._topic_extractor = (
            topic_extractor
            if topic_extractor is not None
            else TopicExtractor()
        )
        self._max_allowed_jump = max_allowed_jump
        self._band_pct = band_pct

    def is_eligible(self, target_area: str) -> bool:

        return target_area in DECONVERGENCE_AREAS

    def diversify_pick(
        self,
        pool: list[RetrievalCandidate],
        best: RetrievalCandidate,
        target: int,
        previous_difficulty: int | None,
        context: AdaptiveRetrievalContext,
        rank_index: dict[int, int],
        selected_bank_items: list[QuestionBankItem],
    ) -> RetrievalCandidate:

        if not self.is_eligible(context.target_area):
            return best

        band_anchor = best

        if (
            self._is_fresh_start(
                context=context,
                selected_bank_items=selected_bank_items,
            )
            and context.target_area == KNOWLEDGE_FRESH_START_AREA
        ):
            band_anchor = max(
                pool,
                key=lambda candidate: self._candidate_score(candidate),
            )

        best_tier = self._adaptive_tier(
            candidate=band_anchor,
            target=target,
            previous_difficulty=previous_difficulty,
        )

        equivalents = self._collect_equivalents(
            pool=pool,
            best=band_anchor,
            best_tier=best_tier,
            target=target,
            previous_difficulty=previous_difficulty,
            context=context,
            selected_bank_items=selected_bank_items,
        )

        if len(equivalents) < 2:
            return best

        return self._pick_diversity_best(
            equivalents=equivalents,
            context=context,
            rank_index=rank_index,
            selected_bank_items=selected_bank_items,
        )

    def _collect_equivalents(
        self,
        pool: list[RetrievalCandidate],
        best: RetrievalCandidate,
        best_tier: tuple[int, int],
        target: int,
        previous_difficulty: int | None,
        context: AdaptiveRetrievalContext,
        selected_bank_items: list[QuestionBankItem],
    ) -> list[RetrievalCandidate]:

        tier_matches = [
            candidate
            for candidate in pool
            if self._matches_adaptive_tier(
                candidate=candidate,
                best_tier=best_tier,
                target=target,
                previous_difficulty=previous_difficulty,
                context=context,
                selected_bank_items=selected_bank_items,
            )
        ]

        if not tier_matches:
            return []

        if self._is_fresh_start(
            context=context,
            selected_bank_items=selected_bank_items,
        ):
            anchor_score = max(
                self._candidate_score(candidate)
                for candidate in tier_matches
            )
        else:
            anchor_score = self._candidate_score(best)

        if self._is_fresh_start(
            context=context,
            selected_bank_items=selected_bank_items,
        ):
            return tier_matches

        floor = self._score_floor(anchor_score)

        return [
            candidate
            for candidate in tier_matches
            if self._candidate_score(candidate) >= floor
        ]

    def _matches_adaptive_tier(
        self,
        candidate: RetrievalCandidate,
        best_tier: tuple[int, int],
        target: int,
        previous_difficulty: int | None,
        context: AdaptiveRetrievalContext,
        selected_bank_items: list[QuestionBankItem],
    ) -> bool:

        tier = self._adaptive_tier(
            candidate=candidate,
            target=target,
            previous_difficulty=previous_difficulty,
        )

        if self._is_fresh_start(
            context=context,
            selected_bank_items=selected_bank_items,
        ):
            return (
                tier[0] <= FRESH_START_MAX_TARGET_DISTANCE
                and tier[1] == best_tier[1]
            )

        return tier == best_tier

    def _pick_diversity_best(
        self,
        equivalents: list[RetrievalCandidate],
        context: AdaptiveRetrievalContext,
        rank_index: dict[int, int],
        selected_bank_items: list[QuestionBankItem],
    ) -> RetrievalCandidate:

        if self._is_fresh_start(
            context=context,
            selected_bank_items=selected_bank_items,
        ):
            return self._pick_fresh_start_equivalent(
                equivalents=equivalents,
                context=context,
            )

        used_ids = self._historical_usage_ids(context)

        def diversity_key(candidate: RetrievalCandidate) -> tuple:

            document_id = str(candidate.document.metadata.get("document_id", ""))
            historical = 1 if document_id in used_ids else 0
            variety = self._variety_scorer.variety_penalty_tuple(
                candidate=candidate,
                context=context,
                selected_bank_items=selected_bank_items,
            )
            novelty = -self._variety_scorer.apply_novelty_scoring(
                candidate=candidate,
                selected_bank_items=selected_bank_items,
            )

            return (historical, *variety, novelty, rank_index[id(candidate)])

        equivalents.sort(key=diversity_key)
        return equivalents[0]

    def _is_fresh_start(
        self,
        context: AdaptiveRetrievalContext,
        selected_bank_items: list[QuestionBankItem],
    ) -> bool:

        if selected_bank_items:
            return False

        if context.already_used_question_ids:
            return False

        memory = context.memory

        return (
            not memory.asked_question_ids
            and not memory.session_selected_prompts
            and not memory.session_used_topics
        )

    def _pick_fresh_start_equivalent(
        self,
        equivalents: list[RetrievalCandidate],
        context: AdaptiveRetrievalContext,
    ) -> RetrievalCandidate:

        if len(equivalents) == 1:
            return equivalents[0]

        theme = get_interview_theme_anchor(context.memory) or ""
        query = context.retrieval_query or ""
        seed = f"{context.current_role}|{context.seniority}|{theme}|{query}"
        used_ids = self._historical_usage_ids(context)
        target = context.target_difficulty or 3
        previous_difficulty = (
            context.memory.difficulty_history[-1]
            if context.memory.difficulty_history
            else None
        )

        def prefix_key(candidate: RetrievalCandidate) -> tuple:

            document_id = str(candidate.document.metadata.get("document_id", ""))
            tier = self._adaptive_tier(
                candidate=candidate,
                target=target,
                previous_difficulty=previous_difficulty,
            )
            historical = 1 if document_id in used_ids else 0
            variety = self._variety_scorer.variety_penalty_tuple(
                candidate=candidate,
                context=context,
                selected_bank_items=[],
            )

            return (
                historical,
                tier[0],
                tier[1],
                *variety,
            )

        if context.target_area == KNOWLEDGE_FRESH_START_AREA:

            def knowledge_tie_break_key(candidate: RetrievalCandidate) -> tuple:

                document_id = str(candidate.document.metadata.get("document_id", ""))
                tier = self._adaptive_tier(
                    candidate=candidate,
                    target=target,
                    previous_difficulty=previous_difficulty,
                )
                historical = 1 if document_id in used_ids else 0
                variety = self._variety_scorer.variety_penalty_tuple(
                    candidate=candidate,
                    context=context,
                    selected_bank_items=[],
                )

                return (
                    historical,
                    tier[0],
                    tier[1],
                    *variety,
                    _CROSS_INTERVIEW_PICK_COUNTS.get(document_id, 0),
                    -self._candidate_score(candidate),
                    document_id,
                )

            pick = min(equivalents, key=knowledge_tie_break_key)
        else:
            best_prefix = min(prefix_key(candidate) for candidate in equivalents)
            bucket = [
                candidate
                for candidate in equivalents
                if prefix_key(candidate) == best_prefix
            ]

            if len(bucket) > 1:
                topics_in_bucket = list(
                    dict.fromkeys(
                        self._topic_extractor.extract(
                            candidate.document.page_content.strip(),
                        )
                        for candidate in bucket
                    ),
                )

                if len(topics_in_bucket) > 1:
                    topic_index = self._rotation_index(seed, len(topics_in_bucket))
                    target_topic = topics_in_bucket[topic_index]
                    bucket = [
                        candidate
                        for candidate in bucket
                        if self._topic_extractor.extract(
                            candidate.document.page_content.strip(),
                        )
                        == target_topic
                    ]

            def tie_break_key(candidate: RetrievalCandidate) -> tuple:

                document_id = str(candidate.document.metadata.get("document_id", ""))

                return (
                    self._rotation_index(f"{seed}|{document_id}", 10_000),
                    -self._candidate_score(candidate),
                    document_id,
                )

            pick = min(bucket, key=tie_break_key)
        document_id = str(pick.document.metadata.get("document_id", ""))

        if context.target_area == KNOWLEDGE_FRESH_START_AREA and document_id:
            _CROSS_INTERVIEW_PICK_COUNTS[document_id] = (
                _CROSS_INTERVIEW_PICK_COUNTS.get(document_id, 0) + 1
            )

        return pick

    def _rotation_index(
        self,
        seed: str,
        size: int,
    ) -> int:

        digest = hashlib.sha256(seed.encode()).hexdigest()
        return int(digest[:12], 16) % size

    def _historical_usage_ids(
        self,
        context: AdaptiveRetrievalContext,
    ) -> set[str]:

        return {
            *context.memory.asked_question_ids,
            *context.already_used_question_ids,
        }

    def _candidate_score(
        self,
        candidate: RetrievalCandidate,
    ) -> float:

        return float(candidate.adaptive_score or candidate.final_score)

    def _score_floor(
        self,
        best_score: float,
    ) -> float:

        margin = max(0.01, best_score * self._band_pct)
        return best_score - margin

    def _adaptive_tier(
        self,
        candidate: RetrievalCandidate,
        target: int,
        previous_difficulty: int | None,
    ) -> tuple[int, int]:

        difficulty = self._candidate_difficulty(candidate)

        if difficulty is None:
            return (999, 1)

        target_distance = abs(difficulty - target)
        jump = (
            abs(difficulty - previous_difficulty)
            if previous_difficulty is not None
            else 0
        )
        spike = 0 if jump <= self._max_allowed_jump else 1

        return (target_distance, spike)

    def _candidate_difficulty(
        self,
        candidate: RetrievalCandidate,
    ) -> int | None:

        raw = candidate.document.metadata.get("difficulty")

        try:
            return int(raw)
        except (TypeError, ValueError):
            return None
