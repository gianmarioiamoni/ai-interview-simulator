# services/question_intelligence/quality/interview_question_quality_filter.py

import re

from services.question_intelligence.quality.contracts.interview_question_quality_result import InterviewQuestionQualityResult
from services.question_intelligence.quality.contracts.quality_decision import QualityDecision


class InterviewQuestionQualityFilter:

    # =====================================================
    # CONFIG
    # =====================================================

    APPROVE_THRESHOLD = 0.7

    REVIEW_THRESHOLD = 0.45

    # =====================================================
    # POSITIVE SIGNALS
    # =====================================================

    POSITIVE_PATTERNS = [
        r"how would you",
        r"design",
        r"implement",
        r"trade[- ]?off",
        r"scalability",
        r"distributed",
        r"architecture",
        r"production",
        r"failure",
        r"optimi[sz]e",
        r"high availability",
        r"fault tolerance",
        r"rate limiter",
        r"load balancer",
        r"replication",
        r"partitioning",
        r"caching",
    ]

    # =====================================================
    # NEGATIVE SIGNALS
    # =====================================================

    NEGATIVE_PATTERNS = [
        r"^how to\s",
        r"^introduction to\s",
        r"^overview of\s",
        r"^summary of\s",
        r"best practices",
        r"tips and tricks",
        r"cheat sheet",
        r"tutorial",
        r"step by step",
    ]

    # =====================================================
    # CONTEXT DEPENDENCY
    # =====================================================

    CONTEXT_DEPENDENT_PATTERNS = [
        r"^when to\s",
        r"^when should",
        r"this approach",
        r"this system",
        r"the cache",
        r"the database",
        r"the above",
        r"the following",
        r"this architecture",
        r"this design",
    ]

    # =====================================================
    # LOW SIGNAL / WEAK QUESTIONS
    # =====================================================

    WEAK_PATTERNS = [
        r"what is",
        r"define",
        r"briefly explain",
    ]

    # =====================================================
    # PUBLIC
    # =====================================================

    def evaluate(
        self,
        text: str,
    ) -> InterviewQuestionQualityResult:

        normalized = text.strip().lower()

        score = 0.0

        quality_signals: list[str] = []

        penalties: list[str] = []

        # -------------------------------------------------
        # POSITIVE SIGNALS
        # -------------------------------------------------

        for pattern in self.POSITIVE_PATTERNS:

            if re.search(
                pattern,
                normalized,
                flags=re.IGNORECASE,
            ):

                score += 0.12

                quality_signals.append(pattern)

        # -------------------------------------------------
        # NEGATIVE SIGNALS
        # -------------------------------------------------

        for pattern in self.NEGATIVE_PATTERNS:

            if re.search(
                pattern,
                normalized,
                flags=re.IGNORECASE,
            ):

                score -= 0.25

                penalties.append(pattern)

        # -------------------------------------------------
        # WEAK SIGNALS
        # -------------------------------------------------

        for pattern in self.WEAK_PATTERNS:

            if re.search(
                pattern,
                normalized,
                flags=re.IGNORECASE,
            ):

                score -= 0.1

                penalties.append(pattern)

        # -------------------------------------------------
        # CONTEXT DEPENDENCY
        # -------------------------------------------------

        is_context_dependent = False

        for pattern in self.CONTEXT_DEPENDENT_PATTERNS:

            if re.search(
                pattern,
                normalized,
                flags=re.IGNORECASE,
            ):

                score -= 0.35

                penalties.append(pattern)

                is_context_dependent = True

        # -------------------------------------------------
        # INTERVIEW STYLE
        # -------------------------------------------------

        is_interview_style = (
            "?" in normalized
            or normalized.startswith("how")
            or normalized.startswith("design")
            or normalized.startswith("implement")
            or normalized.startswith("explain")
        )

        if is_interview_style:
            score += 0.15

        else:
            score -= 0.2

            penalties.append("non_interview_style")

        # -------------------------------------------------
        # ACTIONABILITY
        # -------------------------------------------------

        actionable_terms = [
            "design",
            "implement",
            "optimize",
            "scale",
            "debug",
            "improve",
            "handle",
        ]

        is_actionable = any(term in normalized for term in actionable_terms)

        if is_actionable:
            score += 0.15

        # -------------------------------------------------
        # SHORT FRAGMENT PENALTY
        # -------------------------------------------------

        if len(normalized.split()) < 5:

            score -= 0.25

            penalties.append("too_short")

        # -------------------------------------------------
        # NORMALIZATION
        # -------------------------------------------------

        score = round(
            max(0.0, min(score, 1.0)),
            2,
        )

        # -------------------------------------------------
        # DECISION
        # -------------------------------------------------

        decision = self._make_decision(
            score=score,
            is_context_dependent=is_context_dependent,
        )

        # -------------------------------------------------
        # RESULT
        # -------------------------------------------------

        return InterviewQuestionQualityResult(
            decision=decision,
            score=score,
            quality_signals=quality_signals,
            penalties=penalties,
            is_context_dependent=is_context_dependent,
            is_interview_style=is_interview_style,
            is_actionable=is_actionable,
        )

    # =====================================================
    # INTERNALS
    # =====================================================

    def _make_decision(
        self,
        score: float,
        is_context_dependent: bool,
    ) -> QualityDecision:

        if is_context_dependent:
            return QualityDecision.REJECT

        if score >= self.APPROVE_THRESHOLD:
            return QualityDecision.APPROVE

        if score >= self.REVIEW_THRESHOLD:
            return QualityDecision.REVIEW

        return QualityDecision.REJECT
