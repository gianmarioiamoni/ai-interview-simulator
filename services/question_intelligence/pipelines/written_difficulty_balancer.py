# services/question_intelligence/pipelines/written_difficulty_balancer.py

from typing import List

from domain.contracts.question.question import Question, QuestionDifficulty


class WrittenDifficultyBalancer:
    """
    Selects a balanced subset of questions by difficulty tier.

    Target distribution: 20% EASY / 60% MEDIUM / 20% HARD.
    Falls back to filling remaining slots with any available question when
    one or more buckets are under-represented.
    """

    _TARGET_RATIOS: dict[QuestionDifficulty, float] = {
        QuestionDifficulty.EASY: 0.2,
        QuestionDifficulty.MEDIUM: 0.6,
        QuestionDifficulty.HARD: 0.2,
    }

    def select(
        self,
        questions: List[Question],
        total: int,
    ) -> List[Question]:
        buckets: dict[QuestionDifficulty, List[Question]] = {
            QuestionDifficulty.EASY: [],
            QuestionDifficulty.MEDIUM: [],
            QuestionDifficulty.HARD: [],
        }

        for q in questions:
            buckets[q.difficulty].append(q)

        target = {
            diff: int(total * ratio)
            for diff, ratio in self._TARGET_RATIOS.items()
        }

        selected: List[Question] = []

        for diff, count in target.items():
            selected.extend(buckets[diff][:count])

        if len(selected) < total:
            remaining = [q for q in questions if q not in selected]
            selected.extend(remaining[: total - len(selected)])

        return selected[:total]
