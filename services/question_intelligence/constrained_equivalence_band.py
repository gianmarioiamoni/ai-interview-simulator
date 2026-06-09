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

        best_tier = self._adaptive_tier(
            candidate=best,
            target=target,
            previous_difficulty=previous_difficulty,
        )

        equivalents = self._collect_equivalents(
            pool=pool,
            best=best,
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

        ordered = sorted(
            equivalents,
            key=lambda candidate: (
                -self._candidate_score(candidate),
                str(candidate.document.metadata.get("document_id", "")),
            ),
        )

        theme = get_interview_theme_anchor(context.memory) or ""
        query = context.retrieval_query or ""
        seed = (
            f"{context.current_role}|{context.seniority}|{theme}|{query}"
        )

        topics = [
            (
                candidate,
                self._topic_extractor.extract(
                    candidate.document.page_content.strip(),
                ),
            )
            for candidate in ordered
        ]
        unique_topics = list(dict.fromkeys(topic for _, topic in topics))

        if len(unique_topics) > 1:
            topic_index = self._rotation_index(seed, len(unique_topics))
            target_topic = unique_topics[topic_index]
            bucket = [
                candidate
                for candidate, topic in topics
                if topic == target_topic
            ]
            pick_index = self._rotation_index(f"{seed}|topic", len(bucket))
            return bucket[pick_index]

        pick_index = self._rotation_index(seed, len(ordered))
        return ordered[pick_index]

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
